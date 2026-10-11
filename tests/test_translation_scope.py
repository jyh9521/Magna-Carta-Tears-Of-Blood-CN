import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from prepare_translation_scope import disposition,freeze


def fixture(identity='a',text='칼린츠',**kwargs):
    return dict(id=identity,source_sha256='hash',source_bytes=6,offset=12,decode='strict',controls='recognized',
                semantic='name-or-description-runtime-unverified',references={'ko-KR':text},**kwargs)


class TranslationScopeTests(unittest.TestCase):
    def setUp(self):self.resource=dict(resource='SHIP/a.cha',sha256='resource')
    def test_name_is_candidate_not_visibility(self):self.assertEqual(disposition(self.resource,fixture())[0],'translate-candidate')
    def test_empty(self):self.assertEqual(disposition(self.resource,fixture(text=''))[0],'exclude-empty')
    def test_numeric(self):self.assertEqual(disposition(self.resource,fixture(text='123'))[0],'retain-numeric')
    def test_latin_not_blind_exclusion(self):self.assertEqual(disposition(self.resource,fixture(text='New Game'))[0],'review-latin')
    def test_decode_retained(self):
        e=fixture();e['decode']='failed';self.assertEqual(disposition(self.resource,e)[0],'deferred-decode')
    def test_control_retained(self):
        e=fixture();e['controls']='quarantined';self.assertEqual(disposition(self.resource,e)[0],'deferred-control')
    def test_interior_nul_retained(self):self.assertEqual(disposition(self.resource,fixture(text='가\x00'))[0],'deferred-control')
    def test_internal_retained(self):
        e=fixture();e['semantic']='internal-configuration';self.assertEqual(disposition(self.resource,e)[0],'retain-internal')
    def test_unindexed_no_import(self):
        e=fixture();e['semantic']='unindexed-pool-text-observed';self.assertEqual(disposition(self.resource,e)[0],'retain-reference')
    def test_config_display_candidate(self):
        e=fixture(text='New Game');e['semantic']='visible-text-candidate';r=dict(resource='FILE/a.int');self.assertEqual(disposition(r,e)[0],'translate-candidate')
    def test_alias_and_reuse_not_link(self):
        e=fixture(source_aliases=['old']);r=dict(self.resource,entries=[e,fixture('b')]);b=dict(locale='zh-CN',entries=[dict(id='old',source_sha256='hash',target='卡琳兹',status='draft')])
        rows,s=freeze(dict(resources=[r]),[b]);self.assertEqual(s['existing_translations'],1);self.assertEqual(s['reuse_suggestions'],1)
        self.assertFalse(rows[1]['reuse_suggestion']['linked_group']);self.assertFalse(rows[1]['import_approved'])
    def test_bad_source_hash(self):
        r=dict(self.resource,entries=[fixture()]);b=dict(locale='zh-CN',entries=[dict(id='a',source_sha256='wrong',target='卡琳兹',status='draft')])
        with self.assertRaises(ValueError):freeze(dict(resources=[r]),[b])
    def test_ambiguous_alias_rejected(self):
        r=dict(self.resource,entries=[fixture(source_aliases=['old']),fixture('b',source_aliases=['old'])]);b=dict(locale='zh-CN',entries=[dict(id='old',source_sha256='hash',target='卡琳兹',status='draft')])
        with self.assertRaises(ValueError):freeze(dict(resources=[r]),[b])
    def test_duplicate_target_rejected(self):
        r=dict(self.resource,entries=[fixture()]);b=dict(locale='zh-CN',entries=[dict(id='a',source_sha256='hash',target='卡琳兹',status='draft')])
        with self.assertRaises(ValueError):freeze(dict(resources=[r]),[b,b])
    def test_unresolved_not_counted_translated(self):
        e=fixture();e['semantic']='unresolved';r=dict(self.resource,entries=[e]);rows,s=freeze(dict(resources=[r]),[])
        self.assertEqual(s['dispositions'],{'deferred-semantics':1});self.assertFalse(s['translation_complete'])


if __name__=='__main__':unittest.main()
