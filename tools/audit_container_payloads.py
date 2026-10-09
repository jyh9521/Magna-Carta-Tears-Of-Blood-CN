"""Stream every SHIP/FILE/LINEAR entry through hash and package-table inspection.

This is a full container pass, not proof of semantic text/image coverage.
No archives are copied, rebuilt, or written. Package details stay ignored.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import struct
import sys
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from translate.celfid import decompress_chunked
from research_inventory import package_tables, compact


def streamed_tables(blob, start):
    """Read relocated LINEAR tables; declared serial offsets are NOT stream offsets.

    Observed path[256], zero u32, original-size u32, 64-byte UE2 summary,
    then names/imports/exports consecutively. No serial data is inferred here.
    """
    core.require(start>=264, 'stream wrapper missing')
    wrapper=blob[start-264:start]
    path=wrapper[:256].split(b'\0',1)[0].decode('ascii','strict')
    core.require(path.startswith('../') and b'\0' in wrapper[:256], 'stream wrapper path')
    reserved,original_size=struct.unpack_from('<II',wrapper,256)
    core.require(reserved==0 and original_size>=64,'stream wrapper size')
    data=blob[start:]
    core.require(len(data)>=64, 'truncated stream summary')
    magic,version,flags,nc,no,ec,eo,ic,io=struct.unpack_from('<9I',data)
    core.require(magic==0x9e2a83c1 and no==64 and version&65535==118,
                 'unsupported stream summary')
    core.require(all(c<=len(data) for c in (nc,ec,ic)), 'stream count bounds')
    core.require(all(0<=o<=original_size for o in (no,eo,io)), 'original table bounds')
    names=[];pos=no
    for _ in range(nc):
        length,pos=compact(data,pos);size=abs(length)*(2 if length<0 else 1)
        core.require(length!=0 and pos+size+4<=len(data),'stream name bounds')
        raw=data[pos:pos+size]
        core.require(raw.endswith(b'\0\0' if length<0 else b'\0'),'stream name terminator')
        names.append(raw.decode('utf-16le' if length<0 else 'latin1').rstrip('\0'))
        pos+=size+4
    imports=[];import_start=pos
    for _ in range(ic):
        cp,pos=compact(data,pos);cl,pos=compact(data,pos)
        outer=struct.unpack_from('<i',data,pos)[0];name,pos=compact(data,pos+4)
        core.require(all(0<=n<len(names) for n in (cp,cl,name)), 'stream import name index')
        imports.append(dict(class_package=names[cp],class_name=names[cl],name=names[name],outer=outer))
    exports=[];export_start=pos
    for index in range(ec):
        cl,pos=compact(data,pos);super_index,pos=compact(data,pos)
        outer=struct.unpack_from('<i',data,pos)[0];name,pos=compact(data,pos+4)
        object_flags=struct.unpack_from('<I',data,pos)[0];size,pos=compact(data,pos+4)
        offset=0
        if size>0:offset,pos=compact(data,pos)
        core.require(0<=name<len(names) and -len(imports)<=cl<=ec,'stream export index')
        core.require(size>=0 and offset>=0 and offset+size<=original_size,'original serial bounds')
        exports.append(dict(index=index+1,class_index=cl,**{'class':imports[-cl-1]['name'] if cl<0 else str(cl)},
            name=names[name],outer=outer,super_index=super_index,flags=object_flags,
            declared_size=size,declared_offset=offset,serial_mapping='unresolved'))
    return dict(layout='relocated-stream-tables',package_offset=start,wrapper_path=path,
        original_package_size=original_size,version=version&65535,licensee=version>>16,
        names=names,imports=imports,exports=exports,table_end=start+pos,
        actual_import_offset=start+import_start,actual_export_offset=start+export_start)


def probe_all_packages(blob):
    if blob.startswith(bytes.fromhex('c1832a9e')):
        return [package_probe(blob)]
    result=[];pos=0
    while True:
        pos=blob.find(bytes.fromhex('c1832a9e'),pos)
        if pos<0:break
        # Texture pixels can contain the magic by chance; a wrapper is required.
        if pos>=264 and blob[pos-264:pos-261]==b'../':
            result.append(streamed_tables(blob,pos))
        pos+=4
    return result


def unpack_chunks(blob):
    """Validate framing, then reuse upstream decompression without a disk copy."""
    pos,chunks=0,0
    while pos<len(blob):
        if not any(blob[pos:pos+8]) and not any(blob[pos:]):
            break
        core.require(pos+8<=len(blob),'truncated chunk header')
        unc,cmp=struct.unpack_from('<II',blob,pos)
        core.require(0<unc<=24576 and 0<cmp and pos+8+cmp<=len(blob),'invalid chunk bounds')
        decoder=zlib.decompressobj();data=decoder.decompress(blob[pos+8:pos+8+cmp])
        core.require(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail
                     and len(data)==unc,'chunk length/stream mismatch')
        pos+=8+cmp;chunks+=1
    core.require(chunks>0,'no compressed chunks')
    return decompress_chunked(blob),chunks


def package_probe(blob):
    magic=bytes.fromhex('c1832a9e')
    pos=blob.find(magic,0,min(512,len(blob)))
    if pos<0:
        return None
    data=blob[pos:]
    core.require(len(data)>=36,'truncated package header')
    header=struct.unpack_from('<9I',data)
    for count,offset in [(header[3],header[4]),(header[5],header[6]),(header[7],header[8])]:
        core.require(count<=len(data) and (count==0 or 0<=offset<len(data)), 'package table header bounds')
    tables=package_tables(data)
    for export in tables['exports']:
        export['serial_sha256']=core.digest(data[export['offset']:export['offset']+export['size']])
    return dict(package_offset=pos,package_sha256=core.digest(data),**tables)


def audit(archive_dir,hashes,out):
    out=core.output_directory(out)
    core.require(not any(out.iterdir()),'output must be empty')
    counts,classes,statuses,errors=Counter(),Counter(),Counter(),[]
    inventory=out/'payload-inventory.jsonl';packages=out/'package-tables.jsonl'
    with inventory.open('w',encoding='utf8') as listing, packages.open('w',encoding='utf8') as details:
        for label in ['SHIP.AFS','FILE.AFS','LINEAR.AFS']:
            path=archive_dir/label
            core.require(core.file_digest(path)==hashes[label], 'archive identity mismatch: '+label)
            archive=Afs.open(path);names=filename_toc(archive)
            core.require(len(names)==len(set(names)), 'duplicate archive resource')
            with path.open('rb') as stream:
                for index,name in enumerate(names):
                    blob=archive.read_entry(index,stream)
                    row=dict(archive=label,index=index,name=name,size=len(blob),sha256=core.digest(blob),
                             semantic_text_review='pending',image_text_review='pending')
                    payload=blob
                    try:
                        if name.lower().endswith(('.lin','.lix')):
                            payload,chunks=unpack_chunks(blob)
                            row.update(chunks=chunks,payload_bytes=len(payload),payload_sha256=core.digest(payload))
                            if name.lower().endswith('.lin'):
                                row['wrapper_path']=payload[:128].split(b'\0',1)[0].decode('ascii','strict')
                        tables=probe_all_packages(payload)
                        if tables:
                            table=tables[0]
                            row.update(status='package-tables-read',package_offset=table['package_offset'],
                                       packages=len(tables),names=sum(len(t['names']) for t in tables),
                                       imports=sum(len(t['imports']) for t in tables),exports=sum(len(t['exports']) for t in tables))
                            for table in tables:
                                classes.update(e['class'] for e in table['exports'])
                                details.write(json.dumps(dict(archive=label,index=index,name=name,**table),ensure_ascii=False)+'\n')
                        else:
                            row['status']='non-package-payload-indexed'
                    except (ValueError,IndexError,struct.error,zlib.error,UnicodeError) as error:
                        row.update(status='payload-parse-question',error=str(error))
                        errors.append(dict(archive=label,index=index,name=name,error=str(error)))
                    counts[label]+=1;statuses[row['status']]+=1
                    listing.write(json.dumps(row,ensure_ascii=False)+'\n')
                    if counts[label]%1000==0:
                        print(label,counts[label],flush=True)
            core.require(core.file_digest(path)==hashes[label],'archive changed: '+label)
    summary=dict(schema=1,verified_archive_hashes=hashes,entries=dict(counts),
        statuses=dict(sorted(statuses.items())),export_classes=dict(sorted(classes.items())),
        parse_questions=len(errors),complete_game_text=False,
        result='all three container payloads inspected; property and image semantics pending')
    for name,value in [('summary.json',summary),('parse-questions.json',errors)]:
        path=out/name;path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        core.require(json.loads(path.read_text('utf8'))==value,'JSON reopen mismatch')
    for path in [inventory,packages]:
        with path.open(encoding='utf8') as stream:
            for line in stream:json.loads(line)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-dir',type=Path,required=True)
    parser.add_argument('--coverage-summary',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    hashes=json.loads(args.coverage_summary.read_text('utf8'))['verified_archive_hashes']
    print(json.dumps(audit(args.archive_dir,hashes,args.out),sort_keys=True))


if __name__=='__main__':main()

