"""Generate Korean battle-hook candidates and version-locked EE memory proofs.

Caves are outside ELF load segments; dynamic cave ownership requires runtime QA.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from port_frame_limit_patch import offset

MODES = {
    'ally_max_hp': '战斗：我方最大HP9999（查询时）',
    'ally_heal': '战斗：我方HP恢复9999（查询时）',
    'enemy_one_hp': '战斗：存活敌人HP降至1（查询时）',
    'heal_and_one_hp': '战斗：我方恢复9999＋敌人HP1',
    'ally_leadership': '战斗：我方领导力100（查询时）',
}


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def instruction(op, rs, rt, imm):
    return (op << 26) | (rs << 21) | (rt << 16) | (imm & 65535)


class Assembler:
    def __init__(self, base):
        self.base, self.words, self.labels, self.fixups = base, [], {}, []

    def word(self, value):
        self.words.append(value)

    def label(self, name):
        if name in self.labels:
            raise ValueError('duplicate label')
        self.labels[name] = len(self.words)

    def branch(self, op, rs, rt, name):
        self.fixups.append((len(self.words), name))
        self.word(instruction(op, rs, rt, 0))
        self.word(0)  # explicit branch delay slot

    def finish(self):
        for at, name in self.fixups:
            delta = self.labels[name]-at-1
            if not -32768 <= delta <= 32767:
                raise ValueError('branch out of range')
            self.words[at] |= delta & 65535
        return {self.base+4*i: w for i,w in enumerate(self.words)}


def hp_program(profile, mode):
    a = Assembler(int(profile['hp_cave'],16))
    # Preserve full 128-bit R5900 scratch registers; do not truncate saved GPRs.
    saved = [1,2,3,8,9,10]
    a.word(instruction(9,29,29,-96))
    for i,r in enumerate(saved):
        a.word(instruction(31,29,r,16*i))  # SQ
    a.word(instruction(35,28,8,profile['team_cache_gp_offset']))
    a.branch(4,8,0,'restore')
    a.word(instruction(35,4,9,0x24))
    a.label('class_loop')
    a.branch(4,9,8,'class_ok')
    a.branch(4,9,0,'restore')
    a.word(instruction(35,9,9,0x28))
    a.branch(4,0,0,'class_loop')
    a.label('class_ok')
    a.word(instruction(36,4,8,profile['team_field']))
    a.branch(4,8,0,'ally')
    a.word(instruction(9,0,10,profile['enemy_team']))
    a.branch(4,8,10,'enemy')
    a.branch(4,0,0,'restore')
    for role, enabled in [('ally',mode in ['ally_max_hp','ally_heal','heal_and_one_hp']),
                          ('enemy',mode in ['enemy_one_hp','heal_and_one_hp'])]:
        a.label(role)
        if enabled:
            a.word(instruction(35,4,9,profile['character_field']))
            a.branch(4,9,0,'restore')
            a.word(instruction(35,9,9,profile['status_field']))
            a.branch(4,9,0,'restore')
            # Do not revive already dead actors, including allies.
            a.word(instruction(35,9,10,profile['cur_hp_field']))
            a.branch(6,10,0,'restore')  # BLEZ
            a.word(instruction(9,0,10,9999 if role=='ally' else 1))
            if role=='ally':
                a.word(instruction(43,9,10,profile['max_hp_field']))
            if role=='enemy' or mode!='ally_max_hp':
                a.word(instruction(43,9,10,profile['cur_hp_field']))
        a.branch(4,0,0,'restore')
    a.label('restore')
    for i,r in enumerate(saved):
        a.word(instruction(30,29,r,16*i))  # LQ
    a.word(instruction(9,29,29,96))
    # Replay the displaced original prologue, then resume unchanged code.
    a.word(instruction(9,29,29,-16))
    a.word(instruction(63,29,31,0))  # SD ra,0(sp)
    a.word(0x08000000 | (int(profile['hp_resume'],16)>>2))
    a.word(0)
    writes = a.finish()
    writes[int(profile['hp_hook'],16)] = 0x08000000 | (a.base>>2)
    writes[int(profile['hp_hook'],16)+4] = 0
    return writes


def writes(profile, mode):
    if mode not in MODES:
        raise ValueError('unknown battle mode')
    if mode == 'ally_leadership':
        base = int(profile['lead_cave'],16)
        return {base: 0x3C0142C8, base+4: 0xAC810028,
                base+8: 0x081060FC, base+12: 0,
                int(profile['lead_hook'],16): 0x0C000000 | (base>>2)}
    return hp_program(profile,mode)


def baseline(elf, profile):
    if len(elf)!=profile['elf_size'] or sha(elf)!=profile['elf_sha256']:
        raise ValueError('unsupported original ELF')
    for va,hexdata in profile['anchors'].items():
        raw=bytes.fromhex(hexdata); off=offset(elf,int(va,16))
        if elf[off:off+len(raw)]!=raw:
            raise ValueError('native anchor mismatch')
    memory=bytearray(32*1024*1024)
    phoff=struct.unpack_from('<I',elf,28)[0]
    count=struct.unpack_from('<H',elf,44)[0]
    segments=[]
    for i in range(count):
        typ,off,va,_,size,memsz,_,_=struct.unpack_from('<8I',elf,phoff+32*i)
        if typ==1:
            if va+memsz>len(memory):
                raise ValueError('segment outside EE RAM fixture')
            memory[va:va+size]=elf[off:off+size]
            segments.append((va,va+memsz))
    for mode in MODES:
        for va in writes(profile,mode):
            if va<0x100000 and any(start<=va<end for start,end in segments):
                raise ValueError('cave overlaps ELF segment')
            if va%4 or va+4>len(memory):
                raise ValueError('unaligned/out-of-bounds write')
    return memory


def apply(memory, original, profile, mode, rollback=False):
    expected=bytearray(original)
    patch=writes(profile,mode)
    for va,word in patch.items():
        struct.pack_into('<I',expected,va,word)
    if memory!=(expected if rollback else original):
        raise ValueError('memory fixture fingerprint mismatch')
    return bytes(original if rollback else expected)


def render(profile,base):
    text=base.rstrip()+'\n\n// Battle candidates: KR native bindings; runtime acceptance pending.\n'
    text+='// HP modes are mutually exclusive. Cold boot after switching/off.\n'
    text+='// C1000/C2000 caves: outside original ELF; runtime ownership unverified.\n'
    for mode,label in MODES.items():
        text+=f'\n[{label}]\n'
        text+=f"description={profile['descriptions'][mode]}\n"
        for va,word in sorted(writes(profile,mode).items()):
            text+=f'patch=1,EE,{va:08X},word,{word:08X}\n'
    return text


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['baseline','apply','modified','rollback','pnach'])
    p.add_argument('--elf',type=Path,required=True)
    p.add_argument('--profile',type=Path,required=True)
    p.add_argument('--case',choices=list(MODES))
    p.add_argument('--input',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--base-pnach',type=Path)
    a=p.parse_args(); profile=json.loads(a.profile.read_text('utf8'))
    original=baseline(a.elf.read_bytes(),profile)
    if a.mode=='baseline':
        print(f'BASELINE PASS modes=5 ee_ram_bytes={len(original)} sha256={sha(original)}')
        return
    if a.mode=='pnach':
        result=render(profile,a.base_pnach.read_text('utf8')).encode('utf8')
    else:
        if not a.case:
            raise ValueError('case required')
        if a.mode=='modified':
            apply(a.input.read_bytes(),original,profile,a.case,rollback=True)
            print(f'MODIFIED PASS case={a.case} writes={len(writes(profile,a.case))}')
            return
        memory=a.input.read_bytes() if a.input else original
        result=apply(memory,original,profile,a.case,rollback=a.mode=='rollback')
    if not a.output or a.output.resolve()==a.elf.resolve() or (a.input and a.output.resolve()==a.input.resolve()):
        raise ValueError('separate output required')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(result)
    if a.output.read_bytes()!=result:
        raise ValueError('readback mismatch')
    print(f'{a.mode.upper()} PASS case={a.case or "all"} sha256={sha(result)}')


if __name__=='__main__':
    main()
