"""Synthetic ELF/MIPS checks; no original executable is required."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from research_native import (ElfImage, pair_candidates, analyze, local_window, trace_call,
                             classify_va, read_u32, reginfo_gp, constant_store_candidates, table_audit)


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

    def trace(self, words, index, max_back=8):
        body = struct.pack(f'<{len(words)}I', *words)
        return trace_call(ElfImage(self.elf(body, max(64, len(body)))), 0x100000 + index * 4, max_back)

    def test_indirect_delay_argument(self):
        r = self.trace([0x8e990000, 0x0280202d, 0x27a50060, 0x8f390014, 0x0320f809, 0x24060100], 4)
        self.assertEqual(r['kind'], 'JALR')
        self.assertEqual(r['target_before_delay']['expression'], 'load32(load32(entry_r20 + 0) + 20)')
        self.assertEqual(r['argument_registers']['4']['expression'], 'entry_r20')
        self.assertEqual(r['argument_registers']['5']['expression'], '(entry_r29 + 96)')
        self.assertEqual(r['argument_registers']['6']['known_u32'], 256)
        self.assertEqual(r['argument_registers']['6']['definitions'], [0x100014])

    def test_direct_delay_argument(self):
        r = self.trace([0x0c040010, 0x24060100], 0)
        self.assertEqual(r['target_before_delay']['known_u32'], 0x100040)
        self.assertEqual(r['argument_registers']['6']['known_u32'], 256)

    def test_delay_clobbers_previous_argument(self):
        r = self.trace([0x24060100, 0x0c040010, 0x24060004], 1)
        self.assertEqual(r['argument_registers']['6']['known_u32'], 4)

    def test_load_clobbers_constant(self):
        r = self.trace([0x24060100, 0x8fa60000, 0x0c040010, 0], 2)
        self.assertIsNone(r['argument_registers']['6']['known_u32'])

    def test_earlier_call_and_delay_not_inherited(self):
        r = self.trace([0x0c040010, 0x24060100, 0x0c040020, 0], 2)
        self.assertEqual(r['boundary'], 'earlier_transfer_and_delay_excluded')
        self.assertEqual(r['start_va'], 0x100008)
        self.assertIsNone(r['argument_registers']['6']['known_u32'])

    def test_earlier_branch_delay_not_inherited(self):
        r = self.trace([0x10000001, 0x24060100, 0x0c040020, 0], 2)
        self.assertEqual(r['start_va'], 0x100008)
        self.assertIsNone(r['argument_registers']['6']['known_u32'])

    def test_unknown_barrier(self):
        r = self.trace([0x24060100, 0xe8000000, 0x0c040020, 0], 2)
        self.assertEqual(r['boundary'], 'unsupported_instruction')
        self.assertIsNone(r['argument_registers']['6']['known_u32'])

    def test_unknown_delay_suppresses_arguments(self):
        r = self.trace([0x0c040020, 0xe8000000], 0)
        self.assertFalse(r['delay_supported'])
        self.assertEqual(r['argument_registers'], {})

    def test_store_keeps_argument(self):
        r = self.trace([0x24060100, 0xffbf0050, 0x0c040020, 0], 2)
        self.assertEqual(r['argument_registers']['6']['known_u32'], 256)

    def test_zero_register_write_ignored(self):
        r = self.trace([0x24000100, 0x0c040020, 0x24060004], 1)
        self.assertEqual(r['argument_registers']['6']['known_u32'], 4)

    def test_signed_immediate_low32(self):
        r = self.trace([0x2406ffff, 0x0c040020, 0], 1)
        self.assertEqual(r['argument_registers']['6']['known_u32'], 0xffffffff)

    def test_link_visible_in_delay(self):
        r = self.trace([0x0c040020, 0x27e40000], 0)
        self.assertEqual(r['argument_registers']['4']['known_u32'], 0x100008)

    def test_bound_excludes_old_definition(self):
        r = self.trace([0x24060100, 0, 0x0c040020, 0], 2, 1)
        self.assertIsNone(r['argument_registers']['6']['known_u32'])

    def test_invalid_trace_inputs(self):
        for words, index, bound in [([0, 0], 0, 8), ([0x0c040020], 0, 8), ([0x0c040020, 0], 0, 0), ([0x0c040020, 0], 0, 33), ([0x03201009, 0], 0, 8)]:
            with self.assertRaises(ValueError): self.trace(words, index, bound)

    def test_window_includes_indirect_calls(self):
        words = [0x0320f809, 0x24060100]
        e = ElfImage(self.elf(struct.pack('<2I', *words)))
        r = local_window(e, 0x100000)
        self.assertEqual(len(r['call_argument_candidates']), 1)
        self.assertEqual(r['call_argument_candidates'][0]['kind'], 'JALR')

    def test_target_captured_before_delay_overwrite(self):
        r = self.trace([0x24191234, 0x0320f809, 0x24195678], 1)
        self.assertEqual(r['target_before_delay']['known_u32'], 0x1234)

    def test_lui_ori_and_addu(self):
        r = self.trace([0x3c05004b, 0x34a57990, 0x00a03021, 0x0c040020, 0], 3)
        self.assertEqual(r['argument_registers']['6']['known_u32'], 0x4b7990)

    def test_non_move_daddu_is_barrier(self):
        r = self.trace([0x24060100, 0x00a6302d, 0x0c040020, 0], 2)
        self.assertEqual(r['boundary'], 'unsupported_instruction')
        self.assertIsNone(r['argument_registers']['6']['known_u32'])

    def test_region_classification(self):
        e = ElfImage(self.elf())
        self.assertEqual(classify_va(e, 0x100000), 'file_backed')
        self.assertEqual(classify_va(e, 0x100020), 'memory_only')
        self.assertEqual(classify_va(e, 0x100040), 'unmapped_or_ambiguous')

    def test_read_word_requires_complete_file_mapping(self):
        e = ElfImage(self.elf(b'\x01\x02\x03\x04X'))
        self.assertEqual(read_u32(e, 0x100000), 0x04030201)
        for va in (0x100001, 0x100004, 0x100020):
            with self.assertRaises(ValueError): read_u32(e, va)

    def gp_image(self, body, gp=0x100000, memsize=128):
        body += struct.pack('<6I', 0, 0, 0, 0, 0, gp)
        e = ElfImage(self.elf(body, memsize))
        e.sections = [dict(type=0x70000006, size=24, offset=len(e.blob) - 24)]
        return e

    def test_reginfo_declared_gp(self):
        self.assertIsNone(reginfo_gp(ElfImage(self.elf())))
        e = self.gp_image(bytes(64), 0x5437f0)
        self.assertEqual(reginfo_gp(e), 0x5437f0)

    def test_reginfo_size_and_duplicates_reject(self):
        e = self.gp_image(bytes(64)); e.sections *= 2
        with self.assertRaises(ValueError): reginfo_gp(e)
        e.sections = e.sections[:1]; e.sections[0]['size'] = 20
        with self.assertRaises(ValueError): reginfo_gp(e)

    def test_constant_store_chain(self):
        r = constant_store_candidates([0x3c030050, 0x2463e390, 0xac400004, 0xac430000], {0x4fe390})
        self.assertEqual(len(r), 1)
        self.assertEqual((r[0]['store_word'], r[0]['base_register'], r[0]['displacement']), (3, 2, 0))

    def test_store_chain_clobber_and_unknown_reject(self):
        for w in (0x24030001, 0x8fa30000, 0xe8000000, 0x10000001, 0x0c040020):
            self.assertEqual(constant_store_candidates([0x3c030050, 0x2463e390, w, 0xac430000], {0x4fe390}), [])

    def test_store_chain_bound(self):
        words = [0x3c030050, 0x2463e390, 0, 0xac430000]
        self.assertEqual(constant_store_candidates(words, {0x4fe390}, 1), [])
        for bound in (0, 33):
            with self.assertRaises(ValueError): constant_store_candidates(words, {0x4fe390}, bound)

    def test_store_chain_call_delay_not_carried(self):
        self.assertEqual(constant_store_candidates([0x3c030050, 0x0c040020, 0x2463e390, 0xac430000], {0x4fe390}), [])

    def test_table_word_metadata_not_function_identity(self):
        body = struct.pack('<16I', *([0x100060] + [0] * 15))
        r = table_audit(ElfImage(self.elf(body, 128)), [0x100000], [])
        self.assertEqual(r['tables'][0]['words'][0]['value_region'], 'memory_only')
        self.assertEqual(len(r['tables'][0]['words']), 16)
        self.assertIn('object identity', r['evidence'])

    def test_table_alignment_and_span_reject(self):
        for va in (0x100001, 0x100004):
            with self.assertRaises(ValueError): table_audit(ElfImage(self.elf(bytes(64), 128)), [va], [])

    def test_gp_slot_load_store_and_initial_pointer(self):
        body = bytearray(64)
        struct.pack_into('<3I', body, 0, 0x100060, 0x8f840000, 0xaf8a0000)
        r = table_audit(self.gp_image(bytes(body)), [], [0])['gp_slots'][0]
        self.assertEqual(r['initial_file_word'], 0x100060)
        self.assertEqual(r['initial_word_region'], 'memory_only')
        self.assertEqual(r['load_candidates'], [dict(va=0x100004, register=4)])
        self.assertEqual(r['store_candidates'], [dict(va=0x100008, register=10)])

    def test_gp_memory_only_slot_never_synthesizes_zero(self):
        r = table_audit(self.gp_image(bytes(64)), [], [96])['gp_slots'][0]
        self.assertEqual(r['region'], 'memory_only')
        self.assertIsNone(r['initial_file_word'])

    def test_gp_signed_displacement(self):
        e = self.gp_image(struct.pack('<I', 0x8f84fff0) + bytes(60), 0x100010)
        r = table_audit(e, [], [-16])['gp_slots'][0]
        self.assertEqual(r['slot_va'], 0x100000)
        self.assertEqual(r['load_candidates'][0]['va'], 0x100000)

    def test_selection_validation(self):
        e = self.gp_image(bytes(64))
        for tables, disps in [([], [32768]), ([], [-32769]), ([0x100000]*17, []), ([], [0]*17)]:
            with self.assertRaises(ValueError): table_audit(e, tables, disps)
        with self.assertRaises(ValueError): table_audit(ElfImage(self.elf()), [], [0])

    def test_table_store_report_va_mapping(self):
        words = [0x3c030010, 0x24630040, 0xac430000] + [0]*29
        r = table_audit(ElfImage(self.elf(struct.pack('<32I', *words), 128)), [0x100040], [])
        c = r['tables'][0]['constant_store_candidates'][0]
        self.assertEqual((c['upper_va'], c['lower_va'], c['store_va']), (0x100000, 0x100004, 0x100008))


if __name__ == '__main__': unittest.main()
