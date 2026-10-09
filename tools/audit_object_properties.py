"""Read ordinary UE2 instance property blocks, preserving unparsed native tails.

Generic tag rules follow UEViewer; stack framing is checked against original
Entry.unr objects. Class defaults and streamed serials require separate readers.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from research_inventory import package_tables, compact
from extract_script_buffers import FILE_HASH

HAS_STACK=0x02000000


class Reader:
    def __init__(self,data,pos=0):
        self.data=data;self.pos=pos
        core.require(0<=pos<=len(data),'reader start bounds')

    def take(self,size):
        core.require(size>=0 and self.pos+size<=len(self.data),'truncated object field')
        start=self.pos;self.pos+=size
        return self.data[start:self.pos]

    def integer(self,fmt):
        return struct.unpack('<'+fmt,self.take(struct.calcsize('<'+fmt)))[0]

    def index(self):
        try:value,end=compact(self.data,self.pos)
        except (IndexError,ValueError) as error:raise ValueError('truncated/invalid compact index') from error
        core.require(end-self.pos<=5 and -0x7fffffff<=value<=0x7fffffff,'compact index range')
        self.pos=end
        return value


def ordinary_exports(blob,tables):
    """Reuse package inventory and independently retain export flags/super refs."""
    r=Reader(blob,struct.unpack_from('<I',blob,24)[0]);rows=[]
    for export in tables['exports']:
        cl=r.index();sup=r.index();outer=r.integer('i');name=r.index();flags=r.integer('I');size=r.index()
        offset=r.index() if size>0 else 0
        core.require(0<=name<len(tables['names']),'export name index')
        core.require(-len(tables['imports'])<=sup<=len(tables['exports']),'super reference bounds')
        core.require((cl,outer,tables['names'][name],size,offset)==
            (export['class_index'],export['outer'],export['name'],export['size'],export['offset']),
            'export reader disagreement')
        rows.append(dict(export,flags=flags,super_index=sup))
    return rows


def property_block(serial,names,flags=0):
    r=Reader(serial);stack=None
    if flags&HAS_STACK:
        node=r.index();state=r.index();probe=r.integer('Q');latent=r.integer('I')
        offset=r.index() if node else None
        stack=dict(node=node,state_node=state,probe_mask=probe,latent_action=latent,
                   code_offset=offset,bytes=r.pos)
    start=r.pos;rows=[]
    while r.pos<len(serial):
        tag_start=r.pos;name=r.index()
        core.require(0<=name<len(names),'property name index')
        if names[name]=='None':
            return dict(start=start,end=r.pos,stack=stack,properties=rows,
                        native_tail_bytes=len(serial)-r.pos,
                        native_tail_sha256=core.digest(serial[r.pos:]),
                        native_semantics_verified=False)
        info=r.integer('B');kind=info&15
        core.require(1<=kind<=15,'property type')
        structure=None
        if kind==10:
            sn=r.index();core.require(0<=sn<len(names),'struct name index');structure=names[sn]
        size_code=(info>>4)&7
        size=[1,2,4,12,16][size_code] if size_code<5 else r.integer({5:'B',6:'H',7:'I'}[size_code])
        array_index=0
        if kind!=3 and info&128:
            first=r.integer('B')
            if first<128:array_index=first
            elif first&64:array_index=int.from_bytes(bytes([first])+r.take(3),'big')&0x3fffff
            else:array_index=int.from_bytes(bytes([first])+r.take(1),'big')&0x3fff
        if kind==3:size=0
        value_offset=r.pos;value=r.take(size)
        row=dict(name=names[name],type=kind,tag_offset=tag_start,value_offset=value_offset,
                 value_bytes=size,value_sha256=core.digest(value),array_index=array_index,
                 structure=structure,editable=False)
        if kind==3:row['bool_value']=bool(info&128)
        if kind==13:row.update(string_value(value))
        rows.append(row)
    raise ValueError('property terminator missing')


def string_value(value):
    r=Reader(value);count=r.index()
    if count==0:
        core.require(r.pos==len(value),'empty string trailing bytes')
        return dict(text='',encoding='empty',count=0)
    unit=2 if count<0 else 1;raw=r.take(abs(count)*unit)
    core.require(r.pos==len(value) and raw.endswith(bytes(unit)), 'property string length/terminator')
    codec='utf-16-le' if unit==2 else 'cp949'
    return dict(text=raw[:-unit].decode(codec,errors='strict'),encoding=codec,count=count)


def audit(path,out):
    core.require(core.file_digest(path)==FILE_HASH,'FILE identity mismatch')
    a=Afs.open(path);names=filename_toc(a);out=core.output_directory(out)
    counts=Counter();objects=[];strings=[];questions=[]
    with path.open('rb') as stream:
        for index,name in enumerate(names):
            blob=a.read_entry(index,stream)
            if not blob.startswith(bytes.fromhex('c1832a9e')):continue
            tables=package_tables(blob);package_hash=core.digest(blob);counts['ordinary_packages']+=1
            for export in ordinary_exports(blob,tables):
                ident=f'FILE/{name}/export/{export["index"]}'
                serial=blob[export['offset']:export['offset']+export['size']]
                common=dict(id=ident,package=name,package_sha256=package_hash,export=export,
                            serial_sha256=core.digest(serial),editable=False)
                if export['class_index']==0:
                    counts['class_defaults_pending']+=1
                    objects.append(dict(common,status='class-native-and-defaults-pending'));continue
                if not serial:
                    counts['zero_size']+=1;objects.append(dict(common,status='zero-size'));continue
                try:body=property_block(serial,tables['names'],export['flags'])
                except (ValueError,UnicodeError,struct.error) as error:
                    questions.append(dict(id=ident,error=str(error)));continue
                counts['instance_property_blocks']+=1;counts['tags']+=len(body['properties'])
                counts['with_stack']+=body['stack'] is not None
                counts['with_native_tail']+=body['native_tail_bytes']>0
                objects.append(dict(common,status='property-block-read',**body))
                for number,row in enumerate(body['properties']):
                    if row['type']!=13:continue
                    strings.append(dict(id=ident+f'/property/{number}',source_role='instance-property-reference',
                        semantic='unverified',runtime_visibility_verified=False,
                        absolute_offset=export['offset']+row['value_offset'],**row))
    core.require(core.file_digest(path)==FILE_HASH,'FILE changed')
    summary=dict(source_sha256=FILE_HASH,counts=dict(counts),string_properties=len(strings),
        parse_questions=len(questions),complete_game_text=False,streamed_serial_mapping='unresolved',
        class_defaults_complete=False,native_serial_semantics_complete=False)
    for filename,value in [('objects.json',objects),('strings.json',strings),('questions.json',questions),('summary.json',summary)]:
        p=out/filename;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        core.require(json.loads(p.read_text('utf8'))==value,'output reopen mismatch')
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.archive,a.out),sort_keys=True))
if __name__=='__main__':main()
