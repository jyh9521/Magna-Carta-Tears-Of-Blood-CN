"""Bounded R5900 instruction checks, not emulator/gameplay acceptance."""
import json
import re
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_battle_cheats as tool
PROFILE=json.loads((ROOT/'profiles/cheats/SCKA-20043_AE86E04C-battle.json').read_text('utf8'))


class Machine:
    def __init__(self,code):
        self.code,self.bytes,self.regs=code,{},[0]*32
        self.pc,self.target=0,None

    def store(self,addr,value,size=4):
        for i in range(size):self.bytes[addr+i]=(value>>(8*i))&255

    def load(self,addr,size=4):
        return sum(self.bytes.get(addr+i,0)<<(8*i) for i in range(size))

    def plain(self,word):
        op,rs,rt=word>>26,(word>>21)&31,(word>>16)&31
        imm=word&65535; signed=imm-65536 if imm&32768 else imm
        addr=((self.regs[rs]&0xffffffff)+signed)&0xffffffff
        if word==0:return
        if op==9:self.regs[rt]=(self.regs[rs]+signed)&0xffffffffffffffff
        elif op==15:self.regs[rt]=imm<<16
        elif op in [35,36,30]:
            size={35:4,36:1,30:16}[op];value=self.load(addr,size)
            if op==35 and value&0x80000000:value|=0xffffffff00000000
            self.regs[rt]=value
        elif op in [43,31,63]:self.store(addr,self.regs[rt],{43:4,31:16,63:8}[op])
        else:raise AssertionError(f'unsupported bounded instruction {word:08X}')
        self.regs[0]=0

    def run(self,start,stop,max_steps=500):
        self.pc=start
        for _ in range(max_steps):
            if self.pc==stop:self.target=stop;return
            word=self.code[self.pc];op=word>>26
            if op in [2,3,4,5,6]:
                rs,rt=(word>>21)&31,(word>>16)&31
                imm=word&65535;imm=imm-65536 if imm&32768 else imm
                if op in [2,3]:
                    target=((self.pc+4)&0xf0000000)|((word&0x3ffffff)<<2)
                    if op==3:self.regs[31]=self.pc+8
                else:
                    left,right=self.regs[rs]&0xffffffffffffffff,self.regs[rt]&0xffffffffffffffff
                    signed=left-(1<<64) if left&(1<<63) else left
                    taken=(left==right if op==4 else left!=right if op==5 else signed<=0)
                    target=self.pc+4+4*imm if taken else self.pc+8
                self.plain(self.code[self.pc+4]);self.pc=target
            else:self.plain(word);self.pc+=4
        raise AssertionError('bounded hook did not terminate')


def fixture(mode,team=0,hp=100,kind='battle',derived=False,cache=True):
    m=Machine(tool.writes(PROFILE,mode))
    # Deliberately nonzero high 128-bit lanes detect accidental truncation.
    for r in range(1,32):m.regs[r]=((0xabcdef+r)<<80)|r
    m.regs[4]=0x600000;m.regs[28]=0x700000;m.regs[29]=0x710000;m.regs[31]=0x12345678
    m.store(0x700000+PROFILE['team_cache_gp_offset'],0x610000 if cache else 0)
    m.store(0x600024,0x610100 if derived else 0x610000 if kind=='battle' else 0x620000)
    if derived:m.store(0x610128,0x610000)
    m.store(0x60039c,team,1);m.store(0x60020c,0x630000)
    m.store(0x630060,0x640000);m.store(0x640034,200);m.store(0x6400ac,hp)
    return m


