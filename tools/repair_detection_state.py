"""Audit/repair only the four known discovery-bypass instructions in a state copy.

The original ELF and state are read-only. Unknown instruction words fail closed.
This does not reset event flags or establish that a boss encounter has recovered.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'lib')]
from research_native import ElfImage, ELF_SHA256

BYPASS = {0x3f72c0: 0x1000002c, 0x3f72c4: 0,
          0x3f746c: 0x10000054, 0x3f7470: 0}


def restore_memory(memory, image):
    result = bytearray(memory)
    proof = []
    for address, bypass in BYPASS.items():
        original = struct.unpack_from('<I', image.blob, image.to_offset(address))[0]
        actual = struct.unpack_from('<I', memory, address)[0]
        if actual not in (original, bypass):
            raise ValueError(f'unknown discovery instruction at {address:08X}: {actual:08X}')
        struct.pack_into('<I', result, address, original)
        proof.append(dict(address=f'{address:08X}', actual=f'{actual:08X}',
                          original=f'{original:08X}', bypass=actual == bypass))
    return bytes(result), proof


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--elf', type=Path, required=True)
    p.add_argument('--state', type=Path, required=True)
    p.add_argument('--out', type=Path)
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    elf = a.elf.read_bytes()
    if hashlib.sha256(elf).hexdigest() != ELF_SHA256:
        raise ValueError('unsupported original ELF')
    before = a.state.read_bytes()
    with zipfile.ZipFile(a.state) as z:
        if z.namelist().count('eeMemory.bin') != 1:
            raise ValueError('ambiguous EE memory')
        memory = z.read('eeMemory.bin')
        repaired, proof = restore_memory(memory, ElfImage(elf))
        if a.out:
            if a.out.exists() or a.out.resolve() == a.state.resolve():
                raise ValueError('output must be a new state copy')
            with zipfile.ZipFile(a.out, 'w') as dest:
                for item in z.infolist():
                    dest.writestr(copy.copy(item), repaired if item.filename == 'eeMemory.bin' else z.read(item))
            with zipfile.ZipFile(a.out) as dest:
                for item in z.infolist():
                    expected = repaired if item.filename == 'eeMemory.bin' else z.read(item)
                    if dest.read(item.filename) != expected:
                        raise ValueError('state member readback mismatch')
    if a.state.read_bytes() != before:
        raise ValueError('source state changed')
    report = dict(state=str(a.state.resolve()), source_sha256=hashlib.sha256(before).hexdigest(),
                  instructions=proof, latch=struct.unpack_from('<I', memory, 0xc3fe0)[0],
                  residual_bypass=sum(q['bypass'] for q in proof),
                  repaired_copy=str(a.out.resolve()) if a.out else None,
                  source_unchanged=True, event_flags_changed=False, runtime_verified=False)
    a.report.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    assert json.loads(a.report.read_text('utf8')) == report
    print('DETECTION_STATE_PASS residual_bypass='+str(report['residual_bypass'])+
          ' latch='+str(report['latch'])+' source_unchanged=true repaired='+str(bool(a.out)).lower())


if __name__ == '__main__':
    main()
