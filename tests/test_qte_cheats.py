"""Native leaf instruction proof plus explicit source-derived QTE model.

The rhythm model is not Unreal VM or game execution.
"""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_qte_cheats as tool
from test_battle_cheats import Machine
P=json.loads((ROOT/'profiles/cheats/SCKA-20043_AE86E04C-qte.json').read_text('utf8'))


class GetterMachine(Machine):
    def plain(self,word):
        if word>>26==0 and word&63 in (0x3c,0x3e):
            rt,rd,shift=(word>>16)&31,(word>>11)&31,32+((word>>6)&31)
            v=self.regs[rt]&0xffffffffffffffff
            self.regs[rd]=(v<<shift)&0xffffffffffffffff if word&63==0x3c else v>>shift
        else:super().plain(word)


def leaf(flag,modified):
    row=P['codes'][0];words=list(struct.unpack('<4I',bytes.fromhex(row['context_hex'])))
    if modified:words[-1]=int(row['replacement'],16)
    m=GetterMachine({})
    m.regs=[((0xabcdef+r)<<80)|r for r in range(32)]
    m.regs[0]=0;m.regs[4]=0x600000;m.regs[31]=0x12345678
    m.store(0x6007b5,flag,1);before=m.regs.copy();memory=m.bytes.copy()
    for word in words[:2]:m.plain(word)
    assert words[2]==0x03e00008
    target=m.regs[31];m.plain(words[3])  # Execute JR's delay slot before returning.
    assert target==0x12345678 and m.bytes==memory
    return m.regs,before


class Round:
    """Small model of the recorded GetGreat branch, not the whole rhythm engine."""
    def __init__(self,enabled,style='normal'):
        self.enabled=enabled;self.style=style;self.state='idle';self.playing=False
        self.broken=False;self.cur=0;self.count=0;self.desire=0;self.time=0;self.results=[]
    def start(self):
        self.state='start';self.playing=True;self.results=['great'];self.cur=1;self.count=1;self.desire=1
    def tick(self,delta):
        if self.broken or not self.playing:return
        self.time+=delta
        threshold=(self.count+(self.style=='counter'))*100+15
        if self.time<=threshold or self.state=='idle':return
        if self.desire==self.cur:
            self.results.append('great' if self.enabled else 'miss');self.cur+=1;self.count+=1
            if not self.enabled:self.broken=True;return
        self.desire=self.cur
        if self.cur>=3:self.state='finish';self.playing=False


class QteTests(unittest.TestCase):
    def test_original_getter_all_256_flag_bytes(self):
        for value in range(256):
            regs,before=leaf(value,False);self.assertEqual(regs[2],(value>>1)&1)
            self.assertEqual(regs[:2]+regs[3:],before[:2]+before[3:])
    def test_modified_getter_all_256_flag_bytes(self):
        for value in range(256):
            regs,before=leaf(value,True);self.assertEqual(regs[2],1)
            self.assertEqual(regs[:2]+regs[3:],before[:2]+before[3:])
    def test_profile_displaced_delay_exact_and_only_one_word(self):
        r=P['codes'][0];self.assertEqual((r['va'],r['expected'],r['replacement']),('002F8B8C','000217FE','24020001'))
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(r['context_hex'])),(0x908207b5,0x000217bc,0x03e00008,0x000217fe))
    def test_normal_auto_finishes_after_first_input(self):
        r=Round(True);r.start()
        for _ in range(100):r.tick(10)
        self.assertEqual((r.results,r.state),(['great']*3,'finish'))
    def test_speed_1_2_4_and_large_step_do_not_skip_results(self):
        for speed in (1,2,4,64):
            r=Round(True);r.start()
            for _ in range(100):r.tick(10*speed)
            self.assertEqual(r.results,['great']*3)
    def test_first_input_required_and_menu_idle_untouched(self):
        r=Round(True)
        for _ in range(100):r.tick(100)
        self.assertEqual((r.results,r.state),([],'idle'))
    def test_off_times_out_as_miss(self):
        r=Round(False);r.start();r.tick(200)
        self.assertEqual((r.results,r.broken),(['great','miss'],True))
    def test_pause_and_broken_round_do_not_progress(self):
        for paused in (True,False):
            r=Round(True);r.start();r.playing=not paused;r.broken=not paused
            r.tick(1000);self.assertEqual(r.results,['great'])
    def test_counter_uses_later_deadline(self):
        r=Round(True,'counter');r.start();r.tick(150);self.assertEqual(r.cur,1)
        r.tick(70);self.assertEqual(r.cur,2);r.tick(100);self.assertEqual(r.state,'finish')
    def test_render_is_one_independent_no_input_injection_section(self):
        t=tool.render(P);self.assertEqual(t.count('patch='),1)
        self.assertIn('patch=1,EE,002F8B8C,word,24020001',t);self.assertIn('首键启动',t)
    def test_wrong_source_rejected(self):
        with self.assertRaises(ValueError):tool.validate(bytes(P['elf_size']),P)


if __name__=='__main__':unittest.main()
