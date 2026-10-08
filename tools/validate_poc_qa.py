"""Validate manually recorded PoC QA evidence; never infer gameplay success."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import font_poc as core
from verify_expanded_locale import fresh_output
from name_slot_overlay import name_cases

ENVIRONMENT=('pcsx2_version','bios_identifier','renderer')
RUNTIME_CASES=('cold-boot','two-font-paths','normal-save-load','scene-transition','battle','linked-character-name')
EVIDENCE_EXTENSIONS={'.png','.jpg','.jpeg','.webp','.txt','.log','.mp4','.mkv'}


def validate_receipt(receipt: dict, config: dict, candidate_sha256: str, receipt_path: Path) -> dict:
    core.require(isinstance(receipt,dict),'receipt must be an object')
    core.require(isinstance(candidate_sha256,str) and re.fullmatch(r'[0-9a-f]{64}',candidate_sha256) is not None,'invalid candidate hash')
    core.require(receipt.get('candidate_sha256')==candidate_sha256,'QA candidate hash mismatch')
    expected={entry['id']:entry for entry in config['entries']}
    added=name_cases(config)
    core.require(not set(expected).intersection(c['id'] for c in added),'duplicate configured name case ID')
    expected.update({c['id']:dict(kind=c['kind'],target=c['expected']) for c in added})
    core.require(len(expected)==len(config['entries'])+len(added) and not set(expected).intersection(RUNTIME_CASES),'duplicate configured case ID')
    expected.update({name:None for name in RUNTIME_CASES})
    cases=receipt.get('cases')
    core.require(isinstance(cases,list) and all(isinstance(c,dict) and isinstance(c.get('id'),str) for c in cases),'invalid QA cases')
    ids=[c['id'] for c in cases]
    core.require(len(ids)==len(set(ids)) and set(ids)==set(expected),'QA case inventory mismatch')
    for field in ENVIRONMENT:
        value=receipt.get(field)
        core.require(value is None or isinstance(value,str) and bool(value.strip()),'invalid environment field: '+field)
    records=[]
    for case in cases:
        source=expected[case['id']]
        if source is not None:
            core.require(case.get('kind')==source['kind'] and case.get('expected')==source['target'],'QA expected text mismatch')
        status=case.get('status');paths=case.get('evidence')
        core.require(status in ('untested','pass','fail'),'unknown QA status')
        core.require(isinstance(paths,list) and all(isinstance(p,str) and p.strip() for p in paths),'invalid evidence list')
        if status=='untested':
            core.require(not paths,'untested case has evidence')
        else:
            core.require(paths and all(isinstance(receipt.get(n),str) and receipt[n].strip() for n in ENVIRONMENT),
                         'tested case requires evidence and environment')
        evidence=[];seen=set()
        for name in paths:
            path=(receipt_path.parent/name).resolve()
            core.require(path not in seen,'duplicate evidence path');seen.add(path)
            core.require(path.is_file() and path.stat().st_size>0,'evidence missing or empty')
            core.require(path.suffix.lower() in EVIDENCE_EXTENSIONS,'unsupported evidence type')
            evidence.append(dict(path=str(path),bytes=path.stat().st_size,sha256=core.file_digest(path)))
        records.append(dict(id=case['id'],recorded_status=status,evidence=evidence))
    states=[c['recorded_status'] for c in records]
    outcome='recorded-failure' if 'fail' in states else 'recorded-complete' if all(s=='pass' for s in states) else 'pending'
    return dict(schema=1,candidate_sha256=candidate_sha256,locale=config['locale'],record_state=outcome,
                environment={n:receipt.get(n) for n in ENVIRONMENT},cases=records,
                runtime='manual claims only; not independently verified',
                pending_cases=[c['id'] for c in records if c['recorded_status']=='untested'])


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True)
    p.add_argument('--locale',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();candidate,receipt_path,locale_path=[v.resolve() for v in (a.candidate,a.receipt,a.locale)]
    before={path:core.file_digest(path) for path in (candidate,receipt_path,locale_path)}
    receipt=json.loads(receipt_path.read_text('utf8'));config=json.loads(locale_path.read_text('utf8'))
    result=validate_receipt(receipt,config,before[candidate],receipt_path)
    inputs=[candidate,receipt_path,locale_path]+[Path(e['path']) for c in result['cases'] for e in c['evidence']]
    out=fresh_output(a.out,inputs)
    core.require(all(core.file_digest(path)==sha for path,sha in before.items()),'QA input changed')
    core.require(all(core.file_digest(Path(e['path']))==e['sha256'] for c in result['cases'] for e in c['evidence']),'QA evidence changed')
    result.update(receipt_sha256=before[receipt_path],locale_sha256=before[locale_path])
    (out/'qa-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(f"QA RECORD VALID state={result['record_state']} cases={len(result['cases'])} pending={len(result['pending_cases'])} runtime=manual-claims-only")
    if result['record_state']=='recorded-failure':raise SystemExit(2)


if __name__=='__main__':main()
