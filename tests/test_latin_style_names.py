import json,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from audit_native_style import check_name_equality
class StyleByteEqualityTests(unittest.TestCase):
 def test_ascii_case_and_repeated_labels_preserved(self):self.assertEqual(check_name_equality([b'A',b'a',b'b'],[b'X',b'x',b'y'])['pairs'],3)
 def test_new_collision_rejected(self):
  with self.assertRaisesRegex(ValueError,'partition changed'):check_name_equality([b'a',b'b'],[b'x',b'X'])
 def test_original_equal_class_split_rejected(self):
  with self.assertRaisesRegex(ValueError,'partition changed'):check_name_equality([b'a',b'A'],[b'x',b'y'])
 def test_unicode_casefold_not_used(self):self.assertTrue(check_name_equality(['ß'.encode('utf8'),b'ss'],['ß'.encode('utf8'),b'ss'])['byte_case_equality_partition_preserved'])
 def test_invalid_inputs_rejected(self):
  for a,b in [([],[]),([b'a'],[]),([b'a'],['a']),([b'a'],[b'a\0'])]:
   with self.subTest(a=a,b=b),self.assertRaises(ValueError):check_name_equality(a,b)
class LatinStyleNames(unittest.TestCase):
 def rows(self):return json.loads((R/'locales/zh-CN/latin-style-names-review-01.json').read_text('utf8'))['entries']
 def profile(self):return json.loads((R/'locales/zh-CN/proofreading/style-name-consumers.json').read_text('utf8'))
 def test_ten_bound_reviewed_names(self):
  rows={x['id']:x for x in self.rows()};p=self.profile();self.assertEqual(len(rows),10);self.assertEqual(len(p['additional_latin_name_bindings']),10)
  for b in p['additional_latin_name_bindings']:self.assertEqual((rows[b['id']]['source_sha256'],rows[b['id']]['target']),(b['source_sha256'],b['target']));self.assertIsInstance(b['source_record_key'],int);self.assertEqual(b['field'],0);self.assertFalse(b['runtime_verified']);self.assertEqual(rows[b['id']]['reinsertion_policy'],'translate')
 def test_all249_name_targets_present(self):
  p=self.profile();self.assertEqual(len(p['all_name_bindings']),249);self.assertTrue(all(x['target'] is not None for x in p['all_name_bindings']));self.assertTrue(p['all_names_have_targets']);self.assertEqual(len(p['bindings']),246)
 def test_underscores_preserved_not_resource_renames(self):
  for b in self.profile()['additional_latin_name_bindings']:self.assertEqual(b['source'].count('_'),b['target'].count('_'))
 def test_abbreviations_and_unknown_identity_preserved(self):
  rows={x['id']:x['target'] for x in self.rows()};self.assertIn('S之眼',rows['SHIP/00000468.sgi/record-index/212/field/0']);self.assertIn('D渡鸦',rows['SHIP/00000468.sgi/record-index/214/field/0']);self.assertIn('S之心',rows['SHIP/00000468.sgi/record-index/216/field/0']);self.assertEqual(rows['SHIP/00000468.sgi/record-index/114/field/0'],'winmain的流派');self.assertEqual(rows['SHIP/00000468.sgi/record-index/215/field/0'],'召唤_第一阶段_罗蒂')
 def test_canonical_names_and_dash(self):
  rows={x['id']:x['target'] for x in self.rows()};self.assertIn('凯莉安',rows['SHIP/00000468.sgi/record-index/211/field/0']);self.assertIn('奥哈',rows['SHIP/00000468.sgi/record-index/213/field/0']);self.assertIn('阿米拉',rows['SHIP/00000468.sgi/record-index/208/field/0']);self.assertNotIn('—',''.join(rows.values()))
if __name__=='__main__':unittest.main()
