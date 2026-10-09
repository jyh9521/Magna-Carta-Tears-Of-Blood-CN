"""Read-only fixed region records; full fields include text missed by NUL heuristics."""
from __future__ import annotations
import argparse,json,struct,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from extract_strings import field
from audit_decode_quarantine import checked_span

PROFILES={
 '.itm':dict(kind=25,stride=594,text=[(4,255),(331,255)]),
 '.abi':dict(kind=7,stride=192,text=[(4,40),(64,128)]),
 '.sgi':dict(kind=22,stride=251,text=[(4,100),(184,67)]),
 '.nod':dict(kind=11,stride=132,text=[(4,25),(45,87)]),
 '.dod':dict(kind=14,stride=564,text=[(4,256),(308,256)]),
}


def parse_records(blob,ext):
 core.require(ext in PROFILES,'unsupported region record extension');profile=PROFILES[ext]
 core.require(len(blob)>=8,'record header truncated');count,kind=struct.unpack_from('<II',blob)
 core.require(kind==profile['kind'] and len(blob)==8+count*profile['stride'],'record geometry mismatch')
 result=[]
 for index in range(count):
  start=8+index*profile['stride'];fields=[];cursor=start;opaque=[]
  for n,(relative,size) in enumerate(profile['text']):
   off=start+relative;slot=blob[off:off+size];nul=slot.find(b'\0')
   core.require(nul>=0 and not any(slot[nul:]),'text termination or padding mismatch')
   if off>cursor:opaque.append(dict(offset=cursor,bytes=off-cursor,sha256=core.digest(blob[cursor:off]),semantic='unverified'))
   fields.append(dict(field_index=n,offset=off,slot_bytes=size,slot_sha256=core.digest(slot),raw=slot[:nul]));cursor=off+size
  end=start+profile['stride']
  if cursor<end:opaque.append(dict(offset=cursor,bytes=end-cursor,sha256=core.digest(blob[cursor:end]),semantic='unverified'))
  result.append(dict(index=index,offset=start,size=profile['stride'],key=struct.unpack_from('<I',blob,start)[0],sha256=core.digest(blob[start:end]),text_fields=fields,opaque=opaque))
 return result


def context(row,records):
 start=row['offset'];end=start+row['source_bytes']
 for record in records:
  for f in record['text_fields']:
   if f['offset']<=start<=end<=f['offset']+len(f['raw']):
    return dict(classification='exact-text-field' if start==f['offset'] and end==f['offset']+len(f['raw']) else 'text-subspan',record_index=record['index'],field_index=f['field_index'])
  for m in record['opaque']:
   if m['offset']<=start<end<=m['offset']+m['bytes']:return dict(classification='opaque-metadata',record_index=record['index'])
 return dict(classification='boundary-crossing-or-unresolved')


def audit(corpus_path,ship,out):
 before=core.file_digest(corpus_path);expected=json.loads((ROOT/'docs/EXTRACTION_COVERAGE.json').read_text('utf8'))['verified_archive_hashes']['SHIP.AFS']
 core.require(core.file_digest(ship)==expected,'SHIP identity mismatch')
 corpus=json.loads(corpus_path.read_text('utf8'));a=Afs.open(ship);names=filename_toc(a)
 output=[];inventory=[];links=[];missing=[];counts=Counter()
 with ship.open('rb') as stream:
  for resource in corpus['resources']:
   name=resource['resource'].split('/',1)[1];ext=Path(name).suffix
   if ext not in PROFILES:continue
   blob=a.read_entry(names.index(name),stream);core.require(core.digest(blob)==resource['sha256'] and len(blob)==resource['size'],'resource identity mismatch')
   parsed=parse_records(blob,ext);counts['resources']+=1;counts['records']+=len(parsed)
   old_exact={(e['offset'],e['source_bytes'],e['source_sha256']):e['id'] for e in resource['entries']}
   for record in parsed:
    ids=[]
    for f in record['text_fields']:
     identity=resource['resource']+f"/record-index/{record['index']}/field/{f['field_index']}"
     row=field(identity,f['raw'],f['offset'],resource=resource['resource'],resource_sha256=resource['sha256'],record_index=record['index'],record_key=record['key'],field_index=f['field_index'],slot_bytes=f['slot_bytes'],slot_sha256=f['slot_sha256'],editable=False,reinsertion_approved=False,semantic='visible-or-identifier-unverified')
     previous=old_exact.get((row['offset'],row['source_bytes'],row['source_sha256']))
     row['previous_exact_id']=previous;output.append(row);ids.append(identity)
     if previous is None:
      off=row['offset'];end=off+row['source_bytes'];covered=set()
      for prior in resource['entries']:
       covered.update(range(max(off,prior['offset']),min(end,prior['offset']+prior['source_bytes'])))
      coverage='empty' if not f['raw'] else 'no-prior-text-byte-overlap' if not covered else 'partial-prior-text-byte-overlap' if len(covered)<row['source_bytes'] else 'prior-byte-union-covered'
      missing.append(dict(id=identity,resource=resource['resource'],offset=row['offset'],source_bytes=row['source_bytes'],source_sha256=row['source_sha256'],empty=not f['raw'],prior_byte_coverage=coverage))
    inventory.append(dict(resource=resource['resource'],index=record['index'],key=record['key'],offset=record['offset'],size=record['size'],sha256=record['sha256'],fields=ids,opaque=record['opaque']))
   for old in resource['entries']:
    checked_span(blob,old);links.append(dict(old_id=old['id'],source_sha256=old['source_sha256'],**context(old,parsed),editable=False))
 summary=dict(schema=1,source_corpus_sha256=before,ship_sha256=expected,**counts,text_fields=len(output),
  nonempty_fields=sum(bool(r['source_bytes']) for r in output),empty_fields=sum(not r['source_bytes'] for r in output),decode_failures=sum(r['decode']!='strict' for r in output),
  previous_fields=len(links),previous_contexts=dict(sorted(Counter(r['classification'] for r in links).items())),
  fields_without_previous_exact_view=len(missing),nonempty_without_previous_exact_view=sum(not r['empty'] for r in missing),
  missing_prior_byte_coverage=dict(sorted(Counter(r['prior_byte_coverage'] for r in missing).items())),
  missing_by_extension=dict(sorted(Counter(Path(r['resource']).suffix for r in missing if not r['empty']).items())),
  complete_game_text=False,source_modified=False,translation_gate='coverage-audit-pending')
 out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
 for name,value in [('text-fields.json',output),('records.json',inventory),('previous-contexts.json',links),('missing-full-fields.json',missing),('summary.json',summary)]:
  p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8');core.require(json.loads(p.read_text('utf8'))==value,'output reopen mismatch')
 core.require(core.file_digest(ship)==expected and core.file_digest(corpus_path)==before,'input changed')
 return summary

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['corpus','ship','out']:p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();print(json.dumps(audit(a.corpus,a.ship,a.out),sort_keys=True))
