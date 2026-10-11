from pathlib import Path
import json,unittest
ROOT=Path(__file__).resolve().parents[1]
class DynamicArrayGapReviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows=json.loads((ROOT/'locales/zh-CN/dynamic-array-gap-review-01.json').read_text('utf8'))['entries'];cls.p=json.loads((ROOT/'locales/zh-CN/proofreading/dynamic-array-consumers.json').read_text('utf8'));cls.by={(e['id'].split('/')[1],e['physical_index']):e['target'] for e in cls.p['bindings']}
 def test_nine_reviewed_bound(self):
  self.assertEqual(len(self.rows),9);self.assertEqual(len({e['id'] for e in self.rows}),9)
  for e in self.rows:self.assertEqual(e['status'],'reviewed');self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$')
 def test_profile_matches_source_and_target(self):self.assertEqual({e['id']:(e['source_sha256'],e['target']) for e in self.rows},{e['id']:(e['source_sha256'],e['target']) for e in self.p['bindings']})
 def test_style_sentence_order(self):
  self.assertEqual('卡林兹'+self.by['00001255.tui',22]+'血泪'+self.by['00001255.tui',28],'卡林兹获得流派[血泪]！')
 def test_stat_predicate_precedes_signed_number(self):
  for particle in (35,36):
   for amount in ('0','5','-5','9999'):
    full='卡林兹'+self.by['00001255.tui',29]+'力量'+self.by['00001255.tui',particle]+amount+self.by['00001255.tui',31];self.assertEqual(full,'卡林兹的力量增加了'+amount)
 def test_recipient_label_not_wrong_subject(self):self.assertEqual('卡林兹'+self.by['00001240.tui',67]+'[治疗药]'+'赠送这件道具吗？','卡林兹（收礼者）：[治疗药]赠送这件道具吗？')
 def test_no_global_empty_target_or_runtime_claim(self):
  self.assertFalse(self.p['runtime_verified'])
  for e in self.rows:self.assertTrue(e['target'] or e.get('empty_display_suffix'));self.assertNotIn('—',e['target']);self.assertNotIn('\0',e['target'])
if __name__=='__main__':unittest.main()
