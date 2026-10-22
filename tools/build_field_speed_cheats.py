"""Build version-locked field/detection/battle-speed experimental PNACH.

Offline memory fixtures are not evidence of gameplay acceptance.
"""
import argparse
import json
from pathlib import Path
import struct
from build_battle_cheats import Assembler, instruction as ins, sha
from port_frame_limit_patch import offset


def speed_program(p, factor, gate=None):
    if factor not in (2, 4): raise ValueError('unsupported battle factor')
    if gate is not None and (gate % 4 or not 0 <= gate < 32*1024*1024):
        raise ValueError('invalid runtime gate address')
    a = Assembler(int(p['speed_cave'], 16))
    saved = list(range(8, 14))
    a.word(ins(9, 29, 29, -96))
    for i, r in enumerate(saved): a.word(ins(31, 29, r, i*16))
    a.word(ins(15, 0, 8, int(p['speed_state'], 16) >> 16))
    a.word(ins(13, 8, 8, int(p['speed_state'], 16) & 65535))
    a.word(ins(35, 17, 9, p['level_field']))
    # Only aligned user EE addresses; do not follow a stale saved pointer.
    a.word(ins(15, 0, 11, 0x10))
    a.word((9 << 21) | (11 << 16) | (11 << 11) | 0x2b)
    a.branch(5, 11, 0, 'exit')
    a.word(ins(15, 0, 11, 0x200))
    a.word((9 << 21) | (11 << 16) | (11 << 11) | 0x2b)
    a.branch(4, 11, 0, 'exit')
    a.word(ins(12, 9, 11, 3))
    a.branch(5, 11, 0, 'exit')
    a.word(ins(36, 17, 10, p['current_mode_field']))
    a.word(ins(9, 0, 13, p['battle_mode']))
    a.word(ins(35, 8, 11, 0))
    a.branch(4, 9, 11, 'same_owner')
    a.word(ins(43, 8, 0, 0))
    if gate is not None:
        a.word(ins(15, 0, 11, gate >> 16))
        a.word(ins(13, 11, 11, gate & 65535))
        a.word(ins(35, 11, 11, 0))
        a.word(ins(9, 0, 12, 1))
        a.branch(5, 11, 12, 'exit')
    a.branch(5, 10, 13, 'exit')
    a.word(ins(35, 9, 12, p['time_scale_field']))
    a.branch(4, 0, 0, 'scale')
    a.label('same_owner')
    a.word(ins(35, 9, 11, p['time_scale_field']))
    a.word(ins(35, 8, 12, 4))
    a.word(ins(35, 8, 13, 8))
    if gate is not None:
        a.word(ins(15, 0, 10, gate >> 16))
        a.word(ins(13, 10, 10, gate & 65535))
        a.word(ins(35, 10, 10, 0))
        a.word(ins(9, 0, 9, 1))
        a.branch(5, 10, 9, 'leave_battle')
    a.word(ins(9, 0, 10, p['battle_mode']))
    # Reload current mode into a separate scratch after loading last value.
    a.word(ins(36, 17, 9, p['current_mode_field']))
    a.branch(5, 9, 10, 'leave_battle')
    a.word(ins(35, 17, 9, p['level_field']))
    a.branch(4, 11, 13, 'scale')
    a.word((11 << 21) | (12 << 11) | 0x2d)  # daddu t4,t3,zero
    a.branch(4, 0, 0, 'scale')
    a.label('leave_battle')
    a.word(ins(35, 17, 9, p['level_field']))
    a.branch(5, 11, 13, 'clear')  # another owner changed speed: leave it intact
    a.word(ins(43, 9, 12, p['time_scale_field']))
    a.branch(4, 0, 0, 'clear')
    a.label('scale')
    # Positive normal binary32 range [1/16,4]. Exponent addition is exact x2/x4.
    a.word(ins(15, 0, 11, 0x3d80))
    a.word((12 << 21) | (11 << 16) | (11 << 11) | 0x2b)
    a.branch(5, 11, 0, 'clear')
    a.word(ins(15, 0, 11, 0x4080))
    a.word((11 << 21) | (12 << 16) | (11 << 11) | 0x2b)
    a.branch(5, 11, 0, 'clear')
    a.word(ins(15, 0, 13, 0x80 if factor == 2 else 0x100))
    a.word((12 << 21) | (13 << 16) | (13 << 11) | 0x21)
    a.word(ins(43, 9, 13, p['time_scale_field']))
    a.word(ins(43, 8, 9, 0))
    a.word(ins(43, 8, 12, 4))
    a.word(ins(43, 8, 13, 8))
    a.branch(4, 0, 0, 'exit')
    a.label('clear')
    a.word(ins(43, 8, 0, 0))
    a.label('exit')
    for i, r in enumerate(saved): a.word(ins(30, 29, r, i*16))
    a.word(ins(9, 29, 29, 96))
    a.word(int(p['speed_original'][0], 16))
    a.word(int(p['speed_original'][1], 16))
    a.word(0x08000000 | (int(p['speed_hook'], 16)+8 >> 2))
    a.word(0)
    result = a.finish()
    if max(result)+4 > int(p['speed_state'], 16): raise ValueError('state overlaps code')
    result[int(p['speed_hook'], 16)] = 0x08000000 | (a.base >> 2)
    result[int(p['speed_hook'], 16)+4] = 0
    return result


