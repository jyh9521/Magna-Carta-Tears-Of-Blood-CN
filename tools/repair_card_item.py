"""Snapshot-bound inventory removal on a separate PS2 card image.

Uses a caller-supplied, pinned mymc-py checkout for filesystem/ECC operations.
Game payload changes are profile-bound and independently reread after writing.
"""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import struct
import sys
import zlib


def digest(data):
    return hashlib.sha256(data).hexdigest()


def compact(value):
    if not isinstance(value, int) or not 0 <= value <= 0x7fffffff:
        raise ValueError('unsupported compact count')
    result = bytearray([value & 63])
    value >>= 6
    if value:
        result[0] |= 64
    while value:
        result.append((value & 127) | (128 if value >> 7 else 0))
        value >>= 7
    return bytes(result)


def unpack_blocks(blob):
    parts = []
    at = 0
    while at < len(blob):
        if at + 8 > len(blob):
            raise ValueError('truncated block header')
        n, c = struct.unpack_from('<II', blob, at)
        if not 0 < n <= 20480 or not 0 < c <= len(blob)-at-8:
            raise ValueError('invalid compressed block geometry')
        decoder = zlib.decompressobj()
        raw = decoder.decompress(blob[at+8:at+8+c], n+1)
        if len(raw) != n or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
            raise ValueError('compressed block mismatch')
        parts.append(raw)
        at += 8+c
    if not parts:
        raise ValueError('empty save stream')
    return b''.join(parts)


def pack_blocks(raw):
    result = bytearray()
    for at in range(0, len(raw), 20480):
        part = raw[at:at+20480]
        coded = zlib.compress(part, 9)
        result += struct.pack('<II', len(part), len(coded)) + coded
    return bytes(result)


def remove_item(blob, profile):
    if profile.get('schema') != 1 or digest(blob) != profile['save_sha256']:
        raise ValueError('save identity mismatch')
    raw = unpack_blocks(blob)
    if digest(raw) != profile['unpacked_sha256'] or struct.unpack_from('<I', raw)[0] != profile['version']:
        raise ValueError('serialized save identity/version mismatch')
    at, count, index = (profile[k] for k in ('count_offset', 'count', 'index'))
    header = compact(count)
    if at < 4 or raw[at:at+len(header)] != header or not 0 <= index < count:
        raise ValueError('inventory count/index mismatch')
    start = at+len(header)
    end = start+count*8
    rows_blob = raw[start:end]
    if len(rows_blob) != count*8 or digest(rows_blob) != profile['inventory_sha256']:
        raise ValueError('inventory identity mismatch')
    rows = list(struct.iter_unpack('<ii', rows_blob))
    if any(q <= 0 for _, q in rows):
        raise ValueError('unexpected nonpositive inventory record')
    matches = [j for j, (key, _) in enumerate(rows) if key == profile['item_id']]
    if matches != [index] or rows[index][1] != profile['quantity']:
        raise ValueError('item uniqueness/quantity mismatch')
    offset = start+index*8
    updated = raw[:at] + compact(count-1) + raw[start:offset] + raw[offset+8:]
    result = pack_blocks(updated)
    if unpack_blocks(result) != updated:
        raise ValueError('compressed output readback mismatch')
    return result


def card_files(path, card_class):
    files = {}
    with path.open('rb') as stream:
        mc = card_class(stream, False)
        if not mc.check():
            raise ValueError('memory card filesystem check failed')
        def walk(parent):
            directory = mc.dir_open(parent)
            for i in range(2, len(directory)):
                entry = directory[i]
                if not entry[0] & 0x8000:
                    continue
                name = parent.rstrip(b'/') + b'/' + entry[8]
                if entry[0] & 0x20:
                    walk(name)
                elif entry[0] & 0x10:
                    item = mc.open(name, 'rb')
                    files[name] = item.read()
                    item.close()
            directory.close()
        walk(b'/')
        mc.close()
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('card', 'profile', 'mymc-root', 'out', 'report'):
        parser.add_argument('--'+key, type=Path, required=True)
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text('utf8'))
    original = args.card.read_bytes()
    if digest(original) != profile['card_sha256']:
        raise ValueError('card identity mismatch')
    if args.out.exists() or args.out.resolve() == args.card.resolve():
        raise ValueError('output must be a new card copy')
    if args.report.resolve() in (args.card.resolve(), args.out.resolve(), args.profile.resolve()):
        raise ValueError('report overlaps an input/output')
    sys.path.insert(0, str(args.mymc_root.resolve()/'src'))
    card_class = importlib.import_module('mymc_py.ps2mc').ps2mc
    before = card_files(args.card, card_class)
    target = profile['save_path'].encode('ascii')
    modified = remove_item(before[target], profile)
    shutil.copyfile(args.card, args.out)
    with args.out.open('r+b') as stream:
        mc = card_class(stream, False)
        item = mc.open(target, 'wb')
        item.write(modified)
        item.close()
        mc.close()
    after = card_files(args.out, card_class)
    expected = dict(before)
    expected[target] = modified
    if after != expected or args.card.read_bytes() != original:
        raise ValueError('card readback mismatch or original changed')
    report = dict(source=str(args.card.resolve()), modified=str(args.out.resolve()),
                  source_sha256=digest(original), modified_sha256=digest(args.out.read_bytes()),
                  save_path=profile['save_path'], item_id=profile['item_id'],
                  quantity_before=profile['quantity'], quantity_after=0,
                  inventory_before=profile['count'], inventory_after=profile['count']-1,
                  other_inventory_preserved=True, other_save_payload_bytes_preserved=True,
                  other_files_preserved=len(before)-1, filesystem_check=True,
                  original_unchanged=True, runtime_verified=False)
    args.report.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    if json.loads(args.report.read_text('utf8')) != report:
        raise ValueError('report readback mismatch')
    print('CARD_ITEM_COPY_PASS item='+str(profile['item_id'])+' quantity='+str(profile['quantity'])+
          '->0 other_inventory_preserved=true other_files='+str(len(before)-1)+
          ' filesystem=PASS runtime_verified=false')


if __name__ == '__main__':
    main()
