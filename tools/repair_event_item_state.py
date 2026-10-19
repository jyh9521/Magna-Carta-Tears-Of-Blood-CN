"""Remove one explicitly bound inventory record on a new savestate copy.

The caller supplies a reviewed snapshot-specific profile, not a guessed live
address. No story switch, executable instruction or original state is written.
Passing this check does not prove an encounter has executed in the game.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import zipfile


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def remove_bound_item(memory, profile):
    if profile.get('schema') != 1 or digest(memory) != profile['memory_sha256']:
        raise ValueError('snapshot memory identity mismatch')
    at = profile['inventory_array_offset']
    if not isinstance(at, int) or at < 0 or at + 12 > len(memory) or at % 4:
        raise ValueError('invalid inventory header')
    data, count, capacity = struct.unpack_from('<III', memory, at)
    if (data != profile['inventory_data_offset'] or count != profile['inventory_count']
            or count < 1 or capacity < count or data % 4
            or data < 0 or data + capacity * 8 > len(memory)):
        raise ValueError('inventory geometry mismatch')
    rows = [struct.unpack_from('<ii', memory, data + j * 8) for j in range(count)]
    if any(quantity <= 0 for _, quantity in rows):
        raise ValueError('unexpected nonpositive inventory record')
    matches = [j for j, (key, _) in enumerate(rows) if key == profile['item_id']]
    if matches != [profile['inventory_index']] or rows[matches[0]][1] != profile['expected_quantity']:
        raise ValueError('item identity, uniqueness or quantity mismatch')
    j = matches[0]
    result = bytearray(memory)
    start, end = data + j * 8, data + (count - 1) * 8
    # FArray removal: preserve the order and contents of all remaining records.
    # Capacity and the inactive trailing storage stay untouched.
    result[start:end] = memory[start+8:end+8]
    struct.pack_into('<I', result, at+4, count-1)
    allowed = set(range(start, end)) | set(range(at+4, at+8))
    if any(a != b and i not in allowed for i, (a, b) in enumerate(zip(memory, result))):
        raise ValueError('unselected memory changed')
    actual = [struct.unpack_from('<ii', result, data + k * 8) for k in range(count-1)]
    if actual != rows[:j] + rows[j+1:]:
        raise ValueError('remaining inventory changed')
    return bytes(result)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('state', 'profile', 'elf', 'out', 'report'):
        p.add_argument('--'+key, type=Path, required=True)
    a = p.parse_args()
    profile = json.loads(a.profile.read_text('utf8'))
    original = a.state.read_bytes()
    if digest(original) != profile['state_sha256'] or digest(a.elf.read_bytes()) != profile['elf_sha256']:
        raise ValueError('original state or ELF identity mismatch')
    if a.out.exists() or a.out.resolve() == a.state.resolve():
        raise ValueError('output must be a new state copy')
    with zipfile.ZipFile(a.state) as source:
        if source.namelist().count('eeMemory.bin') != 1:
            raise ValueError('ambiguous EE memory')
        memory = source.read('eeMemory.bin')
        changed = remove_bound_item(memory, profile)
        with zipfile.ZipFile(a.out, 'w') as target:
            for entry in source.infolist():
                target.writestr(copy.copy(entry), changed if entry.filename == 'eeMemory.bin' else source.read(entry))
        with zipfile.ZipFile(a.out) as target:
            if target.namelist() != source.namelist():
                raise ValueError('state member names/order changed')
            for entry in source.infolist():
                expected = changed if entry.filename == 'eeMemory.bin' else source.read(entry)
                if target.read(entry.filename) != expected:
                    raise ValueError('state member readback mismatch')
    if a.state.read_bytes() != original:
        raise ValueError('original state changed')
    report = dict(profile_sha256=digest(a.profile.read_bytes()), source=str(a.state.resolve()),
                  source_sha256=digest(original), modified=str(a.out.resolve()),
                  modified_sha256=digest(a.out.read_bytes()), item_id=profile['item_id'],
                  previous_quantity=profile['expected_quantity'], modified_quantity=0,
                  inventory_before=profile['inventory_count'], inventory_after=profile['inventory_count']-1,
                  changed_bytes=sum(a != b for a, b in zip(memory, changed)),
                  other_inventory_preserved=True, story_switches_preserved=True,
                  native_instructions_preserved=True, original_unchanged=True, runtime_verified=False)
    a.report.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    assert json.loads(a.report.read_text('utf8')) == report
    print('EVENT_ITEM_COPY_PASS item='+str(profile['item_id'])+' quantity='+str(profile['expected_quantity'])+
          '->0 other_inventory_preserved=true story_switches_preserved=true runtime_verified=false')


if __name__ == '__main__':
    main()
