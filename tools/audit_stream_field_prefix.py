"""Bounded source-oracle comparison of the initial Core.u streamed field chain.

This deliberately stops at the first mismatch. It is not a streamed loader.
"""
from __future__ import annotations
import argparse,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from audit_container_payloads import unpack_chunks,probe_all_packages
from audit_object_properties import Reader,ordinary_exports,property_block
from research_inventory import package_tables
from audit_compiled_scripts import body,compiled_script
from audit_class_defaults import class_body
from audit_bundle_contexts import BUNDLE_HASH
from extract_script_buffers import FILE_HASH


def compare_piece(bundle,pos,raw):
    core.require(0<=pos<=len(bundle),'stream piece start')
    end=pos+len(raw)
    if end>len(bundle):return dict(matched=False,reason='stream truncated',offset=pos,bytes=len(raw))
    actual=bundle[pos:end]
    if actual==raw:return dict(matched=True,offset=pos,bytes=len(raw),sha256=core.digest(raw))
    delta=next(i for i,(a,b) in enumerate(zip(actual,raw)) if a!=b)
    return dict(matched=False,reason='source bytes differ',offset=pos,bytes=len(raw),first_difference=delta,
        expected_sha256=core.digest(raw),observed_sha256=core.digest(actual),expected_byte=raw[delta],observed_byte=actual[delta])


def probe(bundle,original,stream_table,root_index=4):
    tables=package_tables(original);exports=ordinary_exports(original,tables)
    core.require(stream_table['wrapper_path']=='../System/UFile/Core.u','unsupported oracle package')
    core.require(tables['names']==stream_table['names'] and len(exports)==len(stream_table['exports']),'oracle table inventory mismatch')
    for e,se in zip(exports,stream_table['exports']):
        core.require(all(e[k]==se[k] for k in ['index','name','class_index','outer','super_index','flags']),'stream/original export metadata mismatch')
        core.require((e['offset'],e['size'])==(se['declared_offset'],se['declared_size']),'stream original coordinates differ')
    core.require(1<=root_index<=len(exports),'root index bounds')
    pos=stream_table['table_end'];seen=set();chunks=[];edges=[];completed=[];question=None
    def piece(raw,index,part,source_offset):
        nonlocal pos
        result=compare_piece(bundle,pos,raw)
        core.require(result['matched'],json.dumps(dict(export=index,part=part,**result),sort_keys=True))
        if raw:chunks.append(dict(export=index,name=exports[index-1]['name'],part=part,source_offset=source_offset,**result))
        pos+=len(raw)
    def obj(index,depth=0,follow_next=True):
        if not index or index in seen:return
        core.require(index>0 and index<=len(exports),'external dependency unresolved')
        core.require(depth<512,'field chain depth limit');seen.add(index);e=exports[index-1]
        raw=original[e['offset']:e['offset']+e['size']]
        if e['class_index']==0:
            p=class_body(raw,tables,e,compiled_script);split=p['script']['end'] if p['script'] else p['header']['script_start'];nxt=p['header']['next_reference'];child=p['header']['children_reference']
        elif e['class'] in ('Function','NativeFunction','Struct','State'):
            p=body(raw,tables,e);split=p['script']['end'];nxt=p['header']['next_reference'];child=p['header']['children_reference']
        else:
            p=property_block(raw,tables['names']);r=Reader(raw,p['end']);r.index();nxt=r.index();split=len(raw);child=0
        piece(raw[:split],index,'prefix',e['offset'])
        if child:edges.append(dict(parent=index,child=child,kind='children-chain'));obj(child,depth+1)
        piece(raw[split:],index,'tail',e['offset']+split)
        completed.append(index)
        if e['class']=='StructProperty':
            # Only single-byte terminal target references observed in this prefix.
            target=Reader(raw,len(raw)-1).index();core.require(0<target<64,'unsupported struct target encoding')
            edges.append(dict(parent=index,child=target,kind='struct-target-without-next-chain'));obj(target,depth+1,False)
        if follow_next and nxt:edges.append(dict(parent=index,child=nxt,kind='next-field-chain'));obj(nxt,depth+1)
    try:obj(root_index)
    except ValueError as error:question=str(error)
    return dict(chunks=chunks,edges=edges,completed_piece_sets=sorted(completed),visited_objects=len(seen),
        matched_prefix_bytes=pos-stream_table['table_end'],stop_offset=pos,question=question,
        root_complete=root_index in completed,full_stream_mapping_verified=False)


def audit(archive,out):
    core.require(core.file_digest(archive)==FILE_HASH,'FILE identity mismatch')
    a=Afs.open(archive);names=filename_toc(a)
    with archive.open('rb') as stream:
        bundle,_=unpack_chunks(a.read_entry(names.index('celfid.lix'),stream));original=a.read_entry(names.index('Core.u'),stream)
    core.require(core.digest(bundle)==BUNDLE_HASH,'bundle identity mismatch')
    table=next(t for t in probe_all_packages(bundle) if t['wrapper_path']=='../System/UFile/Core.u')
    result=probe(bundle,original,table)
    core.require(core.file_digest(archive)==FILE_HASH,'FILE changed')
    summary=dict(schema=1,source_sha256=FILE_HASH,bundle_sha256=BUNDLE_HASH,ordinary_package_sha256=core.digest(original),
        stream_table_end=table['table_end'],visited_objects=result['visited_objects'],matched_chunks=len(result['chunks']),
        completed_piece_sets=len(result['completed_piece_sets']),matched_prefix_bytes=result['matched_prefix_bytes'],
        stop_offset=result['stop_offset'],first_mismatch=result['question'],root_complete=result['root_complete'],
        full_stream_mapping_verified=False,complete_game_text=False,source_modified=False,translation_gate='coverage-audit-pending')
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    for name,value in [('prefix-map.json',result),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(value,indent=2)+'\n',encoding='utf8');core.require(json.loads(p.read_text('utf8'))==value,'JSON reopen')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.archive,a.out),sort_keys=True))
