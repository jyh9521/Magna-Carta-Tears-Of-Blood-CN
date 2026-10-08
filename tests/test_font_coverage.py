"""Synthetic coverage and collision accounting without original game assets."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "lib")]
from audit_font_coverage import observed_slots, scan_fpbs, capacity_summary
from translate.fpb import build_fpb


class FontCoverageTests(unittest.TestCase):
    def setUp(self):
        self.info = {"glyphs": 2667, "ranges": [0xA1A6] + [(l << 8) | 0xA1 for l in range(0xB0, 0xC9)] + [0xC8FF],
                     "bases": [256] + [317 + i * 94 for i in range(25)] + [2667]}
        self.slots = observed_slots(self.info)

    def test_range_cardinality_and_boundaries(self):
        self.assertEqual(len(self.slots), 2350)
        self.assertEqual(self.slots[bytes.fromhex('b0a1')], 317)
        self.assertEqual(self.slots[bytes.fromhex('c8fe')], 2666)
        self.assertNotIn(bytes.fromhex('b0ff'), self.slots)

    def test_reject_different_font_layout(self):
        for key, value in [('glyphs', 2668), ('bases', [0]), ('ranges', [0])]:
            with self.assertRaises(ValueError):
                observed_slots({**self.info, key: value})

    def test_count_pool_once_not_overlapping_windows(self):
        blob = build_fpb(bytes(16), [(1, 2, 4), (2, 2, 2)], '가가가'.encode('cp949'))
        r = scan_fpbs([('a.fpb', blob)], self.slots, {})
        self.assertEqual(r['slots']['b0a1']['original_occurrences'], 3)

    def test_exclude_targets_preserve_outside_usage(self):
        blob = build_fpb(bytes(16), [(1, 2, 2)], '가가'.encode('cp949'))
        r = scan_fpbs([('a.fpb', blob)], self.slots, {'a.fpb': {0}})
        row = r['slots']['b0a1']
        self.assertEqual(row['original_occurrences'], 2)
        self.assertEqual(row['outside_target_windows_occurrences'], 1)
        self.assertEqual(row['outside_target_windows_resources'], ['a.fpb'])

    def test_strict_failures_and_stub_separated(self):
        r = scan_fpbs([('a.fpb', build_fpb(bytes(16), [], b'\xff')), ('b.fpb', bytes(8)), ('c.tui', b'x')], self.slots, {})
        self.assertEqual(r['statuses'], {'decode_failed': 1, 'stub': 1})
        self.assertEqual(r['omitted_resources'], ['a.fpb'])

    def test_missing_target_sequence_rejected(self):
        with self.assertRaises(ValueError):
            scan_fpbs([('a.fpb', build_fpb(bytes(16), [], b'A'))], self.slots, {'a.fpb': {1}})

    def test_summary_scope_and_distinct_resources(self):
        blob = build_fpb(bytes(16), [], '가각'.encode('cp949'))
        r = scan_fpbs([('a.fpb', blob)], self.slots, {})
        s = capacity_summary(r, [{'character': '测', 'bytes': 'b0a1', 'glyph': 317},
                                 {'character': '试', 'bytes': 'b0a2', 'glyph': 318}])
        self.assertEqual(s['used_slots_in_decoded_fpb'], 2)
        self.assertEqual(s['unobserved_slots_in_decoded_fpb'], 2348)
        self.assertEqual(s['outside_target_resource_count'], 1)
        self.assertEqual(s['outside_target_occurrences'], 2)

    def test_map_mismatch_rejected(self):
        r = scan_fpbs([], self.slots, {})
        with self.assertRaises(ValueError):
            capacity_summary(r, [{'character': '测', 'bytes': 'b0a1', 'glyph': 318}])


if __name__ == '__main__':
    unittest.main()
