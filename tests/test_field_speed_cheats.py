"""Instruction-model checks only, never runtime acceptance."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_field_speed_cheats as tool
from test_battle_cheats import Machine
P=json.loads((ROOT/'profiles/cheats/SCKA-20043_AE86E04C-field-speed.json').read_text('utf8'))


def bits(value): return struct.unpack('<I',struct.pack('<f',value))[0]


class SpeedMachine(Machine):
    def __init__(self,code): super().__init__(code);self.fpu=[0]*32
    def plain(self,w):
        op,rs,rt,rd=w>>26,(w>>21)&31,(w>>16)&31,(w>>11)&31
        if op==12:self.regs[rt]=self.regs[rs]&(w&65535)
        elif op==13:self.regs[rt]=self.regs[rs]|(w&65535)
        elif op==0 and w&63 in (0x21,0x2d,0x2b):
            if w&63==0x2b:self.regs[rd]=int((self.regs[rs]&0xffffffffffffffff)<(self.regs[rt]&0xffffffffffffffff))
            else:self.regs[rd]=(self.regs[rs]+self.regs[rt])&0xffffffffffffffff
        elif op==49:
            imm=w&65535;imm=imm-65536 if imm&32768 else imm
            self.fpu[rt]=self.load((self.regs[rs]+imm)&0xffffffff)
        else:super().plain(w)
        self.regs[0]=0


def fixture(factor=2,mode=2,speed=1.0,level=0x620000):
    m=SpeedMachine(tool.writes(P,f'battle_{factor}x'))
    for r in range(1,32):m.regs[r]=((0xabcdef+r)<<80)|r
    m.regs[17]=0x600000;m.regs[29]=0x710000
    m.store(0x600078,level);m.store(0x60024b,mode,1)
    m.store(0x600220,0x640000);m.store(0x71003c,bits(0.125))
    m.store(level+0x23c,bits(speed))
    return m


class FieldSpeedTests(unittest.TestCase):
    def tick(self,m):
        before=m.regs.copy();fpu=m.fpu.copy()
        m.run(int(P['speed_hook'],16),int(P['speed_hook'],16)+8)
        for r in range(1,32):
            if r!=2:self.assertEqual(m.regs[r],before[r],f'register {r}')
        self.assertEqual(m.regs[2],0x640000)
        self.assertEqual(m.fpu[0],bits(0.125))
        self.assertEqual(m.fpu[1:],fpu[1:])

    def test_original_tick_does_not_change_speed(self):
        m=fixture();m.code={0x3fe208:0x8e220220,0x3fe20c:0xc7a0003c}
        self.tick(m);self.assertEqual(m.load(0x62023c),bits(1.0))

    def test_both_factors_and_non_compounding(self):
        for factor in (2,4):
            for base in (0.0625,0.1,0.5,1.0,1.5,4.0):
                m=fixture(factor,speed=base)
                for _ in range(3):self.tick(m);self.assertEqual(m.load(0x62023c),bits(base*factor))

    def test_leave_battle_restores_base(self):
        for factor in (2,4):
            m=fixture(factor,speed=0.5);self.tick(m)
            m.store(0x60024b,1,1);self.tick(m)
            self.assertEqual(m.load(0x62023c),bits(0.5));self.assertEqual(m.load(0xc43f0),0)

    def test_nonbattle_modes_untouched(self):
        for mode in (0,1,3,4,5,6,255):
            m=fixture(mode=mode,speed=0.25);self.tick(m)
            self.assertEqual(m.load(0x62023c),bits(0.25))

    def test_external_speed_change_adopted(self):
        m=fixture();self.tick(m);m.store(0x62023c,bits(0.25));self.tick(m)
        self.assertEqual(m.load(0x62023c),bits(0.5))
        m.store(0x60024b,1,1);self.tick(m);self.assertEqual(m.load(0x62023c),bits(0.25))

    def test_external_change_on_exit_is_preserved(self):
        m=fixture();self.tick(m);m.store(0x62023c,bits(0.25));m.store(0x60024b,1,1)
        self.tick(m);self.assertEqual(m.load(0x62023c),bits(0.25))

    def test_new_level_never_dereferences_old_owner(self):
        m=fixture();self.tick(m);m.store(0x600078,0x630000)
        m.store(0x63023c,bits(0.5));self.tick(m)
        self.assertEqual(m.load(0x63023c),bits(1.0));self.assertEqual(m.load(0x62023c),bits(2.0))
        m.store(0x60024b,1,1);self.tick(m);self.assertEqual(m.load(0x63023c),bits(0.5))

    def test_invalid_level_no_dereference(self):
        for level in (0,0x600001,0x02000000,0xffffffff):
            m=fixture(level=level);self.tick(m);self.assertEqual(m.load(0xc43f0),0)

    def test_zero_negative_nan_infinite_and_outside_range_untouched(self):
        for speed in (0.0,-1.0,0.01,8.0,float('nan'),float('inf')):
            m=fixture(speed=speed);original=m.load(0x62023c);self.tick(m)
            self.assertEqual(m.load(0x62023c),original);self.assertEqual(m.load(0xc43f0),0)

    def test_detection_branches_reach_original_epilogues(self):
        code=tool.writes(P,'undetected')
        for start,stop in [(0x3f72c0,0x3f7374),(0x3f746c,0x3f75c0)]:
            m=SpeedMachine(code);before=m.regs.copy();m.run(start,stop)
            self.assertEqual(m.regs,before)

    def test_walk_candidate_only_changes_config_indices(self):
        code=tool.writes(P,'walk_base_speed')
        self.assertEqual(code,{0x388924:0x24050048,0x388950:0x24050048})
        for w in code.values():
            m=SpeedMachine({});m.plain(w);self.assertEqual(m.regs[5],0x48)
        self.assertTrue(P['cases']['walk_base_speed']['withdrawn'])
        self.assertNotIn('[侦测移动',tool.render(P))

    def test_render_names_state_startup_only_and_mutual_exclusion(self):
        text=tool.render(P)
        self.assertEqual(text.count('patch=0,'),6)
        self.assertEqual(text.count('['),3)
        self.assertIn('最多选1项',text)
        for factor in (2,4):
            self.assertTrue(max(v for v in tool.writes(P,f'battle_{factor}x') if v<0x100000)<0xc43f0)

    def test_reject_bad_elf(self):
        for blob in (b'',bytes(P['elf_size'])):
            with self.assertRaises(ValueError):tool.baseline(blob,P)


if __name__=='__main__':unittest.main()
