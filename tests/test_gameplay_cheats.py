import json
import re
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import build_gameplay_cheats as tool


class GameplayCheatTests(unittest.TestCase):
    def setUp(self):
        self.profile = json.loads((ROOT/'profiles/cheats/SCKA-20043_AE86E04C.json').read_text('utf8'))

    def test_render_eight_sections(self):
        text = tool.render(self.profile, 'gametitle=fixture\n')
        self.assertEqual(text.count('patch=1,EE,'), 8)
        self.assertNotIn('0x', text)

    def test_descriptions_are_chinese(self):
        for row in self.profile['codes']:
            self.assertTrue(row['description'])
            self.assertIsNone(re.search('[A-Za-z]',row['description']))

    def test_unknown_elf_rejected(self):
        with self.assertRaisesRegex(ValueError, 'size'):
            tool.validate(b'', self.profile)

    def test_money_operands(self):
        row = self.profile['codes'][1]
        old, new = int(row['expected'], 16), int(row['replacement'], 16)
        self.assertEqual(old & ~63, new & ~63)
        self.assertEqual((old & 63, new & 63), (0x23, 0x21))
        self.assertEqual(((new>>21)&31, (new>>16)&31, (new>>11)&31), (2,5,2))

    def test_item_operands(self):
        row = next(r for r in self.profile['codes'] if r['id'] == 'item_increase')
        new = int(row['replacement'], 16)
        self.assertEqual(((new>>21)&31, (new>>16)&31, (new>>11)&31), (2,6,2))

    def test_item_99_is_v0(self):
        self.assertEqual(self.profile['codes'][4]['replacement'], '24020063')

    def test_spend_store_and_item_store(self):
        self.assertEqual(self.profile['codes'][0]['expected'], 'AC620000')
        self.assertEqual(self.profile['codes'][3]['expected'], 'AC620004')

    def test_free_spend_branch_target(self):
        row = next(r for r in self.profile['codes'] if r['id'] == 'spend_free')
        self.assertEqual(row['expected'], '14200004')
        self.assertEqual(int(row['va'],16)+4+4*(int(row['replacement'],16)&65535), 0x3a0708)

    def test_item_98(self):
        row = next(r for r in self.profile['codes'] if r['id'] == 'item_count_98')
        self.assertEqual(row['replacement'], '24020062')


if __name__ == '__main__':
    unittest.main()
