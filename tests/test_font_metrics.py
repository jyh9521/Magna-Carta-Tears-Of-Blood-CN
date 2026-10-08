"""Synthetic metric-consumer tests; original instruction bytes are not fixtures."""
from pathlib import Path
import struct
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from research_font_metrics import metric_prefix, audit, branch_target


def imm(op, rs, rt, value):
    return op << 26 | rs << 21 | rt << 16 | value


def fixture():
    # Same scalar dataflow using generated ISA words, not extracted code.
    return struct.pack('<6I', imm(35, 20, 4, 0x68), imm(12, 2, 5, 65535),
        imm(35, 20, 3, 0x54), imm(43, 29, 3, 0xe0),
        4 << 21 | 5 << 16 | 3 << 11 | 0x21, imm(36, 3, 3, 0))


class MetricTests(unittest.TestCase):
    def test_all_unsigned_values(self):
        values = bytes(range(256))
        for glyph in range(256):
            self.assertEqual(metric_prefix(fixture(), values, glyph, 21),
                             dict(metric=glyph, index=glyph, steps=5))

    def test_index_above_255(self):
        self.assertEqual(metric_prefix(fixture(), b'\x07' * 2667, 2666, 18)['index'], 2666)

    def test_uint16_mask(self):
        self.assertEqual(metric_prefix(fixture(), b'\x0c\x13', 65537, 21)['metric'], 19)

    def test_exact_end_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unmapped model memory'):
            metric_prefix(fixture(), b'\x13' * 2667, 2667, 21)

    def test_empty_rejected(self):
        with self.assertRaises(ValueError): metric_prefix(fixture(), b'', 0, 21)

    def test_invalid_code_size(self):
        with self.assertRaises(ValueError): metric_prefix(fixture()[:-4], b'\x13', 0, 21)

    def test_invalid_glyph(self):
        for glyph in (-1, 0x100000000):
            with self.assertRaises(ValueError): metric_prefix(fixture(), b'\x13', glyph, 21)

    def test_invalid_height(self):
        with self.assertRaises(ValueError): metric_prefix(fixture(), b'\x13', 0, -1)

    def test_unsupported_operation(self):
        blob = struct.pack('<I', 0xffffffff) + fixture()[4:]
        with self.assertRaisesRegex(ValueError, 'unsupported'): metric_prefix(blob, b'\x13', 0, 21)

    def test_transfer_rejected(self):
        blob = struct.pack('<I', imm(4, 0, 0, 0)) + fixture()[4:]
        with self.assertRaisesRegex(ValueError, 'transfer'): metric_prefix(blob, b'\x13', 0, 21)

    def test_branch_target_includes_pc_plus_four(self):
        self.assertEqual(branch_target(imm(5, 2, 0, 0x21), 0x272734), 0x2727bc)

    def test_negative_branch(self):
        self.assertEqual(branch_target(imm(4, 0, 0, 65535), 0x1000), 0x1000)

    def test_invalid_branch(self):
        with self.assertRaises(ValueError): branch_target(0, 0x1000)

    def test_excluded_store_identity(self):
        blob = fixture()[:12] + bytes(4) + fixture()[16:]
        with self.assertRaisesRegex(ValueError, 'stack store'): metric_prefix(blob, b'\x13', 0, 21)

    def test_version_rejected(self):
        with self.assertRaisesRegex(ValueError, 'fingerprint'): audit(bytes(64))


if __name__ == '__main__': unittest.main()
