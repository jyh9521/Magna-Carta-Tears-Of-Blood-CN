"""Cheat regression: all-effect audit and emitted speed-gate instruction models."""
from contextlib import ExitStack
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tests')]
import unify_cheat_hotkeys as tool
import build_field_speed_cheats as field
import build_hotkey_cheats as hotkey
from test_field_speed_cheats import fixture,bits
from test_hotkey_cheats import execute_input

HP,F,Q=tool.profiles();LATCH=int(HP[0]['state_address'],16)


class AllHotkeyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=bytearray(32*1024*1024)
        for profile in (HP[2],F):
            for va,data in profile['anchors'].items():
                raw=bytes.fromhex(data);start=int(va,16);cls.original[start:start+len(raw)]=raw
        for row in HP[1]['codes']+Q['codes']:
            struct.pack_into('<I',cls.original,int(row['va'],16),int(row['expected'],16))
        struct.pack_into('<I',cls.original,0x1c69e4,0x28410002)
        core=hotkey.controller_program(HP[0])
        src='gametitle=controlled fixture\n[controller]\npatch=0,EE,000C3FE0,word,00000000\n'
        for va,w in sorted(core.items()):src+=f'patch=1,EE,{va:08X},word,{w:08X}\n'
        src+='[hint]\ndescription=instruction-only\n[already_gated]\n'
        src+='\n'.join(hotkey.blocks(HP[0],{0x1c69e4:0x28410001},{0x1c69e4:0x28410002}))+'\n'
        src+='[restore]\npatch=1,EE,001C69E4,word,28410002\n'
        src+='[undetected]\n'
        for va,w in field.writes(F,'undetected').items():src+=f'patch=1,EE,{va:08X},word,{w:08X}\n'
        src+='[auto_qte]\npatch=1,EE,002F8B8C,word,24020001\n'
        for factor in (2,4):
            src+=f'[speed_{factor}]\ndescription=speed\n'
            for i in (0,4,8):src+=f"patch=0,EE,{int(F['speed_state'],16)+i:08X},word,00000000\n"
            for va,w in field.speed_program(F,factor).items():src+=f'patch=1,EE,{va:08X},word,{w:08X}\n'
        cls.source=src

    def mocked(self):
        stack=ExitStack()
        stack.enter_context(patch.object(hotkey,'original_memory',return_value=self.original))
        stack.enter_context(patch.object(field,'baseline',return_value=self.original))
        stack.enter_context(patch.object(tool.qte,'validate',return_value=b''))
        return stack

    def built(self):
        with self.mocked():return tool.render(b'fixture',self.source)

    def test_identifies_four_previously_ungated_effects(self):
        with self.mocked():rows=tool.audit(b'fixture',self.source)[3]
        self.assertEqual(sum(r['kind'] in ('ungated','speed_ungated') for r in rows),4)

    def test_all_effects_gated_and_legacy_core_unchanged(self):
        new=self.built()
        with self.mocked():
            rows=tool.audit(b'fixture',new)[3]
            before=tool.parse(self.source)[1];after=tool.parse(new)[1]
        self.assertFalse(any(r['kind'] in ('ungated','speed_ungated') for r in rows))
        self.assertEqual([r['label'] for r in before],[r['label'] for r in after])
        for i in (0,2,3):self.assertEqual(before[i]['commands'],after[i]['commands'])

    def test_stateless_selected_on_off_using_controller_packets(self):
        text=self.built()
        for label,writes in [('undetected',field.writes(F,'undetected')),('auto_qte',{0x2f8b8c:0x24020001})]:
            memory=hotkey.apply_pnach(self.original,text,{'controller',label},startup=True)
            for key,state in [(0x11,1),(0,1),(0x41,0),(0,0),(0x11,1),(0x41,0)]:
                old=struct.unpack_from('<I',memory,LATCH)[0]
                latch=execute_input(key,old).load(LATCH);self.assertEqual(latch,state)
                changed=bytearray(memory);struct.pack_into('<I',changed,LATCH,latch)
                memory=hotkey.apply_pnach(changed,text,{'controller',label})
                for va,w in (writes if state else hotkey.restore_words(self.original,writes)).items():
                    self.assertEqual(struct.unpack_from('<I',memory,va)[0],w)

    def test_unselected_effects_untouched_when_global_on(self):
        text=self.built();mem=bytearray(self.original);struct.pack_into('<I',mem,LATCH,1)
        result=hotkey.apply_pnach(mem,text,{'controller'})
        for case in ('undetected','battle_2x','battle_4x'):
            for va in field.writes(F,case):self.assertEqual(result[va:va+4],self.original[va:va+4])
        self.assertEqual(result[0x2f8b8c:0x2f8b90],self.original[0x2f8b8c:0x2f8b90])

    def machine(self,factor=2,flag=0,**kwargs):
        m=fixture(factor,**kwargs);m.code=field.speed_program(F,factor,gate=LATCH);m.store(LATCH,flag)
        return m

    def tick(self,m):
        before=m.regs.copy();fpu=m.fpu.copy()
        m.run(int(F['speed_hook'],16),int(F['speed_hook'],16)+8)
        for r in range(1,32):
            if r!=2:self.assertEqual(m.regs[r],before[r],str(r))
        self.assertEqual(m.regs[2],0x640000);self.assertEqual(m.fpu[0],bits(0.125))
        self.assertEqual(m.fpu[1:],fpu[1:])

    def test_speed_default_off_has_no_write(self):
        for factor in (2,4):
            m=self.machine(factor);self.tick(m)
            self.assertEqual(m.load(0x62023c),bits(1.0));self.assertEqual(m.load(0xc43f0),0)

    def test_speed_select_up_down_restores_while_still_in_battle(self):
        for factor in (2,4):
            m=self.machine(factor)
            for key,expect in [(0x11,factor),(0,factor),(0x41,1),(0,1),(0x11,factor),(0x41,1)]:
                m.store(LATCH,execute_input(key,m.load(LATCH)).load(LATCH));self.tick(m)
                self.assertEqual(m.load(0x62023c),bits(expect))
            self.assertEqual(m.load(0x60024b,1),2)

    def test_speed_gate_preserves_slow_motion_base(self):
        for factor in (2,4):
            m=self.machine(factor,1,speed=0.5);self.tick(m)
            self.assertEqual(m.load(0x62023c),bits(0.5*factor));m.store(LATCH,0);self.tick(m)
            self.assertEqual(m.load(0x62023c),bits(0.5))

    def test_speed_off_preserves_external_value(self):
        m=self.machine(flag=1);self.tick(m);m.store(0x62023c,bits(0.25));m.store(LATCH,0);self.tick(m)
        self.assertEqual(m.load(0x62023c),bits(0.25));self.assertEqual(m.load(0xc43f0),0)

    def test_speed_neutral_does_not_compound(self):
        m=self.machine(flag=1)
        for _ in range(10):self.tick(m);self.assertEqual(m.load(0x62023c),bits(2))

    def test_invalid_latch_is_off(self):
        for value in (2,0x10001,0xffffffff):
            m=self.machine(flag=value);self.tick(m);self.assertEqual(m.load(0x62023c),bits(1))
            m=self.machine(flag=1);self.tick(m);m.store(LATCH,value);self.tick(m)
            self.assertEqual(m.load(0x62023c),bits(1))

    def test_speed_exit_and_new_owner_safe(self):
        m=self.machine(flag=1);self.tick(m);m.store(0x60024b,1,1);self.tick(m)
        self.assertEqual(m.load(0x62023c),bits(1))
        m=self.machine(flag=1);self.tick(m);m.store(0x600078,0x630000);m.store(0x63023c,bits(0.5))
        m.store(LATCH,0);self.tick(m)
        self.assertEqual(m.load(0x63023c),bits(0.5));self.assertEqual(m.load(0x62023c),bits(2))

    def test_rejects_unknown_write_and_bad_conditional_count(self):
        for source in (self.source+'[unknown]\npatch=1,EE,00600000,word,00000001\n',self.source.replace('E0010001','E0020001',1)):
            with self.mocked(),self.assertRaises(ValueError):tool.render(b'fixture',source)

    def test_idempotent_and_no_duplicate_hotkey_note(self):
        text=self.built()
        with self.mocked():self.assertEqual(tool.render(b'fixture',text),text)

    def test_caves_and_invalid_gate_bounds(self):
        for factor in (2,4):self.assertLess(max(va for va in field.speed_program(F,factor,gate=LATCH) if va<0x100000),0xc43f0)
        for addr in (-1,3,32*1024*1024):
            with self.assertRaises(ValueError):field.speed_program(F,2,gate=addr)


if __name__=='__main__':unittest.main()
