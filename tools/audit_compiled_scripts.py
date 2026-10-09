"""Bounded structural audit of ordinary Function/NativeFunction/State/Struct.

The numeric token grammar is checked against this original package set, not
declared a general Unreal VM implementation. No execution or writing is done.
"""
from __future__ import annotations
import argparse,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from audit_object_properties import Reader,ordinary_exports,property_block
from research_inventory import package_tables
from extract_script_buffers import FILE_HASH


def compiled_script(reader,virtual_size,tables):
    core.require(0<=virtual_size<=4*1024*1024,'script size limit')
    start=reader.pos;virtual=0;tokens=[];references=[];strings=[]
    def fixed(n):
        nonlocal virtual
        raw=reader.take(n);virtual+=n;return raw
    def reference(name=False):
        nonlocal virtual
        at=reader.pos;value=reader.index();virtual+=4
        if name:core.require(0<=value<len(tables['names']),'script name reference bounds')
        else:core.require(-len(tables['imports'])<=value<=len(tables['exports']),'script object reference bounds')
        references.append(dict(offset=at,value=value,kind='name' if name else 'object'))
        return value
    def token(depth=0,parent=None):
        nonlocal virtual
        core.require(depth<64,'script recursion limit')
        at=reader.pos;vo=virtual;x=reader.integer('B');virtual+=1
        tokens.append(dict(offset=at,virtual_offset=vo,opcode=x,depth=depth,parent_opcode=parent))
        child=lambda:token(depth+1,x)
        if x>=0x60:
            if x<0x70:fixed(1)
            while child()!=0x16:pass
        elif x in (0,1,2,0x20,0x29,0x47,0x48):reference()
        elif x in (0x1b,0x38,0x1c):
            reference(x!=0x1c)
            while child()!=0x16:pass
        elif x==0x21:reference(True)
        elif x in (0x1d,0x1e):fixed(4)
        elif x in (0x22,0x23):fixed(12)
        elif x in (0x24,0x2c):fixed(1)
        elif x in (0x1f,0x34):
            unit=1 if x==0x1f else 2;raw=bytearray();value_offset=reader.pos
            while True:
                chunk=fixed(unit)
                if chunk==bytes(unit):break
                raw.extend(chunk)
            codec='cp949' if unit==1 else 'utf-16-le'
            try:text=bytes(raw).decode(codec,errors='strict');error=None
            except UnicodeError as e:text=None;error=str(e)
            strings.append(dict(opcode=x,token_offset=at,offset=value_offset,source_bytes=len(raw),
                sha256=core.digest(bytes(raw)),encoding=codec,text=text,decode_error=error,
                terminated=True,editable=False,semantic='compiled-string-reference',runtime_visibility_verified=False))
        elif x==0x06:fixed(2)
        elif x==0x0a:
            if fixed(2)!=b'\xff\xff':child()
        elif x==0x0c:
            while True:
                name=reference(True);fixed(4)
                if tables['names'][name]=='None':break
        elif x in (0x05,0x2b):fixed(1);child()
        elif x in (0x07,0x09,0x18):fixed(2);child()
        elif x in (0x12,0x19):child();fixed(3);child()
        elif x in (0x13,0x2e,0x36):reference();child()
        elif x in (0x32,0x33):reference();child();child()
        elif x in (0xf,0x10,0x14,0x1a):child();child()
        elif x==0x11:
            for _ in range(4):child()
        elif x==0x2f:child();fixed(2)
        elif x in (4,0xd,0xe,0x2d,0x37) or (0x39<=x<=0x59):child()
        elif x in (8,0xb,0x15,0x16,0x17,0x25,0x26,0x27,0x28,0x2a,0x30,0x31):pass
        else:raise ValueError(f'unsupported compiled opcode 0x{x:02x} at {at}')
        core.require(virtual<=virtual_size,'script virtual size overflow')
        return x
    while virtual<virtual_size:token()
    core.require(virtual==virtual_size,'script virtual size mismatch')
    return dict(start=start,end=reader.pos,disk_bytes=reader.pos-start,virtual_bytes=virtual,
        sha256=core.digest(reader.data[start:reader.pos]),tokens=tokens,references=references,
        strings=strings,opcode_semantics_complete=False,execution_verified=False,editable=False)


