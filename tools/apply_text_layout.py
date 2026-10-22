"""Apply bound PlayBook layout records without changing visible text or other controls."""
from pathlib import Path
import sys,json,struct,collections
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','src','lib')]
import font_poc as c
from build_locale import checked_archive
from translate.celfid import decompress_chunked,recompress_chunked
from bundle_resource import overlay_segments

def rewrite_bound(blob,entries):
 n=struct.unpack_from('<I',blob)[0];end=4+n*12;c.require(n>0 and end+4<=len(blob),'FPB table bounds')
 size=struct.unpack_from('<I',blob,end)[0];pool=blob[end+4:end+4+size];tail=blob[end+4+size:];rows=[struct.unpack_from('<III',blob,4+j*12) for j in range(n)];edits={q['record_index']:q for q in entries};c.require(len(edits)==len(entries),'duplicate record edits')
 newpool=bytearray();newrows=[];cursor=0
 for j,(key,start,length) in enumerate(rows):
  c.require(cursor<=start and start+length<=len(pool),'overlapping FPB record')
  newpool.extend(pool[cursor:start]);newstart=len(newpool);raw=pool[start:start+length]
  if j in edits:
   q=edits[j];c.require((key,start,length)==(q['key'],q['offset'],q['length']) and raw==bytes.fromhex(q['old_hex']),'bound record baseline mismatch')
   c.require(q['previous_target'].replace('$n','')==q['target'].replace('$n',''),'layout changed content/controls')
   raw=bytes.fromhex(q['new_hex'])
  newpool.extend(raw);newrows.append((key,newstart,len(raw)));cursor=start+length
 newpool.extend(pool[cursor:]);result=struct.pack('<I',n)+b''.join(struct.pack('<III',*q) for q in newrows)+struct.pack('<I',len(newpool))+newpool+tail
 c.require([q[0] for q in rows]==[q[0] for q in newrows],'FPB key order changed');return result

def apply(file,ship,profile,out):
 c.require(c.file_digest(ship)==profile['base_ship_sha256'],'SHIP baseline mismatch');c.require(c.file_digest(file)==profile['base_file_sha256'],'FILE baseline mismatch');_,se=c.archive_entries(ship);_,fe=c.archive_entries(file);s=dict(se);f=dict(fe);bundle=decompress_chunked(f['celfid.lix']);groups=collections.defaultdict(list)
 for q in profile['entries']:groups[q['resource']].append(q)
 overrides={};segments=[];receipts=[]
 for name,qs in groups.items():
  old=s[name];record_edits=[q for q in qs if 'record_index' in q];new=rewrite_bound(old,record_edits) if record_edits else old
  from apply_ui_layout_copies import same_size_overlay
  fixed=[q for q in qs if 'record_index' not in q]
  if fixed:
   for q in fixed:c.require(q['previous_target'].replace('$n','')==q['target'].replace('$n','') and q['previous_target'].count('$n')==q['target'].count('$n'),'fixed layout changed content/control count')
   new=same_size_overlay(new,[dict(offset=q['offset'],original=bytes.fromhex(q['old_hex']),modified=bytes.fromhex(q['new_hex'])) for q in fixed])
  count=bundle.count(old)
  c.require(not count or len(old)==len(new),'resized startup cache requires explicit size record profile')
  start=0
  for j in range(count):
   at=bundle.index(old,start);segments.append(dict(label=name,offset=at,original=old,modified=new));start=at+len(old)
  overrides[name.lower()]=new;receipts.append({'resource':name,'baseline_sha256':c.digest(old),'modified_sha256':c.digest(new),'fields':len(qs),'cache_copies':count})
 out.mkdir(parents=True,exist_ok=False)
 overrides[se[0][0].lower()]=c.manifest_overlay(se[0][1],{n:len(raw) for n,raw in overrides.items()});checked_archive(ship,out/'SHIP.AFS',overrides)
 if segments:
  modified,proof=overlay_segments(bundle,segments,expected_sha256=c.digest(bundle));compressed=recompress_chunked(modified);c.require(decompress_chunked(compressed)==modified,'cache roundtrip');o={'celfid.lix':compressed};o[fe[0][0].lower()]=c.manifest_overlay(fe[0][1],{n:len(raw) for n,raw in o.items()});checked_archive(file,out/'FILE.AFS',o)
 else:
  import shutil;shutil.copyfile(file,out/'FILE.AFS');proof=[]
 (out/'text-layout-build.json').write_text(json.dumps({'resources':receipts,'cache':proof,'scanned_fields':profile['scanned_fields'],'changed_fields':len(profile['entries'])},indent=2)+'\n','utf8')
 print('TEXT_LAYOUT_AFS_PASS scanned='+str(profile['scanned_fields'])+' fields='+str(len(profile['entries']))+' resources='+str(len(groups))+' cache_copies='+str(len(segments))+' visible_content_controls_preserved=true')
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('file','ship','profile','out'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();apply(a.file,a.ship,json.loads(a.profile.read_text('utf8')),a.out)
