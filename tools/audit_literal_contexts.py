"""Resolve structural ancestry and table references for compiled string constants.

Labels are package symbol evidence, not execution or visibility proof.
"""
from __future__ import annotations
import argparse,json,sys
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from research_inventory import package_tables
from audit_object_properties import ordinary_exports,Reader
from audit_compiled_scripts import body
from extract_script_buffers import FILE_HASH


def ancestry(tokens):
    parents={};stack=[];previous=-1
    for t in tokens:
        core.require(t['offset']>previous,'token order');previous=t['offset']
        depth=t['depth'];core.require(0<=depth<=len(stack),'token depth jump')
        stack=stack[:depth]
        core.require(t['parent_opcode']==(stack[-1]['opcode'] if stack else None),'token parent disagreement')
        parents[t['offset']]=list(stack);stack.append(t)
    return parents


def symbolic(token,serial,tables,natives):
    opcode=token['opcode'];r=Reader(serial,token['offset']+1);out=dict(offset=token['offset'],opcode=opcode)
    if opcode>=0x60:
        index=(opcode-0x60)*256+r.integer('B') if opcode<0x70 else opcode
        out.update(reference_kind='native-index',reference_value=index,symbols=sorted(natives.get(index,set())))
    elif opcode in (0x1b,0x38):
        value=r.index();core.require(0<=value<len(tables['names']),'call name bounds')
        out.update(reference_kind='name',reference_value=value,symbols=[tables['names'][value]])
    elif opcode==0x1c:
        value=r.index();core.require(-len(tables['imports'])<=value<=len(tables['exports']),'call object bounds')
        name=tables['exports'][value-1]['name'] if value>0 else tables['imports'][-value-1]['name'] if value<0 else None
        out.update(reference_kind='object',reference_value=value,symbols=[name] if name else [])
    return out


def audit(archive,objects_path,strings_path,out):
    core.require(core.file_digest(archive)==FILE_HASH,'FILE identity mismatch')
    hashes={str(p):core.file_digest(p) for p in (objects_path,strings_path)}
    objects=json.loads(objects_path.read_text('utf8'));strings=json.loads(strings_path.read_text('utf8'))
    core.require(len({o['id'] for o in objects})==len(objects),'duplicate object identity')
    core.require(len({s['id'] for s in strings})==len(strings),'duplicate string identity')
    natives=defaultdict(set)
    for obj in objects:
        if 'native_index' in obj['tail']:natives[obj['tail']['native_index']].add(obj['export']['name'])
    selected=defaultdict(list)
    for row in strings:selected[row['id'].split('/string/')[0]].append(row)
    afs=Afs.open(archive);names=filename_toc(afs);packages={};result=[];all_symbols=Counter();questions=[]
    with archive.open('rb') as stream:
        for obj in objects:
            package=obj['package']
            if package not in packages:
                blob=afs.read_entry(names.index(package),stream);tables=package_tables(blob);exports=ordinary_exports(blob,tables);packages[package]=(blob,tables,exports)
            blob,tables,exports=packages[package];exp=exports[obj['export']['index']-1]
            core.require(core.digest(blob)==obj['package_sha256'] and exp==obj['export'],'compiled object inventory mismatch')
            serial=blob[exp['offset']:exp['offset']+exp['size']]
            core.require(core.digest(serial)==obj['serial_sha256'],'compiled serial hash')
            parsed=body(serial,tables,exp)
            core.require(all(parsed[key]==obj[key] for key in parsed),'compiled object reparse mismatch')
            parents=ancestry(parsed['script']['tokens']);tokens={t['offset']:t for t in parsed['script']['tokens']}
            literals={x['token_offset']:x for x in parsed['script']['strings']}
            core.require(len(selected[obj['id']])==len(literals),'string inventory count')
            for row in selected[obj['id']]:
                original=literals[row['token_offset']]
                core.require(all(row[key]==value for key,value in original.items()),'compiled literal mismatch')
                chain=[symbolic(t,serial,tables,natives) for t in parents[row['token_offset']]]
                calls=[t for t in chain if 'reference_kind' in t]
                missing=[t for t in calls if not t['symbols']]
                if missing:questions.append(dict(id=row['id'],unresolved_calls=missing))
                all_symbols.update(symbol for t in calls for symbol in t['symbols'])
                result.append(dict(row,parent_opcode=tokens[row['token_offset']]['parent_opcode'],ancestors=chain,call_context=calls,
                    assignment_context=any(t['opcode']==0x0f for t in chain),runtime_visibility_verified=False,semantic_classification='pending-context-review'))
    core.require(set(selected)<=set(o['id'] for o in objects),'unknown string owner')
    core.require(len(result)==len(strings),'string coverage mismatch')
    core.require(core.file_digest(archive)==FILE_HASH and all(core.file_digest(Path(p))==h for p,h in hashes.items()),'input changed')
    summary=dict(schema=1,source_sha256=FILE_HASH,input_hashes=hashes,objects_reparsed=len(objects),string_constants=len(result),
        strings_with_call_context=sum(bool(r['call_context']) for r in result),strings_with_assignment_context=sum(r['assignment_context'] for r in result),
        unresolved_call_rows=len(questions),parent_opcodes={f'0x{k:02x}':v for k,v in sorted(Counter(r['parent_opcode'] for r in result).items())},
        ancestor_symbol_occurrences=dict(sorted(all_symbols.items())),native_symbol_collisions={str(k):sorted(v) for k,v in natives.items() if k and len(v)>1},
        native_index_zero_symbols=len(natives.get(0,set())),
        complete_game_text=False,runtime_visibility_verified=False,source_modified=False,translation_gate='coverage-audit-pending')
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    for name,value in [('contexts.json',result),('questions.json',questions),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8');core.require(json.loads(p.read_text('utf8'))==value,'JSON reopen')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['archive','objects','strings','out']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.archive,a.objects,a.strings,a.out),sort_keys=True))
