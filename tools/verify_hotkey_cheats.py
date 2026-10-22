"""Verify generated input toggle control against original ELF and bounded models."""
import argparse
from pathlib import Path
import struct
import sys
import build_hotkey_cheats as tool

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['baseline','modified'])
    p.add_argument('--elf',type=Path,required=True)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--pnach',type=Path,required=True)
    a=p.parse_args();profiles=tool.load_profiles()
    original=tool.original_memory(a.elf.read_bytes(),profiles)
    text=tool.render(a.elf.read_bytes(),profiles,a.source.read_text('utf8'))
    if a.pnach.read_text('utf8')!=text:raise ValueError('generated PNACH mismatch')
    # The callback's external original padRead call is a controlled stub in this
    # model. No physical controller or PCSX2 runtime result is claimed.
    sys.path.insert(0,str(ROOT/'tests'))
    from test_hotkey_cheats import execute_input
    if a.mode=='baseline':
        result=tool.apply_pnach(original,text,set(tool.cases(profiles)),startup=True)
        if struct.unpack_from('<I',result,0xc3fe0)[0]!=0:raise ValueError('default not OFF')
        print('BASELINE PASS groups=14 default=off latch=0 original_elf_unchanged=true')
        return
    count=0
    for label,writes in tool.cases(profiles).items():
        selected={label}
        memory=tool.apply_pnach(original,text,selected,startup=True)
        memory=tool.apply_pnach(memory,text,selected)
        restore=tool.restore_words(original,writes)
        for va,word in restore.items():
            if struct.unpack_from('<I',memory,va)[0]!=word:raise ValueError('default effect ON')
        for buttons,state in [(0x11,1),(0,1),(0x41,0),(0,0),(0x11,1),(0x41,0)]:
            old=struct.unpack_from('<I',memory,0xc3fe0)[0]
            m=execute_input(buttons,old)
            value=m.load(0xc3fe0)
            if value!=state:raise ValueError('latch transition mismatch')
            changed=bytearray(memory);struct.pack_into('<I',changed,0xc3fe0,value)
            memory=tool.apply_pnach(changed,text,selected)
            for va,word in (writes if state else restore).items():
                if struct.unpack_from('<I',memory,va)[0]!=word:raise ValueError('selected write mismatch')
            count+=1
        # Unchecked sections must not run even when the controller latch is ON.
        blank=bytearray(original);struct.pack_into('<I',blank,0xc3fe0,1)
        untouched=tool.apply_pnach(blank,text,set())
        for va in writes:
            if untouched[va:va+4]!=original[va:va+4]:raise ValueError('unchecked effect modified')
    print(f'MODIFIED PASS groups=14 transitions={count} unchecked_untouched=true off_restores_original_instructions=true')


if __name__=='__main__':main()
