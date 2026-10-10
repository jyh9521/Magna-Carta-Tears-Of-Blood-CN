"""Extend exact stream context with bounded texture and map property records.

No declared-size skipping of unknown native payloads is allowed.
"""
from pathlib import Path
from collections import Counter
import argparse, json, sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from audit_container_payloads import unpack_chunks,probe_all_packages
from audit_bundle_contexts import BUNDLE_HASH
from extract_script_buffers import FILE_HASH
from audit_stream_candidate_contexts import wrapper_record,SpanIndex
from audit_stream_texture import stream_mips
from audit_texture_mips import palette,property_value
from audit_object_properties import property_block,ordinary_exports,Reader,string_value
from audit_class_defaults import class_body
from audit_compiled_scripts import body,compiled_script
from research_inventory import package_tables
CONTEXT_HASH='7fab9f9cd88294c313ee51bbcfceba745b3dcc40045a204fed40aeb32d75ecba'


def commandlet_oracle(bundle,source,tables,exports,start=4185028,end=4185368):
    pos=start;seen=set();spans=[]
    def piece(raw,e,part):
        nonlocal pos
        core.require(pos+len(raw)<=end and bundle[pos:pos+len(raw)]==raw,'Commandlet source correspondence mismatch')
        if raw:spans.append(dict(start=pos,end=pos+len(raw),kind='source-identical-commandlet-field',package='Core.u',export=e['index'],part=part,sha256=core.digest(raw)))
        pos+=len(raw)
    def obj(index):
        core.require(index not in seen and 0<index<=len(exports),'Commandlet cycle/reference bounds');seen.add(index)
        e=exports[index-1];raw=source[e['offset']:e['offset']+e['size']]
        if e['class_index']==0:
            p=class_body(raw,tables,e,compiled_script);core.require(p['script'] is None,'unexpected class bytecode')
            split=p['header']['script_start'];nxt=p['header']['next_reference'];child=p['header']['children_reference']
        elif e['class'] in ('Function','NativeFunction','State','Struct'):
            p=body(raw,tables,e);split=p['script']['end'];nxt=p['header']['next_reference'];child=p['header']['children_reference']
        else:
            p=property_block(raw,tables['names']);r=Reader(raw,p['end']);r.index();nxt=r.index();child=0;split=len(raw)
        piece(raw[:split],e,'prefix')
        if child:obj(child)
        piece(raw[split:],e,'tail')
        if nxt:obj(nxt)
    core.require(exports[7]['name']=='Commandlet','Commandlet root identity');obj(8)
    core.require(pos==end,'Commandlet end mismatch')
    return spans


def map_properties(bundle,tables,start=4190811,end=4191209):
    selected=[2,3,5,7,8,1];pos=start;spans=[];records=[]
    for index in selected:
        e=tables['exports'][index-1]
        raw=bundle[pos:end];p=property_block(raw,tables['names'],e['flags']);size=p['end']
        core.require(size==e['declared_size'],'property record size mismatch')
        if e['flags']&0x02000000:
            core.require(p['stack']['node']==e['class_index'] and p['stack']['state_node']==e['class_index'],'property stack class mismatch')
        for prop in p['properties']:
            value=raw[prop['value_offset']:prop['value_offset']+prop['value_bytes']]
            if prop['type']==7:
                core.require(prop['name']=='Char_ID','unreviewed legacy string field');prop.update(string_value(value));prop['semantic']='character-identifier-not-display-name'
            if prop['type'] in (5,6):
                q=Reader(value);ref=q.index();core.require(q.pos==len(value),'tag reference size')
                core.require(0<=ref<len(tables['names']) if prop['type']==6 else -len(tables['imports'])<=ref<=len(tables['exports']),'tag reference bounds')
        spans.append(dict(start=pos,end=pos+size,kind='bounded-map-property-record',export=index,name=e['name'],sha256=core.digest(bundle[pos:pos+size])))
        records.append(dict(export=e,start=pos,end=pos+size,stack=p['stack'],properties=p['properties'],editable=False,runtime_identity_verified=False))
        pos+=size
    core.require(pos==end,'map property sequence end mismatch')
    return spans,records


def segment_candidate(row,spans):
    start,end=row['offset'],row['offset']+row['bytes'];parts=[];pos=start
    for span in spans:
        if span['end']<=pos:continue
        if span['start']>pos:break
        stop=min(end,span['end']);parts.append(dict(start=pos,end=stop,context=span));pos=stop
        if pos==end:return parts
    return None


