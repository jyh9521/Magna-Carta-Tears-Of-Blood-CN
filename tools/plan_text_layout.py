from pathlib import Path
import sys,json,re,collections,struct
sys.path[:0]=['tools','lib','src'];import font_poc as c
from research_inventory import font_data
from localization.text import MappedEncoder
from text_layout import wrap,CLOSING
import argparse
p=argparse.ArgumentParser(description='Plan metric-based PlayBook layout from reviewed translation batches')
for name in ('locale-dir','font','map','file','ship','config','out'):p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();r=Path(__file__).resolve().parents[1];cfg=json.loads(a.config.read_text('utf8'));inv={'terms':cfg['protected_terms']};entries={}
for p in a.locale_dir.glob('*.json'):
 b=json.loads(p.read_text('utf8'))
 for q in b.get('entries',[]):
  if q.get('status')=='reviewed' and isinstance(q.get('target'),str):entries[q['id']]={**q,'batch':str(p.resolve())}
font=a.font.read_bytes();i=font_data(font);m=json.loads(a.map.read_text('utf8'));enc=MappedEncoder(m['entries'],font_tables=i);lookup={q['character']:q['glyph'] for q in m['entries']}
def measure(text):
 text=re.sub(r'\$D\d{2}','',text)
 return sum(font[i['metrics_start']+(lookup[ch] if ch in lookup else ord(ch))] if ch in lookup or ord(ch)<128 else 18 for ch in text)
ship=dict(c.archive_entries(a.ship)[1]);planned=[];unbound=[];risks=[]
for q in entries.values():
 t=q['target'];at=q['id'].split('/');issues=[]
 if '$n' in t:
  if any(line and line[0] in CLOSING for line in t.split('$n')):issues.append('explicit-leading-punctuation')
  if any(term[:j]+'$n'+term[j:] in t for term in inv['terms'] for j in range(1,len(term))):issues.append('explicit-split-phrase')
 if issues:risks.append({'id':q['id'],'issues':issues})
 # Apply metric reflow to PlayBook bodies; short names/options without breaks are unchanged.
 if len(at)<2 or not at[1].endswith('.fpb') or '$' in t.replace('$n','') or '\x00' in t or not t.strip():continue
 target=wrap(t,measure,cfg['dialogue_width'],inv['terms'])
 if target==t:continue
 blob=ship[at[1]];n=struct.unpack_from('<I',blob)[0];pool_at=4+n*12+4;pool_size=struct.unpack_from('<I',blob,4+n*12)[0];pool=blob[pool_at:pool_at+pool_size]
 raw=enc.encode_characters(t);new=enc.encode_characters(target);matches=[]
 for j in range(n):
  key,start,size=struct.unpack_from('<III',blob,4+12*j)
  body=pool[start:start+size]
  if body.rstrip(b'\0')==raw:matches.append((j,key,start,size,len(body)-len(raw)))
 if len(matches)>1 and '/seq/' in q['id']:
  desired=int(q['id'].rsplit('/',1)[1]);matches=[x for x in matches if x[1]==desired]
 if len(matches)!=1:unbound.append({'id':q['id'],'matches':matches,'target':t});continue
 j,key,start,size,padding=matches[0];planned.append({'id':q['id'],'source_sha256':q['source_sha256'],'resource':at[1],'record_index':j,'key':key,'offset':start,'length':size,'old_hex':(raw+bytes(padding)).hex(),'new_hex':(new+bytes(padding)).hex(),'previous_target':t,'target':target,'width':cfg['dialogue_width'],'lines':target.split('$n')})
for override in cfg.get('fixed_overrides',[]):
 q=entries[override['id']];old=q['target'];new=override['target'];c.require(old.replace('$n','')==new.replace('$n','') and old.count('$n')==new.count('$n'),'fixed override changes text/control count')
 name=q['id'].split('/')[1];blob=ship[name];before=enc.encode_characters(old);after=enc.encode_characters(new);c.require(len(before)==len(after) and blob.count(before)==1,'fixed override not uniquely bound')
 planned.append(dict(id=q['id'],resource=name,offset=blob.index(before),length=len(before),old_hex=before.hex(),new_hex=after.hex(),previous_target=old,target=new,lines=new.split('$n'),source_sha256=q['source_sha256'],width=None))
profile={'schema':1,'locale':cfg['locale'],'scanned_fields':len(entries),'width':cfg['dialogue_width'],'width_status':'conservative dialogue content budget; not all UI windows share this width','entries':planned,'explicit_risks_all_backends':risks,'unbound':unbound,'terms':inv['terms'],'base_file_sha256':c.file_digest(a.file),'base_ship_sha256':c.file_digest(a.ship)}
a.out.write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n','utf8');print('SCAN',len(entries),'planned',len(planned),'unbound',len(unbound),'explicit',len(risks));print(unbound[:4])
