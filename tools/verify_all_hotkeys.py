"""Verify actual unified PNACH blocks and speed-maintenance emitted code."""
import argparse
from pathlib import Path
import struct
import sys
import unify_cheat_hotkeys as tool
import build_hotkey_cheats as hotkey
import build_field_speed_cheats as field

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from test_hotkey_cheats import execute_input
from test_field_speed_cheats import fixture,bits


def verify(elf,source,candidate,phase):
    before=tool.audit(elf,source)[3]
    original,_,groups,rows=tool.audit(elf,candidate)
    if tool.render(elf,source)!=candidate:raise ValueError('candidate does not match guarded transformation')
    if [r['label'] for r in before]!=[r['label'] for r in rows]:raise ValueError('section names/order changed')
    profile,f,q=tool.profiles();latch=int(profile[0]['state_address'],16)
    core={r['label'] for r in rows if r['kind']=='controller'}
    effects=[r for r in rows if r['kind'] in ('conditional','speed_runtime_gate')]
    if any(r['kind'] in ('ungated','speed_ungated') for r in rows):raise ValueError('ungated effect remains')
    if phase=='baseline':
        missing=sum(r['kind'] in ('ungated','speed_ungated') for r in before)
        memory=hotkey.apply_pnach(original,candidate,{r['label'] for r in rows},startup=True)
        if struct.unpack_from('<I',memory,latch)[0]!=0:raise ValueError('not default OFF')
        print(f'BASELINE PASS effects={len(effects)} previously_ungated={missing} default=off');return
    transitions=0
    for row in effects:
        enabled=core|{row['label']}
        memory=hotkey.apply_pnach(original,candidate,enabled,startup=True)
        memory=hotkey.apply_pnach(memory,candidate,enabled)
        if row['kind']=='speed_runtime_gate':
            factor=row['factor'];expected=field.speed_program(f,factor,gate=latch)
            machine=fixture(factor)
            machine.code={va:struct.unpack_from('<I',memory,va)[0] for va in expected}
        else:
            for va,w in row['off'].items():
                if struct.unpack_from('<I',memory,va)[0]!=w:raise ValueError('default stateless effect ON')
        for key,state in [(0x11,1),(0,1),(0x41,0),(0,0),(0x11,1),(0x41,0)]:
            old=struct.unpack_from('<I',memory,latch)[0]
            got=execute_input(key,old).load(latch)
            if got!=state:raise ValueError('input latch transition mismatch')
            changed=bytearray(memory);struct.pack_into('<I',changed,latch,got)
            memory=hotkey.apply_pnach(changed,candidate,enabled)
            if row['kind']=='conditional':
                for va,w in (row['on'] if state else row['off']).items():
                    if struct.unpack_from('<I',memory,va)[0]!=w:raise ValueError('stateless effect ON/OFF mismatch')
            else:
                machine.code={va:struct.unpack_from('<I',memory,va)[0] for va in expected}
                machine.store(latch,got)
                machine.run(int(f['speed_hook'],16),int(f['speed_hook'],16)+8)
                if machine.load(0x62023c)!=bits(factor if state else 1):raise ValueError('owned battle speed not restored while still in battle')
                if machine.load(0x60024b,1)!=2:raise ValueError('speed proof left battle')
            transitions+=1
        blank=bytearray(original);struct.pack_into('<I',blank,latch,1)
        untouched=hotkey.apply_pnach(blank,candidate,core)
        check=row['on'] if row['kind']=='conditional' else field.speed_program(f,row['factor'],gate=latch)
        for va in check:
            if untouched[va:va+4]!=original[va:va+4]:raise ValueError('unchecked effect applied')
    print(f'MODIFIED PASS effects={len(effects)} transitions={transitions} ungated=0 speed_OFF_restores_owned_base=true unchecked_untouched=true')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('phase',choices=['baseline','modified'])
    ap.add_argument('--elf',type=Path,required=True);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--pnach',type=Path,required=True)
    a=ap.parse_args();verify(a.elf.read_bytes(),a.source.read_text('utf8'),a.pnach.read_text('utf8'),a.phase)
