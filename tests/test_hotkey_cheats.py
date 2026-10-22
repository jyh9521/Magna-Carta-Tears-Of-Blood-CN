"""Controller callback and emitted PNACH models; not physical input acceptance."""
import struct
import sys
from pathlib import Path
from unittest.mock import patch
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tests')]
import build_hotkey_cheats as tool
from test_battle_cheats import Machine

PROFILES=tool.load_profiles();PROFILE=PROFILES[0]


class ControllerMachine(Machine):
    def plain(self,w):
        op,rs,rt=w>>26,(w>>21)&31,(w>>16)&31;imm=w&65535
        if op in [12,13,14]:
            self.regs[rt]=self.regs[rs]&imm if op==12 else self.regs[rs]|imm if op==13 else self.regs[rs]^imm
        elif op==55:
            imm=imm-65536 if imm&32768 else imm
            self.regs[rt]=self.load(((self.regs[rs]&0xffffffff)+imm)&0xffffffff,8)
        elif op==0 and w and (w&63)==0:
            rd,shift=(w>>11)&31,(w>>6)&31
            self.regs[rd]=(self.regs[rt]<<shift)&0xffffffff
        elif op==0 and (w&63)==0x25:self.regs[(w>>11)&31]=self.regs[rs]|self.regs[rt]
        else:super().plain(w)

    def run(self,start,stop,max_steps=500):
        self.pc=start
        for _ in range(max_steps):
            if self.pc==stop:self.target=stop;return
            if self.pc==int(PROFILE['pad_read'],16):
                self.stock_calls+=1
                self.asserted_args=(self.regs[4],self.regs[5],self.regs[6])
                for i,v in enumerate(self.packet):self.store(self.regs[6]+i,v,1)
                self.regs[2]=self.read_result
                for r in [4,5,6,8,9,10,11]:self.regs[r]=(0xabc000+r)<<80|r
                self.expected_return=self.regs.copy()
                self.pc=self.regs[31];continue
            w=self.code[self.pc];op=w>>26
            if op in [2,3,4,5,6] or w==0x03e00008:
                rs,rt=(w>>21)&31,(w>>16)&31;imm=w&65535;imm=imm-65536 if imm&32768 else imm
                if w==0x03e00008:target=self.regs[31]
                elif op in [2,3]:
                    target=((self.pc+4)&0xf0000000)|((w&0x3ffffff)<<2)
                    if op==3:self.regs[31]=self.pc+8
                else:
                    left,right=self.regs[rs]&0xffffffffffffffff,self.regs[rt]&0xffffffffffffffff
                    signed=left-(1<<64) if left&(1<<63) else left
                    taken=left==right if op==4 else left!=right if op==5 else signed<=0
                    target=self.pc+4+4*imm if taken else self.pc+8
                self.plain(self.code[self.pc+4]);self.pc=target
            else:self.plain(w);self.pc+=4
        raise AssertionError('controller wrapper did not return')


def execute_input(buttons,state=0,port=0,slot=0,ok=0,mode=0x73,result=32,raw_packet=None):
    code=tool.controller_program(PROFILE)
    code[int(PROFILE['input_hook'],16)+4]=0x260602a4
    m=ControllerMachine(code);m.stock_calls=0;m.read_result=result
    raw=buttons^65535;m.packet=[ok,mode,raw&255,raw>>8] if raw_packet is None else list(raw_packet)
    for r in range(1,32):m.regs[r]=(0xabcdef+r)<<80|r
    m.regs[4]=port;m.regs[5]=slot;m.regs[16]=0x600000;m.regs[29]=0x700000
    m.store(int(PROFILE['state_address'],16),state)
    m.run(int(PROFILE['input_hook'],16),int(PROFILE['input_hook'],16)+8)
    return m


class HotkeyCheatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=bytearray(32*1024*1024)
        for va,data in PROFILES[2]['anchors'].items():
            raw=bytes.fromhex(data);cls.original[int(va,16):int(va,16)+len(raw)]=raw
        for row in PROFILES[1]['codes']:
            struct.pack_into('<I',cls.original,int(row['va'],16),int(row['expected'],16))
        struct.pack_into('<I',cls.original,0x1c69e4,0x28410002)
        struct.pack_into('<I',cls.original,int(PROFILE['input_hook'],16),0x0c048200)
        labels=tool.cases(PROFILES);source='gametitle=fixture\n'
        for label,writes in labels.items():
            source+='['+label+']\ndescription=说明\n'
            for va,word in writes.items():source+=f'patch=1,EE,{va:08X},word,{word:08X}\n'
        cls.source=source
        with patch.object(tool,'original_memory',return_value=cls.original):
            cls.text=tool.render(b'controlled fixture',PROFILES,source)

    def test_select_up_on(self):self.assertEqual(execute_input(0x11).load(0xc3fe0),1)
    def test_runtime_captured_packets_enable(self):
        # Actual primary DMA packets captured while SELECT+Up was held.
        # Extra directions/buttons must not prevent the chord from working.
        for packet in ['0073eeff','0073ceff','0073eef7']:
            self.assertEqual(execute_input(0,raw_packet=bytes.fromhex(packet)).load(0xc3fe0),1)
    def test_raw_select_down_packet_disables(self):
        self.assertEqual(execute_input(0,1,raw_packet=bytes.fromhex('0073beff')).load(0xc3fe0),0)
    def test_select_down_off(self):self.assertEqual(execute_input(0x41,1).load(0xc3fe0),0)
    def test_both_directions_off_wins(self):self.assertEqual(execute_input(0x51,1).load(0xc3fe0),0)
    def test_neutral_keeps_state(self):
        for state in [0,1]:self.assertEqual(execute_input(0,state).load(0xc3fe0),state)
    def test_single_buttons_do_not_toggle(self):
        for key in [1,16,64,256,0x8000]:
            for state in [0,1]:self.assertEqual(execute_input(key,state).load(0xc3fe0),state)
    def test_additional_button_allowed(self):self.assertEqual(execute_input(0x8011).load(0xc3fe0),1)
    def test_port_and_slot_filter(self):
        for port,slot in [(1,0),(0,1)]:self.assertEqual(execute_input(0x41,1,port,slot).load(0xc3fe0),1)
    def test_invalid_read_disables(self):
        for kwargs in [{'ok':1},{'mode':0},{'result':0}]:self.assertEqual(execute_input(0x11,1,**kwargs).load(0xc3fe0),0)
    def test_supported_packet_modes(self):
        for mode in PROFILE['valid_modes']:self.assertEqual(execute_input(0x11,mode=mode).load(0xc3fe0),1)
    def test_stock_return_and_full_width_registers(self):
        m=execute_input(0x11)
        self.assertEqual(m.stock_calls,1);self.assertEqual(m.asserted_args,(0,0,0x6002a4))
        self.assertEqual(m.regs[2],32);self.assertEqual(m.regs[29],0x700000)
        self.assertEqual(m.regs[31],0x17c740)
        for r in range(1,32):
            if r not in [29,31]:self.assertEqual(m.regs[r],m.expected_return[r])

    def test_startup_is_off(self):
        memory=bytearray(self.original);struct.pack_into('<I',memory,0xc3fe0,1)
        result=tool.apply_pnach(memory,self.text,set(),startup=True)
        self.assertEqual(struct.unpack_from('<I',result,0xc3fe0)[0],0)

    def test_all_fourteen_on_off_restore_original_words(self):
        for label,writes in tool.cases(PROFILES).items():
            with self.subTest(label=label):
                default=tool.apply_pnach(self.original,self.text,{label})
                off=tool.restore_words(self.original,writes)
                for va,word in off.items():self.assertEqual(struct.unpack_from('<I',default,va)[0],word)
                memory=bytearray(default);struct.pack_into('<I',memory,0xc3fe0,1)
                active=tool.apply_pnach(memory,self.text,{label})
                for va,word in writes.items():self.assertEqual(struct.unpack_from('<I',active,va)[0],word)
                memory=bytearray(active);struct.pack_into('<I',memory,0xc3fe0,0)
                restored=tool.apply_pnach(memory,self.text,{label})
                for va,word in off.items():self.assertEqual(struct.unpack_from('<I',restored,va)[0],word)

    def test_unchecked_project_stays_original(self):
        memory=bytearray(self.original);struct.pack_into('<I',memory,0xc3fe0,1)
        result=tool.apply_pnach(memory,self.text,set())
        for body in tool.cases(PROFILES).values():
            for va in body:self.assertEqual(result[va:va+4],self.original[va:va+4])

    def test_controller_code_unlabelled(self):
        core=self.text.split('[',1)[0]
        self.assertIn('patch=1,EE,0017C738,word,0C030C00',core)

    def test_unknown_source_rejected(self):
        with patch.object(tool,'original_memory',return_value=self.original):
            with self.assertRaisesRegex(ValueError,'unrecognized'):
                tool.render(b'fixture',PROFILES,self.source.replace('28410001','28410003'))


if __name__=='__main__':unittest.main()
