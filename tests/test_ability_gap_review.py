import json,re,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('tools','src','lib')]
from validate_translation_batch import glossary_terms

class AbilityGapReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch=json.loads((ROOT/'locales/zh-CN/ability-gap-review-01.json').read_text('utf8'))
        cls.rows=cls.batch['entries'];cls.terms=dict(glossary_terms(ROOT/'GLOSSARY.md'))
    def test_complete_remaining_abi_batch(self):self.assertEqual(len(self.rows),403)
    def test_source_bound_unique(self):
        self.assertEqual(len({e['id'] for e in self.rows}),403)
        for e in self.rows:
            self.assertRegex(e['id'],r'^SHIP/00000466\.abi/record-index/\d+/field/[01]$')
            self.assertRegex(e['source_sha256'],r'^[0-9a-f]{64}$')
    def test_reviewed_nonempty(self):
        self.assertTrue(all(e['status']=='reviewed' and e['target'] for e in self.rows))
    def test_placeholder_not_invented_mechanics(self):
        self.assertEqual(sum(e['target']=='你能懂吗？' for e in self.rows),185)
        self.assertEqual(sum(e['target']=='说了也不懂' for e in self.rows),2)
    def test_sound_actor_not_soundless(self):
        self.assertEqual(self.terms['사운드리스응원'],'语音莉丝加油')
        self.assertEqual(self.terms['사운드리스치료의바람'],'语音莉丝治愈之风')
    def test_names_and_element_disambiguation(self):
        self.assertEqual(self.terms['운디네공격(강)'],'温蒂妮攻击(江)')
        self.assertEqual(self.terms['캐리안공격'],'凯莉安攻击')
        self.assertEqual(self.terms['오르하패밀리어_마법'],'奥尔哈使魔_魔法')
    def test_no_dash_or_control_damage(self):
        for e in self.rows:self.assertNotIn('—',e['target']);self.assertNotIn('\0',e['target'])

if __name__=='__main__':unittest.main()
