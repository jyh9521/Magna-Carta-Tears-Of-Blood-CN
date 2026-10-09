"""Inspect ordinary class metadata and zero-bytecode default property blocks.

Nonzero bytecode is explicitly pending; it is never skipped using its virtual
length as a disk byte count. The observed extra u32 remains uninterpreted.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from research_inventory import package_tables
from extract_script_buffers import FILE_HASH
from audit_object_properties import Reader,ordinary_exports,property_block


def class_body(serial,tables,export,bytecode_reader=None):
    core.require(tables['version']==118,'unsupported class version')
    names=tables['names'];r=Reader(serial)
    def reference():
        value=r.index()
        core.require(-len(tables['imports'])<=value<=len(tables['exports']),'class object reference bounds')
        return value
    def name_index():
        value=r.index();core.require(0<=value<len(names),'class name reference bounds');return value
    def count():
        value=r.index();core.require(0<=value<=len(serial),'class array count');return value
    super_ref=reference();next_ref=reference();script_ref=reference();children_ref=reference();friendly=name_index()
    core.require(super_ref==export['super_index'],'class super/table disagreement')
    core.require(names[friendly]==export['name'],'class friendly name disagreement')
    line=r.integer('i');text_pos=r.integer('i')
    observed_word=r.integer('I');script_size=r.integer('I')
    header=dict(super_reference=super_ref,next_reference=next_ref,script_reference=script_ref,
        children_reference=children_ref,friendly_name=names[friendly],line=line,text_position=text_pos,
        observed_pre_script_word=observed_word,observed_pre_script_word_semantic='unverified',
        virtual_script_bytes=script_size,script_start=r.pos)
    if script_size and bytecode_reader is None:
        return dict(status='nonzero-bytecode-pending',header=header,defaults_complete=False,
            remaining_bytes=len(serial)-r.pos,remaining_sha256=core.digest(serial[r.pos:]))
    script=None
    if script_size:
        script=bytecode_reader(r,script_size,tables)
    probe=r.integer('Q');ignore=r.integer('Q');labels=r.integer('H');state_flags=r.integer('I')
    class_flags=r.integer('I');guid=r.take(16).hex()
    dependencies=[]
    for _ in range(count()):dependencies.append(dict(reference=reference(),deep=r.integer('I'),crc=r.integer('I')))
    imports=[name_index() for _ in range(count())]
    within=reference();config=name_index();hide=[name_index() for _ in range(count())]
    start=r.pos;block=property_block(serial[start:],names)
    core.require(block['native_tail_bytes']==0,'class defaults trailing bytes')
    for row in block['properties']:
        row['tag_offset']+=start;row['value_offset']+=start
    block['start']+=start;block['end']+=start
    return dict(status='bounded-bytecode-defaults-read' if script_size else 'zero-bytecode-defaults-read',header=header,
        script=script,
        state=dict(probe_mask=probe,ignore_mask=ignore,label_table_offset=labels,flags=state_flags),
        class_flags=class_flags,guid=guid,dependencies=dependencies,package_import_names=imports,
        within_reference=within,config_name=names[config],hide_categories=[names[n] for n in hide],
        defaults_complete=True,property_block=block,runtime_visibility_verified=False)


def audit(path,out,bytecode_reader=None):
    core.require(core.file_digest(path)==FILE_HASH,'FILE identity mismatch')
    a=Afs.open(path);names=filename_toc(a);out=core.output_directory(out)
    counts=Counter();classes=[];strings=[];questions=[]
    with path.open('rb') as stream:
        for index,name in enumerate(names):
            blob=a.read_entry(index,stream)
            if not blob.startswith(bytes.fromhex('c1832a9e')):continue
            tables=package_tables(blob);package_hash=core.digest(blob)
            for export in ordinary_exports(blob,tables):
                if export['class_index']!=0:continue
                ident=f'FILE/{name}/export/{export["index"]}'
                serial=blob[export['offset']:export['offset']+export['size']]
                common=dict(id=ident,package=name,package_sha256=package_hash,export=export,
                    serial_sha256=core.digest(serial),editable=False)
                try:body=class_body(serial,tables,export,bytecode_reader)
                except (ValueError,UnicodeError) as error:
                    questions.append(dict(id=ident,error=str(error)));continue
                classes.append(dict(common,**body));counts[body['status']]+=1
                if not body['defaults_complete']:continue
                counts['default_tags']+=len(body['property_block']['properties'])
                for number,row in enumerate(body['property_block']['properties']):
                    if row['type']!=13:continue
                    strings.append(dict(id=ident+f'/default-property/{number}',package=name,owner=export['name'],
                        source_role='class-default-reference',semantic='unverified',runtime_visibility_verified=False,
                        absolute_offset=export['offset']+row['value_offset'],**row))
    core.require(core.file_digest(path)==FILE_HASH,'FILE changed')
    summary=dict(source_sha256=FILE_HASH,counts=dict(counts),classes=len(classes),
        string_properties=len(strings),parse_questions=len(questions),complete_game_text=False,
        class_defaults_complete=bool(classes) and not questions and all(c['defaults_complete'] for c in classes),
        bytecode_decoder_complete=False)
    for filename,value in [('classes.json',classes),('strings.json',strings),('questions.json',questions),('summary.json',summary)]:
        p=out/filename;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        core.require(json.loads(p.read_text('utf8'))==value,'output reopen mismatch')
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.archive,a.out),sort_keys=True))
if __name__=='__main__':main()
