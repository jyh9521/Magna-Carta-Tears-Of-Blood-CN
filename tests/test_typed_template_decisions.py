from pathlib import Path
import json,unittest
ROOT=Path(__file__).resolve().parents[1]
class TypedTemplateTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=json.loads((ROOT/'locales/zh-CN/proofreading/typed-template-import-decisions.json').read_text('utf8'));cls.rows=cls.p['bindings'];cls.batch={x['id']:x for x in json.loads((ROOT/'locales/zh-CN/interface-review-02.json').read_text('utf8'))['entries']}
 def test_three_unique_bindings(self):self.assertEqual(len(self.rows),3);self.assertEqual(len({q['id'] for q in self.rows}),3)
 def test_language_source_targets_preserved(self):
  for q in self.rows:
   e=self.batch[q['id']];self.assertEqual((e['source_sha256'],e['target']),(q['source_sha256'],q['target']));self.assertEqual(e['status'],'reviewed');self.assertEqual(e['reinsertion_policy'],'translate')
 def test_numeric_keys_not_ordinals(self):
  self.assertEqual([(q['record_key'],q['physical_index']) for q in self.rows],[(30,23),(31,24),(1,1)])
  for q in self.rows:self.assertTrue(q['lookup_result']['found']);self.assertEqual(q['lookup_result']['index'],q['physical_index'])
 def test_no_runtime_or_marker_replacement_claim(self):
  self.assertFalse(self.p['runtime_verified'])
  for q in self.rows:self.assertFalse(q['runtime_execution_verified']);self.assertFalse(q['placeholder_runtime_semantics_verified']);self.assertTrue(q['bank_storage_binding_verified'])
 def test_tilde_exact_count_and_no_dash(self):
  for q in self.rows:self.assertEqual(q['source'].count('~'),q['target'].count('~'));self.assertNotIn('—',q['target'])
 def test_typed_bank_slot_and_loader(self):
  for q in self.rows:self.assertEqual(q['fixed_slot_bytes'],256);self.assertEqual(q['native_loader']['record_stride'],28);self.assertIn(q['resource'].split('/')[-1],q['native_loader']['path']);self.assertTrue(q['native_loader']['instructions'])
 def test_pilot_currency_is_canonical(self):self.assertEqual(self.rows[-1]['target'],'将消耗希德币。确定前往吗？')
if __name__=='__main__':unittest.main()
