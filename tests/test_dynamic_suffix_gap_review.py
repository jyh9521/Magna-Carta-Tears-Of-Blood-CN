from pathlib import Path
import json,unittest
ROOT=Path(__file__).resolve().parents[1]
class DynamicSuffixReviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows=json.loads((ROOT/'locales/zh-CN/dynamic-suffix-gap-review-01.json').read_text('utf8'))['entries'];cls.p=json.loads((ROOT/'locales/zh-CN/proofreading/dynamic-suffix-decisions.json').read_text('utf8'));cls.by={(e['id'].split('/')[1],e['record_key']):e['target'] for e in cls.p['bindings']}
 def test_eight_reviewed_unique_source_bound(self):
  self.assertEqual(len(self.rows),8);self.assertEqual(len({x['id'] for x in self.rows}),8)
  self.assertEqual({e['id']:(e['source_sha256'],e['target']) for e in self.rows},{e['id']:(e['source_sha256'],e['target']) for e in self.p['bindings']})
  for x in self.rows:self.assertEqual(x['status'],'reviewed');self.assertRegex(x['source_sha256'],r'^[0-9a-f]{64}$')
 def test_duplicate_suffix_consistency(self):self.assertEqual(self.by['00001240.tui',219],self.by['00001240.tui',260])
 def test_canonical_affinity_no_gender_invention(self):
  for key in (7,8):self.assertIn('友好度',self.by['00002380.tui',key]);self.assertNotIn('好感度',self.by['00002380.tui',key])
  self.assertEqual('卡林兹'+self.by['00001240.tui',168],'卡林兹发来了通讯')
 def test_map_label_word_order(self):self.assertEqual('莱斯'+self.by['00002381.tui',4],'莱斯：是否前往？')
 def test_confidence_and_immutable_tokens(self):
  self.assertFalse(self.p['runtime_verified']);m=self.p['map_consumer'];self.assertEqual(m['key'],4);t={x['offset']:x for x in m['tokens']};self.assertEqual(t[428]['int'],4);self.assertEqual(t[430]['field'],'TextID');self.assertEqual(t[439]['field'],'TextID');self.assertEqual(t[455]['field'],'MapTextList');self.assertEqual(t[553]['field'],'NextNodeData');self.assertEqual(t[559]['field'],'TextData')
  for x in self.rows:self.assertTrue(x['target']);self.assertNotIn('—',x['target'])
if __name__=='__main__':unittest.main()
