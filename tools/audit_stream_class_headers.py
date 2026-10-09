"""Inventory exact ordinary class-header occurrences in the fixed celfid stream.

Occurrences are source-oracle anchors, not serial boundaries or text coverage.
No game resource is written; unmatched definitions remain explicit.
"""
from __future__ import annotations
import argparse,json,struct,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from audit_container_payloads import unpack_chunks,probe_all_packages
from audit_object_properties import Reader,ordinary_exports
from research_inventory import package_tables
from audit_class_defaults import class_body
from audit_compiled_scripts import compiled_script
from audit_bundle_contexts import BUNDLE_HASH
from extract_script_buffers import FILE_HASH


def occurrences(blob,header):
    core.require(len(header)>=21,'class header too short')
    result=[];start=0
    while True:
        offset=blob.find(header,start)
        if offset<0:return result
        result.append(offset);start=offset+1


def check_tables(original,stream):
    core.require(original['names']==stream['names'],'class oracle names mismatch')
    core.require(original['imports']==stream['imports'],'class oracle imports mismatch')
    core.require(len(original['exports'])==len(stream['exports']),'class oracle export count')
    for e,se in zip(original['exports'],stream['exports']):
        core.require(all(e[k]==se[k] for k in ('index','name','class_index','outer','super_index','flags')),'class oracle export metadata')
        core.require((e['size'],e['offset'])==(se['declared_size'],se['declared_offset']),'class oracle original coordinates')


def full_imports(blob,tables):
    count,offset=struct.unpack_from('<II',blob,28);r=Reader(blob,offset);rows=[]
    names=tables['names']
    for _ in range(count):
        cp=r.index();cl=r.index();outer=r.integer('i');name=r.index()
        core.require(all(0<=i<len(names) for i in (cp,cl,name)),'import name bounds')
        rows.append(dict(class_package=names[cp],class_name=names[cl],name=names[name],outer=outer))
    core.require([dict(**{'class':row['class_name']},name=row['name'],outer=row['outer']) for row in rows]==tables['imports'],'ordinary import reader disagreement')
    return rows


def audit(archive,out):
    core.require(core.file_digest(archive)==FILE_HASH,'FILE identity mismatch')
    a=Afs.open(archive);names=filename_toc(a);rows=[];packages=[];counts=Counter()
    with archive.open('rb') as f:
        bundle,_=unpack_chunks(a.read_entry(names.index('celfid.lix'),f))
        core.require(core.digest(bundle)==BUNDLE_HASH,'bundle identity mismatch')
        streams={Path(t['wrapper_path']).name:t for t in probe_all_packages(bundle)}
        for index,name in enumerate(names):
            blob=a.read_entry(index,f)
            if not blob.startswith(bytes.fromhex('c1832a9e')):continue
            tables=package_tables(blob);exports=ordinary_exports(blob,tables)
            stream=streams.get(name)
            if stream:check_tables(dict(tables,exports=exports,imports=full_imports(blob,tables)),stream)
            package_rows=[]
            for e in exports:
                if e['class_index']!=0:continue
                raw=blob[e['offset']:e['offset']+e['size']]
                parsed=class_body(raw,tables,e,compiled_script)
                header=raw[:parsed['header']['script_start']]
                positions=occurrences(bundle,header)
                row=dict(id=f'FILE/{name}/export/{e["index"]}',package=name,export=e['index'],name=e['name'],
                    source_package_sha256=core.digest(blob),source_header_offset=e['offset'],
                    header_bytes=len(header),header_sha256=core.digest(header),stream_offsets=positions,
                    status='unmatched' if not positions else 'unique-anchor' if len(positions)==1 else 'ambiguous-anchor',
                    header=parsed['header'],ordinary_defaults_closed=parsed['defaults_complete'],
                    table_identity_verified=stream is not None,serial_mapping_verified=False,
                    runtime_visibility_verified=False,editable=False)
                rows.append(row);package_rows.append(row);counts[row['status']]+=1
            packages.append(dict(package=name,source_sha256=core.digest(blob),classes=len(package_rows),
                table_identity_verified=stream is not None,
                statuses=dict(Counter(r['status'] for r in package_rows))))
    core.require(core.file_digest(archive)==FILE_HASH,'FILE changed')
    summary=dict(schema=1,source_sha256=FILE_HASH,bundle_sha256=BUNDLE_HASH,bundle_bytes=len(bundle),
        ordinary_packages=len(packages),ordinary_classes=len(rows),statuses=dict(counts),
        header_occurrences=sum(len(r['stream_offsets']) for r in rows),
        matched_header_bytes=sum(r['header_bytes']*len(r['stream_offsets']) for r in rows),
        source_tables_verified=sum(p['table_identity_verified'] for p in packages),
        all_ordinary_class_headers_inspected=True,full_stream_mapping_verified=False,
        complete_game_text=False,source_modified=False,translation_gate='coverage-audit-pending')
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    for name,value in [('anchors.json',rows),('packages.json',packages),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        core.require(json.loads(p.read_text('utf8'))==value,'JSON reopen')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();print(json.dumps(audit(args.archive,args.out),sort_keys=True))
