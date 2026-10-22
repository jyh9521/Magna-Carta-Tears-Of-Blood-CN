"""Structural grouping and spending OFF behavior, using controlled RAM."""
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'tests')]
import build_grouped_cheats as grouped
import build_hotkey_cheats as hotkey
from test_hotkey_cheats import HotkeyCheatTests, PROFILES


class GroupedCheatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        HotkeyCheatTests.setUpClass()
        cls.original = HotkeyCheatTests.original
        source = HotkeyCheatTests.source
        with patch.object(hotkey, 'original_memory', return_value=cls.original):
            cls.flat = hotkey.render(b'fixture', PROFILES, source)
            # Keep the source identity check while avoiding proprietary test assets.
            with patch.object(hotkey, 'render', return_value=cls.flat):
                cls.text = grouped.render(b'fixture', cls.flat)

    def test_order_and_noncheckable_parent_encoding(self):
        _, groups = grouped.split_sections(self.text)
        self.assertEqual(list(groups)[:5], [
            '60 FPS', grouped.HINT, grouped.SPEND + '\\关闭',
            grouped.NAMES['消费不扣钱'], grouped.NAMES['消费反加钱']])
        self.assertNotIn(grouped.SPEND, groups)  # Qt creates a parent, not a cheat row.
        self.assertEqual(len(groups), 19)

    def test_existing_bodies_and_controller_unchanged(self):
        h1, flat = grouped.split_sections(self.flat)
        h2, result = grouped.split_sections(self.text)
        self.assertFalse(any(s.startswith('patch=') for s in h2))
        self.assertEqual([s for s in h1 if s.startswith('patch=')],
                         [s for s in result[grouped.CONTROL] if s.startswith('patch=')])
        for name, body in flat.items():
            self.assertEqual('\n'.join(body).strip(),
                             '\n'.join(result[grouped.NAMES.get(name, name)]).strip())

    def test_spending_off_does_not_disable_other_effects(self):
        memory = bytearray(self.original)
        struct.pack_into('<I', memory, 0xc3fe0, 1)
        active = hotkey.apply_pnach(memory, self.text,
            {grouped.NAMES['消费反加钱'], '60 FPS', grouped.NAMES['使用物品不减少'], grouped.CONTROL})
        self.assertEqual(struct.unpack_from('<I', active, 0x3a06f8)[0], 0x00451021)
        off = hotkey.apply_pnach(active, self.text,
            {grouped.SPEND + '\\关闭', '60 FPS', grouped.NAMES['使用物品不减少'], grouped.CONTROL})
        for label in grouped.FAMILIES[grouped.SPEND]:
            for va, word in hotkey.restore_words(self.original, hotkey.cases(PROFILES)[label]).items():
                self.assertEqual(struct.unpack_from('<I', off, va)[0], word)
        self.assertEqual(struct.unpack_from('<I', off, 0x1c69e4)[0], 0x28410001)
        self.assertEqual(struct.unpack_from('<I', off, 0x39fbb0)[0], 0)

    def test_hint_has_no_commands(self):
        _, groups = grouped.split_sections(self.text)
        self.assertFalse(any(s.startswith('patch=') for s in groups[grouped.HINT]))

    def test_selection_migration_preserves_other_settings(self):
        before = '[EmuCore]\nEnableCheats = true\n[Patches]\nEnable = Widescreen 16:9\n[Cheats]\nEnable = 消费\\反加钱\nEnable = 使用物品不减少\nEnable = Custom\n[Other]\nValue = 9\n'
        after = grouped.migrate_selection_ini(before)
        self.assertIn('Enable = ' + grouped.NAMES['消费反加钱'], after)
        self.assertIn('Enable = ' + grouped.NAMES['使用物品不减少'], after)
        self.assertIn('Enable = Custom', after)
        self.assertEqual(after.count('Enable = ' + grouped.CONTROL), 1)
        self.assertIn('[Patches]\nEnable = Widescreen 16:9', after)
        self.assertTrue(after.endswith('[Other]\nValue = 9\n'))
        self.assertEqual(grouped.migrate_selection_ini(after), after)

    def test_all_family_off_words_come_from_original(self):
        _, groups = grouped.split_sections(self.text)
        for family, labels in grouped.FAMILIES.items():
            expected = {}
            for label in labels:
                expected.update(hotkey.restore_words(self.original, hotkey.cases(PROFILES)[label]))
            commands = [s for s in groups[family + '\\关闭'] if s.startswith('patch=')]
            actual = {}
            for line in commands:
                _, _, va, kind, word = line.split('=', 1)[1].split(',')
                self.assertEqual(kind, 'word')
                actual[int(va, 16)] = int(word, 16)
            self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
