"""Descriptions use Arabic quantities without changing cheat identities."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CheatDescriptionTests(unittest.TestCase):
    def test_profile_descriptions_use_arabic_quantities(self):
        base = ROOT / 'profiles/cheats'
        gameplay = json.loads((base / 'SCKA-20043_AE86E04C.json').read_text('utf8'))
        battle = json.loads((base / 'SCKA-20043_AE86E04C-battle.json').read_text('utf8'))
        texts = [row['description'] for row in gameplay['codes']]
        texts += list(battle['descriptions'].values())
        for text in texts:
            for token in ['九十九', '九十八', '九千九百九十九', '一百万', '一百', '降至一', '一项', '一种']:
                self.assertNotIn(token, text)

    def test_direct_and_hotkey_descriptions_match(self):
        def descriptions(name):
            lines = (ROOT / 'src/patches' / name).read_text('utf8').splitlines()
            return [line for line in lines if line.startswith('description=')]
        direct = descriptions('SCKA-20043_AE86E04C.pnach')
        hotkey = descriptions('SCKA-20043_AE86E04C-hotkeys.pnach')
        self.assertEqual(len(direct), 14)
        self.assertEqual(hotkey, [s + '选择键加上开启，加下关闭；默认关闭。' for s in direct])


if __name__ == '__main__':
    unittest.main()
