"""Reviewed locale data regressions, not runtime visibility assertions."""
from pathlib import Path
import json
import re
import unittest
import unicodedata

ROOT = Path(__file__).resolve().parents[1]


def batch(name):
    return json.loads((ROOT / 'locales/zh-CN' / name).read_text('utf8'))['entries']


class CourseCraftingTests(unittest.TestCase):
    def test_course_pairs_keep_independent_source_identities(self):
        rows = batch('dojo-course-review-01.json')
        self.assertEqual(len(rows), 80)
        self.assertEqual(len({r['id'] for r in rows}), 80)
        pairs = {}
        for row in rows:
            resource, field = row['id'].rsplit('/field/', 1)
            pairs.setdefault(resource, set()).add(int(field))
            self.assertEqual(row['status'], 'reviewed')
            self.assertRegex(row['source_sha256'], r'^[0-9a-f]{64}$')
        self.assertEqual(len(pairs), 40)
        self.assertTrue(all(fields == {0, 1} for fields in pairs.values()))

    def test_turn_limit_and_incoming_attack_rules_are_not_confused(self):
        rows = {r['id']: r['target'] for r in batch('dojo-course-review-01.json')}
        for resource, turns in zip(range(13356, 13361), range(7, 2, -1)):
            text = rows[f'SHIP/{resource:08d}.dod/record-index/0/field/1']
            self.assertIn(f'必须在{turns}回合内获胜。', text)
        for resource, attacks in zip(range(13363, 13368), range(3, 8)):
            text = rows[f'SHIP/{resource:08d}.dod/record-index/0/field/1']
            self.assertIn(f'只要撑过{attacks}次攻击，', text)
            self.assertIn('并击败对手。', text)

    def test_crafting_fifteen_triples_do_not_silently_include_tail_labels(self):
        rows = batch('weapon-crafting-review-01.json')
        self.assertEqual(len(rows), 45)
        self.assertEqual({r['id'] for r in rows}, {
            f'SHIP/00002106.odd/record-index/{record}/field/{field}'
            for record in range(15) for field in range(3)
        })
        self.assertTrue(all(r['status'] == 'reviewed' for r in rows))

    def test_explicit_line_breaks_do_not_start_with_punctuation(self):
        for name in ('dojo-course-review-01.json', 'weapon-crafting-review-01.json'):
            for row in batch(name):
                self.assertIsNone(re.search(r'[가-힣ぁ-ヿ]', row['target']))
                self.assertFalse(any(unicodedata.category(c) == 'Pd' for c in row['target']))
                for line in row['target'].split('$n'):
                    self.assertTrue(line)
                    self.assertFalse(unicodedata.category(line[0]).startswith('P'))


if __name__ == '__main__':
    unittest.main()
