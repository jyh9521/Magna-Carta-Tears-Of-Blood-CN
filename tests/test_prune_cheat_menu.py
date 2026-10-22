"""Menu pruning changes section membership/names, never retained commands."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import struct

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prune_cheat_menu as prune
import build_grouped_cheats as groups


class PruneMenuTests(unittest.TestCase):
    def test_removed_sections_and_standalone_item(self):
        source = 'gametitle=fixture\n'
        names = ['60帧', prune.KEEP_ITEM, *sorted(prune.REMOVED), groups.CONTROL]
        for index, name in enumerate(names):
            source += f'[{name}]\ndescription=自定义描述{index}\npatch=1,EE,00100000,word,{index:08X}\n'
        result = prune.prune_pnach(source)
        h1, before = groups.split_sections(source)
        h2, after = groups.split_sections(result)
        self.assertEqual(h1, h2)
        self.assertFalse(prune.REMOVED & after.keys())
        self.assertNotIn(prune.KEEP_ITEM, after)
        for name, body in after.items():
            self.assertEqual(body, before[prune.KEEP_ITEM if name == prune.ITEM_NAME else name])

    def test_ini_preserves_independent_settings_and_checked_item(self):
        before = '[Patches]\nEnable = Widescreen 16:9\n[Cheats]\n'
        for name in [prune.KEEP_ITEM, *sorted(prune.REMOVED), groups.CONTROL, '60帧']:
            before += 'Enable = ' + name + '\n'
        after = prune.prune_ini(before)
        self.assertIn('Enable = ' + prune.ITEM_NAME, after)
        self.assertIn('Enable = ' + groups.CONTROL, after)
        self.assertIn('[Patches]\nEnable = Widescreen 16:9', after)
        for name in prune.REMOVED:
            self.assertNotIn('Enable = ' + name, after)

    def test_unrecognized_layout_rejected(self):
        with self.assertRaises(ValueError):
            prune.prune_pnach('[60帧]\ndescription=fixture\n')

    def test_remove_exact_named_section(self):
        text = '[A]\ndescription=保留\n[B]\npatch=1,EE,00100000,word,00000000\n[C]\ndescription=保留2\n'
        result = prune.remove_named_section(text, 'B')
        _, before = groups.split_sections(text)
        _, after = groups.split_sections(result)
        self.assertEqual(after, {name: body for name, body in before.items() if name != 'B'})
        with self.assertRaises(ValueError):
            prune.remove_named_section(result, 'B')

    def test_restore_money_on_off_and_preserve_item(self):
        source = '[60帧]\ndescription=自定义\n[' + prune.ITEM_NAME + ']\ndescription=保留我的描述\n'
        original = bytearray(32 * 1024 * 1024)
        struct.pack_into('<I', original, 0x3a0e78, 0x14200003)
        with patch.object(prune.hotkey, 'original_memory', return_value=original):
            restored = prune.restore_money_gain(source, b'controlled ELF')
        _, before = groups.split_sections(source)
        _, after = groups.split_sections(restored)
        for name, body in before.items():
            self.assertEqual(body, after[name])
        for state, expected in [(0, 0x14200003), (1, 0), (0, 0x14200003)]:
            struct.pack_into('<I', original, 0xc3fe0, state)
            original = bytearray(prune.hotkey.apply_pnach(original, restored, {prune.MONEY_NAME}))
            self.assertEqual(struct.unpack_from('<I', original, 0x3a0e78)[0], expected)
        with self.assertRaises(ValueError):
            prune.restore_money_gain(restored, b'controlled ELF')


if __name__ == '__main__':
    unittest.main()
