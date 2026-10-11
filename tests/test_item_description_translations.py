"""Locale proofreading regressions; no font/import/runtime acceptance implied."""
from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from audit_translation_consistency import audit
from extract_strings import field
from validate_translation_batch import glossary_terms


def rows():
    return json.loads((ROOT / 'locales/zh-CN/item-description-review-01.json').read_text('utf8'))['entries']


class ItemDescriptionTests(unittest.TestCase):
    def test_reviewed_descriptions_keep_unique_source_bound_identities(self):
        data = rows()
        self.assertEqual(len(data), 425)
        self.assertEqual(len({r['id'] for r in data}), 425)
        for row in data:
            self.assertEqual(row['status'], 'reviewed')
            self.assertTrue(row['id'].endswith('/field/1'))
            self.assertRegex(row['source_sha256'], r'^[0-9a-f]{64}$')
            self.assertNotIn('@RETAIN', row['target'])

    def test_ally_enemy_scope_and_numeric_multipliers(self):
        data = {r['id']: r['target'] for r in rows()}
        def text(record):
            return data[f'SHIP/00000953.itm/record-index/{record}/field/1']
        self.assertEqual(text(370), '提高我方一人的物理攻击力')
        self.assertEqual(text(371), '提高我方全员的物理攻击力')
        self.assertEqual(text(372), '降低敌方全体的物理攻击力')
        self.assertEqual(text(407), '使敌方一人中毒')
        self.assertEqual(text(438), '将获得的经验值提高到1.25倍')
        self.assertEqual(text(439), '将获得的经验值提高到1.5倍')

    def test_long_common_words_do_not_misidentify_character_names(self):
        terms = glossary_terms(ROOT / 'GLOSSARY.md')
        for source, target in [('크리스탈', '水晶'), ('다이아몬드', '钻石'), ('크리스', '克里斯')]:
            src = field('test-id', source.encode('cp949'), 0)
            corpus = dict(source_locale='ko-KR', resources=[dict(entries=[src])])
            batch = dict(schema=1, locale='zh-CN', entries=[dict(
                id=src['id'], source_sha256=src['source_sha256'], target=target, status='reviewed')])
            self.assertEqual(audit(corpus, [('batch', batch)], terms)['summary']['lexical_issues'], 0)

    def test_same_record_name_decisions_remain_explicit(self):
        data = {r['id']: r for r in rows()}
        sword = data['SHIP/00000953.itm/record-index/477/field/1']
        self.assertEqual(sword['target'], '阿格雷安的剑')
        self.assertIn('does not claim recovered original characters', sword['context'])
        flow = data['SHIP/00000953.itm/record-index/358/field/1']
        self.assertEqual(flow['target'], '天命启心流秘传书')
        self.assertIn('canonical name from field0', flow['context'])


if __name__ == '__main__':
    unittest.main()
