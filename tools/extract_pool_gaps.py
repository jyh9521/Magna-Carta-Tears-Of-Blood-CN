"""Export every uncovered FPB pool span without inventing sequence IDs."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from translate.fpb import parse_fpb_raw
from extract_strings import field

def uncovered(size,spans):
    cursor=0;gaps=[]
    for off,length in sorted(spans):
        core.require(0<=off<=size and 0<=length and off+length<=size,'pool span bounds')
        if off>cursor:gaps.append((cursor,off-cursor))
        cursor=max(cursor,off+length)
    if cursor<size:gaps.append((cursor,size-cursor))
    return gaps

def audit(catalog_path,ship,out):
    before=core.file_digest(catalog_path);catalog=json.loads(catalog_path.read_text('utf8'))
    expected=json.loads((ROOT/'docs/EXTRACTION_COVERAGE.json').read_text('utf8'))['verified_archive_hashes']['SHIP.AFS']
    core.require(core.file_digest(ship)==expected,'SHIP identity mismatch')
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    archive=Afs.open(ship);names=filename_toc(archive);index={n:i for i,n in enumerate(names)}
    additions=[];exceptions=[];count=0;pool_bytes=0;covered=0
    with ship.open('rb') as stream:
        for resource in catalog['resources']:
            if not resource['resource'].endswith('.fpb'):continue
            count+=1;name=resource['resource'].split('/',1)[1];blob=archive.read_entry(index[name],stream)
            core.require(len(blob)==resource['size'] and core.digest(blob)==resource['sha256'],'FPB identity mismatch')
            try:_,windows,pool=parse_fpb_raw(blob)
            except ValueError as error:
                exceptions.append(dict(resource=resource['resource'],sha256=core.digest(blob),size=len(blob),raw_hex=blob.hex(),error=str(error)))
                continue
            core.require(core.digest(pool)==resource['pool']['source_sha256'],'pool reference mismatch')
            spans=[];invalid=[]
            for row in resource['entries']:
                off,length=row['offset'],row['source_bytes']
                if not 0<=off<=off+length<=len(pool):invalid.append(row['id']);continue
                core.require(core.digest(pool[off:off+length])==row['source_sha256'],'field identity mismatch')
                spans.append((off,length))
            gaps=uncovered(len(pool),spans);pool_bytes+=len(pool);covered+=len(pool)-sum(n for _,n in gaps)
            if invalid:exceptions.append(dict(resource=resource['resource'],invalid_spans=invalid))
            for off,length in gaps:
                row=field(resource['resource']+f'/pool-gap/{off}/{length}',pool[off:off+length],off,
                    resource=resource['resource'],resource_sha256=resource['sha256'],coordinate='fpb-pool',
                    semantic='unindexed-pool-text-observed',editable=False,backend_eligible=False,
                    sequence_id=None,detection='source-field-byte-coverage-complement')
                additions.append(row)
    core.require(core.file_digest(ship)==expected and core.file_digest(catalog_path)==before,'source changed')
    summary=dict(schema=1,source_corpus_sha256=before,ship_sha256=expected,fpb_resources=count,pool_bytes=pool_bytes,
        existing_field_union_bytes=covered,gap_fields=len(additions),gap_bytes=sum(r['source_bytes'] for r in additions),
        gap_decode_failures=sum(r['decode']!='strict' for r in additions),parse_exceptions=len(exceptions),
        complete_game_text=False,result='FPB pool coverage complement exported; no fabricated sequence IDs or translation changes')
    for name,data in [('pool-gap-fields.json',additions),('parse-exceptions.json',exceptions),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        core.require(json.loads(p.read_text('utf8'))==data,'gap reopen mismatch')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--catalog',type=Path,required=True);p.add_argument('--ship',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    print(json.dumps(audit(a.catalog,a.ship,a.out),sort_keys=True))
