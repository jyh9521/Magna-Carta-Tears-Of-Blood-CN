"""Build separate resource copies for explicitly reviewed, source-bound fields.

Fixed-field geometry and full-slot hashes must come from the audited corpus.
This does not infer visibility, linked groups, cache synchronization or ISO QA.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'src'),str(ROOT/'lib')]
import font_poc as core
from source_interpretation import source_text,source_codec,decode_source,control_policy,encode_target
from localization.text import MappedEncoder,validate_target,rewrite_fpb
from translate.fpb import parse_fpb_raw,synthesize_implicit_seq0
from research_inventory import font_data


def fixed_extent(entry):
    if 'slot_bytes' in entry:span=entry['slot_bytes']
    elif 'field_span' in entry:span=entry['field_span']
    elif 'byte_capacity' in entry:span=entry['byte_capacity']+1
    elif 'observed_byte_capacity' in entry:span=entry['observed_byte_capacity']+1
    else:raise ValueError('audited fixed extent missing')
    digest=entry.get('slot_sha256',entry.get('field_sha256'))
    core.require(type(span) is int and span>0 and isinstance(digest,str),'invalid audited fixed extent')
    return span,digest


def fingerprint_extent(entry,write_span):
    # Leading-only catalogs hash the full upstream segment, including the
    # opaque trailer, but permit writing only the first NUL/zero-run region.
    leading=not any(k in entry for k in ('slot_bytes','field_span','byte_capacity'))
    trailer=entry.get('trailer_bytes',0) if leading else 0
    core.require(type(trailer) is int and trailer>=0,'invalid trailer extent')
    return write_span+trailer


def require_write_policy(target):
    # Linguistic review does not authorize rewriting a lookup/editor label.
    core.require(target.get('reinsertion_policy','translate')=='translate',
                 'translation reinsertion policy does not authorize writing')


def require_source_role(entry):
    core.require(entry.get('semantic') not in ('internal-configuration','diagnostic-text','fixed-word-payload-not-translatable','unindexed-pool-text-observed','unresolved'),
                 'non-display or unresolved field not permitted')


def binding_index(corpus):
    index={};aliases=defaultdict(list)
    for resource in corpus['resources']:
        for entry in resource['entries']:
            core.require(entry['id'] not in index,'duplicate corpus identity')
            index[entry['id']]=(resource,entry)
            for alias in entry.get('source_aliases',[]):
                core.require(isinstance(alias,str) and bool(alias),'invalid source alias')
                aliases[alias].append(entry['id'])
    return index,aliases


def resolve_source(index,aliases,target):
    identity=target['id']
    if identity in index:
        core.require(all(i==identity for i in aliases.get(identity,[])),'canonical identity collides with source alias')
        canonical=identity
    else:
        candidates=aliases.get(identity,[])
        core.require(len(candidates)==1,'ambiguous or missing translation alias')
        canonical=candidates[0]
    resource,entry=index[canonical]
    core.require(entry['source_sha256']==target['source_sha256'],'translation source mismatch')
    # Keep the external translation identity. This local binding view does not
    # mutate the frozen corpus or merge resources/cache copies.
    return resource,dict(entry,id=identity,canonical_id=canonical)


def rewrite_fields(original,entries,targets,encoder):
    core.require(len(entries)==len(targets) and bool(entries),'empty or mismatched field selections')
    modified=bytearray(original);ranges=[];report=[]
    for entry,target in zip(entries,targets):
        require_write_policy(target)
        core.require(target.get('status')=='reviewed','field translation not reviewed')
        core.require(entry.get('decode')=='strict' and entry.get('controls')=='recognized','source field quarantined')
        require_source_role(entry)
        core.require(entry['id']==target['id'] and entry['source_sha256']==target['source_sha256'],'source binding mismatch')
        offset=entry['offset'];span,digest=fixed_extent(entry)
        core.require(type(offset) is int and 0<=offset and offset+span<=len(original),'fixed field outside resource')
        core.require(all(offset+span<=a or offset>=b for a,b in ranges),'overlapping field writes')
        hashed_span=fingerprint_extent(entry,span)
        core.require(offset+hashed_span<=len(original),'fingerprint extent outside resource')
        whole=original[offset:offset+hashed_span]
        core.require(core.digest(whole)==digest,'original slot fingerprint mismatch: '+entry['id'])
        if hashed_span>span:
            core.require(core.digest(whole[span:])==entry.get('trailer_sha256'),'original trailer fingerprint mismatch')
        slot=whole[:span]
        length=entry['source_bytes'];core.require(type(length) is int and 0<=length<span,'invalid source length')
        raw=slot[:length];core.require(slot[length]==0 and not any(slot[length:]),'slot terminator or padding is not clean')
        core.require(core.digest(raw)==entry['source_sha256'],'original field fingerprint mismatch')
        source=decode_source(raw,entry)
        from ui_punctuation import validated_empty_suffix
        if target['target'] == '':
            validated_empty_suffix(entry,target)
        else:
            validate_target(source,target['target'],control_policy=control_policy(entry,target['target']))
        encoded=encode_target(encoder,entry,target['target'])
        core.require(len(encoded)<span,'fixed field byte overflow')
        modified[offset:offset+span]=encoded+bytes(span-len(encoded));ranges.append((offset,offset+span))
        report.append(dict(id=entry['id'],canonical_id=entry.get('canonical_id',entry['id']),offset=offset,capacity_bytes=span-1,fingerprint_bytes=hashed_span,encoded_bytes=len(encoded),
                           encoded_hex=encoded.hex(),source_sha256=entry['source_sha256'],target=target['target']))
    for i,(before,after) in enumerate(zip(original,modified)):
        if before!=after:core.require(any(a<=i<b for a,b in ranges),'unselected byte changed')
    return bytes(modified),report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--corpus',type=Path,required=True)
    p.add_argument('--batch',type=Path,action='append',required=True);p.add_argument('--map',type=Path,required=True)
    p.add_argument('--font-resource',type=Path,required=True)
    p.add_argument('--archive',type=Path,required=True);p.add_argument('--archive-sha256',required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    core.require(core.file_digest(a.archive)==a.archive_sha256,'original archive fingerprint mismatch')
    c=json.loads(a.corpus.read_text('utf8'));batches=[json.loads(p.read_text('utf8')) for p in a.batch]
    core.require(all(b.get('schema')==1 and b.get('locale')==batches[0].get('locale') for b in batches),'incompatible translation batches')
    b=dict(locale=batches[0]['locale'],entries=[e for batch in batches for e in batch['entries']])
    mapping=json.loads(a.map.read_text('utf8'));core.require(mapping.get('locale')==b['locale'],'font map locale mismatch')
    encoder=MappedEncoder(mapping['entries'],font_tables=font_data(a.font_resource.read_bytes()))
    index,aliases=binding_index(c)
    groups=defaultdict(list);seen=set()
    for t in b['entries']:
        require_write_policy(t)
        r,e=resolve_source(index,aliases,t)
        core.require(e['canonical_id'] not in seen,'unknown or duplicate target identity');seen.add(e['canonical_id'])
        core.require(r['resource'].startswith('SHIP/'),'unsupported archive member')
        require_source_role(e)
        core.require(t.get('status')=='reviewed' and e['source_sha256']==t['source_sha256'],'unreviewed or mismatched field')
        groups[r['resource']].append((r,e,t))
    out=core.output_directory(a.out);ship=dict(core.archive_entries(a.archive)[1]);receipts=[]
    for resource,rows in sorted(groups.items()):
        name=Path(resource).name;old=ship[name];core.require(core.digest(old)==rows[0][0]['sha256'],'resource fingerprint mismatch')
        if name.endswith('.fpb'):
            _,windows,pool=parse_fpb_raw(old);views={s:pool[o:o+n] for s,o,n in synthesize_implicit_seq0(windows,len(pool))}
            for _,e,t in rows:
                core.require(e.get('decode')=='strict' and e.get('controls')=='recognized','FPB source quarantined')
                core.require(core.digest(views[e['seq']])==e['source_sha256'],'FPB window fingerprint mismatch')
                validate_target(decode_source(views[e['seq']],e),t['target'],control_policy=control_policy(e,t['target']))
            changed,fields=rewrite_fpb(old,{e['seq']:t['target'] for _,e,t in rows},encoder,source_encodings={e['seq']:source_codec(e) for _,e,t in rows},source_control_policies={e['seq']:control_policy(e,t['target']) for _,e,t in rows if control_policy(e,t['target']) is not None})
            _,windows,pool=parse_fpb_raw(changed);views={s:pool[o:o+n] for s,o,n in synthesize_implicit_seq0(windows,len(pool))}
            for _,e,t in rows:core.require(views[e['seq']].split(b'\0',1)[0]==encode_target(encoder,e,t['target']),'FPB target readback mismatch')
        else:
            changed,fields=rewrite_fields(old,[e for _,e,_ in rows],[t for _,_,t in rows],encoder)
            for row in fields:
                start=row['offset'];end=start+row['encoded_bytes'];core.require(changed[start:end].hex()==row['encoded_hex'],'fixed target readback mismatch')
        path=out/name;path.write_bytes(changed);core.require(path.read_bytes()==changed,'resource copy readback mismatch')
        receipts.append(dict(resource=resource,original_sha256=core.digest(old),modified_sha256=core.digest(changed),
                             original_bytes=len(old),modified_bytes=len(changed),fields=fields,selected_fields=len(rows)))
    core.require(core.file_digest(a.archive)==a.archive_sha256,'original archive changed')
    report=dict(schema=1,locale=b['locale'],archive_sha256=a.archive_sha256,corpus_sha256=core.file_digest(a.corpus),
                batch_sha256={str(p):core.file_digest(p) for p in a.batch},map_sha256=core.file_digest(a.map),font_sha256=core.file_digest(a.font_resource),resources=receipts,
                cache_synchronized=False,iso_generated=False,runtime_verified=False)
    (out/'reinsertion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print(f'AUDITED RESOURCE COPY PASS resources={len(receipts)} fields={len(seen)} source_unchanged=true overflow=0 iso_generated=false')


if __name__=='__main__':main()
