"""Identity-bound decode quarantine audit; alternate readings never authorize import."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from translate.fpb import parse_fpb_raw


def reading(raw,codec):
    try:
        text=raw.decode(codec,errors='strict')
        return dict(strict=True,roundtrip=text.encode(codec)==raw,text=text)
    except (UnicodeDecodeError,UnicodeEncodeError) as error:
        return dict(strict=False,error_byte=error.start,reason=str(error))


def boundaries(raw,codec):
    """Byte boundaries only when strict decoding AND exact re-encoding succeed."""
    result=reading(raw,codec)
    if not result.get('roundtrip'):return None
    pos=0;edges={0}
    for ch in result['text']:
        pos+=len(ch.encode(codec));edges.add(pos)
    core.require(pos==len(raw),'character boundary size mismatch')
    return edges


def checked_span(data,row):
    off=row['offset'];size=row['source_bytes']
    core.require(isinstance(off,int) and isinstance(size,int) and 0<=off<=off+size<=len(data),'source span bounds')
    raw=data[off:off+size]
    core.require(core.digest(raw)==row['source_sha256'],'source field identity mismatch')
    return raw


def fields(catalog):
    rows=[(r,e) for r in catalog['resources'] for e in r['entries']]
    core.require(len({e['id'] for _,e in rows})==len(rows),'duplicate source ID')
    return rows


def reconcile(old,active):
    current={e['id']:e for _,e in fields(active)};superseded=[];retained=[]
    for resource,row in fields(old):
        if row['decode']!='failed':continue
        other=current.get(row['id'])
        same=other is not None and other['source_sha256']==row['source_sha256']
        record=dict(id=row['id'],resource=resource['resource'],source_sha256=row['source_sha256'],status='same-active-field' if same else 'superseded-source-view')
        (retained if same else superseded).append(record)
    return retained,superseded


def audit(corpus_path,old_path,ship,interpretations_path,out):
    inputs=[corpus_path,old_path,ship,interpretations_path]
    hashes={str(p):core.file_digest(p) for p in inputs}
    expected=json.loads((ROOT/'docs/EXTRACTION_COVERAGE.json').read_text('utf8'))['verified_archive_hashes']['SHIP.AFS']
    core.require(hashes[str(ship)]==expected,'SHIP identity mismatch')
    corpus=json.loads(corpus_path.read_text('utf8'));old=json.loads(old_path.read_text('utf8'))
    core.require(corpus['iso_sha256']==old['iso_sha256'],'catalog ISO identity mismatch')
    all_fields=fields(corpus);index_rows={e['id']:e for _,e in all_fields}
    interpretations=json.loads(interpretations_path.read_text('utf8'))['entries']
    core.require(len({r['id'] for r in interpretations})==len(interpretations),'duplicate interpretation ID')
    joined={}
    for row in interpretations:
        core.require(row['id'] in index_rows and row['source_sha256']==index_rows[row['id']]['source_sha256'],'interpretation source mismatch')
        core.require(row['reinsertion_approved'] is False,'unexpected import approval')
        joined[row['id']]=row
    archive=Afs.open(ship);names=filename_toc(archive)
    core.require(len(names)==len(set(names)),'duplicate archive name')
    name_index={n:i for i,n in enumerate(names)}
    failures=[];pools=[];verified_interpretations=0
    with ship.open('rb') as stream:
        for resource in corpus['resources']:
            name=resource['resource'].split('/',1)[1]
            blob=archive.read_entry(name_index[name],stream)
            core.require(len(blob)==resource['size'] and core.digest(blob)==resource['sha256'],'resource identity mismatch')
            data=blob;edges=None;pool_readings=None
            if name.endswith('.fpb') and resource.get('pool'):
                data=parse_fpb_raw(blob)[2]
                core.require(core.digest(data)==resource['pool']['source_sha256'],'pool identity mismatch')
                pool_readings={codec:reading(data,codec) for codec in ['cp949','cp932']}
                edges=boundaries(data,'cp949')
            failed_here=[]
            for row in resource['entries']:
                raw=checked_span(data,row)
                source=reading(raw,'cp949')
                core.require(source['strict']==(row['decode']=='strict'),'catalog decode mismatch')
                if row['id'] in joined:
                    check=reading(raw,joined[row['id']]['source_encoding'])
                    core.require(check.get('roundtrip') is True,'interpretation no longer roundtrips')
                    verified_interpretations+=1
                if source['strict']:continue
                alt=reading(raw,'cp932')
                off=row['offset'];end=off+len(raw)
                boundary=None if edges is None else dict(start_aligned=off in edges,end_aligned=end in edges)
                classification=('cp949-pool-window-splits-character' if boundary is not None and not all(boundary.values()) else
                    'alternate-cp932-pool-reading' if pool_readings and pool_readings['cp932'].get('roundtrip') and alt.get('roundtrip') else
                    'alternate-cp932-field-reading' if alt.get('roundtrip') else 'unresolved-decode')
                record=dict(id=row['id'],resource=resource['resource'],resource_sha256=resource['sha256'],coordinate='fpb-pool' if pool_readings else 'resource',
                    offset=off,source_bytes=len(raw),source_sha256=core.digest(raw),raw_hex=raw.hex(),cp949=source,cp932=alt,
                    cp949_pool_boundary=boundary,classification=classification,existing_interpretation=row['id'] in joined,
                    editable=False,reinsertion_approved=False,runtime_encoding_verified=False)
                failures.append(record);failed_here.append(record)
            if failed_here and pool_readings:
                pools.append(dict(resource=resource['resource'],pool_bytes=len(data),pool_sha256=core.digest(data),readings=pool_readings,
                    failed_windows=len(failed_here),cp949_unaligned_windows=sum(r['classification']=='cp949-pool-window-splits-character' for r in failed_here),
                    editable=False,runtime_encoding_verified=False))
    retained,superseded=reconcile(old,corpus)
    summary=dict(schema=1,source_corpus_sha256=hashes[str(corpus_path)],old_catalog_sha256=hashes[str(old_path)],ship_sha256=expected,
        resources=len(corpus['resources']),active_fields=len(all_fields),active_decode_failures=len(failures),
        failure_formats=dict(sorted(Counter(Path(r['resource']).suffix for r in failures).items())),
        classifications=dict(sorted(Counter(r['classification'] for r in failures).items())),
        old_decode_failures=len(retained)+len(superseded),old_failures_retained=len(retained),old_failures_superseded=len(superseded),
        affected_fpb_pools=len(pools),cp932_roundtrip_fpb_pools=sum(p['readings']['cp932'].get('roundtrip') is True for p in pools),
        existing_interpretations_verified=verified_interpretations,failed_fields_with_prior_interpretation=sum(r['existing_interpretation'] for r in failures),
        complete_game_text=False,translation_gate='coverage-audit-pending',source_modified=False)
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    for name,value in [('failures.json',failures),('pools.json',pools),('superseded-failures.json',superseded),('summary.json',summary)]:
        path=out/name;path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        core.require(json.loads(path.read_text('utf8'))==value,'output reopen mismatch')
    core.require(all(core.file_digest(p)==hashes[str(p)] for p in inputs),'input changed')
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['corpus','old-catalog','ship','interpretations','out']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.corpus,a.old_catalog,a.ship,a.interpretations,a.out),sort_keys=True))
if __name__=='__main__':main()
