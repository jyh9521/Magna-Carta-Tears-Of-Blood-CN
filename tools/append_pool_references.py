"""Append verified FPB pool complements as non-editable source references."""
from __future__ import annotations
import argparse,copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import font_poc as core
from extract_pool_gaps import audit as gaps_audit
from consolidate_audited_fields import draft_links
from assemble_source_corpus import indexed


def append_fields(resources,additions):
    merged=copy.deepcopy(resources);by_resource={r['resource']:r for r in merged};existing=indexed(merged)
    for row in additions:
        core.require(row['id'] not in existing,'duplicate pool reference ID')
        core.require(row['resource'] in by_resource,'pool reference resource missing')
        r=by_resource[row['resource']]
        core.require(row['resource_sha256']==r['sha256'],'pool reference resource hash mismatch')
        core.require(row.get('coordinate')=='fpb-pool' and row.get('sequence_id') is None,'pool reference coordinate/sequence mismatch')
        core.require(row.get('editable') is False and row.get('backend_eligible') is False,'pool reference unexpectedly editable')
        start=row['offset'];end=start+row['source_bytes']
        core.require(0<=start<end<=r['pool']['source_bytes'],'pool reference bounds')
        core.require(not any(start<e['offset']+e['source_bytes'] and e['offset']<end for e in r['entries']),'pool reference overlaps existing field')
        r['entries'].append(copy.deepcopy(row));existing[row['id']]=row
    return merged


def audit(corpus_path,ship,batches,out):
    inputs=[corpus_path,ship,*batches];hashes={str(p):core.file_digest(p) for p in inputs}
    original=json.loads(corpus_path.read_text('utf8'));out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    gap_summary=gaps_audit(corpus_path,ship,out/'gaps')
    additions=json.loads((out/'gaps/pool-gap-fields.json').read_text('utf8'))
    merged=append_fields(original['resources'],additions)
    drafts=[e for p in batches for e in json.loads(p.read_text('utf8'))['entries']]
    links=draft_links(original['resources'],merged,[],drafts)
    core.require(all(x['disposition']=='exact-source-link' for x in links),'draft link not preserved')
    rows=list(indexed(merged).values());summary=dict(schema=1,previous_corpus_sha256=hashes[str(corpus_path)],
        active_resources=len(merged),previous_fields=len(indexed(original['resources'])),active_fields=len(rows),
        nonempty_fields=sum(bool(e['source_bytes']) for e in rows),decode_failures=sum(e['decode']=='failed' for e in rows),
        added_pool_references=len(additions),added_pool_bytes=sum(e['source_bytes'] for e in additions),
        fabricated_sequence_ids=0,drafts_preserved=len(links),drafts_remapped=0,
        complete_game_text=False,translation_gate='coverage-audit-pending',source_modified=False)
    corpus=copy.deepcopy(original);corpus.update(resources=merged,revision='verified-fixed-fields-and-pool-complements',
        previous_corpus_sha256=hashes[str(corpus_path)],complete_game_text=False,translation_gate='coverage-audit-pending')
    for name,value in [('source-corpus.json',corpus),('draft-links.json',links),('pool-audit-summary.json',gap_summary),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        core.require(json.loads(p.read_text('utf8'))==value,'output reopen mismatch')
    core.require(all(core.file_digest(p)==hashes[str(p)] for p in inputs),'input changed')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--corpus',type=Path,required=True);p.add_argument('--ship',type=Path,required=True);p.add_argument('--batch',type=Path,action='append',required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.corpus,a.ship,a.batch,a.out),sort_keys=True))