def body(serial,tables,export):
    core.require(tables['version']==118,'unsupported script package version')
    props=property_block(serial,tables['names'],export['flags']);r=Reader(serial,props['end'])
    refs=[r.index() for _ in range(4)];friendly=r.index()
    core.require(all(-len(tables['imports'])<=v<=len(tables['exports']) for v in refs),'struct header references')
    core.require(refs[0]==export['super_index'],'script super/table disagreement')
    core.require(0<=friendly<len(tables['names']),'script friendly name bounds')
    # Operator-friendly symbols legitimately differ from exported function names.
    header=dict(super_reference=refs[0],next_reference=refs[1],script_reference=refs[2],children_reference=refs[3],
        friendly_name=tables['names'][friendly],line=r.integer('i'),text_position=r.integer('i'),
        observed_pre_script_word=r.integer('I'),observed_pre_script_word_semantic='unverified',virtual_script_bytes=r.integer('I'))
    script=compiled_script(r,header['virtual_script_bytes'],tables);tail={}
    if export['class'] in ('Function','NativeFunction'):
        tail=dict(precedence_byte=r.integer('B'),flags=r.integer('I'))
        if tail['flags']&0x40:tail['replication_offset']=r.integer('H')
        if export['class']=='NativeFunction':tail['native_index']=r.integer('H')
    elif export['class']=='State':
        tail=dict(probe_mask=r.integer('Q'),ignore_mask=r.integer('Q'),label_table_offset=r.integer('H'),flags=r.integer('I'))
    elif export['class']!='Struct':raise ValueError('unsupported script export class')
    core.require(r.pos==len(serial),'script object trailing bytes')
    return dict(property_block=props,header=header,script=script,tail=tail,all_bytes_closed=True)


def audit(path,out):
    core.require(core.file_digest(path)==FILE_HASH,'FILE identity mismatch')
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output directory not empty')
    a=Afs.open(path);names=filename_toc(a);objects=[];strings=[];questions=[];counts=Counter();opcodes=Counter()
    with path.open('rb') as stream:
        for ix,name in enumerate(names):
            blob=a.read_entry(ix,stream)
            if not blob.startswith(bytes.fromhex('c1832a9e')):continue
            tables=package_tables(blob);exports=ordinary_exports(blob,tables);by_index={e['index']:e for e in exports}
            for e in exports:
                if e['class'] not in ('Function','NativeFunction','State','Struct'):continue
                ident=f'FILE/{name}/export/{e["index"]}';serial=blob[e['offset']:e['offset']+e['size']]
                common=dict(id=ident,package=name,package_sha256=core.digest(blob),export=e,
                    serial_sha256=core.digest(serial),editable=False)
                counts[e['class']]+=1
                try:b=body(serial,tables,e)
                except (ValueError,UnicodeError) as error:
                    questions.append(dict(common,error=str(error)));continue
                objects.append(dict(common,**b));opcodes.update(t['opcode'] for t in b['script']['tokens'])
                for n,row in enumerate(b['script']['strings']):
                    absolute=e['offset']+row['offset'];raw=blob[absolute:absolute+row['source_bytes']]
                    core.require(core.digest(raw)==row['sha256'],'literal absolute span mismatch')
                    strings.append(dict(id=ident+f'/string/{n}',package=name,owner=e['name'],owner_index=e['outer'],
                        owner_class=by_index[e['outer']]['name'] if e['outer'] in by_index else None,
                        serial_sha256=common['serial_sha256'],absolute_offset=absolute,**row))
    core.require(core.file_digest(path)==FILE_HASH,'FILE changed')
    summary=dict(schema=1,source_sha256=FILE_HASH,export_counts=dict(counts),objects=len(objects),
        parse_questions=len(questions),all_selected_exports_closed=len(objects)==sum(counts.values()) and not questions,
        disk_script_bytes=sum(o['script']['disk_bytes'] for o in objects),
        virtual_script_bytes=sum(o['script']['virtual_bytes'] for o in objects),tokens=sum(opcodes.values()),
        opcodes={f'0x{k:02x}':v for k,v in sorted(opcodes.items())},string_constants=len(strings),
        decode_failures=sum(s['decode_error'] is not None for s in strings),
        hangul_constants=sum(s['text'] is not None and any('\uac00'<=c<='\ud7a3' for c in s['text']) for s in strings),
        full_vm_semantics_verified=False,streamed_scripts_audited=False,source_modified=False,
        complete_game_text=False,translation_gate='coverage-audit-pending')
    for name,value in [('objects.json',objects),('strings.json',strings),('questions.json',questions),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        core.require(json.loads(p.read_text('utf8'))==value,'JSON reopen mismatch')
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.archive,a.out),sort_keys=True))
if __name__=='__main__':main()
