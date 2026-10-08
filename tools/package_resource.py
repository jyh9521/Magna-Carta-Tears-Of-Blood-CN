"""Append-only export replacement for explicitly fingerprinted UE packages.

Original payloads and tables remain in place; a replacement export table is
appended and the header points to it. This does not rebuild a celfid bundle.
"""
from __future__ import annotations
import hashlib
import struct
from font_resource import encode_compact, require
from research_inventory import package_tables


def export_records(blob: bytes, *, expected_version: tuple[int, int]) -> tuple[list[dict], int]:
    require(len(blob) >= 64 and blob[:4] == bytes.fromhex('c1832a9e'), 'invalid package header')
    version, flags, nc, no, ec, eo, ic, io = struct.unpack_from('<8I', blob, 4)
    require((version & 65535, version >> 16) == expected_version, 'unsupported package version')
    require(flags == 1, 'unsupported package flags')
    require(0 < ec <= len(blob) // 10 and 64 <= eo < len(blob), 'invalid export table bounds')
    require(0 < nc <= len(blob) and 64 <= no < len(blob), 'invalid name table bounds')
    require(ic <= len(blob) // 7 and (not ic or 64 <= io < len(blob)), 'invalid import table bounds')

    def read(pos: int) -> tuple[int, int]:
        require(pos < len(blob), 'truncated compact index')
        first = blob[pos]; pos += 1
        value = first & 63; more = first & 64; shift = 6
        for _ in range(4):
            if not more: break
            require(pos < len(blob), 'truncated compact index')
            byte = blob[pos]; pos += 1
            value |= (byte & 127) << shift; more = byte & 128; shift += 7
        require(not more and value <= 0x7fffffff, 'invalid compact index')
        return (-value if first & 128 else value), pos

    records = []; pos = eo
    for index in range(1, ec + 1):
        start = pos
        _, pos = read(pos); _, pos = read(pos)
        require(pos + 4 <= len(blob), 'truncated export outer'); pos += 4
        name, pos = read(pos)
        require(0 <= name < nc and pos + 4 <= len(blob), 'invalid export name/flags'); pos += 4
        prefix = blob[start:pos]
        size, pos = read(pos); offset = 0
        if size > 0: offset, pos = read(pos)
        require(size >= 0 and (size == 0 or 64 <= offset and offset + size <= len(blob)), 'export outside package')
        records.append(dict(index=index, prefix=prefix, size=size, offset=offset, raw=blob[start:pos]))
    # Reject export/table overlap rather than guessing unknown layouts.
    spans = sorted((x['offset'], x['offset'] + x['size']) for x in records if x['size'])
    require(all(end <= start for (_, end), (start, _) in zip(spans, spans[1:])), 'overlapping exports')
    require(all(end <= eo or start >= pos for start, end in spans), 'export overlaps table')
    return records, pos


def replace_exports(blob: bytes, replacements: dict[int, bytes], *, expected_sha256: str,
                    expected_version: tuple[int, int]) -> tuple[bytes, dict]:
    require(hashlib.sha256(blob).hexdigest() == expected_sha256, 'package fingerprint mismatch')
    records, table_end = export_records(blob, expected_version=expected_version)
    require(bool(replacements), 'no export replacements')
    require(all(type(index) is int and 1 <= index <= len(records) for index in replacements), 'unknown export index')
    require(all(type(value) is bytes and value for value in replacements.values()), 'empty/invalid export replacement')
    result = bytearray(blob); changed = []
    table = bytearray()
    for entry in records:
        index = entry['index']
        if index not in replacements:
            table += entry['raw']; continue
        require(entry['size'] > 0, 'zero-size export replacement unsupported')
        payload = replacements[index]; offset = len(result); result += payload
        table += entry['prefix'] + encode_compact(len(payload)) + encode_compact(offset)
        changed.append(dict(index=index, old_offset=entry['offset'], old_size=entry['size'],
                            new_offset=offset, new_size=len(payload), sha256=hashlib.sha256(payload).hexdigest()))
    table_offset = len(result); result += table
    require(len(result) <= 0x7fffffff, 'package exceeds compact offset capacity')
    struct.pack_into('<I', result, 24, table_offset)
    modified = bytes(result)
    after, end = export_records(modified, expected_version=expected_version)
    require(end == len(modified), 'appended export table not at EOF')
    require(modified[:24] == blob[:24] and modified[28:len(blob)] == blob[28:], 'original package bytes changed')
    for old, new in zip(records, after, strict=True):
        require(old['prefix'] == new['prefix'], 'export identity changed')
        expected = replacements.get(old['index'], blob[old['offset']:old['offset'] + old['size']])
        require(modified[new['offset']:new['offset'] + new['size']] == expected, 'export payload mismatch')
        if old['index'] not in replacements: require(old == new, 'untargeted export metadata changed')
    before_tables, after_tables = package_tables(blob), package_tables(modified)
    require(before_tables['names'] == after_tables['names'] and before_tables['imports'] == after_tables['imports'],
            'name/import tables changed')
    return modified, dict(original_size=len(blob), modified_size=len(modified), old_table_offset=struct.unpack_from('<I', blob, 24)[0],
                         old_table_end=table_end, new_table_offset=table_offset, exports=len(records), changed=changed,
                         original_payloads_retained=True, runtime='unverified')
