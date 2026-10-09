"""Read-only POD block audit; observed 24 text slots, prefix meaning unverified."""
from __future__ import annotations
import argparse,json,struct,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from extract_strings import field
from audit_decode_quarantine import checked_span,reading
from audit_region_records import context
OFFSETS=tuple([20+512*i for i in range(10)]+[5144]+[5656+512*i for i in range(4)]+[7708+512*i for i in range(4)]+[9756]+[10268+512*i for i in range(4)])


def parse_block(blob):
 core.require(len(blob)==12328,'POD block size mismatch')
 core.require(struct.unpack_from('<III',blob)==(31,1,0),'POD observed prefix mismatch')
 fields=[];opaque=[];cursor=0
 for index,off in enumerate(OFFSETS):
  if off>cursor:opaque.append(dict(offset=cursor,bytes=off-cursor,sha256=core.digest(blob[cursor:off]),semantic='unverified'))
  slot=blob[off:off+512];nul=slot.find(b'\0');core.require(nul>=0 and not any(slot[nul:]),'POD text termination or padding mismatch')
  fields.append(dict(field_index=index,offset=off,slot_bytes=512,slot_sha256=core.digest(slot),raw=slot[:nul]));cursor=off+512
 if cursor<len(blob):opaque.append(dict(offset=cursor,bytes=len(blob)-cursor,sha256=core.digest(blob[cursor:]),semantic='unverified'))
 return dict(index=0,text_fields=fields,opaque=opaque)


def audit(corpus_path,ship,out):
 before=core.file_digest(corpus_path);expected=json.loads((ROOT/'docs/EXTRACTION_COVERAGE.json').read_text('utf8'))['verified_archive_hashes']['SHIP.AFS']
 core.require(core.file_digest(ship)==expected,'SHIP identity mismatch')
 corpus=json.loads(corpus_path.read_text('utf8'));a=Afs.open(ship);names=filename_toc(a);output=[];links=[];inventory=[]
 with ship.open('rb') as stream:
  for resource in corpus['resources']:
   if not resource['resource'].endswith('.pod'):continue
   blob=a.read_entry(names.index(resource['resource'].split('/',1)[1]),stream)
   core.require(len(blob)==resource['size'] and core.digest(blob)==resource['sha256'],'resource identity mismatch')
   parsed=parse_block(blob);previous={(e['offset'],e['source_bytes'],e['source_sha256']):e['id'] for e in resource['entries']}
   for f in parsed['text_fields']:
    row=field(resource['resource']+f"/field/{f['field_index']}",f['raw'],f['offset'],resource=resource['resource'],resource_sha256=resource['sha256'],
      field_index=f['field_index'],slot_bytes=512,slot_sha256=f['slot_sha256'],editable=False,reinsertion_approved=False,semantic='dialogue-or-identifier-unverified')
    row['previous_exact_id']=previous.get((row['offset'],row['source_bytes'],row['source_sha256']))
    if row['decode']=='failed':row['cp932_alternative']=reading(f['raw'],'cp932')
    output.append(row)
   for e in resource['entries']:
    checked_span(blob,e);links.append(dict(old_id=e['id'],source_sha256=e['source_sha256'],**context(e,[parsed]),editable=False))
   inventory.append(dict(resource=resource['resource'],sha256=resource['sha256'],opaque=parsed['opaque'],observed_u32=[dict(offset=off,value=struct.unpack_from('<I',blob,off)[0],semantic='unverified') for off in [0,4,8,12,16,5140,7704,12316,12320,12324]]))
 missing=[r for r in output if r['source_bytes'] and r['previous_exact_id'] is None]
 summary=dict(schema=1,source_corpus_sha256=before,ship_sha256=expected,resources=len(inventory),text_fields=len(output),
   nonempty_fields=sum(bool(r['source_bytes']) for r in output),empty_fields=sum(not r['source_bytes'] for r in output),decode_failures=sum(r['decode']=='failed' for r in output),
   cp932_roundtrip_failed_fields=sum(r.get('cp932_alternative',{}).get('roundtrip') is True for r in output),
   previous_fields=len(links),previous_contexts=dict(sorted(Counter(r['classification'] for r in links).items())),nonempty_without_previous_exact_view=len(missing),
   complete_game_text=False,source_modified=False,translation_gate='coverage-audit-pending')
 out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
 for name,value in [('text-fields.json',output),('block-metadata.json',inventory),('previous-contexts.json',links),('missing-full-fields.json',[dict(id=r['id'],offset=r['offset'],source_sha256=r['source_sha256'],source_bytes=r['source_bytes']) for r in missing]),('summary.json',summary)]:
  p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8');core.require(json.loads(p.read_text('utf8'))==value,'output reopen mismatch')
 core.require(core.file_digest(ship)==expected and core.file_digest(corpus_path)==before,'input changed')
 return summary

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['corpus','ship','out']:p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();print(json.dumps(audit(a.corpus,a.ship,a.out),sort_keys=True))
