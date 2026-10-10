"""Record verified baseline decoding failures as temporarily deferred research.

Alternative-codec evidence remains separate. No source field is deleted, and
no claim that every possible encoding fails is inferred from a CP949 failure.
"""
from pathlib import Path
from collections import Counter
import argparse
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import font_poc as core
CORPUS_HASH='39884cc3e9175811800c92ee8ae7f3d1a50b96a67bb9d0d41cf0fb8f84895dc6'


def verify_failure(entry):
    core.require(entry['decode']=='failed','entry not marked failed')
    core.require(isinstance(entry.get('raw_hex'),str),'failure lacks original bytes')
    raw=bytes.fromhex(entry['raw_hex'])
    core.require(len(raw)==entry['source_bytes'] and core.digest(raw)==entry['source_sha256'],'failure byte identity mismatch')
    try:raw.decode('cp949',errors='strict')
    except UnicodeDecodeError as error:
        return dict(start=error.start,end=error.end,reason=error.reason)
    raise ValueError('failure marker contradicts strict CP949 decoding')


def ledger(corpus):
    rows=[];ids=set();fields=0
    for resource in corpus['resources']:
        for entry in resource['entries']:
            fields+=1
            core.require(entry['id'] not in ids,'duplicate source field');ids.add(entry['id'])
            if entry.get('decode')!='failed':continue
            failure=verify_failure(entry)
            reviews=[r for r in entry.get('coverage_reviews',[]) if r['layer']=='decode']
            core.require(all(r['source_sha256']==entry['source_sha256'] for r in reviews),'alternative evidence source mismatch')
            rows.append(dict(id=entry['id'],resource=resource['resource'],offset=entry['offset'],
                             source_bytes=entry['source_bytes'],source_sha256=entry['source_sha256'],
                             baseline_codec='cp949',strict_failure=failure,
                             status='temporarily-deferred-baseline-decode',
                             alternatives=reviews,all_codecs_failed=False,
                             field_deleted=False,editable=False,backend_eligible=False))
    return rows,dict(fields=fields,deferred=len(rows),by_extension=dict(sorted(Counter(
        Path(r['resource']).suffix for r in rows).items())),source_fields_deleted=0,
        silent_loss=False,all_codecs_failed=False,complete_game_text=False,
        coverage_review_complete=False,translation_gate='coverage-audit-pending')


def audit(corpus_path,out):
    core.require(core.file_digest(corpus_path)==CORPUS_HASH,'unsupported reviewed corpus')
    rows,summary=ledger(json.loads(corpus_path.read_text('utf8')))
    core.require(summary['fields']==20151 and len(rows)==167,'baseline failure inventory mismatch')
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    for name,value in [('deferred.json',rows),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8')
        core.require(json.loads(p.read_text('utf8'))==value,'JSON reopen mismatch')
    core.require(core.file_digest(corpus_path)==CORPUS_HASH,'corpus changed')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('corpus','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.corpus,a.out),sort_keys=True))
