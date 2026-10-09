"""Append reviewed-by-structure config values to a read-only source snapshot."""
from pathlib import Path
from collections import Counter
import argparse,copy,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from audit_config_entries import parse_lines,exact_positions
from audit_container_payloads import unpack_chunks
from extract_script_buffers import FILE_HASH
from audit_bundle_contexts import BUNDLE_HASH
from assemble_source_corpus import indexed
from consolidate_audited_fields import draft_links
BASE_CORPUS_HASH='a9c7a9b0344cfebeda01014ffab83c00dd94e7e4b5de4d286eedc3447d031c18'

def merge_config_resources(original,supplements):
    indexed(original)
    names=[r['resource'] for r in original]+[r['resource'] for r in supplements]
    core.require(len(names)==len(set(names)),'config resource identity collides')
    merged=copy.deepcopy(original)+copy.deepcopy(supplements);indexed(merged)
    core.require(merged[:len(original)]==original,'old source fields changed')
    for resource in supplements:
        for row in resource['entries']:
            core.require(row.get('editable') is False and row.get('backend_eligible') is False and row.get('semantic_review')=='pending','unreviewed config accidentally editable')
    return merged

def consolidate(corpus_path,archive,batches,out):
    core.require(core.file_digest(corpus_path)==BASE_CORPUS_HASH,'base corpus identity mismatch')
    core.require(core.file_digest(archive)==FILE_HASH,'FILE identity mismatch')
    before={str(p):core.file_digest(p) for p in [corpus_path,archive,*batches]}
    original=json.loads(corpus_path.read_text('utf8'));supplements=[];mirrors=[]
    afs=Afs.open(archive);names=filename_toc(afs)
    with archive.open('rb') as f:
        bundle,_=unpack_chunks(afs.read_entry(names.index('celfid.lix'),f));core.require(core.digest(bundle)==BUNDLE_HASH,'bundle mismatch')
        for i,name in enumerate(names):
            if not name.lower().endswith(('.ini','.int')):continue
            raw=afs.read_entry(i,f);lines,values=parse_lines(raw);entries=[];resource='FILE/'+name
            for row in values:
                entries.append(dict(id=resource+'/line/'+str(row['line']),offset=row['value_offset'],offset_scope='resource-absolute',source_sha256=row['value_sha256'],source_bytes=row['value_bytes'],source_encoding='ascii',source_locale='und',references={'und':row['value']},decode='strict',bounds_valid=True,section=row['section'],section_occurrence=row['section_occurrence'],key=row['key'],line=row['line'],semantic='config-value-unverified',semantic_review='pending',controls='research-unclassified',editable=False,backend_eligible=False,placeholder_candidates=row['placeholder_candidates']))
            supplements.append(dict(resource=resource,size=len(raw),sha256=core.digest(raw),entries=entries,geometry='verified-config-lines',metadata_semantics='unverified',editable=False,line_count=len(lines)))
            offsets=exact_positions(bundle,raw)
            if offsets:mirrors.append(dict(resource=resource,sha256=core.digest(raw),decompressed_offsets=offsets,relationship='exact-byte-mirror-not-runtime-linked-group'))
    merged=merge_config_resources(original['resources'],supplements)
    drafts=[row for path in batches for row in json.loads(path.read_text('utf8'))['entries']]
    links=draft_links(original['resources'],merged,[],drafts)
    core.require(all(x['disposition']=='exact-source-link' for x in links),'draft source remap required')
    corpus=copy.deepcopy(original);corpus.update(resources=merged,revision='audited-resource-fields-plus-config-values',previous_corpus_sha256=BASE_CORPUS_HASH,complete_game_text=False,translation_gate='coverage-audit-pending')
    corpus['celfid_resource_mirrors'].extend(mirrors)
    rows=list(indexed(merged).values())
    summary=dict(schema=1,previous_corpus_sha256=BASE_CORPUS_HASH,active_resources=len(merged),active_fields=len(rows),nonempty_fields=sum(bool(x['source_bytes']) for x in rows),empty_fields=sum(not x['source_bytes'] for x in rows),decode_failures=sum(x['decode']=='failed' for x in rows),quarantined_controls=sum(x.get('controls')=='quarantined' for x in rows),config_resources_added=len(supplements),config_values_added=sum(len(r['entries']) for r in supplements),config_backend_enabled=False,drafts_preserved=len(links),draft_links=dict(Counter(x['disposition'] for x in links)),old_resources_unchanged=True,old_candidates_unchanged=corpus['celfid_candidates']==original['celfid_candidates'],complete_game_text=False,translation_gate='coverage-audit-pending',source_modified=False)
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    for name,value in [('source-corpus.json',corpus),('draft-links.json',links)]:
        p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8');core.require(json.loads(p.read_text('utf8'))==value,'JSON reopen')
    summary['source_corpus_sha256']=core.file_digest(out/'source-corpus.json')
    p=out/'summary.json';p.write_text(json.dumps(summary,indent=2)+'\n','utf8');core.require(json.loads(p.read_text('utf8'))==summary,'summary reopen')
    core.require(all(core.file_digest(p)==before[str(p)] for p in [corpus_path,archive,*batches]),'input changed')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['corpus','archive','out']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--batch',type=Path,action='append',required=True)
    a=p.parse_args();print(json.dumps(consolidate(a.corpus,a.archive,a.batch,a.out),sort_keys=True))
