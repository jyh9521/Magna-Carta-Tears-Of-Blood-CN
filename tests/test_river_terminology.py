"""River and Water are separate game elements, not spelling variants."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RiverTerminologyTests(unittest.TestCase):
    def setUp(self):
        self.entries = {}
        for path in (ROOT / 'locales/zh-CN').glob('*review-*.json'):
            for entry in json.loads(path.read_text('utf8')).get('entries', []):
                self.entries[entry['id']] = entry

    def test_reviewed_scene_uses_river_name(self):
        for seq in (5, 6, 9, 11, 26):
            entry = self.entries[f'SHIP/00007488.fpb/seq/{seq}']
            self.assertIn('江之卡恩', entry['target'])
            self.assertNotIn('河之卡恩', entry['target'])
            self.assertEqual('reviewed', entry['status'])

    def test_river_monster_and_item_names(self):
        expected = {
            'SHIP/00000460.cha/record-index/126/field/0': '江之遗迹神兽',
            'SHIP/00000460.cha/record-index/189/field/0': '江之遗迹神兽',
            'SHIP/00006461.mdg/record-index/33/field/0': '江之神兽',
            'SHIP/00000953.itm/record-index/452/field/0': '江之卡恩珠',
        }
        for key, target in expected.items():
            self.assertEqual(target, self.entries[key]['target'])

    def test_same_record_item_description_uses_river_element(self):
        entry = self.entries['SHIP/00000953.itm/record-index/310/field/1']
        self.assertEqual('蕴含江属性气息的碎片', entry['target'])
        entry = self.entries['SHIP/00000682.tui/record/23/field/0/index/20']
        self.assertEqual('增加江属性的卡恩', entry['target'])

    def test_water_is_not_merged_with_river(self):
        target = self.entries['SHIP/00016655.cht/slot/9']['target']
        self.assertIn('水与江之卡恩', target)
        self.assertIn('江与水之卡恩', target)
        target = self.entries['SHIP/00016573.fpb/seq/3']['target']
        self.assertIn('江之卡恩（阳阳阴）', target)

    def test_non_element_river_words_are_not_globally_replaced(self):
        expected = {
            'SHIP/00000953.itm/record-index/154/field/0': '长河手镯',
            'SHIP/00000953.itm/record-index/155/field/0': '银河手镯',
            'SHIP/00000953.itm/record-index/283/field/0': '南河结晶',
        }
        for key, target in expected.items():
            self.assertEqual(target, self.entries[key]['target'])

    def test_invention_name_is_not_split_by_control(self):
        target = self.entries['SHIP/00007488.fpb/seq/14']['target']
        self.assertIn('“冰之世界”', target)
        self.assertEqual(2, target.count('$n'))
        self.assertNotIn('冰之$n世界', target)

    def test_full_resource_review_keeps_source_bound_entries(self):
        entries = [entry for key, entry in self.entries.items()
                   if key.startswith('SHIP/00007488.fpb/')]
        self.assertEqual(34, len(entries))
        for entry in entries:
            self.assertEqual('reviewed', entry['status'])
            self.assertEqual(64, len(entry['source_sha256']))
        self.assertIn('蕾哈丝', self.entries['SHIP/00007488.fpb/seq/21']['target'])
        self.assertIn('天才克里斯', self.entries['SHIP/00007488.fpb/seq/30']['target'])


if __name__ == '__main__':
    unittest.main()
