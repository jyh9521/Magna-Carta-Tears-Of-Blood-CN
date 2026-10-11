import json,re,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','src','lib')]
from localization.text import validate_target
from validate_translation_batch import glossary_terms
class LatinTailTests(unittest.TestCase):
 def data(self):
  batch=json.loads((ROOT/'locales/zh-CN/latin-tail-review-01.json').read_text('utf8'));review=json.loads((ROOT/'locales/zh-CN/proofreading/latin-tail-scope-decisions.json').read_text('utf8'));return batch,review
 def test_nine_targets_unique(self):
  b,r=self.data();self.assertEqual(len(b['entries']),9);self.assertEqual(len({e['id'] for e in b['entries']}),9)
 def test_ten_scope_decisions_unique(self):
  b,r=self.data();self.assertEqual(len(r['entries']),10);self.assertEqual(len({e['id'] for e in r['entries']}),10)
 def test_gibberish_retained_not_translated(self):
  b,r=self.data();d=next(e for e in r['entries'] if e['source']=='vbvb b');self.assertEqual(d['disposition'],'retain-literal-source');self.assertNotIn(d['id'],{e['id'] for e in b['entries']})
 def test_review_cannot_claim_visibility_or_import(self):
  b,r=self.data();self.assertTrue(all(e['runtime_visibility_verified'] is False and e['import_approved'] is False for e in r['entries']))
 def test_source_hashes_and_control_order(self):
  b,r=self.data();ix={e['id']:e for e in r['entries']}
  for e in b['entries']:
   self.assertEqual(e['source_sha256'],ix[e['id']]['source_sha256']);validate_target(ix[e['id']]['source'],e['target']);self.assertEqual(re.findall(r'\d+',ix[e['id']]['source']),re.findall(r'\d+',e['target']))
 def test_new_spelling_aliases_canonical(self):
  terms=dict(glossary_terms(ROOT/'GLOSSARY.md'));self.assertEqual({k:terms[k] for k in ('Sid','Orha1','Orha2','pparkjju','pparkjju2')},{'Sid':'希德币','Orha1':'奥尔哈1','Orha2':'奥尔哈2','pparkjju':'朴柱','pparkjju2':'朴柱2'})
 def test_reviewed_targets_no_dash_or_foreign_script(self):
  b,r=self.data();self.assertTrue(all(e['status']=='reviewed' and e['reinsertion_policy']=='translate' and not re.search('[가-힣—―]',e['target']) for e in b['entries']))
 def test_fixed_resource_categories(self):
  b,r=self.data();self.assertEqual(sum('.tui/' in e['id'] for e in b['entries']),1);self.assertEqual(sum('.gft/' in e['id'] for e in b['entries']),2);self.assertEqual(sum('.fds/' in e['id'] for e in b['entries']),6)