def writes(p, case):
    row = p['cases'][case]
    if 'factor' in row: return speed_program(p, row['factor'])
    return {int(k, 16): int(v, 16) for k, v in row['writes'].items()}


def baseline(elf, p):
    if len(elf) != p['elf_size'] or sha(elf) != p['elf_sha256']:
        raise ValueError('unsupported original ELF fingerprint')
    for va, data in p['anchors'].items():
        raw = bytes.fromhex(data); at = offset(elf, int(va, 16))
        if elf[at:at+len(raw)] != raw: raise ValueError('anchor mismatch')
    mem = bytearray(32*1024*1024); segments=[]
    phoff = struct.unpack_from('<I', elf, 28)[0]
    for i in range(struct.unpack_from('<H', elf, 44)[0]):
        typ, off, va, _, size, total, _, _ = struct.unpack_from('<8I', elf, phoff+32*i)
        if typ == 1:
            if va+total > len(mem): raise ValueError('load segment outside fixture')
            mem[va:va+size] = elf[off:off+size]; segments.append((va, va+total))
    for case in p['cases']:
        for va in writes(p, case):
            if va%4 or not 0 <= va <= len(mem)-4: raise ValueError('write bounds')
            if va < 0x100000 and any(lo <= va < hi for lo, hi in segments):
                raise ValueError('cave overlaps load map')
            if va >= 0x100000 and not any(lo <= va < hi for lo, hi in segments):
                raise ValueError('hook outside load map')
    if any(lo <= int(p['speed_state'],16) < hi for lo,hi in segments):
        raise ValueError('state overlaps load map')
    return bytes(mem)


def transformed(original, p, case):
    result=bytearray(original)
    for va, word in writes(p, case).items(): struct.pack_into('<I', result, va, word)
    return bytes(result)


def render(p):
    result=f"gametitle=Magna Carta NTSC-K experimental field/speed cheats\n// {p['serial']} / {p['crc']}\n// Offline candidates; gameplay acceptance pending. Cold boot after changing selection.\n"
    for case,row in p['cases'].items():
        if row.get('withdrawn',False): continue
        result += f"\n[{row['label']}]\ndescription={row['description']}\n"
        if 'factor' in row:
            for delta in (0,4,8): result += f"patch=0,EE,{int(p['speed_state'],16)+delta:08X},word,00000000\n"
        for va,word in sorted(writes(p,case).items()): result+=f'patch=1,EE,{va:08X},word,{word:08X}\n'
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode',choices=['baseline','apply','modified','rollback','pnach'])
    ap.add_argument('--elf',type=Path,required=True);ap.add_argument('--profile',type=Path,required=True)
    ap.add_argument('--case');ap.add_argument('--input',type=Path);ap.add_argument('--output',type=Path)
    a=ap.parse_args();p=json.loads(a.profile.read_text('utf8'));original=baseline(a.elf.read_bytes(),p)
    if a.mode=='baseline': print(f'BASELINE PASS cases={len(p["cases"])} sha256={sha(original)}');return
    if a.mode=='pnach': result=render(p).encode('utf8')
    else:
        changed=transformed(original,p,a.case)
        if a.mode in ('modified','rollback') and a.input.read_bytes()!=changed:
            raise ValueError('modified fixture fingerprint mismatch')
        if a.mode=='modified':print(f'MODIFIED PASS case={a.case} writes={len(writes(p,a.case))} sha256={sha(changed)}');return
        result=original if a.mode=='rollback' else changed
    if not a.output or a.output.resolve()==a.elf.resolve() or (a.input and a.output.resolve()==a.input.resolve()):
        raise ValueError('separate output required')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(result)
    if a.output.read_bytes()!=result: raise ValueError('output readback mismatch')
    print(f'{a.mode.upper()} PASS case={a.case or "all"} sha256={sha(result)}')


if __name__=='__main__': main()
