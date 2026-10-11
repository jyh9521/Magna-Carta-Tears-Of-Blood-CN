import copy,json,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/p) for p in ('tools','src')]
from prepare_translation_scope import freeze
from localization.text import protected_tokens
class ExplicitScopeReviews(unittest.TestCase):
 def fixture(self):
  e=dict(id='a',source_sha256='fieldhash',source_bytes=1,offset=4,decode='strict',controls='recognized',semantic='dialogue-window',references={'ko-KR':'N'})
  c=dict(resources=[dict(resource='SHIP/a.fpb',sha256='resourcehash',entries=[e])]);d=dict(id='a',resource='SHIP/a.fpb',resource_sha256='resourcehash',source_sha256='fieldhash',source_bytes=1,offset=4,source='N',disposition='retain-literal-source',reason='Keep exact source without assigning control role.',runtime_visibility_verified=False,import_approved=False)
  return c,dict(schema=1,entries=[d])
 def test_default_api_unchanged(self):
  c,p=self.fixture();rows,s=freeze(c,[]);self.assertEqual(rows[0]['disposition'],'review-latin');self.assertEqual(s['explicit_linguistic_reviews'],0)
 def test_retention_not_runtime_or_iso_approval(self):
  c,p=self.fixture();rows,s=freeze(c,[],[p]);self.assertTrue(rows[0]['source_retention_required']);self.assertFalse(rows[0]['consumer_role_verified']);self.assertFalse(rows[0]['import_approved']);self.assertFalse(s['full_iso_ready']);self.assertFalse(s['coverage_review_complete'])
 def test_every_source_binding_rejected_on_mismatch(self):
  for k in ('resource','resource_sha256','source_sha256','offset','source_bytes','source'):
   c,p=self.fixture();p['entries'][0][k]='wrong'
   with self.subTest(k=k),self.assertRaises(ValueError):freeze(c,[],[p])
 def test_duplicate_review_rejected(self):
  c,p=self.fixture()
  with self.assertRaises(ValueError):freeze(c,[],[p,p])
 def test_unknown_identity_rejected(self):
  c,p=self.fixture();p['entries'][0]['id']='missing'
  with self.assertRaises(ValueError):freeze(c,[],[p])
 def test_quarantine_not_bypassed(self):
  for key,value in [('decode','failed'),('controls','quarantined'),('semantic','unresolved')]:
   c,p=self.fixture();c['resources'][0]['entries'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):freeze(c,[],[p])
 def test_runtime_or_import_claim_rejected(self):
  for k in ('runtime_visibility_verified','import_approved'):
   c,p=self.fixture();p['entries'][0][k]=True
   with self.subTest(k=k),self.assertRaises(ValueError):freeze(c,[],[p])
 def test_unsupported_disposition_rejected(self):
  c,p=self.fixture();p['entries'][0]['disposition']='exclude-unused'
  with self.assertRaises(ValueError):freeze(c,[],[p])
 def test_missing_reason_rejected(self):
  c,p=self.fixture();p['entries'][0]['reason']=' '
  with self.assertRaises(ValueError):freeze(c,[],[p])
 def test_retention_cannot_be_imported(self):
  c,p=self.fixture();b=dict(locale='zh-CN',entries=[dict(id='a',source_sha256='fieldhash',target='是',status='reviewed')])
  with self.assertRaises(ValueError):freeze(c,[b],[p])
 def test_reviewed_prose_still_requires_import_verification(self):
  c,p=self.fixture();p['entries'][0]['disposition']='translate-candidate';rows,s=freeze(c,[],[p]);self.assertFalse(rows[0]['import_approved']);self.assertEqual(s['unfilled_translation_candidates'],1)
class LatinProseReview(unittest.TestCase):
 def batch(self):return json.loads((R/'locales/zh-CN/latin-prose-gap-review-02.json').read_text('utf8'))['entries']
 def profile(self):return json.loads((R/'locales/zh-CN/proofreading/latin-prose-consumers.json').read_text('utf8'))['bindings']
 def test_22_unique_reviewed_fields(self):
  b=self.batch();self.assertEqual(len(b),22);self.assertEqual(len({e['id'] for e in b}),22);self.assertTrue(all(e['status']=='reviewed' and e['reinsertion_policy']=='translate' for e in b))
 def test_control_sequences_and_bound_targets(self):
  ix={e['id']:e for e in self.batch()}
  for e in self.profile():self.assertEqual(protected_tokens(e['source']),protected_tokens(e['target']));self.assertEqual((e['source_sha256'],e['target']),(ix[e['id']]['source_sha256'],ix[e['id']]['target']));self.assertFalse(e['specific_event_execution_verified'])
 def test_source_language_wish_and_quantity_not_rewritten(self):
  ix={e['id']:e['target'] for e in self.batch()};self.assertIn('韩文',ix['SHIP/00003922.cht/slot/15']);self.assertIn('100次',ix['SHIP/00003922.cht/slot/4']);self.assertNotIn('中文',ix['SHIP/00003922.cht/slot/15'])
 def test_incantation_matches_existing_hangul_reading(self):
  other=json.loads((R/'locales/zh-CN/story-gap-review-01.json').read_text('utf8'))['entries'];adj=next(e['target'] for e in other if e['id']=='SHIP/00007682.fpb/seq/1');new=next(e['target'] for e in self.batch() if e['id']=='SHIP/00007682.fpb/seq/0');self.assertEqual(new,adj[1:-1])
 def test_160_source_decisions_and_no_dash_or_invented_gender(self):
  p=json.loads((R/'locales/zh-CN/proofreading/source-scope-decisions.json').read_text('utf8'));self.assertEqual(len(p['entries']),160);self.assertEqual(sum(e['disposition']=='retain-literal-source' for e in p['entries']),138)
  for e in self.batch():self.assertNotIn('—',e['target']);self.assertNotIn('她',e['target'])
if __name__=='__main__':unittest.main()