def audit(file,contexts_path,out):
    core.require(core.file_digest(file)==FILE_HASH and core.file_digest(contexts_path)==CONTEXT_HASH,'input identity mismatch')
    a=Afs.open(file);names=filename_toc(a)
    with file.open('rb') as f:
        b,_=unpack_chunks(a.read_entry(names.index('celfid.lix'),f));original=a.read_entry(names.index('Core.u'),f);ini=a.read_entry(names.index('psx2game.ini'),f)
    core.require(core.digest(b)==BUNDLE_HASH,'bundle mismatch');tables=probe_all_packages(b)
    ct=package_tables(original);spans=commandlet_oracle(b,original,ct,ordinary_exports(original,ct))
    mt=next(t for t in tables if t['package_offset']==4185632)
    core.require(mt['wrapper_path']=='../Maps/00000118.unr' and mt['table_end']==4188034,'map table identity')
    for pos in [4185368,4185500,4188034,4191209,4191341]:
        s=wrapper_record(b,pos,mt['wrapper_path'],mt['original_package_size']);s['kind']='verified-map-wrapper';spans.append(s)
    spans.append(dict(start=mt['package_offset'],end=mt['table_end'],kind='stream-package-table'))
    ms,records=map_properties(b,mt);spans.extend(ms)
    tt=next(t for t in tables if t['wrapper_path']=='../Textures/00014366.utx');e=tt['exports'][0]
    texture=b[3214774:3217619];tp=property_block(texture,tt['names'],e['flags'])
    core.require(tp['end']==61 and property_value(texture,tp['properties'],'Palette',5)==b'\x02','texture property geometry')
    mips=stream_mips(texture,tp['end'],e['declared_offset']);pal=b[3217619:3218646];pp=property_block(pal,tt['names'],tt['exports'][1]['flags']);palette(pal,pp['end'])
    spans.append(dict(start=3214774,end=3217619,kind='bounded-texture-pixels-and-properties',sha256=core.digest(texture)))
    spans.append(dict(start=3217619,end=3218646,kind='bounded-palette-colors',sha256=core.digest(pal)))
    core.require(b[528:528+len(ini)]==ini,'initial config mirror');ini_end=528+len(ini)
    spans.append(dict(start=528,end=ini_end,kind='source-identical-config-body'))
    engine=next(t for t in tables if t['wrapper_path']=='../System/UFile/Engine.u')
    s=wrapper_record(b,ini_end,engine['wrapper_path'],engine['original_package_size']);s['kind']='source-wrapper-record';spans.append(s)
    spans=SpanIndex(spans).rows
    rows=json.loads(contexts_path.read_text('utf8'));updated=[]
    for row in rows:
        start,end=row['offset'],row['offset']+row['bytes'];core.require(core.digest(b[start:end])==row['source_sha256'],'candidate bytes mismatch')
        r=dict(row)
        if r['category']=='unresolved-byte-context':
            parts=segment_candidate(r,spans)
            if parts:
                for part in parts:part['sha256']=core.digest(b[part['start']:part['end']])
                r.update(category=parts[0]['context']['kind'] if len(parts)==1 else 'verified-composite-boundary-context',context_parts=parts)
        updated.append(r)
    summary=dict(schema=1,candidates=len(rows),counts=dict(sorted(Counter(r['category'] for r in updated).items())),recontextualized=sum(a!=z for a,z in zip(rows,updated)),
        commandlet_bytes=340,map_property_records=len(records),map_property_bytes=398,texture_mips=len(mips),map_wrappers=5,
        unresolved_byte_contexts=sum(r['category']=='unresolved-byte-context' for r in updated),source_modified=False,complete_game_text=False,
        full_native_mesh_verified=False,full_map_native_verified=False,runtime_visibility_verified=False,translation_gate='coverage-audit-pending')
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    for name,value in [('contexts.json',updated),('spans.json',spans),('map-properties.json',records),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8');core.require(json.loads(p.read_text('utf8'))==value,'JSON reopen')
    core.require(core.file_digest(file)==FILE_HASH and core.file_digest(contexts_path)==CONTEXT_HASH,'input changed')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['file','contexts','out']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.file,a.contexts,a.out),sort_keys=True))
