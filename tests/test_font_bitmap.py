"""Synthetic bitmap projection and SRAV tests; no original assets or ISA fixture."""
from pathlib import Path
import struct
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from research_font_bitmap import project_pixel, convert_bitmap, audit, SIZE
from research_glyph_lookup import ReadOnlyMips


def reg(fn, rs, rt, rd, shift=0): return rs << 21 | rt << 16 | rd << 11 | shift << 6 | fn


def fixture():
    words = [0] * (SIZE // 4)
    words[4] = reg(7, 6, 5, 14)
    words[6] = 12 << 26 | 14 << 21 | 15 << 16 | 3
    words[8] = reg(0, 0, 15, 14, 4)
    words[10] = reg(0x23, 14, 15, 14)
    words[11] = reg(0, 0, 14, 14, 2)
    return struct.pack('<' + str(len(words)) + 'I', *words)


TABLE = [[((v >> (2 * x)) & 3) * 60 for x in range(4)] for v in range(256)]


class BitmapTests(unittest.TestCase):
    def shift(self, value, amount, shift_field=0):
        r = [0] * 32; r[4], r[5] = amount, value
        ReadOnlyMips(bytes(4), 0x1000, []).effect(reg(7, 4, 5, 2, shift_field), r)
        return r[2]

    def test_srav_positive(self): self.assertEqual(self.shift(128, 2), 32)
    def test_srav_negative(self): self.assertEqual(self.shift(0x80000000, 1), 0xc0000000)
    def test_srav_masks_amount(self): self.assertEqual(self.shift(0x80000000, 33), 0xc0000000)
    def test_srav_noncanonical(self):
        with self.assertRaisesRegex(ValueError, 'noncanonical'): self.shift(4, 1, 1)
    def test_all_byte_positions(self):
        for v in range(256):
            for s in (0, 2, 4, 6): self.assertEqual(project_pixel(fixture(), v, s), TABLE[v][s // 2])
    def test_level_values(self): self.assertEqual([project_pixel(fixture(), v, 0) for v in range(4)], [0, 60, 120, 180])
    def test_invalid_pixel_input(self):
        for v, s in ((-1, 0), (256, 0), (1, 1), (1, 8)):
            with self.assertRaises(ValueError): project_pixel(fixture(), v, s)
    def test_fragment_length(self):
        with self.assertRaises(ValueError): project_pixel(fixture()[:-4], 0, 0)
    def test_transfer_rejected(self):
        blob = bytearray(fixture()); struct.pack_into('<I', blob, 16, 4 << 26)
        with self.assertRaisesRegex(ValueError, 'transfer'): project_pixel(bytes(blob), 0, 0)
    def test_unsupported_rejected(self):
        blob = bytearray(fixture()); struct.pack_into('<I', blob, 16, 0xffffffff)
        with self.assertRaisesRegex(ValueError, 'unsupported'): project_pixel(bytes(blob), 0, 0)
    def test_low_bits_first(self): self.assertEqual(convert_bitmap(b'\xe4', 1, 1, 4, 1, TABLE), bytes([0, 60, 120, 180]))
    def test_row_padding_excluded(self): self.assertEqual(convert_bitmap(b'\xe4\xff', 1, 1, 5, 2, TABLE), bytes([0, 60, 120, 180, 180]))
    def test_glyph_row_order(self): self.assertEqual(convert_bitmap(b'\x00\x55\xaa\xff', 2, 2, 1, 1, TABLE), bytes([0, 60, 120, 180]))
    def test_invalid_geometry(self):
        for g,h,w,s in ((0,1,1,1),(1,0,1,1),(1,1,0,1),(1,1,5,1)):
            with self.assertRaises(ValueError): convert_bitmap(b'\x00',g,h,w,s,TABLE)
        with self.assertRaises(ValueError): convert_bitmap(b'\x00\x00',1,1,1,1,TABLE)
    def test_invalid_table(self):
        with self.assertRaises(ValueError): convert_bitmap(b'\x00',1,1,1,1,TABLE[:-1])
        bad = [list(x) for x in TABLE]; bad[0][0] = 256
        with self.assertRaises(ValueError): convert_bitmap(b'\x00',1,1,1,1,bad)
    def test_version_rejected(self):
        with self.assertRaisesRegex(ValueError, 'fingerprint'): audit(bytes(64))


if __name__ == '__main__': unittest.main()
