"""Synthetic ELF/MIPS checks; no original executable is required."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from research_native import ElfImage, pair_candidates, analyze, local_window


class NativeResearchTests(unittest.TestCase):
    def elf(self, body=b"A" * 32, memsize=64):
        b = bytearray(128 + len(body)); b[:7] = b'\x7fELF\x01\x01\x01'
        struct.pack_into('<HHIIIIIHHHHHH', b, 16, 2, 8, 1, 0x100000, 52, 0, 0, 52, 32, 1, 40, 0, 0)
        struct.pack_into('<8I', b, 52, 1, 128, 0x100000, 0x100000, len(body), memsize, 7, 128)
        b[128:] = body
        return bytes(b)

    def test_bidirectional_mapping(self):
        e = ElfImage(self.elf()); self.assertEqual(e.to_va(132), 0x100004)
        self.assertEqual(e.to_offset(0x100004), 132)

    def test_bss_is_not_file_bytes(self):
        with self.assertRaises(ValueError): ElfImage(self.elf()).to_offset(0x100020)

    def test_header_and_segment_bounds(self):
        for blob in (b'ELF', self.elf()[:100], self.elf(memsize=1)):
            with self.assertRaises(ValueError): ElfImage(blob)

    def test_wrong_endian_or_machine(self):
        for offset, value in ((5, 2), (18, 3)):
            b = bytearray(self.elf()); b[offset] = value
            with self.assertRaises(ValueError): ElfImage(bytes(b))

    def test_signed_addiu(self):
        r = pair_candidates([0x3c05004c, 0x24a58000], {0x4b8000})
        self.assertEqual(r[0]['address'], 0x4b8000)

    def test_ori_is_zero_extended(self):
        self.assertEqual(pair_candidates([0x3c05004b, 0x34a58000], {0x4b8000})[0]['operation'], 'ORI')

    def test_register_clobber_rejects(self):
        self.assertEqual(pair_candidates([0x3c05004b, 0x24050001, 0x24a57990], {0x4b7990}), [])

    def test_store_does_not_clobber(self):
        self.assertEqual(len(pair_candidates([0x3c05004b, 0xffbf0050, 0x24a57990], {0x4b7990})), 1)

    def test_call_delay_slot_only(self):
        r = pair_candidates([0x3c05004b, 0x0c0685bc, 0x24a57990], {0x4b7990})
        self.assertTrue(r[0]['delay_slot'])
        self.assertEqual(pair_candidates([0x3c05004b, 0x0c0685bc, 0, 0x24a57990], {0x4b7990}), [])

    def test_branch_unknown_and_zero_register_reject(self):
        for words in ([0x3c05004b, 0x10000001, 0x24a57990], [0x3c05004b, 0xe8000000, 0x24a57990], [0x3c00004b, 0x24007990]):
            self.assertEqual(pair_candidates(words, {0x4b7990}), [])

    def test_selected_strings_and_pointer_words(self):
        body = b'UFontObj\0' + bytes(3) + struct.pack('<I', 0x100000)
        report = analyze(self.elf(body))
        self.assertEqual(report['strings'][0]['pointer_words'], [0x10000c])
        self.assertEqual(report['symbol_entries'], 0)

    def test_local_window_constants_and_call_target(self):
        body = struct.pack('<III', 0x24060100, 0x0c040010, 0)
        result = local_window(ElfImage(self.elf(body)), 0x100000)
        self.assertEqual(result['span_bytes'], 12)
        self.assertEqual(result['direct_jal_candidates'][0]['target'], 0x100040)
        self.assertEqual(result['addiu_zero_size_candidates'][0]['immediate'], 256)
        self.assertFalse(result['function_boundary_verified'])


if __name__ == '__main__': unittest.main()
