import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib','src')]
from localization.text import SINGLE_TAB_POLICY,single_tab_parts,protected_tokens,validate_target,MappedEncoder
from source_interpretation import control_policy
class SingleTABTests(unittest.TestCase):
 def test_parts(self):self.assertEqual(single_tab_parts('a\tb'),['a','b'])
 def test_terminal_tab(self):self.assertEqual(single_tab_parts('a\t'),['a',''])
 def test_missing_tab_rejected(self):
  with self.assertRaises(ValueError):single_tab_parts('a')
 def test_repeated_tab_rejected(self):
  with self.assertRaises(ValueError):single_tab_parts('a\tb\t')
 def test_empty_body_rejected(self):
  with self.assertRaises(ValueError):single_tab_parts('\t')
 def test_other_controls_rejected(self):
  for text in ('a\t\n','a\t\r','a\t\0','a\t\x01'):
   with self.subTest(text=repr(text)),self.assertRaises(ValueError):single_tab_parts(text)
 def test_original_numbers_preserved(self):validate_target('atk+1\tdef+3','attack+1\tdefense+3',control_policy=SINGLE_TAB_POLICY)
 def test_numbers_crossing_boundary_rejected(self):
  with self.assertRaisesRegex(ValueError,'TAB boundary'):validate_target('atk+1\tdef+3','attack\t1 defense+3',control_policy=SINGLE_TAB_POLICY)
 def test_numbers_changed_rejected(self):
  with self.assertRaises(ValueError):validate_target('atk+1\tdef+3','attack+2\tdefense+3',control_policy=SINGLE_TAB_POLICY)
 def test_tokens_order_preserved(self):self.assertEqual(protected_tokens('a$n\t%d',control_policy=SINGLE_TAB_POLICY),['$n','\t','%d'])
 def test_tokens_crossing_boundary_rejected(self):
  with self.assertRaises(ValueError):validate_target('a$n\tb','a\tb$n',control_policy=SINGLE_TAB_POLICY)
 def test_default_validation_still_rejects(self):
  with self.assertRaises(ValueError):validate_target('a\tb','c\td')
 def test_explicit_encoder_byte09(self):self.assertEqual(MappedEncoder([]).encode('a\tb',control_policy=SINGLE_TAB_POLICY),b'a\x09b')
 def test_default_encoder_still_rejects(self):
  with self.assertRaises(ValueError):MappedEncoder([]).encode('a\tb')
 def test_unbound_entry_rejected(self):
  with self.assertRaises(ValueError):control_policy(dict(source_control_policy=SINGLE_TAB_POLICY,source_sha256='x'))
