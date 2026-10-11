import json,unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/p) for p in ('tools','src')]
from localization.text import protected_tokens
class LatinDialogueTests(unittest.TestCase):
 def rows(self):return json.loads((R/'locales/zh-CN/latin-dialogue-gap-review-01.json').read_text('utf8'))['entries']
 def bindings(self):return json.loads((R/'locales/zh-CN/proofreading/latin-dialogue-consumers.json').read_text('utf8'))['bindings']
 def test_exact14_unique_reviewed_fields(self):
  rows=self.rows();self.assertEqual(len(rows),14);self.assertEqual(len({x['id'] for x in rows}),14);self.assertTrue(all(x['status']=='reviewed' and x['reinsertion_policy']=='translate' for x in rows))
 def test_control_sequences_preserved(self):
  for b in self.bindings():self.assertEqual(protected_tokens(b['source']),protected_tokens(b['target']))
 def test_exact_native_binding_targets(self):
  rows={r['id']:r for r in self.rows()}
  for b in self.bindings():self.assertEqual((rows[b['id']]['source_sha256'],rows[b['id']]['target']),(b['source_sha256'],b['target']));self.assertIsInstance(b['native_record_key'],int);self.assertFalse(b['specific_event_execution_verified'])
 def test_test_messages_remain_tests_not_story(self):
  rows={r['id']:r for r in self.rows()};self.assertEqual(rows['SHIP/00002271.fpb/seq/0']['target'],'这是测试场景。首先，$n测试角色指令。');self.assertEqual(rows['SHIP/00002271.fpb/seq/1']['target'].count('$n'),2);self.assertIn('被中断的动画',rows['SHIP/00002271.fpb/seq/1']['target'])
 def test_names_and_dash_not_invented(self):
  for r in self.rows():self.assertNotIn('—',r['target']);self.assertNotIn('卡琳兹',r['target']);self.assertNotIn('莉丝',r['target'])
if __name__=='__main__':unittest.main()
