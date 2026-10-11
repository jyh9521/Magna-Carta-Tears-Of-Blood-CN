import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('tools','lib','src')]
from prepare_source_interpretations import merge_profiles
from audit_alternate_source_readings import audit_field
from font_poc import digest

class KatakanaInterpretationTests(unittest.TestCase):
    def profile(self,identity='a'):
        return dict(schema=1,locale='zh-CN',source_corpus_sha256='f'*64,entries=[dict(id=identity)])
    def test_merge_retains_order_and_does_not_mutate_inputs(self):
        a,b=self.profile(),self.profile('b');before=copy.deepcopy([a,b]);m=merge_profiles([a,b]);self.assertEqual([x['id'] for x in m['entries']],['a','b']);self.assertEqual([a,b],before)
    def test_single_profile_is_byte_content_compatible(self):
        p=self.profile();self.assertEqual(merge_profiles([p]),p)
    def test_duplicate_identity_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):merge_profiles([self.profile(),self.profile()])
    def test_schema_mismatch_rejected(self):
        p=self.profile('b');p['schema']=2
        with self.assertRaisesRegex(ValueError,'schema'):merge_profiles([self.profile(),p])
    def test_corpus_mismatch_rejected(self):
        p=self.profile('b');p['source_corpus_sha256']='e'*64
        with self.assertRaisesRegex(ValueError,'corpus'):merge_profiles([self.profile(),p])
    def test_locale_mismatch_rejected(self):
        p=self.profile('b');p['locale']='ja-JP'
        with self.assertRaisesRegex(ValueError,'locale'):merge_profiles([self.profile(),p])
    def test_missing_profiles_rejected(self):
        with self.assertRaisesRegex(ValueError,'missing'):merge_profiles([])
    def test_missing_fingerprint_rejected(self):
        p=self.profile();del p['source_corpus_sha256']
        with self.assertRaisesRegex(ValueError,'fingerprint'):merge_profiles([p])
    def test_fixed_profiles_merge_without_inventing_locale(self):
        a=dict(schema=1,source_corpus_sha256='f'*64,bindings=[dict(id='a')]);b=copy.deepcopy(a);b['bindings'][0]['id']='b';m=merge_profiles([a,b],'bindings',False);self.assertNotIn('locale',m);self.assertEqual(len(m['bindings']),2)
    def fixture(self,text):
        raw=text.encode('cp932');r=dict(resource='SHIP/sample.cht',sha256=digest(raw));e=dict(id='sample',offset=0,source_bytes=len(raw),source_sha256=digest(raw),raw_hex=raw.hex(),decode='failed');d=dict(**e,resource=r['resource'],resource_sha256=r['sha256'],source_encoding='cp932',reading_sha256=digest(text.encode('utf8')),target='莉丝！',status='reviewed',import_approved=False,runtime_encoding_verified=False);return r,e,d,raw
    def test_fullwidth_katakana_only_accepted_with_all_hashes(self):
        self.assertEqual(audit_field(*self.fixture('リース！'))['source'],'リース！')
    def test_halfwidth_noise_not_promoted(self):
        with self.assertRaisesRegex(ValueError,'lexical'):audit_field(*self.fixture('^^ﾇﾏﾇ'))
    def test_private_use_with_katakana_still_rejected(self):
        with self.assertRaisesRegex(ValueError,'private-use'):audit_field(*self.fixture('リース\ue000'))
    def test_new_five_profile_preserves_canonical_names_and_controls(self):
        p=json.loads((ROOT/'locales/zh-CN/proofreading/alternate-source-readings-02.json').read_text('utf8'));self.assertEqual(len(p['entries']),5);self.assertEqual(sum('native_binding' in x for x in p['entries']),4);self.assertEqual([x['target'] for x in p['entries']],['$D06阿玛巴德？$D26 $D06巫女？','$D08莉丝？？$D68 $D15莉丝！','莉丝！','长剑！优质盾！','阿蜜拉女王？']);self.assertTrue(all(x['status']=='reviewed' and x['import_approved'] is False and x['runtime_encoding_verified'] is False for x in p['entries']))
    def test_combined_readings_keep_old154_and_add_exact5(self):
        p=ROOT/'locales/zh-CN/proofreading';a=json.loads((p/'alternate-source-readings.json').read_text('utf8'));b=json.loads((p/'alternate-source-readings-02.json').read_text('utf8'));m=merge_profiles([a,b]);self.assertEqual(m['entries'][:154],a['entries']);self.assertEqual(len(m['entries']),159)
    def test_new_fixed_binding_is_physical_record12(self):
        p=json.loads((ROOT/'locales/zh-CN/proofreading/alternate-fixed-consumers-02.json').read_text('utf8'));self.assertEqual(len(p['bindings']),1);b=p['bindings'][0];self.assertEqual((b['id'],b['offset'],b['record_index'],b['native_read_bytes']),('SHIP/00004044.cht/slot/12',6412,12,512));self.assertFalse(b['runtime_verified'])
