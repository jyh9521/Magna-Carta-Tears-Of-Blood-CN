"""Reproduce coverage-review layers and preserve every original source identity."""
from pathlib import Path
from collections import Counter
import argparse,copy,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from audit_config_semantics import audit as configs,CORPUS_HASH
from audit_stream_tail_contexts import audit as contexts
from audit_numeric_resources import audit as numeric
from audit_compiled_semantics import audit as scripts
from audit_decode_quarantine import audit as decodes
from audit_control_observations import audit as controls
from consolidate_audited_fields import draft_links


def annotate(corpus,config_rows,numeric_rows,decode_rows,control_rows):
    result=copy.deepcopy(corpus);active={e['id']:e for r in result['resources'] for e in r['entries']}
    for label,rows in [('config',config_rows),('numeric',numeric_rows),('decode',decode_rows),('control',control_rows)]:
        core.require(len({r['id'] for r in rows})==len(rows),'duplicate review ID')
        for row in rows:
            core.require(row['id'] in active and active[row['id']]['source_sha256']==row['source_sha256'],'review identity mismatch')
            target=active[row['id']]
            core.require(target['editable'] is False and row['editable'] is False,'unexpected edit permission')
            review=dict(layer=label,source_sha256=row['source_sha256'],editable=False,backend_eligible=False)
            if label=='config':
                target.update(semantic=row['category'],semantic_review=row['semantic_review'],semantic_reason=row['reason'])
                review.update(category=row['category'],reason=row['reason'],evidence_level=row['evidence_level'])
            elif label=='numeric':
                target.update(semantic='fixed-word-payload-not-translatable',semantic_review='numeric-geometry-classified')
                review.update(category=row['category'],record=row['record'],first_word=row['first_word'],last_word=row['last_word'])
            elif label=='decode':review.update(classification=row['classification'],runtime_encoding_verified=False)
            else:review.update(observations=len(row['observations']),runtime_semantics_verified=False)
            target.setdefault('coverage_reviews',[]).append(review)
    for old_resource,new_resource in zip(corpus['resources'],result['resources']):
        core.require(old_resource['resource']==new_resource['resource'],'resource order changed')
        for old,new in zip(old_resource['entries'],new_resource['entries']):
            for key in ['id','source_sha256','source_bytes','offset','references','decode','controls','editable']:
                core.require(old.get(key)==new.get(key),'protected source field changed: '+key)
    result.update(revision='config-numeric-decode-control-reviewed-readonly',previous_corpus_sha256=CORPUS_HASH,
        complete_game_text=False,translation_gate='coverage-audit-pending')
    return result


def audit(corpus,old_catalog,ship,file,elf,interpretations,context_path,objects,strings,batches,out):
    inputs=[corpus,old_catalog,ship,file,elf,interpretations,context_path,objects,strings,*batches]
    hashes={str(p):core.file_digest(p) for p in inputs}
    core.require(hashes[str(corpus)]==CORPUS_HASH,'corpus identity mismatch')
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    summaries={}
    summaries['config']=configs(corpus,file,out/'config')
    summaries['stream']=contexts(file,context_path,out/'stream')
    summaries['numeric']=numeric(corpus,ship,file,elf,out/'numeric')
    summaries['compiled']=scripts(file,objects,strings,out/'compiled')
    base=json.loads(corpus.read_text('utf8'));projection=copy.deepcopy(base)
    projection['resources']=[r for r in base['resources'] if r['resource'].startswith('SHIP/')]
    projection_path=out/'ship-source-projection.json';projection_path.write_text(json.dumps(projection,ensure_ascii=False,indent=2)+'\n','utf8')
    summaries['decode']=decodes(projection_path,old_catalog,ship,interpretations,out/'decode')
    summaries['control']=controls(corpus,out/'control')
    read=lambda folder,name:json.loads((out/folder/name).read_text('utf8'))
    reviewed=annotate(base,read('config','classifications.json'),read('numeric','candidate-contexts.json'),read('decode','failures.json'),read('control','control-observations.json'))
    drafts=[e for path in batches for e in json.loads(path.read_text('utf8'))['entries']]
    links=draft_links(base['resources'],reviewed['resources'],[],drafts)
    core.require(len(links)==6334 and all(r['disposition']=='exact-source-link' for r in links),'draft links changed')
    reviewed['celfid_context_review']=dict(candidates=35048,unresolved=summaries['stream']['unresolved_byte_contexts'],context_file='stream/contexts.json')
    summary=dict(schema=1,source_corpus_sha256=CORPUS_HASH,resources=len(reviewed['resources']),fields=sum(len(r['entries']) for r in reviewed['resources']),
        drafts_preserved=len(links),draft_links=dict(Counter(r['disposition'] for r in links)),input_hashes=hashes,
        review_summaries=summaries,complete_game_text=False,coverage_review_complete=False,translation_gate='coverage-audit-pending',
        source_identity_fields_unchanged=True,source_modified=False,backend_permissions_unchanged=True)
    for name,value in [('source-corpus.json',reviewed),('draft-links.json',links),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8');core.require(json.loads(p.read_text('utf8'))==value,'JSON reopen')
    core.require(all(core.file_digest(p)==hashes[str(p)] for p in inputs),'input changed')
    return dict(resources=summary['resources'],fields=summary['fields'],drafts_preserved=len(links),
        source_corpus_sha256=core.file_digest(out/'source-corpus.json'),complete_game_text=False,coverage_review_complete=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['corpus','old-catalog','ship','file','elf','interpretations','contexts','objects','strings','out']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--batch',type=Path,action='append',required=True)
    a=p.parse_args();print(json.dumps(audit(a.corpus,a.old_catalog,a.ship,a.file,a.elf,a.interpretations,a.contexts,a.objects,a.strings,a.batch,a.out),sort_keys=True))
