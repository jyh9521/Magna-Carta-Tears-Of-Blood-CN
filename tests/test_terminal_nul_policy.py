import sys,struct,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib','src')]
from localization.text import TERMINAL_NUL_POLICY,terminal_nul_body,protected_tokens,validate_target,MappedEncoder,rewrite_fpb
from translate.fpb import build_fpb,parse_fpb_raw
from audit_native_playbook import native_records
class TerminalNULTests(unittest.TestCase):
 def test_body_strips_only_terminal_padding(self):self.assertEqual(terminal_nul_body('body'+ '\0'*6),'body')
 def test_nul_free_target_body(self):self.assertEqual(terminal_nul_body('body'),'body')
 def test_empty_or_control_body_rejected(self):
  for s in ('','\0'*6,'bo\0dy\0','body\n\0','body\t\0'):
   with self.subTest(s=repr(s)),self.assertRaises(ValueError):terminal_nul_body(s)
 def test_default_target_still_rejects(self):
  with self.assertRaises(ValueError):validate_target('body\0','text\0')
 def test_padded_source_nul_free_target(self):validate_target('body'+ '\0'*6,'text',control_policy=TERMINAL_NUL_POLICY)
 def test_target_padding_is_rejected(self):
  with self.assertRaises(ValueError):validate_target('body\0','text\0',control_policy=TERMINAL_NUL_POLICY)
 def test_source_unknown_markup_rejected(self):
  with self.assertRaises(ValueError):protected_tokens('body%\0',control_policy=TERMINAL_NUL_POLICY)
 def test_protected_tokens_retained(self):self.assertEqual(protected_tokens('body$n%d\0',control_policy=TERMINAL_NUL_POLICY),['$n','%d'])
 def test_target_numbers_unchanged(self):
  with self.assertRaises(ValueError):validate_target('body2\0','text3',control_policy=TERMINAL_NUL_POLICY)
 def fixture(self,padding=6):return build_fpb(struct.pack('<4I',1,0,0,0),[],b'body'+bytes(padding))
 def test_native_header_length_preserves_six_zeros(self):
  new,report=rewrite_fpb(self.fixture(),{0:'longer text'},MappedEncoder([]),source_control_policies={0:TERMINAL_NUL_POLICY});rows,pool=native_records(new);self.assertEqual(rows,[(0,0,17)]);self.assertEqual(pool,b'longer text'+bytes(6));self.assertEqual(report[0]['new_length'],17)
 def test_default_fpb_behavior_unchanged(self):
  # Default grammar does not bind storage padding; strict source policy required.
  # The original default API remains compatible, so no new automatic padding handling.
  new,report=rewrite_fpb(self.fixture(),{0:'text'},MappedEncoder([]));self.assertEqual(parse_fpb_raw(new)[2],b'text')
 def test_explicit_fpb_requires_original_padding(self):
  with self.assertRaisesRegex(ValueError,'requires original padding'):rewrite_fpb(self.fixture(0),{0:'text'},MappedEncoder([]),source_control_policies={0:TERMINAL_NUL_POLICY})
 def test_nonselected_pool_bytes_preserved(self):
  raw=build_fpb(struct.pack('<4I',2,0,0,0),[(1,10,4)],b'body'+bytes(6)+b'KEEP');new,_=rewrite_fpb(raw,{0:'text'},MappedEncoder([]),source_control_policies={0:TERMINAL_NUL_POLICY});rows,pool=native_records(new);self.assertEqual(pool[rows[1][1]:],b'KEEP')

 def test_unbound_scope_nul_still_deferred(self):
  from prepare_translation_scope import disposition
  self.assertEqual(disposition(dict(resource='SHIP/sample.fpb'),dict(references={'ko-KR':'한글\0'},decode='strict',controls='recognized')),('deferred-control','protected-structure'))
 def test_forged_scope_nul_policy_rejected(self):
  from prepare_translation_scope import disposition
  with self.assertRaises(ValueError):disposition(dict(resource='SHIP/sample.fpb'),dict(references={'ko-KR':'한글\0'},decode='strict',controls='recognized',source_control_policy=TERMINAL_NUL_POLICY))
