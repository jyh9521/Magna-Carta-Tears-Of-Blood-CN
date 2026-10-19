"""Bounded emitted-code and PNACH checks; not in-game acceptance."""
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import protect_story_item_removal as tool
P=json.loads((ROOT/'profiles/cheats/SCKA-20043_AE86E04C-item-story.json').read_text('utf8'))


class Machine:
    def __init__(self,code,caller,old=1,remove=1):
        self.code=code;self.regs=[(0x12345+i)<<80|i for i in range(32)]
        self.regs[0]=0;self.regs[2]=old-remove;self.regs[3]=0x600000
        self.regs[29]=0x710000;self.regs[31]=caller;self.memory={}
        self.write(0x600004,old,4)
    def write(self,at,v,n):
        for i in range(n):self.memory[at+i]=(v>>(i*8))&255
    def read(self,at,n):return sum(self.memory[at+i]<<(i*8) for i in range(n))
    def plain(self,w):
        op,rs,rt=w>>26,(w>>21)&31,(w>>16)&31
        imm=w&65535;imm=imm-65536 if imm&32768 else imm
        at=((self.regs[rs]&0xffffffff)+imm)&0xffffffff
        if not w:return
        if op==9:self.regs[rt]=(self.regs[rs]+imm)&0xffffffffffffffff
        elif op==15:self.regs[rt]=(w&65535)<<16
        elif op in (31,43):self.write(at,self.regs[rt],16 if op==31 else 4)
        elif op in (30,35):self.regs[rt]=self.read(at,16 if op==30 else 4)
        else:raise AssertionError(hex(w))
        self.regs[0]=0
    def run(self):
        pc=P['hook']
        for _ in range(100):
            if pc==P['resume']:return
            w=self.code[pc];op=w>>26
            if op in (2,4,5):
                if op==2:dest=((pc+4)&0xf0000000)|((w&0x3ffffff)<<2)
                else:
                    a=self.regs[(w>>21)&31]&0xffffffffffffffff;b=self.regs[(w>>16)&31]&0xffffffffffffffff
                    imm=w&65535;imm=imm-65536 if imm&32768 else imm
                    take=(a==b) if op==4 else (a!=b);dest=pc+4+4*imm if take else pc+8
                self.plain(self.code[pc+4]);pc=dest
            else:self.plain(w);pc+=4
        raise AssertionError('hook did not terminate')


def old_section():
    return '['+P['section']+']\ndescription=legacy\n'+''.join([
        f"patch=1,EE,E0010001,extended,{P['latch']:08X}\n",
        f"patch=1,EE,{0x20000000|P['hook']:08X},extended,00000000\n",
        f"patch=1,EE,E0010000,extended,{P['latch']:08X}\n",
        f"patch=1,EE,{0x20000000|P['hook']:08X},extended,AC620004\n"])


def applied(text,state):
    lo,hi=tool.section_span(text,P['section']);cmds=tool.commands(text[lo:hi]);out={};i=0
    while i<len(cmds):
        _,addr,kind,value=cmds[i];i+=1
        if addr>>28==14:
            assert value==P['latch'];count=(addr>>16)&255
            if (addr&65535)!=state:i+=count
        else:out[addr&0xfffffff]=value
    return out


class ItemStoryCheatTests(unittest.TestCase):
    def built(self):
        with patch.object(tool,'validate'):
            return tool.render(b'fixture',P,'header\n'+old_section()+'[other]\ndescription=keep\n')
    def test_legacy_reproduces_story_failure(self):
        m=Machine({P['hook']:0,P['hook']+4:0x8c620004},P['script_returns'][1]);m.run()
        self.assertEqual(m.read(0x600004,4),1)
    def test_all_story_callers_decrement(self):
        for ra in P['script_returns']:
            for n in (1,2,99):
                m=Machine(tool.program(P),ra,n);m.run()
                self.assertEqual(m.read(0x600004,4),n-1)
    def test_ordinary_retains_quantity(self):
        for n in (1,2,99):
            m=Machine(tool.program(P),P['ordinary_return'],n);m.run()
            self.assertEqual(m.read(0x600004,4),n)
    def test_unknown_caller_uses_stock(self):
        m=Machine(tool.program(P),0x123456);m.run();self.assertEqual(m.read(0x600004,4),0)
    def test_preserves_registers_including_128bit_at_and_stack(self):
        for ra in [P['ordinary_return'],*P['script_returns']]:
            m=Machine(tool.program(P),ra);before=m.regs.copy();m.run()
            for r in range(32):
                if r!=2:self.assertEqual(m.regs[r],before[r],r)
    def test_on_off_and_reenable(self):
        text=self.built()
        for state in (0,1,0,1):
            code=applied(text,state)
            m=Machine(code,P['script_returns'][0]);m.run();self.assertEqual(m.read(0x600004,4),0)
            m=Machine(code,P['ordinary_return']);m.run();self.assertEqual(m.read(0x600004,4),state)
    def test_other_sections_exact(self):
        result=self.built();self.assertTrue(result.startswith('header\n'));self.assertTrue(result.endswith('[other]\ndescription=keep\n'))
    def test_unknown_source_refused(self):
        with patch.object(tool,'validate'):
            with self.assertRaises(ValueError):tool.render(b'fixture',P,old_section().replace('00000000','24020001'))
    def test_cave_collision_refused(self):
        with patch.object(tool,'validate'):
            with self.assertRaises(ValueError):tool.render(b'fixture',P,old_section()+f"[other]\npatch=1,EE,{P['cave']:08X},word,00000000\n")
    def test_wrong_elf_refused(self):
        with self.assertRaises(ValueError):tool.validate(b'unknown',P)


if __name__=='__main__':unittest.main()
