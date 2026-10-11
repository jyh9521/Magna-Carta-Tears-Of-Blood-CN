"""Audit canonical terminology and exact-source-bound translation batches.

This report records lexical consistency, not human proofreading or UI acceptance.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'src'),str(ROOT/'lib')]
import font_poc as core
from validate_translation_batch import glossary_terms, validate


def audit(corpus,batches,terms,unexpected_script_pattern=None):
    entries=[e for resource in corpus['resources'] for e in resource['entries']]
    by_id={e['id']:e for e in entries}
    core.require(len(entries)==len(by_id),'duplicate source identity')
    aliases=defaultdict(set)
    for e in entries:
        for alias in e.get('source_aliases',[]):aliases[alias].add(e['id'])
    canonical=dict(terms)
    pattern='|'.join(re.escape(t) for t in sorted(canonical,key=len,reverse=True))
    source_text=lambda e:e.get('references',{}).get(corpus['source_locale'],'')
    source_values=Counter(source_text(e) for e in entries)
    term_rows=[dict(source=s,target=t,exact_source_fields=source_values[s],exact_only=s in terms.exact_only) for s,t in terms]
    issues=[];validated=[];seen=set();translations=defaultdict(list)
    for filename,batch in batches:
        core.require(batch.get('locale') is not None,'missing locale')
        for target in batch['entries']:
            identity=target['id']
            if identity not in by_id:
                core.require(len(aliases[identity])==1,'unknown or ambiguous translation identity')
                identity=next(iter(aliases[identity]))
            core.require(identity not in seen,'duplicate translation across batches');seen.add(identity)
            source=by_id[identity]
            core.require(source['source_sha256']==target['source_sha256'],'translation source mismatch')
            text=source_text(source)
            for match in re.finditer(pattern,text):
                term=match.group()
                if term in terms.exact_only and text.strip()!=term:continue
                if canonical[term] not in target['target']:
                    issues.append(dict(kind='term-mismatch',batch=filename,id=identity,source_term=term,expected=canonical[term],target=target['target']))
            if unexpected_script_pattern and re.search(unexpected_script_pattern,target['target']):
                issues.append(dict(kind='source-script-in-target',batch=filename,id=identity,target=target['target']))
            translations[text].append(dict(id=identity,target=target['target'],batch=filename,status=target['status']))
        try:
            result=validate(corpus,batch,terms)
        except ValueError as exc:
            result=dict(error=str(exc));issues.append(dict(kind='batch-validation',batch=filename,error=str(exc)))
        validated.append(dict(batch=filename,**result))
    # Different targets for the same source require context review, never silent
    # harmonization. Identical source bytes do not establish resource linkage.
    variants=[dict(source=s,occurrences=v,linked_group=False) for s,v in translations.items() if len({x['target'] for x in v})>1]
    return dict(schema=1,terms=term_rows,batches=validated,issues=issues,context_variants=variants,
                summary=dict(glossary_terms=len(terms),batches=len(batches),translation_fields=len(seen),
                             lexical_issues=len(issues),same_source_target_variants=len(variants),
                             statuses=dict(Counter(x['status'] for _,b in batches for x in b['entries'])),
                             human_proofreading_complete=False,full_game_text_complete=False))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--corpus',type=Path,required=True);p.add_argument('--glossary',type=Path,required=True)
    p.add_argument('--batch',type=Path,action='append',required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--unexpected-script-pattern',help='Locale-selected regex; generic audits do not assume target scripts')
    a=p.parse_args();out=core.output_directory(a.out)
    paths=[a.corpus,a.glossary,*a.batch];before={str(x.resolve()):core.file_digest(x) for x in paths}
    result=audit(json.loads(a.corpus.read_text('utf8')),[(str(x),json.loads(x.read_text('utf8'))) for x in a.batch],glossary_terms(a.glossary),a.unexpected_script_pattern)
    result['input_sha256']=before
    (out/'consistency.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    core.require(before=={str(x.resolve()):core.file_digest(x) for x in paths},'audit input changed')
    print('CONSISTENCY AUDIT '+json.dumps(result['summary'],sort_keys=True),flush=True)


if __name__=='__main__':main()
