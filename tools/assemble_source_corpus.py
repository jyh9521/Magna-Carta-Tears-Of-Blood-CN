"""Assemble a read-only structural corpus with explicit supersession and aliases.

Source coverage remains incomplete. Drafts are linked only by exact byte identity;
no translation is rewritten, approved or imported into game resources.
"""
from __future__ import annotations
import argparse
from collections import Counter
import copy
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import font_poc as core
from extract_record_fields import audit as extract_records
from audit_extraction_coverage import alternate_candidate


def indexed(resources):
    result = {}
    for resource in resources:
        for row in resource['entries']:
            core.require(row['id'] not in result,'duplicate source id')
            result[row['id']] = row
    return result


def merge_resources(original, supplement):
    core.require(len({r['resource'] for r in original})==len(original),'duplicate original resource')
    core.require(len({r['resource'] for r in supplement})==len(supplement),'duplicate supplement resource')
    old = {r['resource']:r for r in original}
    additions = {r['resource']:copy.deepcopy(r) for r in supplement}
    core.require(set(additions)<=set(old),'unknown supplement resource')
    aliases, superseded = [], []
    for name,new in additions.items():
        prior = old[name]
        core.require(new['sha256']==prior['sha256'] and new['size']==prior['size'],
                     'supplement resource identity mismatch')
        superseded.append(copy.deepcopy(prior))
        spans = {}
        for row in prior['entries']:
            key = (row['offset'],row['source_bytes'],row['source_sha256'])
            spans.setdefault(key,[]).append(row['id'])
        for row in new['entries']:
            row['source_aliases'] = spans.get((row['offset'],row['source_bytes'],row['source_sha256']),[])
            aliases.extend(dict(old_id=identity,new_id=row['id'],source_sha256=row['source_sha256'])
                           for identity in row['source_aliases'])
    merged = [additions.get(r['resource'],copy.deepcopy(r)) for r in original]
    indexed(merged)
    return merged,aliases,superseded


def link_drafts(original, merged, aliases, drafts):
    old,new = indexed(original),indexed(merged)
    reverse = {}
    for alias in aliases:
        reverse.setdefault(alias['old_id'],[]).append(alias['new_id'])
    links,seen = [],set()
    for draft in drafts:
        identity = draft['id']
        core.require(identity not in seen,'duplicate draft id');seen.add(identity)
        core.require(identity in old and old[identity]['source_sha256']==draft['source_sha256'],
                     'draft source identity mismatch')
        targets = [identity] if identity in new else reverse.get(identity,[])
        core.require(len(targets)<=1,'ambiguous draft alias')
        if targets:
            core.require(new[targets[0]]['source_sha256']==draft['source_sha256'], 'alias hash mismatch')
        links.append(dict(old_id=identity, new_id=targets[0] if targets else None,
            source_sha256=draft['source_sha256'],
            disposition='retained-id' if identity in new else 'exact-byte-alias' if targets else 'requires-source-remap',
            draft_preserved=True,translation_written=False,reinsertion_approved=False))
    return links


def assemble(catalog_path: Path, ship: Path, batches: list[Path], out: Path):
    before = {str(p):core.file_digest(p) for p in [catalog_path,ship,*batches]}
    catalog = json.loads(catalog_path.read_text('utf8'))
    out = core.output_directory(out)
    core.require(not any(out.iterdir()),'output must be empty')
    supplement_summary = extract_records(catalog_path,ship,out/'records')
    supplements = json.loads((out/'records/record-fields.json').read_text('utf8'))['resources']
    merged,aliases,superseded = merge_resources(catalog['resources'],supplements)
    drafts = []
    for path in batches:
        drafts.extend(json.loads(path.read_text('utf8'))['entries'])
    links = link_drafts(catalog['resources'],merged,aliases,drafts)
    # Recover actual bytes by offsets, not by re-encoding the catalog display text.
    from cri_afs import Afs
    from afs import filename_toc
    archive = Afs.open(ship);names=filename_toc(archive);lookup={n:i for i,n in enumerate(names)}
    encoding = []
    with ship.open('rb') as stream:
        for resource in supplements:
            blob=archive.read_entry(lookup[resource['resource'].split('/',1)[1]],stream)
            for row in resource['entries']:
                raw=blob[row['offset']:row['offset']+row['source_bytes']]
                core.require(core.digest(raw)==row['source_sha256'],'supplement field identity mismatch')
                text=row.get('references',{}).get('ko-KR','')
                candidate=alternate_candidate(row,raw)
                encoding.append(dict(id=row['id'],source_sha256=row['source_sha256'],
                    source_decode=row['decode'], cp949_kana=bool(re.search('[\u3040-\u30ff]',text)),
                    nonempty_ascii=bool(raw) and all(32<=b<127 for b in raw),
                    cp932_candidate=candidate, semantic='unverified', editable=False))
    rows = list(indexed(merged).values())
    summary = dict(schema=1,source_catalog_sha256=before[str(catalog_path)],
        original_fields=sum(len(r['entries']) for r in catalog['resources']),
        superseded_fields=sum(len(r['entries']) for r in superseded),
        supplementary_fields=supplement_summary['fields'], active_fields=len(rows),
        active_resources=len(merged), exact_source_aliases=len(aliases),
        draft_links=dict(sorted(Counter(e['disposition'] for e in links).items())),
        drafts_preserved=len(links), supplement_cp949_kana_fields=sum(e['cp949_kana'] for e in encoding),
        supplement_ascii_fields=sum(e['nonempty_ascii'] for e in encoding),
        supplement_cp932_candidates=sum(e['cp932_candidate'] is not None for e in encoding),
        complete_game_text=False,translation_gate='coverage-audit-not-complete',
        result='known-format corpus assembled; remaining coverage and semantics unresolved')
    corpus=copy.deepcopy(catalog);corpus['resources']=merged
    corpus.update(complete_game_text=False,translation_gate=summary['translation_gate'],
                  revision='structured-record-supplement',source_catalog_sha256=before[str(catalog_path)])
    for name,value in [('summary.json',summary),('source-corpus.json',corpus),
            ('superseded-resources.json',superseded),('source-aliases.json',aliases),
            ('draft-links.json',links),('supplement-encoding-audit.json',encoding)]:
        path=out/name;path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        core.require(json.loads(path.read_text('utf8'))==value,'output reopen mismatch')
    core.require(all(core.file_digest(Path(p))==sha for p,sha in before.items()),'input changed')
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog',type=Path,required=True)
    parser.add_argument('--ship',type=Path,required=True)
    parser.add_argument('--batch',type=Path,action='append',required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(assemble(args.catalog,args.ship,args.batch,args.out),sort_keys=True))


if __name__=='__main__':
    main()
