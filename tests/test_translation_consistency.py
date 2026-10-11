from pathlib import Path
import copy,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from audit_translation_consistency import audit
from validate_translation_batch import GlossaryTerms
from extract_strings import field

class ConsistencyTests(unittest.TestCase):
    def setUp(self):
        row=field('id','칼린츠'.encode('cp949'),0)
        self.c=dict(source_locale='ko-KR',resources=[dict(entries=[row])])
        self.b=dict(schema=1,locale='zh-CN',entries=[dict(id='id',source_sha256=row['source_sha256'],target='卡林兹',status='draft')])
        self.t=GlossaryTerms();self.t.append(('칼린츠','卡林兹'))
    def run_audit(self,**kw):return audit(self.c,[('batch',self.b)],self.t,**kw)
    def test_success_does_not_assert_proofreading(self):
        x=self.run_audit();self.assertEqual(x['summary']['lexical_issues'],0)
        self.assertFalse(x['summary']['human_proofreading_complete'])
    def test_source_hash_rejected(self):
        self.b['entries'][0]['source_sha256']='0'*64
        with self.assertRaises(ValueError):self.run_audit()
    def test_glossary_missing_is_reported(self):
        self.b['entries'][0]['target']='错误名字'
        x=self.run_audit();self.assertTrue(any(i['kind']=='term-mismatch' for i in x['issues']))
    def test_alias_preserves_identity(self):
        self.c['resources'][0]['entries'][0]['source_aliases']=['legacy'];self.b['entries'][0]['id']='legacy'
        self.assertEqual(self.run_audit()['summary']['translation_fields'],1)
    def test_cross_batch_duplicate_rejected(self):
        with self.assertRaises(ValueError):audit(self.c,[('a',self.b),('b',self.b)],self.t)
    def test_script_filter_opt_in(self):
        self.b['entries'][0]['target']='卡林兹かな'
        self.assertFalse(any(i['kind']=='source-script-in-target' for i in self.run_audit()['issues']))
        self.assertTrue(any(i['kind']=='source-script-in-target' for i in self.run_audit(unexpected_script_pattern='[ぁ-ヿ]')['issues']))
    def test_variant_not_automatically_unified(self):
        row=copy.deepcopy(self.c['resources'][0]['entries'][0]);row['id']='id2';self.c['resources'][0]['entries'].append(row)
        target=copy.deepcopy(self.b['entries'][0]);target.update(id='id2',target='卡林兹大人');self.b['entries'].append(target)
        x=self.run_audit();self.assertEqual(x['summary']['same_source_target_variants'],1)
        self.assertFalse(x['context_variants'][0]['linked_group'])
    def test_character_pronoun_profile_binds_canonical_terms(self):
        import json
        from validate_translation_batch import glossary_terms
        p=json.loads((ROOT/'locales/zh-CN/character-reference.json').read_text('utf8'))
        canonical=dict(glossary_terms(ROOT/'GLOSSARY.md'));seen=set()
        for row in p['characters']:
            self.assertIn(row['canonical_source'],canonical)
            self.assertNotIn(row['canonical_source'],seen);seen.add(row['canonical_source'])
            self.assertEqual(row['default_pronoun'],{'male':'他','female':'她'}[row['gender']])
        self.assertEqual(next(x for x in p['characters'] if x['canonical_source']=='칼린츠')['gender'],'male')
    def test_name_suffix_homophone_does_not_force_a_person_name(self):
        row=field('id','우리 남편보다 악취미네.'.encode('cp949'),0)
        self.c['resources'][0]['entries']=[row]
        self.b['entries'][0].update(source_sha256=row['source_sha256'],target='你比我丈夫还没品味。')
        self.t=GlossaryTerms();self.t.append(('미네','米奈'));self.t.exact_only.add('미네')
        self.assertEqual(self.run_audit()['summary']['lexical_issues'],0)
    def test_gift_reaction_batch_is_complete_and_keeps_independent_ids(self):
        import json
        b=json.loads((ROOT/'locales/zh-CN/gift-reactions-review-01.json').read_text('utf8'))
        self.assertEqual(len(b['entries']),747)
        self.assertEqual(len({e['id'] for e in b['entries']}),747)
        self.assertTrue(all(e['status']=='reviewed' and e['target'].strip() for e in b['entries']))
        self.assertTrue(all('.gft/' in e['id'] for e in b['entries']))
    def test_homophone_project_rule_is_registered(self):
        from validate_translation_batch import glossary_terms
        self.assertIn('미네',glossary_terms(ROOT/'GLOSSARY.md').exact_only)
