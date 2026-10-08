"""Synthetic read-only instruction tests; no original ELF instructions fixture."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from research_glyph_lookup import ReadOnlyMips, ENTRY, lookup, signed


def immediate(op, rs, rt, value):
    return op << 26 | rs << 21 | rt << 16 | (value & 65535)


def register(fn, rs, rt, rd, shift=0):
    return rs << 21 | rt << 16 | rd << 11 | shift << 6 | fn


def code(words):
    return struct.pack(f'<{len(words)}I', *words)


RETURN_WORDS = [register(8, 31, 0, 0), 0]


class GlyphLookupTests(unittest.TestCase):
    def execute(self, words, registers=None, blocks=None, budget=1024):
        return ReadOnlyMips(code(words), ENTRY, blocks or []).run(registers or {}, budget)

    def test_signed_comparison(self):
        r = self.execute([register(0x2a, 4, 5, 2)] + RETURN_WORDS, {4: 0xffffffff, 5: 1})
        self.assertEqual(r['return_u32'], 1)
        self.assertEqual(signed(0x80000000), -2147483648)

    def test_arithmetic_wrap_and_signed_immediate(self):
        r = self.execute([immediate(9, 4, 2, -1), register(0x21, 2, 5, 2), register(0x23, 2, 6, 2)] + RETURN_WORDS, {4: 0, 5: 2, 6: 3})
        self.assertEqual(r['return_u32'], 0xfffffffe)

    def test_lui_shift_or_and(self):
        words = [immediate(15, 0, 2, 0x8000), register(0, 0, 4, 3, 8), register(0x25, 2, 3, 2), immediate(12, 2, 2, 0xffff)] + RETURN_WORDS
        self.assertEqual(self.execute(words, {4: 0x81})['return_u32'], 0x8100)

    def test_signed_and_unsigned_byte_load(self):
        for op, result in [(32, 0xffffff80), (36, 128)]:
            r = self.execute([immediate(op, 4, 2, 0)] + RETURN_WORDS, {4: 0x1000}, [(0x1000, b'\x80')])
            self.assertEqual(r['return_u32'], result)

    def test_halfword_and_word_little_endian(self):
        for op, result in [(37, 0x0201), (35, 0x04030201)]:
            r = self.execute([immediate(op, 4, 2, 0)] + RETURN_WORDS, {4: 0x1000}, [(0x1000, bytes([1, 2, 3, 4]))])
            self.assertEqual(r['return_u32'], result)

    def test_taken_branch_executes_delay_once(self):
        words = [immediate(4, 0, 0, 2), immediate(9, 2, 2, 7), immediate(9, 2, 2, 100)] + RETURN_WORDS
        r = self.execute(words)
        self.assertEqual((r['return_u32'], r['steps']), (7, 4))

    def test_untaken_branch_still_executes_delay(self):
        words = [immediate(5, 0, 0, 2), immediate(9, 2, 2, 7), immediate(9, 2, 2, 100)] + RETURN_WORDS
        self.assertEqual(self.execute(words)['return_u32'], 107)

    def test_return_delay_changes_result(self):
        self.assertEqual(self.execute([RETURN_WORDS[0], immediate(9, 0, 2, 42)])['return_u32'], 42)

    def test_zero_register_remains_zero(self):
        r = self.execute([immediate(9, 0, 0, 99), immediate(9, 0, 2, 5)] + RETURN_WORDS, {0: 7})
        self.assertEqual(r['return_u32'], 5)

    def test_loop_budget_and_delay_budget(self):
        with self.assertRaisesRegex(ValueError, 'budget'): self.execute([immediate(4, 0, 0, -1), 0], budget=6)
        with self.assertRaisesRegex(ValueError, 'budget'): self.execute(RETURN_WORDS, budget=1)

    def test_unsupported_and_nested_transfer_reject(self):
        for words in ([0xffffffff] + RETURN_WORDS, [RETURN_WORDS[0], immediate(4, 0, 0, 0)], [0x0c000000, 0]):
            with self.assertRaises(ValueError): self.execute(words)

    def test_fetch_and_memory_bounds(self):
        with self.assertRaises(ValueError): self.execute([0])
        for address in (0x1001, 0x1004):
            with self.assertRaises(ValueError): self.execute([immediate(35, 4, 2, 0)] + RETURN_WORDS, {4: address}, [(0x1000, b'1234')])

    def test_overlaps_empty_code_and_bad_alignment(self):
        for blob, entry, blocks in [(b'', ENTRY, []), (b'X', ENTRY, []), (code(RETURN_WORDS), ENTRY + 1, []), (code(RETURN_WORDS), ENTRY, [(ENTRY, b'X')])]:
            with self.assertRaises(ValueError): ReadOnlyMips(blob, entry, blocks)

    def test_noncanonical_and_store_reject(self):
        for word in (immediate(15, 1, 2, 3), register(0, 1, 2, 3), register(0x21, 1, 2, 3, 1), immediate(43, 4, 2, 0), register(8, 31, 1, 0)):
            with self.assertRaises(ValueError): self.execute([word] + RETURN_WORDS)

    def test_object_fixture_field_flag(self):
        toy = code([immediate(35, 4, 2, 0x4c)] + RETURN_WORDS)
        for enabled in (0, 1):
            self.assertEqual(lookup(toy, [0x8100, 0x8200], [256, 300], b'\x81\x00', enabled=enabled)['return_u32'], enabled)

    def test_truncated_input_read_reject(self):
        toy = code([immediate(36, 5, 2, 1)] + RETURN_WORDS)
        with self.assertRaisesRegex(ValueError, 'unmapped'): lookup(toy, [0x8100, 0x8200], [256, 300], b'\x81')

    def test_invalid_fixture_and_registers(self):
        for ranges, bases, encoded in [([1], [1], b'A'), ([1, 2], [1], b'A'), ([1, 65536], [1, 2], b'A'), ([1, 2], [1, 2], b'')]:
            with self.assertRaises(ValueError): lookup(code(RETURN_WORDS), ranges, bases, encoded)
        with self.assertRaises(ValueError): self.execute(RETURN_WORDS, {32: 0})


if __name__ == '__main__': unittest.main()
