"""Read-only bounded repetition correspondence for ordinary script prefixes.

This is a diagnostic source oracle, not a streaming bytecode reader. Optional
repeated bytes are retained, never deleted, executed or treated as editable.
"""
from __future__ import annotations
import argparse,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from audit_container_payloads import unpack_chunks
from audit_object_properties import ordinary_exports
from research_inventory import package_tables
from audit_compiled_scripts import body
from audit_bundle_contexts import BUNDLE_HASH
from extract_script_buffers import FILE_HASH


def repetition_sites(raw,script):
    start,end=script['start'],script['end'];tokens=script['tokens']
    core.require(0<=start<=end<=len(raw),'script source bounds')
    previous=start-1;sites={};stack=[];children={};subtree_ends={}
    for number,t in enumerate(tokens):
        at=t['offset'];depth=t['depth']
        core.require(previous<at<end and at>=start,'token source order/bounds')
        core.require(raw[at]==t['opcode'],'token/source disagreement')
        core.require(0<=depth<64,'token depth bounds')
        while stack and tokens[stack[-1]]['depth']>=depth:subtree_ends[stack.pop()]=at
        core.require(depth==len(stack),'token depth discontinuity')
        if stack:children.setdefault(stack[-1],[]).append(number)
        stack.append(number);sites[at]='opcode';previous=at
    while stack:subtree_ends[stack.pop()]=end
    core.require(bool(tokens)==(start<end),'script token inventory')
    for number,t in enumerate(tokens):
        if t['opcode']==0x2f:
            at=subtree_ends[number]-2
            core.require(at>t['offset'] and at+2<=end,'iterator trailing word bounds')
            sites[at]='iterator-word-low-byte'
        if t['opcode'] in (0x12,0x19):
            direct=children.get(number,[])
            core.require(len(direct)==2,'context child inventory')
            at=tokens[direct[1]]['offset']-3
            core.require(at>tokens[direct[0]]['offset'] and at+3<=end,'context skip word bounds')
            sites[at]='context-word-low-byte'
    return sites


def align_prefix(bundle,offset,raw,script):
    sites=repetition_sites(raw,script);start,end=script['start'],script['end']
    core.require(0<=offset<=len(bundle),'candidate bounds')
    core.require(bundle[offset:offset+start]==raw[:start],'candidate header mismatch')
    states={offset+start:1}
    for source_offset in range(start,end):
        value=raw[source_offset];following={}
        for pos,ways in states.items():
            if pos>=len(bundle) or bundle[pos]!=value:continue
            following[pos+1]=min(2,following.get(pos+1,0)+ways)
            if source_offset in sites and pos+1<len(bundle) and bundle[pos+1]==value:
                following[pos+2]=min(2,following.get(pos+2,0)+ways)
        if not following:return dict(matched=False,first_source_mismatch=source_offset,last_stream_positions=sorted(states))
        core.require(len(following)<=64,'alignment state limit')
        states=following
    return dict(matched=True,ends=[dict(offset=pos,bytes=pos-offset,sha256=core.digest(bundle[offset:pos]),
        extra_bytes=pos-offset-end,alignment_paths='one' if ways==1 else 'at-least-two') for pos,ways in sorted(states.items())],
        unique_end=len(states)==1,site_counts=dict(Counter(sites.values())),semantic='bounded-repetition-correspondence',
        independent_stream_reader=False,execution_verified=False,editable=False)


def header_positions(bundle,header):
    core.require(len(header)>=21,'script header too short');positions=[];start=0
    while True:
        pos=bundle.find(header,start)
        if pos<0:return positions
        positions.append(pos);start=pos+1


def audit(archive,out):
    core.require(core.file_digest(archive)==FILE_HASH,'FILE identity mismatch')
    a=Afs.open(archive);names=filename_toc(a);rows=[];counts=Counter();packages={}
    with archive.open('rb') as f:
        bundle,_=unpack_chunks(a.read_entry(names.index('celfid.lix'),f))
        core.require(core.digest(bundle)==BUNDLE_HASH,'bundle identity mismatch')
        for index,name in enumerate(names):
            blob=a.read_entry(index,f)
            if not blob.startswith(bytes.fromhex('c1832a9e')):continue
            tables=package_tables(blob);package_hash=core.digest(blob);package_counts=Counter()
            for e in ordinary_exports(blob,tables):
                if e['class'] not in ('Function','NativeFunction','State','Struct'):continue
                raw=blob[e['offset']:e['offset']+e['size']];parsed=body(raw,tables,e);script=parsed['script']
                positions=header_positions(bundle,raw[:script['start']])
                candidates=[dict(header_offset=pos,**align_prefix(bundle,pos,raw,script)) for pos in positions]
                status='header-unmatched' if not positions else 'correspondence-fit' if all(c['matched'] for c in candidates) else 'correspondence-mismatch'
                counts[status]+=1;package_counts[status]+=1
                rows.append(dict(id=f'FILE/{name}/export/{e["index"]}',package=name,export=e['index'],name=e['name'],
                    class_name=e['class'],package_sha256=package_hash,serial_sha256=core.digest(raw),
                    source_header_offset=e['offset'],source_prefix_bytes=script['end'],source_script_bytes=script['disk_bytes'],
                    source_script_sha256=script['sha256'],literal_constants=len(script['strings']),
                    status=status,header_occurrences=len(positions),candidates=candidates,
                    tail_and_children_mapping_verified=False,runtime_visibility_verified=False,editable=False))
            if package_counts:packages[name]=dict(package_counts)
    core.require(core.file_digest(archive)==FILE_HASH,'FILE changed')
    matched=[r for r in rows if r['status']=='correspondence-fit']
    summary=dict(schema=1,source_sha256=FILE_HASH,bundle_sha256=BUNDLE_HASH,ordinary_script_objects=len(rows),
        statuses=dict(counts),packages=packages,header_occurrences=sum(r['header_occurrences'] for r in rows),
        ambiguous_header_objects=sum(r['header_occurrences']>1 for r in rows),
        candidate_alignments=sum(len(r['candidates']) for r in rows),
        matched_candidate_alignments=sum(c['matched'] for r in rows for c in r['candidates']),
        multiple_end_candidates=sum(c['matched'] and not c['unique_end'] for r in rows for c in r['candidates']),
        ambiguous_path_candidates=sum(c['matched'] and any(e['alignment_paths']!='one' for e in c['ends']) for r in rows for c in r['candidates']),
        matched_source_script_bytes=sum(r['source_script_bytes'] for r in matched),
        literal_constants_in_fitting_source_objects=sum(r['literal_constants'] for r in matched),
        all_ordinary_scripts_inspected=True,full_stream_mapping_verified=False,full_vm_semantics_verified=False,
        complete_game_text=False,source_modified=False,translation_gate='coverage-audit-pending')
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    for name,value in [('correspondence.json',rows),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        core.require(json.loads(p.read_text('utf8'))==value,'JSON reopen')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();print(json.dumps(audit(args.archive,args.out),sort_keys=True))
