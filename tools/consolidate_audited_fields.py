"""Re-run audited layouts and consolidate known text without rewriting drafts."""
from __future__ import annotations
import argparse,copy,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import font_poc as core
from assemble_source_corpus import merge_resources,indexed
from audit_name_records import audit as names_audit
from audit_region_records import audit as regions_audit
from audit_dialogue_blocks import audit as blocks_audit


def draft_links(original,merged,aliases,drafts):
 old=indexed(original);new=indexed(merged);older={};reverse={}
 for row in old.values():
  for identity in row.get('source_aliases',[]):older.setdefault(identity,[]).append(row['id'])
 for alias in aliases:reverse.setdefault(alias['old_id'],[]).append(alias['new_id'])
 seen=set();links=[]
 for draft in drafts:
  identity=draft['id'];core.require(identity not in seen,'duplicate draft ID');seen.add(identity)
  sources=[identity] if identity in old else older.get(identity,[])
  core.require(len(sources)==1,'missing or ambiguous draft source alias')
  source=sources[0];core.require(old[source]['source_sha256']==draft['source_sha256'],'draft source mismatch')
  candidates=[source] if source in new else reverse.get(source,[])
  core.require(len(candidates)<=1,'ambiguous new draft source alias')
  target=candidates[0] if candidates else None
  if target:core.require(new[target]['source_sha256']==draft['source_sha256'],'new draft source hash mismatch')
  links.append(dict(old_id=identity,current_source_id=source,new_id=target,source_sha256=draft['source_sha256'],
   disposition='exact-source-link' if target else 'requires-source-remap',draft_preserved=True,translation_written=False,reinsertion_approved=False))
 return links


def consolidate(corpus_path,ship,batches,out):
 inputs=[corpus_path,ship,*batches];before={str(p):core.file_digest(p) for p in inputs}
 original=json.loads(corpus_path.read_text('utf8'));out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
 products=[('names',names_audit),('regions',regions_audit),('blocks',blocks_audit)];supplements=[];old={r['resource']:r for r in original['resources']};layout_summaries={}
 for label,reader in products:
  folder=out/label;layout_summaries[label]=reader(corpus_path,ship,folder)
  rows=json.loads((folder/'text-fields.json').read_text('utf8'));grouped={}
  for row in rows:grouped.setdefault(row['resource'],[]).append(row)
  for resource,entries in grouped.items():
   prior=old[resource];supplements.append(dict(resource=resource,size=prior['size'],sha256=prior['sha256'],entries=entries,
    geometry='verified-static-complete-text-fields',layout_audit=label,metadata_semantics='unverified',editable=False))
 merged,aliases,superseded=merge_resources(original['resources'],supplements)
 drafts=[e for path in batches for e in json.loads(path.read_text('utf8'))['entries']];links=draft_links(original['resources'],merged,aliases,drafts)
 rows=list(indexed(merged).values());summary=dict(schema=1,previous_corpus_sha256=before[str(corpus_path)],
  active_resources=len(merged),previous_fields=len(indexed(original['resources'])),active_fields=len(rows),
  replaced_resources=len(supplements),replaced_old_fields=sum(len(r['entries']) for r in superseded),replacement_fields=sum(len(r['entries']) for r in supplements),
  nonempty_fields=sum(bool(r['source_bytes']) for r in rows),decode_failures=sum(r['decode']=='failed' for r in rows),
  quarantined_controls=sum(r.get('controls')=='quarantined' for r in rows),exact_aliases=len(aliases),
  drafts_preserved=len(links),draft_links=dict(sorted(Counter(r['disposition'] for r in links).items())),
  complete_game_text=False,translation_gate='coverage-audit-pending',source_modified=False)
 corpus=copy.deepcopy(original);corpus.update(resources=merged,revision='complete-fixed-region-and-dialogue-blocks',previous_corpus_sha256=before[str(corpus_path)],complete_game_text=False,translation_gate='coverage-audit-pending')
 for name,value in [('source-corpus.json',corpus),('source-aliases.json',aliases),('superseded-resources.json',superseded),('draft-links.json',links),('layout-summaries.json',layout_summaries),('summary.json',summary)]:
  p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8');core.require(json.loads(p.read_text('utf8'))==value,'output reopen mismatch')
 core.require(all(core.file_digest(p)==before[str(p)] for p in inputs),'input changed')
 return summary

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--corpus',type=Path,required=True);p.add_argument('--ship',type=Path,required=True);p.add_argument('--batch',type=Path,action='append',required=True);p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();print(json.dumps(consolidate(a.corpus,a.ship,a.batch,a.out),sort_keys=True))