class BattleCheatTests(unittest.TestCase):
    def test_baseline_prologue_leaves_hp_unchanged(self):
        m=fixture('ally_heal')
        m.code={0x399190:0x27bdfff0,0x399194:0xffbf0000}
        m.run(0x399190,0x399198)
        self.assertEqual((m.load(0x640034),m.load(0x6400ac)),(200,100))

    def execute(self,mode,**kwargs):
        m=fixture(mode,**kwargs);before=m.regs.copy()
        m.run(int(PROFILE['hp_hook'],16),int(PROFILE['hp_resume'],16))
        for r in [1,2,3,4,5,6,7,8,9,10,16,17,28,31]:self.assertEqual(m.regs[r],before[r])
        self.assertEqual(m.regs[29],before[29]-16)
        self.assertEqual(m.load(m.regs[29],8),before[31]&0xffffffffffffffff)
        return m

    def test_ally_heal(self):
        m=self.execute('ally_heal');self.assertEqual((m.load(0x640034),m.load(0x6400ac)),(9999,9999))

    def test_max_hp_only(self):
        m=self.execute('ally_max_hp');self.assertEqual((m.load(0x640034),m.load(0x6400ac)),(9999,100))

    def test_enemy_one_hp(self):
        m=self.execute('enemy_one_hp',team=5);self.assertEqual((m.load(0x640034),m.load(0x6400ac)),(200,1))

    def test_combo_both_roles(self):
        for team,expected in [(0,9999),(5,1)]:
            m=self.execute('heal_and_one_hp',team=team);self.assertEqual(m.load(0x6400ac),expected)

    def test_other_teams_unchanged(self):
        for team in [1,2,3,4,6,255]:
            m=self.execute('heal_and_one_hp',team=team);self.assertEqual(m.load(0x6400ac),100)

    def test_opposite_role_unchanged(self):
        for mode,team in [('ally_heal',5),('ally_max_hp',5),('enemy_one_hp',0)]:
            m=self.execute(mode,team=team);self.assertEqual(m.load(0x6400ac),100)

    def test_dead_not_revived(self):
        for team in [0,5]:
            for hp in [0,-1]:
                m=self.execute('heal_and_one_hp',team=team,hp=hp);self.assertEqual(m.load(0x6400ac),hp&0xffffffff)

    def test_nonbattle_unchanged(self):
        m=self.execute('heal_and_one_hp',kind='other');self.assertEqual(m.load(0x6400ac),100)

    def test_derived_battle_class(self):
        m=self.execute('ally_heal',derived=True);self.assertEqual(m.load(0x6400ac),9999)

    def test_uninitialized_class_cache(self):
        m=self.execute('ally_heal',cache=False);self.assertEqual(m.load(0x6400ac),100)

    def test_null_character_or_status(self):
        for addr in [0x60020c,0x630060]:
            m=fixture('ally_heal');m.store(addr,0)
            m.run(int(PROFILE['hp_hook'],16),int(PROFILE['hp_resume'],16))
            self.assertEqual(m.load(0x6400ac),100)

    def test_leadership_tail_and_delay_slot(self):
        m=Machine(tool.writes(PROFILE,'ally_leadership'));m.regs[4]=0x650000;m.regs[31]=0x3fd760
        m.store(0x650028,0)
        m.run(int(PROFILE['lead_cave'],16),0x4183f0)
        self.assertEqual(m.load(0x650028),0x42c80000)
        self.assertEqual(struct.unpack('<f',struct.pack('<I',m.load(0x650028)))[0],100.0)
        self.assertEqual(m.regs[31],0x3fd760)
        self.assertEqual(tool.writes(PROFILE,'ally_leadership')[0x3fd758],0x0c030800)

    def test_render_five_sections(self):
        text=tool.render(PROFILE,'gametitle=fixture')
        self.assertEqual(text.count('[战斗：'),5)

    def test_descriptions_are_chinese(self):
        for description in PROFILE['descriptions'].values():
            self.assertTrue(description)
            self.assertIsNone(re.search('[A-Za-z]',description))

    def test_unknown_version_rejected(self):
        with self.assertRaisesRegex(ValueError,'original ELF'):
            tool.baseline(b'',PROFILE)


if __name__=='__main__':unittest.main()
