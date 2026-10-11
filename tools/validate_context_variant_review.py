"""Validate source-bound editorial decisions without inferring resource linkage."""
from __future__ import annotations
import argparse,hashlib,json
from collections import defaultdict
from pathlib import Path

def require(condition,message):
 if not condition:raise ValueError(message)

def validate(corpus,batches,review):
 index={e['id']:e for r in corpus['resources'] for e in r['entries']};aliases=defaultdict(set)
 for e in index.values():
  for alias in e.get('source_aliases',[]):aliases[alias].add(e['id'])
 targets={};by_source=defaultdict(dict)
 for batch in batches:
  require(batch['locale']==review['locale'],'locale mismatch')
  for e in batch['entries']:
   identity=e['id']
   if identity not in index:
    require(len(aliases[identity])==1,'unknown or ambiguous source alias');identity=next(iter(aliases[identity]))
   require(identity not in targets,'duplicate translation identity');src=index[identity];require(src['source_sha256']==e['source_sha256'],'source hash mismatch');targets[identity]=e
   by_source[src['references'].get(corpus['source_locale'],'')][identity]=e
 require(review['schema']==1 and review['reviewed_groups']==len(review['groups']),'invalid review group count')
 decisions={};normalized=0
 for group in review['groups']:
  text=group['source'];require(text not in decisions,'duplicate review source');decisions[text]=group
  require(group['review_status']=='reviewed' and bool(group['rationale']),'unreviewed context decision');require(group['linked_group'] is False,'editorial review does not verify consumer linkage');require(group['decision'] in ('normalize-target','retain-context-variant'),'unknown decision')
  occurrences={e['id']:e for e in group['occurrences']};require(len(occurrences)==len(group['occurrences']),'duplicate reviewed occurrence');require(set(occurrences)==set(by_source[text]),'review occurrence coverage mismatch')
  for identity,e in occurrences.items():
   source=index[identity];target=targets[identity];require(e['source_sha256']==source['source_sha256'],'review source binding changed');require(e['target']==target['target'] and target['status']=='reviewed','review target drift or unreviewed target')
   for context in e['context']:
    src=index.get(context['id']);require(src is not None and context['source_sha256']==src['source_sha256'] and context['references']==src.get('references',{}),'context evidence changed')
  if group['decision']=='normalize-target':require(len({e['target'] for e in occurrences.values()})==1,'normalized targets differ');normalized+=1
 for text,es in by_source.items():
  if len({e['target'] for e in es.values()})>1:require(text in decisions,'unreviewed same-source variant')
 return dict(reviewed_groups=len(decisions),normalized_groups=normalized,retained_groups=len(decisions)-normalized,existing_variant_review_complete=True,consumer_linkage_verified=False,full_game_scope_complete=False)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--corpus',type=Path,required=True);p.add_argument('--batch',type=Path,action='append',required=True);p.add_argument('--review',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();review=json.loads(a.review.read_text('utf8'));require(hashlib.sha256(a.corpus.read_bytes()).hexdigest()==review['source_corpus_sha256'],'review corpus binding changed');summary=validate(json.loads(a.corpus.read_text('utf8')),[json.loads(b.read_text('utf8')) for b in a.batch],review);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(dict(summary=summary,input_sha256={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in [a.corpus,a.review,*a.batch]}),ensure_ascii=False,indent=2)+'\n','utf8');print('CONTEXT_VARIANT_REVIEW_PASS '+json.dumps(summary,sort_keys=True))
if __name__=='__main__':main()
