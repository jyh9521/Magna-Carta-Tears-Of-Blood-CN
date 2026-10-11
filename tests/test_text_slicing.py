from pathlib import Path
import json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'src'),str(ROOT/'lib')]
from audit_text_slicing import scalar,signed
from import_audited_fields import require_write_policy
class Image:
 def __init__(self,words):self.blob=struct.pack('<'+'I'*len(words),*words)
 def to_offset(self,va):
  off=va-0x1000
  if not 0<=off<=len(self.blob)-4:raise ValueError('outside code fixture')
  return off
class TextSlicingTests(unittest.TestCase):
 def run_scalar(self,words,regs=None,memory=None,limit=100):return scalar(Image(words),0x1000,0x1000+4*len(words),regs or {},memory or {},limit)
 def test_zero_register_is_immutable(self):self.assertEqual(self.run_scalar([0x24000007])['registers'][0],0)
 def test_signed_addiu_wraps_low32(self):self.assertEqual(self.run_scalar([0x2402ffff])['registers'][2],0xffffffff)
 def test_branch_delay_executes_before_taken_target(self):self.assertEqual(self.run_scalar([0x10000002,0x24020003,0x24020009])['registers'][2],3)
 def test_non_taken_branch_runs_delay_then_fallthrough(self):self.assertEqual(self.run_scalar([0x14000002,0x24020003,0x24420004])['registers'][2],7)
 def test_signed_byte_high_bit_through_64bit_shift(self):
  words=[0x80220000,(2<<16)|(2<<11)|(24<<6)|0x3c,(2<<16)|(2<<11)|(24<<6)|0x3f,0x30420080]
  self.assertEqual(self.run_scalar(words,{1:0x2000},{0x2000:0xb0})['registers'][2],128);self.assertEqual(self.run_scalar(words,{1:0x2000},{0x2000:65})['registers'][2],0)
 def test_missing_fixture_memory_rejected(self):
  with self.assertRaisesRegex(ValueError,'outside supplied'):self.run_scalar([0x80220000],{1:0x2000},{})
 def test_unknown_instruction_rejected(self):
  with self.assertRaisesRegex(ValueError,'unsupported'):self.run_scalar([0xfc000000])
 def test_loop_budget_rejected(self):
  with self.assertRaisesRegex(ValueError,'bound exceeded'):self.run_scalar([0x1000ffff,0],limit=10)
 def test_bgez_uses_signed32_and_delay(self):
  words=[0x04410002,0x24030001,0x24030008]
  self.assertEqual(self.run_scalar(words,{2:0xffffffff})['registers'][3],8);self.assertEqual(self.run_scalar(words,{2:0})['registers'][3],1)
 def test_cost_prefix_satisfies_both_character_and_byte_boundaries(self):
  p=json.loads((ROOT/'locales/zh-CN/dynamic-text-constraints.json').read_text('utf8'));e=next(e for e in p['fields'] if e['kind']=='fixed-slice-insert');target=e['target'];self.assertEqual(target[:5],'消灾需花费');self.assertEqual(target[5],' ')
  encode=lambda s:b''.join(bytes([0xb0,0xa1]) if ord(c)>127 else c.encode('ascii') for c in s)
  self.assertEqual(len(encode(target[:6])),11);self.assertEqual(e['character_boundary'],5);self.assertEqual(e['byte_boundary'],11)
 def test_repaired_currency_suffixes_do_not_prepend_cost_verb(self):
  es=json.loads((ROOT/'locales/zh-CN/dynamic-text-constraints.json').read_text('utf8'))['fields'];suffix=[e['target'] for e in es if e['kind']=='amount-prefix'];self.assertEqual(set(suffix),{'希德币。是否占卜？','希德币。是否购买？'})
 def test_scalar_proof_does_not_authorize_incomplete_consumer_binding(self):
  es=json.loads((ROOT/'locales/zh-CN/interface-review-02.json').read_text('utf8'))['entries'];p=json.loads((ROOT/'locales/zh-CN/dynamic-text-constraints.json').read_text('utf8'));self.assertTrue(p['full_consumer_binding_verified']);self.assertFalse(p['runtime_verified'])
  for q in p['fields']:
   e=next(e for e in es if e['id']==q['id']);self.assertEqual(e['target'],q['target']);self.assertEqual(e['source_sha256'],q['source_sha256'])
   require_write_policy(e)
   held=dict(e,reinsertion_policy='pending-role-review')
   with self.assertRaisesRegex(ValueError,'reinsertion policy'):require_write_policy(held)
 def test_gym_cost_insertion_keeps_three_character_prefix(self):
  es=json.loads((ROOT/'locales/zh-CN/dynamic-text-constraints.json').read_text('utf8'))['fields'];e=next(e for e in es if e['kind']=='character-slice-insert')
  self.assertEqual(e['character_boundary'],3);self.assertIsNone(e['byte_boundary']);target=e['target'];self.assertEqual(target[:3],'修炼需');self.assertEqual(target[3:],'希德币。是否修炼？')
  for amount in ('0','1','100','99999'):
   self.assertEqual(target[:3]+' '+amount+target[3:],'修炼需 '+amount+'希德币。是否修炼？')
if __name__=='__main__':unittest.main()
