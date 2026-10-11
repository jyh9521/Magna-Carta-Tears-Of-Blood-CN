from pathlib import Path
import unittest,json
R=Path(__file__).resolve().parents[1]
class AmountConsumerTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.p=json.loads((R/'locales/zh-CN/proofreading/amount-consumers.json').read_text('utf8'));cls.c=json.loads((R/'locales/zh-CN/dynamic-text-constraints.json').read_text('utf8'));cls.rows=cls.p['bindings']
 def test_four_complete_static_not_runtime(self):
  self.assertEqual(len(self.rows),4);self.assertTrue(self.p['static_consumer_binding_verified']);self.assertFalse(self.p['runtime_verified'])
  for x in self.rows:self.assertTrue(x['static_consumer_binding_verified']);self.assertFalse(x['runtime_verified'])
 def test_policy_matches_bound_source_target(self):
  self.assertEqual({x['id']:(x['source_sha256'],x['target']) for x in self.rows},{x['id']:(x['source_sha256'],x['target']) for x in self.c['fields']})
  for x in self.c['fields']:self.assertEqual(x['write_policy'],'translate');self.assertTrue(x['consumer_binding_complete'])
 def test_compiled_getters_search_keys_not_ordinals(self):
  for x in self.rows:
   g=x['key_getter']
   if g:
    self.assertIn(g['function'],('GetStoreMainText','GetDVMainText'));tokens=g['tokens'];self.assertIn('Key',{t.get('field') for t in tokens});self.assertIn('ID',{t.get('field') for t in tokens});self.assertIn('MainText',{t.get('field') for t in tokens});self.assertIn(['EqualEqual_IntInt'],[t.get('symbols') for t in tokens])
 def test_store_price_suffix_actual_tokens(self):
  x=next(x for x in self.rows if '/00001239.tui/' in x['id']);t=x['consumers'][0]['tokens'];self.assertIn('CurPrice',{z.get('field') for z in t});self.assertIn(['GetStoreMainText'],[z.get('symbols') for z in t]);self.assertIn(7,{z.get('int') for z in t})
 def test_exorcism_both_original_slice_paths(self):
  x=next(x for x in self.rows if x['kind']=='fixed-slice-insert');t=[t for q in x['consumers'] for t in q['tokens']];self.assertTrue({5,11}<={z.get('int') for z in t});self.assertTrue({'Left','Mid','LeftA','MidA'}<={s for z in t for s in z.get('symbols',[])})
 def test_gym_native_key_and_matching_out_index(self):
  x=next(x for x in self.rows if x['kind']=='character-slice-insert');self.assertEqual(len(x['consumers']),2)
  for c in x['consumers']:
   t=c['tokens'];self.assertIn(['GetGymTextDataIndex'],[z.get('symbols') for z in t]);self.assertIn('Index',{z.get('field') for z in t});self.assertIn('GymTextList',{z.get('field') for z in t});self.assertIn(17,{z.get('int') for z in t});self.assertIn(3,{z.get('int') for z in t})
if __name__=='__main__':unittest.main()
