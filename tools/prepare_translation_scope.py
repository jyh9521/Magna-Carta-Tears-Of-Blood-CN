"""Freeze per-field translation dispositions without inventing runtime visibility.

Exact source aliases retain independent resource identities. Empty/internal data,
quarantined sources and unresolved data are never counted as translated.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('tools','src','lib')]
import font_poc as core


from source_interpretation import source_text,control_policy


def disposition(resource,entry):
    text=source_text(entry);semantic=entry.get('semantic','')
    if entry.get('config_metadata_retention') is not None:
        from prepare_config_metadata_retention import verified_retention
        if verified_retention(entry):return 'retain-config-metadata',entry['config_metadata_retention']['role']
    if entry.get('source_fault_retention') is not None:
        from prepare_source_fault_retention import verified_retention
        if verified_retention(entry):return 'retain-source-fault',entry['source_fault_retention']['classification']
    if entry.get('decode')=='failed':return 'deferred-decode','original-bytes-retained'
    if not text:return 'exclude-empty','no-display-content'
    if semantic in ('internal-configuration','diagnostic-text','fixed-word-payload-not-translatable'):
        return 'retain-internal',semantic
    if semantic=='unindexed-pool-text-observed':return 'retain-reference','no-sequence-identity'
    if entry.get('controls')=='quarantined':return 'deferred-control','protected-structure'
    if '\x00' in text:
        from localization.text import TERMINAL_NUL_POLICY,terminal_nul_body
        if control_policy(entry) != TERMINAL_NUL_POLICY:return 'deferred-control','protected-structure'
        terminal_nul_body(text)
    if semantic=='unresolved':return 'deferred-semantics','unresolved-role'
    if re.fullmatch(r'[\d\s.,+\-*/:]+',text):return 'retain-numeric','not-language'
    if Path(resource['resource']).suffix.lower() in ('.ini','.int'):
        if semantic=='visible-text-candidate':return 'translate-candidate','configuration-display-candidate'
        return 'deferred-semantics','unclassified-configuration'
    if not re.search(r'[가-힣ぁ-ヿ一-鿿]',text):return 'review-latin','identifier-or-visible-latin-not-assumed'
    return 'translate-candidate','structured-language-field-candidate'


def freeze(corpus,batches,reviews=()):
    rows=[];index={};aliases=defaultdict(list)
    for resource in corpus['resources']:
        for entry in resource['entries']:
            identity=entry['id'];core.require(identity not in index,'duplicate corpus identity');index[identity]=entry
            for alias in entry.get('source_aliases',[]):aliases[alias].append(identity)
            category,reason=disposition(resource,entry)
            rows.append(dict(id=identity,resource=resource['resource'],resource_sha256=resource['sha256'],
                             source_sha256=entry['source_sha256'],source_bytes=entry.get('source_bytes'),offset=entry.get('offset'),
                             disposition=category,reason=reason,translation_status='missing',runtime_visibility_verified=False,
                             import_approved=False,**({'source_retention_required':True,'source_fault_reviewed':True} if category=='retain-source-fault' else {}),
                             **({'source_retention_required':True,'configuration_metadata_reviewed':True} if category=='retain-config-metadata' else {})))
    # Explicit linguistic decisions do not authorize imports or prove consumers.
    # Only the ambiguous Latin bucket can be refined; decode/control quarantine
    # and technical roles cannot be bypassed with this interface.
    reviewed=set();row_index={row['id']:row for row in rows}
    for profile in reviews:
        core.require(profile.get('schema')==1,'unsupported scope review schema')
        for decision in profile['entries']:
            identity=decision['id'];core.require(identity in row_index and identity not in reviewed,'missing or duplicate scope review identity')
            row=row_index[identity];source=index[identity]
            core.require(row['disposition']=='review-latin','scope review cannot bypass source quarantine or roles')
            core.require(all(decision.get(k)==row[k] for k in ('resource','resource_sha256','source_sha256','offset','source_bytes')),'scope review source binding mismatch')
            core.require(decision.get('source')==source_text(source),'scope review source text mismatch')
            category=decision.get('disposition');core.require(category in ('retain-literal-source','translate-candidate'),'unsupported scope review disposition')
            core.require(isinstance(decision.get('reason'),str) and bool(decision['reason'].strip()),'scope review reason missing')
            core.require(decision.get('runtime_visibility_verified') is False and decision.get('import_approved') is False,'linguistic scope review cannot claim runtime visibility or approve imports')
            row.update(disposition=category,reason=decision['reason'],linguistic_reviewed=True,
                       source_retention_required=category=='retain-literal-source',consumer_role_verified=False)
            reviewed.add(identity)
    translated={};original_to_ids=defaultdict(list)
    for batch in batches:
        core.require(batch.get('locale')=='zh-CN','mixed translation locale')
        for entry in batch['entries']:
            identity=entry['id']
            if identity not in index:
                core.require(len(aliases[identity])==1,'ambiguous or missing translation alias');identity=aliases[identity][0]
            source=index[identity];core.require(source['source_sha256']==entry['source_sha256'],'translation source mismatch')
            core.require(identity not in translated,'duplicate target identity')
            translated[identity]=entry
            original_to_ids[source_text(source)].append(identity)
    for row in rows:
        if row['id'] in translated:
            row['translation_status']=translated[row['id']]['status']
            row['target']=translated[row['id']]['target']
            policy=translated[row['id']].get('reinsertion_policy','translate')
            core.require(not row.get('source_retention_required') or policy=='retain-original','literal source retention conflicts with translation import')
            core.require(policy in ('translate','retain-original','pending-role-review'),
                         'invalid reinsertion policy')
            row['reinsertion_policy']=policy
        else:
            text=source_text(index[row['id']]);ids=original_to_ids.get(text,[])
            targets={translated[i]['target'] for i in ids}
            if text and len(targets)==1 and row['disposition']=='translate-candidate':
                row['reuse_suggestion']=dict(target=next(iter(targets)),exact_source_ids=ids,
                                             independent_context_review_required=True,linked_group=False)
    counts=Counter(row['disposition'] for row in rows)
    summary=dict(fields=len(rows),dispositions=dict(sorted(counts.items())),existing_translations=len(translated),
                 explicit_linguistic_reviews=len(reviewed),
                 pending_role_review_translations=sum(r.get('reinsertion_policy')=='pending-role-review' for r in rows),
                 retained_original_reference_translations=sum(r.get('reinsertion_policy')=='retain-original' for r in rows),
                 unfilled_translation_candidates=sum(r['disposition']=='translate-candidate' and r['translation_status']=='missing' for r in rows),
                 reuse_suggestions=sum('reuse_suggestion' in r for r in rows),
                 coverage_review_complete=False,translation_complete=False,full_iso_ready=False)
    return rows,summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--corpus',type=Path,required=True)
    p.add_argument('--batch',type=Path,action='append',required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--review',type=Path,action='append',default=[])
    a=p.parse_args();out=core.output_directory(a.out)
    corpus=json.loads(a.corpus.read_text('utf8'));batches=[json.loads(p.read_text('utf8')) for p in a.batch]
    rows,summary=freeze(corpus,batches,[json.loads(p.read_text('utf8')) for p in a.review])
    receipt=dict(schema=1,locale='zh-CN',iso_sha256=corpus['iso_sha256'],corpus_sha256=core.file_digest(a.corpus),
                 batch_sha256={str(p):core.file_digest(p) for p in a.batch},fields=rows,summary=summary)
    receipt['review_sha256']={str(p):core.file_digest(p) for p in a.review}
    (out/'scope.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n','utf8')
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n','utf8')
    print('TRANSLATION SCOPE PASS '+json.dumps(summary,sort_keys=True))


if __name__=='__main__':main()
