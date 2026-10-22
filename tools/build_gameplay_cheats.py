"""Generate version-locked gameplay PNACH and separate offline ELF proofs.

Profile carries region-specific data; generic tooling never shifts addresses.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from port_frame_limit_patch import offset


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def validate(blob, profile, row=None, modified=False):
    if len(blob) != profile['elf_size']:
        raise ValueError('ELF size mismatch')
    original = bytearray(blob)
    if modified:
        if row is None:
            raise ValueError('modified proof requires case')
        off = offset(blob, int(row['va'], 16))
        if struct.unpack_from('<I', blob, off)[0] != int(row['replacement'], 16):
            raise ValueError('modified word mismatch')
        struct.pack_into('<I', original, off, int(row['expected'], 16))
    if sha(original) != profile['elf_sha256']:
        raise ValueError('unsupported ELF fingerprint')
    for code in profile['codes']:
        off = offset(original, int(code['context_start'], 16))
        context = bytes.fromhex(code['context_hex'])
        if original[off:off+len(context)] != context:
            raise ValueError('context mismatch')
    return bytes(original)


def transform(blob, profile, row, rollback=False):
    original = validate(blob, profile, row, modified=rollback)
    if rollback:
        return original
    result = bytearray(blob)
    struct.pack_into('<I', result, offset(blob, int(row['va'], 16)), int(row['replacement'], 16))
    validate(result, profile, row, modified=True)
    return bytes(result)


def render(profile, base):
    text = base.rstrip() + '\n\n// Gameplay ports: static verified; runtime pending.\n'
    text += '// Upstream: root670/CheatDevicePS2/CheatDatabase.txt (GPL-3.0).\n'
    text += '// Select ONE money-spend mode and ONE item mode at a time.\n'
    text += '// JP reference: https://xterminatorex.seesaa.net/category/6006620-2.html\n'
    text += '// Disable item modes before equipment changes (JP hang report; KR not tested).\n'
    for row in profile['codes']:
        text += (f"\n[{row['label']}]\n" +
                 f"description={row['description']}\n" +
                 f"// {row['id']}; original {row['expected']}; {row['binding']}\n"
                 f"patch=1,EE,{row['va']},word,{row['replacement']}\n")
    return text


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['baseline', 'apply', 'modified', 'rollback', 'pnach'])
    p.add_argument('--profile', type=Path, required=True)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--case')
    p.add_argument('--output', type=Path)
    p.add_argument('--base-pnach', type=Path)
    a = p.parse_args()
    profile = json.loads(a.profile.read_text('utf8'))
    blob = a.input.read_bytes()
    row = next((r for r in profile['codes'] if r['id'] == a.case), None)
    if a.mode in ['apply', 'modified', 'rollback'] and row is None:
        raise ValueError('known case required')
    if a.mode == 'baseline':
        validate(blob, profile)
        print(f"BASELINE PASS cases={len(profile['codes'])} sha256={sha(blob)}")
    elif a.mode == 'modified':
        validate(blob, profile, row, modified=True)
        print(f"MODIFIED PASS case={row['id']} va={row['va']} word={row['replacement']}")
    else:
        if a.output is None or a.output.resolve() == a.input.resolve():
            raise ValueError('separate output required')
        if a.mode == 'pnach':
            validate(blob, profile)
            if a.base_pnach is None:
                raise ValueError('base PNACH required')
            result = render(profile, a.base_pnach.read_text('utf8')).encode('utf8')
        else:
            result = transform(blob, profile, row, rollback=a.mode == 'rollback')
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_bytes(result)
        if a.output.read_bytes() != result:
            raise ValueError('output readback mismatch')
        print(f"{a.mode.upper()} PASS case={a.case or 'all'} sha256={sha(result)}")


if __name__ == '__main__':
    main()
