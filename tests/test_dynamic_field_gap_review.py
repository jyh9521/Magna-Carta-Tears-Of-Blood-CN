from pathlib import Path
import json,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
class DynamicFieldGapTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows=json.loads((ROOT/'locales/zh-CN/dynamic-field-gap-review-01.json').read_text('utf8'))['entries'];cls.profile=json.loads((ROOT/'locales/zh-CN/proofreading/dynamic-field-consumers.json').read_text('utf8'))
 def test_six_source_bound_reviewed(self):
  self.assertEqual(len(self.rows),6)
  for e in self.rows:self.assertEqual(e['status'],'reviewed');self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$')
 def test_profile_exact_current_values(self):
  self.assertEqual({e['id']:(e['source_sha256'],e['target']) for e in self.rows},{e['id']:(e['source_sha256'],e['target']) for e in self.profile['bindings']})
 def test_native_record_key_not_ordinal(self):
  self.assertEqual(self.profile['native_lookup'],'0x3127a0')
  for e in self.profile['bindings']:self.assertNotEqual(e['native_key'],e['physical_index'])
 def test_affinity_composition_keeps_name_and_relation(self):
  bindings=[e for e in self.profile['bindings'] if e['native_key'] in (92,93,208)]
  self.assertEqual(len(bindings),3)
  for e in bindings:self.assertEqual(e['composition'],'CharName + MainText');self.assertTrue(e['target'].startswith('的友好度'));self.assertEqual(e['sample_result'],'卡琳兹'+e['target'])
 def test_brackets_slash_spaces_are_component_text(self):
  bykey={e['native_key']:e for e in self.profile['bindings']};self.assertEqual(bykey[300]['target'],'最高伤害记录 [ ');self.assertEqual(bykey[301]['target'],' ] / 记录刷新次数 [ ');self.assertEqual(bykey[303]['target'],'认证编号 [ ')
  for k in (300,301,303):self.assertEqual(bykey[k]['composition'],'SetText(MainText) independent UI component')
 def test_static_binding_not_game_execution_claim(self):
  self.assertFalse(self.profile['runtime_verified'])
  for e in self.profile['bindings']:self.assertFalse(e['runtime_verified']);self.assertRegex(e['consumer_serial_sha256'],r'^[a-f0-9]{64}$');self.assertNotIn('—',e['target'])
if __name__=='__main__':unittest.main()
