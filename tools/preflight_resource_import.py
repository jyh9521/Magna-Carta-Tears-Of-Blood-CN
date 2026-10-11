"""Account for every reviewed target and dry-run existing resource-copy backends.

The selected batch is an experimental copy plan, not runtime-role approval.
An overflow or backend error holds the entire selected resource, not just one
field. Pending policies are reported verbatim and are never changed.
"""
from pathlib import Path
import argparse
from collections import defaultdict,Counter
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'src'),str(ROOT/'lib')]
import font_poc as core
from source_interpretation import source_text,source_codec,decode_source,control_policy,encode_target
from import_audited_fields import binding_index,resolve_source,require_write_policy,require_source_role,fixed_extent,rewrite_fields
from localization.text import MappedEncoder,validate_target,rewrite_fpb
from translate.fpb import parse_fpb_raw,synthesize_implicit_seq0
from research_inventory import font_data


def preflight(corpus,batches,ship,encoder):
    index,aliases=binding_index(corpus);seen=set();groups=defaultdict(list);deferred=[]
    locale=batches[0]['locale']
    for batch in batches:
        core.require(batch.get('schema')==1 and batch.get('locale')==locale,'incompatible translation batch')
        for target in batch['entries']:
            resource,entry=resolve_source(index,aliases,target)
            canonical=entry['canonical_id']
            core.require(canonical not in seen,'duplicate canonical target');seen.add(canonical)
            core.require(target.get('status')=='reviewed','unreviewed target')
            policy=target.get('reinsertion_policy','translate')
            core.require(policy in ('translate','pending-role-review','retain-original'),'unknown reinsertion policy')
            if policy!='translate':
                deferred.append(dict(id=target['id'],canonical_id=canonical,resource=resource['resource'],reason=policy))
                continue
            core.require(resource['resource'].startswith('SHIP/'),'unsupported archive member')
            groups[resource['resource']].append((resource,entry,target))
    selected=[];resources=[];blocked=[]
    for name,rows in sorted(groups.items()):
        member=Path(name).name
        core.require(member in ship,'source archive member missing')
        original=ship[member]
        core.require(core.digest(original)==rows[0][0]['sha256'],'source resource fingerprint mismatch')
        field_errors=[]
        views=None
        if member.endswith('.fpb'):
            _,windows,pool=parse_fpb_raw(original)
            views={s:pool[o:o+n] for s,o,n in synthesize_implicit_seq0(windows,len(pool))}
        for resource,entry,target in rows:
            require_write_policy(target)
            require_source_role(entry)
            core.require(entry.get('decode')=='strict' and entry.get('controls')=='recognized','quarantined source selection')
            from ui_punctuation import validated_empty_suffix
            if target['target'] == '':
                validated_empty_suffix(entry,target)
            else:
                validate_target(source_text(entry),target['target'],control_policy=control_policy(entry,target['target']))
            encoded=encode_target(encoder,entry,target['target'])
            if views is not None:
                core.require(entry['seq'] in views and core.digest(views[entry['seq']])==entry['source_sha256'],'FPB source view mismatch')
                decode_source(views[entry['seq']],entry)
            else:
                span,_=fixed_extent(entry)
                if len(encoded)>=span:
                    field_errors.append(dict(id=target['id'],canonical_id=entry['canonical_id'],reason='fixed-field-byte-overflow',encoded_bytes=len(encoded),capacity_bytes=span-1,target=target['target']))
        if field_errors:
            blocked.extend(field_errors)
            resources.append(dict(resource=name,selected_fields=len(rows),disposition='held-whole-resource',field_errors=field_errors))
            continue
        try:
            if views is not None:
                modified,receipt=rewrite_fpb(original,{e['seq']:t['target'] for _,e,t in rows},encoder,source_encodings={e['seq']:source_codec(e) for _,e,t in rows},source_control_policies={e['seq']:control_policy(e,t['target']) for _,e,t in rows if control_policy(e,t['target']) is not None})
            else:
                modified,receipt=rewrite_fields(original,[e for _,e,_ in rows],[t for _,_,t in rows],encoder)
        except ValueError as error:
            resources.append(dict(resource=name,selected_fields=len(rows),disposition='held-whole-resource',backend_error=str(error)))
            continue
        selected.extend(t for _,_,t in rows)
        resources.append(dict(resource=name,selected_fields=len(rows),disposition='dry-run-pass',original_sha256=core.digest(original),experimental_modified_sha256=core.digest(modified),original_bytes=len(original),modified_bytes=len(modified)))
    held=sum(r['selected_fields'] for r in resources if r['disposition']=='held-whole-resource')
    core.require(len(selected)+len(deferred)+held==len(seen),'target accounting disagreement')
    report=dict(targets=len(seen),copy_selected_fields=len(selected),policy_deferred_fields=len(deferred),whole_resource_held_fields=held,
                selected_resources=sum(r['disposition']=='dry-run-pass' for r in resources),held_resources=sum(r['disposition']=='held-whole-resource' for r in resources),
                capacity_overflow_fields=len(blocked),deferred=deferred,resources=resources,overflows=blocked,
                runtime_roles_verified=False,final_iso_authorized=False)
    return dict(schema=1,locale=locale,entries=selected),report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('corpus','map','font-resource','archive','out'):p.add_argument('--'+arg,type=Path,required=True)
    p.add_argument('--batch',type=Path,action='append',required=True)
    p.add_argument('--archive-sha256',required=True)
    args=p.parse_args()
    core.require(core.file_digest(args.archive)==args.archive_sha256,'original archive fingerprint mismatch')
    corpus=json.loads(args.corpus.read_text('utf8'));batches=[json.loads(p.read_text('utf8')) for p in args.batch]
    mapping=json.loads(args.map.read_text('utf8'));core.require(batches and all(mapping['locale']==b['locale'] for b in batches),'font locale mismatch')
    encoder=MappedEncoder(mapping['entries'],font_tables=font_data(args.font_resource.read_bytes()))
    ship=dict(core.archive_entries(args.archive)[1])
    batch,report=preflight(corpus,batches,ship,encoder)
    core.require(core.file_digest(args.archive)==args.archive_sha256,'original archive changed')
    report['input_sha256']={str(p):core.file_digest(p) for p in [args.corpus,args.map,args.font_resource,args.archive]+args.batch}
    out=core.output_directory(args.out)
    (out/'selected-copy-batch.json').write_text(json.dumps(batch,ensure_ascii=False,indent=2)+'\n','utf8')
    (out/'preflight.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print('RESOURCE_PREFLIGHT_PASS '+json.dumps({k:v for k,v in report.items() if isinstance(v,(int,bool))},sort_keys=True))


if __name__=='__main__':main()
