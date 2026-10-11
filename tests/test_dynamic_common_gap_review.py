from pathlib import Path
import unittest,json
ROOT=Path(__file__).resolve().parents[1]
class DynamicCommonDecisionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows=json.loads((ROOT/'locales/zh-CN/dynamic-common-gap-review-01.json').read_text('utf8'))['entries'];cls.p=json.loads((ROOT/'locales/zh-CN/proofreading/dynamic-common-decisions.json').read_text('utf8'));cls.by={x['record_key']:x['target'] for x in cls.p['bindings']}
 def test_source_bound_review_decisions(self):
  self.assertEqual(len(self.rows),8);self.assertEqual({x['id']:(x['source_sha256'],x['target']) for x in self.rows},{x['id']:(x['source_sha256'],x['target']) for x in self.p['bindings']})
  for x in self.rows:self.assertEqual(x['status'],'reviewed')
 def test_candidate_money_composition(self):
  for amount in ('5','100','-5'):self.assertEqual(self.by[13]+amount+self.by[14],'金钱减少了'+amount+'希德币')
 def test_candidate_party_roles(self):
  self.assertEqual('卡林兹'+self.by[25]+'玛雅'+self.by[27],'卡林兹队伍：玛雅加入了队伍');self.assertEqual('卡林兹'+self.by[26]+'玛雅'+self.by[28],'卡林兹队伍：玛雅被移出队伍');self.assertEqual('卡林兹'+self.by[24],'卡林兹队伍已设为当前队伍')
 def test_third_particle_consistent_with_existing_decision(self):
  old=json.loads((ROOT/'locales/zh-CN/proofreading/dynamic-array-consumers.json').read_text('utf8'))['bindings'];pairs={x['physical_index']:x['target'] for x in old if '/00001255.tui/' in x['id']};self.assertEqual(self.by[31],pairs[35]);self.assertEqual(self.by[31],pairs[36]);self.assertEqual('卡林兹的力量'+self.by[31]+'5'+pairs[31],'卡林兹的力量增加了5')
 def test_no_consumer_or_runtime_claim(self):
  self.assertFalse(self.p['runtime_verified']);self.assertFalse(self.p['consumer_order_verified'])
  for x in self.rows:self.assertTrue(x['target']);self.assertNotIn('—',x['target'])
if __name__=='__main__':unittest.main()
