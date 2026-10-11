from pathlib import Path
import json,copy,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from validate_context_variant_review import validate
class ContextVariantReviewTests(unittest.TestCase):
 def fixture(self):
  c=dict(source_locale='ko-KR',resources=[dict(entries=[dict(id='a',source_sha256='1',references={'ko-KR':'왜?'}),dict(id='b',source_sha256='2',references={'ko-KR':'왜?'})])]);b=[dict(locale='fixture',entries=[dict(id='a',source_sha256='1',target='Why?',status='reviewed'),dict(id='b',source_sha256='2',target='What?',status='reviewed')])];r=dict(schema=1,locale='fixture',reviewed_groups=1,groups=[dict(source='왜?',review_status='reviewed',rationale='Different previous sentences.',linked_group=False,decision='retain-context-variant',occurrences=[dict(id=x['id'],source_sha256=x['source_sha256'],target=x['target'],context=[]) for x in b[0]['entries']])]);return c,b,r
 def test_reviewed_variants_do_not_claim_runtime_or_full_scope(self):
  x=validate(*self.fixture());self.assertTrue(x['existing_variant_review_complete']);self.assertFalse(x['consumer_linkage_verified']);self.assertFalse(x['full_game_scope_complete'])
 def test_changed_target_requires_re_review(self):
  c,b,r=self.fixture();b[0]['entries'][0]['target']='Changed'
  with self.assertRaisesRegex(ValueError,'drift'):validate(c,b,r)
 def test_missing_occurrence_fails(self):
  c,b,r=self.fixture();r['groups'][0]['occurrences'].pop()
  with self.assertRaisesRegex(ValueError,'coverage'):validate(c,b,r)
 def test_unreviewed_variant_fails(self):
  c,b,r=self.fixture();r['groups']=[];r['reviewed_groups']=0
  with self.assertRaisesRegex(ValueError,'unreviewed'):validate(c,b,r)
 def test_editorial_review_cannot_assert_resource_linkage(self):
  c,b,r=self.fixture();r['groups'][0]['linked_group']=True
  with self.assertRaisesRegex(ValueError,'linkage'):validate(c,b,r)
 def test_claimed_normalization_requires_one_target(self):
  c,b,r=self.fixture();r['groups'][0]['decision']='normalize-target'
  with self.assertRaisesRegex(ValueError,'differ'):validate(c,b,r)
 def test_changed_source_evidence_fails(self):
  c,b,r=self.fixture();r['groups'][0]['occurrences'][0]['source_sha256']='wrong'
  with self.assertRaisesRegex(ValueError,'binding'):validate(c,b,r)
 def test_project_context_decisions_cover56_original_groups(self):
  r=json.loads((ROOT/'locales/zh-CN/proofreading/context-variants.json').read_text('utf8'));self.assertEqual(r['reviewed_groups'],56);self.assertEqual(sum(g['decision']=='normalize-target' for g in r['groups']),4);self.assertEqual(sum(g['decision']=='retain-context-variant' for g in r['groups']),52);self.assertTrue(all(g['linked_group'] is False for g in r['groups']))
if __name__=='__main__':unittest.main()
