"""Version-locked static TUI loader arguments and serialized property chains.

No runtime offset assignment or game execution is inferred from field names.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'lib')]
from research_native import ElfImage, ELF_SHA256
from audit_object_properties import Reader
from research_inventory import package_tables
from extract_script_buffers import FILE_HASH
from cri_afs import Afs
from afs import filename_toc


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def descriptor(serial, names, kind):
    r = Reader(serial)
    terminator, parent, next_field = r.index(), r.index(), r.index()
    require(0 <= terminator < len(names) and names[terminator] == 'None', 'property defaults not empty')
    require(parent == 0, 'inherited property descriptor unsupported')
    dimension, flags = r.integer('I'), r.integer('I')
    category = r.index()
    require(dimension == 1, 'property array dimension unsupported')
    inner = r.index() if kind in ('ArrayProperty', 'StructProperty') else None
    require(r.pos == len(serial), 'unparsed property descriptor bytes')
    return dict(next_reference=next_field, dimension=dimension, flags=flags,
                category_reference=category, inner_reference=inner)


def chain(rows, start, outer):
    result = []
    seen = set()
    while start:
        require(start in rows and start not in seen, 'property chain missing reference or cycle')
        seen.add(start)
        row = rows[start]
        require(row['outer'] == outer, 'property chain crosses owner')
        result.append(row)
        start = row['next_reference']
    return result


def loader(image, base, path_va, array_offset, filename):
    evidence = []
    def check(relative, expected, meaning):
        at = base + relative
        word = struct.unpack_from('<I', image.blob, image.to_offset(at))[0]
        require(word == expected, 'loader instruction mismatch at '+hex(at))
        evidence.append(dict(va=hex(at), word=hex(word), meaning=meaning))
    # Three independently checked loaders share instruction geometry, not names.
    check(4, 0x3c050000 | (path_va >> 16), 'path LUI a1')
    check(12, 0x24a50000 | (path_va & 65535), 'path ADDIU a1')
    off = image.to_offset(path_va)
    raw_path = image.blob[off:].split(b'\0', 1)[0]
    require(raw_path == b'..\\UIText\\'+filename.encode('ascii'), 'native TUI path mismatch')
    check(0x5c, 0x0320f809, 'read header count virtual call')
    check(0x60, 0x24060004, 'count read 4 bytes in delay slot')
    check(0x74, 0x0320f809, 'read second header virtual call')
    check(0x78, 0x24060004, 'second header read 4 bytes in delay slot')
    check(0x84, 0x0c0c7520, 'array append helper 0x31d480')
    check(0x88, 0x26650000 | array_offset, 'array address this plus offset')
    check(0xb8, 0x24060004, 'record key read size 4')
    check(0xbc, 0x8e620000 | array_offset, 'load array data pointer')
    check(0xc4, 0x000518c0, 'record index times 8')
    check(0xc8, 0x00651823, 'subtract record index')
    check(0xcc, 0x00031880, 'multiply by 4: record stride 28')
    check(0xd0, 0x00438021, 'record pointer data plus stride')
    check(0xd4, 0x0320f809, 'key read virtual call')
    check(0xd8, 0x0200282d, 'key destination record pointer in delay slot')
    for call, size, dest, conversion, scratch in (
        (0xec, 0xf0, 0xf8, 0x114, 0x118),
        (0x180, 0x184, 0x18c, 0x1a8, 0x1ac),
    ):
        check(call, 0x0320f809, 'text read virtual call')
        check(size, 0x24060100, 'text read 256 bytes in delay slot')
        check(dest, 0x26040000 | (4 if call == 0xec else 16), 'string object destination')
        check(conversion, 0x0c069530, 'buffer conversion helper 0x1a54c0')
        check(scratch, 0x27a40050, 'conversion input scratch sp plus 0x50')
    return dict(path=raw_path.decode('ascii'), function_va=hex(base),
                array_offset=hex(array_offset), record_stride=28,
                source_record_geometry=[4, 256, 256], destination_offsets=[0, 4, 16],
                instructions=evidence, runtime_execution_verified=False,
                conversion_semantics_verified=False)


def inspect_packages(archive):
    require(digest(archive.read_bytes()) == FILE_HASH, 'unsupported original FILE.AFS')
    a = Afs.open(archive)
    names = filename_toc(a)
    result = {}
    with archive.open('rb') as stream:
        for package in ('Core.u', 'MrtsEngine.u'):
            blob = a.read_entry(names.index(package), stream)
            t = package_tables(blob)
            rows = {}
            for i, e in enumerate(t['exports'], 1):
                if e['class'] not in ('IntProperty','StrProperty','ArrayProperty','StructProperty'):
                    continue
                serial = blob[e['offset']:e['offset']+e['size']]
                # Only the selected owners; other property kinds need their own parser.
                if package == 'Core.u' and e['outer'] != 438:
                    continue
                if package == 'MrtsEngine.u' and e['name'] not in (
                    'StoreTextList','BlacksmithTextList','DivinationTextList','GymTextList'):
                    continue
                rows[i] = dict(export=i, name=e['name'], kind=e['class'], outer=e['outer'],
                               serial_sha256=digest(serial), **descriptor(serial,t['names'],e['class']))
                if e['class'] == 'ArrayProperty':
                    require(0 < rows[i]['inner_reference'] <= len(t['exports']), 'array inner reference bounds')
                    inner = t['exports'][rows[i]['inner_reference']-1]
                    require(inner['class']=='StructProperty' and inner['outer']==i, 'array inner owner/type mismatch')
                    data = blob[inner['offset']:inner['offset']+inner['size']]
                    d = descriptor(data,t['names'],inner['class'])
                    ref = d['inner_reference']
                    require(-len(t['imports']) <= ref < 0 and t['imports'][-ref-1]['name']=='MrtsTextData', 'array element struct mismatch')
                    rows[i]['inner_struct'] = dict(name='MrtsTextData', export=rows[i]['inner_reference'],
                                                  serial_sha256=digest(data), **d)
            if package == 'Core.u':
                ordered = chain(rows, 413, 438)
                require([x['name'] for x in ordered]==['Key','MainText','HelpText'], 'text struct field chain mismatch')
                require([x['kind'] for x in ordered]==['IntProperty','StrProperty','StrProperty'], 'text struct field types mismatch')
            else:
                ordered = [rows[i] for i in (96,163,151,746)]
                require([x['next_reference'] for x in ordered]==[163,151,746,680], 'text list field adjacency mismatch')
            result[package] = dict(package_sha256=digest(blob), fields=ordered)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--elf',type=Path,required=True)
    p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    raw=args.elf.read_bytes()
    require(digest(raw)==ELF_SHA256, 'unsupported original ELF')
    image=ElfImage(raw)
    loads=[loader(image,*x) for x in (
        (0x308250,0x4b7810,0x148,'00001239.tui'),
        (0x308600,0x4b7830,0x160,'00000682.tui'),
        (0x308950,0x4b7850,0x16c,'00001249.tui'),
    )]
    report=dict(elf_sha256=ELF_SHA256,archive_sha256=FILE_HASH,loaders=loads,
                properties=inspect_packages(args.archive),
                runtime_field_offsets_verified=False, reinsertion_authorized=False)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
    print('NATIVE_TEXT_LOADERS_PASS loaders=3 struct_fields=3 array_fields=4 runtime_field_offsets_verified=false')


if __name__=='__main__':
    main()
