"""Source-bound remaining legacy review and composed-field write quarantine."""
from pathlib import Path
import json,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'src'),str(ROOT/'lib')]
from import_audited_fields import require_write_policy
from localization.text import protected_tokens
class RemainingBatchProofreadingTests(unittest.TestCase):
 def batch(self,name):return json.loads((ROOT/'locales/zh-CN'/name).read_text('utf8'))['entries']
 def entry(self,name,part):return next(x for x in self.batch(name) if part in x['id'])
 def test_all_four_remaining_legacy_batches_linguistically_reviewed(self):
  for name in ['character-commentary-review-01.json','interface-review-02.json','menu-review-01.json','opening-review-01.json']:
   self.assertTrue(all(e['status']=='reviewed' for e in self.batch(name)))
 def test_desert_crossing_does_not_invent_travel_mode(self):
  e=self.entry('character-commentary-review-01.json','/record/22/');self.assertNotIn('徒步',e['target']);self.assertIn('克里斯大帝',e['target']);self.assertEqual(protected_tokens(e['target']),['$n']*3)
 def test_speech_loss_not_language_loss_and_cherished_person_not_split(self):
  e=self.entry('character-commentary-review-01.json','/record/58/');self.assertIn('失去说话能力',e['target']);self.assertNotIn('失去语言',e['target']);self.assertIn('珍视的人',self.entry('character-commentary-review-01.json','/record/52/')['target'])
 def test_fortune_shop_and_current_equipment_labels(self):
  es=self.batch('interface-review-02.json');self.assertFalse(any('占卜馆' in e['target'] for e in es));self.assertEqual(self.entry('menu-review-01.json','/record/8/')['target'],'当前装备');self.assertEqual(self.entry('opening-review-01.json','/record/50/')['target'],'振动')
 def test_three_templates_have_typed_storage_decision_four_amounts_source_bound(self):
  profile=json.loads((ROOT/'locales/zh-CN/proofreading/typed-template-import-decisions.json').read_text('utf8'));self.assertEqual(len(profile['bindings']),3)
  for q in profile['bindings']:
   e=next(e for e in self.batch('interface-review-02.json') if e['id']==q['id']);self.assertEqual((e['source_sha256'],e['target']),(q['source_sha256'],q['target']));self.assertTrue(q['bank_storage_binding_verified']);self.assertFalse(q['runtime_execution_verified']);require_write_policy(e)
  p=json.loads((ROOT/'locales/zh-CN/proofreading/amount-consumers.json').read_text('utf8'));self.assertEqual(len(p['bindings']),4)
  for q in p['bindings']:
   e=next(e for e in self.batch('interface-review-02.json') if e['id']==q['id']);self.assertEqual((e['source_sha256'],e['target']),(q['source_sha256'],q['target']));self.assertTrue(q['static_consumer_binding_verified']);require_write_policy(e)
 def test_tilde_fragments_retain_marker_and_acquisition_verb(self):
  a=self.entry('interface-review-02.json','00001249.tui/record/30/');b=self.entry('interface-review-02.json','00001249.tui/record/31/');self.assertEqual(a['target'],'~的流派');self.assertEqual(b['target'],'获得了~');self.assertIn('~',a['target']);self.assertIn('~',b['target'])
 def test_ija_project_name_unified_without_source_identifier_merge(self):
  a=self.entry('interface-review-02.json','00002792.tui/record/42/');self.assertEqual(a['target'],'伊夏');s=(ROOT/'GLOSSARY.md').read_text('utf8');self.assertIn('| 이쟈 | 伊夏 |',s);self.assertIn('身份关联为高置信推定',s)
 def test_opening_character_alias_and_card_fragments_preserved(self):
  a=self.entry('opening-review-01.json','00000460.cha/slot/0');self.assertEqual(a['source_sha256'],'44af1a401b28f2ea3c962306fdb2e074d7be32815498585e7c86f080f3ef6540');self.assertEqual(a['target'],'卡林兹')
  es=self.batch('opening-review-01.json');s=''.join(next(e['target'] for e in es if ('/record/'+str(n)+'/') in e['id']) for n in [96,166,165]);self.assertEqual(s,'正在检查插槽1中的记忆卡(PS2)。请勿关闭电源，也勿拔出记忆卡(PS2)。')
if __name__=='__main__':unittest.main()
