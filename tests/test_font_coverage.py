"""Synthetic coverage and collision accounting without original game assets."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "lib")]
from audit_font_coverage import observed_slots, scan_fpbs, capacity_summary, inspect_tui, scan_tuis, combine_inventories
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

    def tui(self, fields):
        return struct.pack('<II', len(fields), 2) + b''.join(struct.pack('<I', i) + raw.ljust(512, b'\0') for i, raw in fields)

    def test_tui_geometry_and_source_identity(self):
        blob = self.tui([(176, '가'.encode('cp949'))])
        report, fields = inspect_tui(blob)
        self.assertEqual(report['status'], 'geometry-verified')
        self.assertEqual(report['fields'][0]['offset'], 12)
        self.assertEqual(fields, [(176, bytes.fromhex('b0a1'))])
        self.assertEqual(report['fields'][0]['encoded_bytes'], 2)

    def test_tui_bad_geometry_rejected(self):
        for blob in (b'X', self.tui([(1, b'A')])[:-1], struct.pack('<II', 0, 3)):
            self.assertEqual(inspect_tui(blob)[1], [])
            self.assertNotEqual(inspect_tui(blob)[0]['status'], 'geometry-verified')

    def test_tui_duplicate_ids_rejected(self):
        self.assertEqual(inspect_tui(self.tui([(1, b'A'), (1, b'B')]))[0]['status'], 'duplicate-record-id')

    def test_tui_nul_and_padding(self):
        report, fields = inspect_tui(self.tui([(1, b'A' * 512), (2, b'A\0B'), (3, b'')]))
        self.assertEqual([f['status'] for f in report['fields']], ['missing-nul', 'nonzero-padding', 'empty'])
        self.assertEqual(fields, [])

    def test_tui_decode_failures_and_unknown_structure(self):
        report, fields = inspect_tui(self.tui([(1, b'\xff'), (2, b'%q'), (3, b'A\tB')]))
        self.assertEqual(report['fields'][0]['status'], 'decode-failed')
        self.assertFalse(report['fields'][1]['protected_structures_known'])
        self.assertTrue(report['fields'][2]['has_raw_control'])
        self.assertEqual(len(fields), 2)

    def test_tui_target_exclusion_and_bundle_not_double_counted(self):
        blob = self.tui([(176, bytes.fromhex('b0a1')), (177, bytes.fromhex('b0a1'))])
        r = scan_tuis([('a.tui', blob)], self.slots, {'a.tui': {176}}, blob + blob)
        self.assertEqual(r['slots']['b0a1']['original_occurrences'], 2)
        self.assertEqual(r['slots']['b0a1']['outside_target_windows_occurrences'], 1)
        self.assertEqual(r['resources']['a.tui']['exact_bundle_copy_count'], 2)

    def test_tui_exclusion_requires_decoded_field(self):
        with self.assertRaises(ValueError):
            scan_tuis([('a.tui', self.tui([(1, b'\xff')]))], self.slots, {'a.tui': {1}}, b'')

    def test_combine_counts_and_resource_union(self):
        f = scan_fpbs([('a.fpb', build_fpb(bytes(16), [], bytes.fromhex('b0a1')))], self.slots, {})
        t = scan_tuis([('b.tui', self.tui([(1, bytes.fromhex('b0a1'))]))], self.slots, {}, b'')
        row = combine_inventories(f, t)['slots']['b0a1']
        self.assertEqual(row['original_occurrences'], 2)
        self.assertEqual(row['resources'], ['a.fpb', 'b.tui'])
        summary = capacity_summary(combine_inventories(f, t), [], scope='decoded_fpb_and_tui')
        self.assertEqual(summary['used_slots_in_decoded_fpb_and_tui'], 1)
        self.assertNotIn('used_slots_in_decoded_fpb', summary)

    def test_combine_rejects_mismatched_domains(self):
        f = scan_fpbs([], self.slots, {})
        with self.assertRaises(ValueError):
            combine_inventories(f, {'slots': {}})
        with self.assertRaises(ValueError):
            combine_inventories()

    def test_tui_report_does_not_export_text(self):
        report, _ = inspect_tui(self.tui([(1, b'INTERNAL_KEY')]))
        self.assertNotIn('INTERNAL_KEY', str(report))


if __name__ == '__main__':
    unittest.main()
