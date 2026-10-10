import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from audit_vif_contexts import annotate, packet, packet_block, unpack_size
from font_poc import digest


class VifContextTests(unittest.TestCase):
    def sample(self):
        return struct.pack('<4I', 0x60000007, 0, 0x01000101, 0x6c068000) + bytes(96) + struct.pack('<4I', 0, 0, 0x17000000, 0)

    def mutate(self, offset, value):
        data = bytearray(self.sample())
        struct.pack_into('<I', data, offset, value)
        return bytes(data)

    def row(self, data, start, size, category='unresolved-byte-context'):
        return dict(id='fixture', offset=start, bytes=size, source_sha256=digest(data[start:start+size]), category=category)

    def test_complete_packet(self):
        p = packet(self.sample(), 0, 128)
        self.assertEqual((p['end'], p['qwc'], len(p['commands'])), (128, 7, 6))
    def test_tag_truncated(self):
        with self.assertRaises(ValueError): packet(bytes(15), 0, 15)
    def test_wrong_tag_id(self):
        with self.assertRaises(ValueError): packet(self.mutate(0, 0x70000007), 0, 128)
    def test_tag_reserved_bits(self):
        with self.assertRaises(ValueError): packet(self.mutate(0, 0x60010007), 0, 128)
    def test_tag_address(self):
        with self.assertRaises(ValueError): packet(self.mutate(4, 4), 0, 128)
    def test_qwc_overrun(self):
        with self.assertRaises(ValueError): packet(self.mutate(0, 0x60000008), 0, 128)
    def test_negative_start(self):
        with self.assertRaises(ValueError): packet(self.sample(), -1, 128)
    def test_limit_past_eof(self):
        with self.assertRaises(ValueError): packet(self.sample(), 0, 129)
    def test_zero_qwc(self):
        with self.assertRaises(ValueError): packet(self.mutate(0, 0x60000000), 0, 128)
    def test_unreviewed_command(self):
        with self.assertRaises(ValueError): packet(self.mutate(112, 0x02000000), 0, 128)
    def test_unpack_before_cycle(self):
        with self.assertRaises(ValueError): packet(self.mutate(8, 0x6c068000), 0, 128)
    def test_unpack_overrun(self):
        with self.assertRaises(ValueError): packet(self.mutate(12, 0x6cff8000), 0, 128)
    def test_interrupt(self):
        with self.assertRaises(ValueError): packet(self.mutate(8, 0x81000101), 0, 128)
    def test_cycle_reserved_num(self):
        with self.assertRaises(ValueError): packet(self.mutate(8, 0x01010101), 0, 128)
    def test_nop_reserved_bits(self):
        with self.assertRaises(ValueError): packet(self.mutate(112, 1), 0, 128)
    def test_missing_mscnt(self):
        with self.assertRaises(ValueError): packet(self.mutate(120, 0), 0, 128)
    def test_v4_32(self): self.assertEqual(unpack_size(0x6c068000, 1, 1)['raw_bytes'], 96)
    def test_v3_8_padding(self): self.assertEqual(unpack_size(0x6a038000, 4, 1)['padded_bytes'], 12)
    def test_v2_32(self): self.assertEqual(unpack_size(0x64038000, 4, 1)['raw_bytes'], 24)
    def test_masked_scalar(self): self.assertTrue(unpack_size(0x71308000, 1, 1)['masked'])
    def test_num_zero(self): self.assertEqual(unpack_size(0x6c008000, 1, 1)['num'], 256)
    def test_wl_zero_fill(self): self.assertEqual(unpack_size(0x6c008000, 1, 0)['input_vectors'], 1)
    def test_cl_zero(self): self.assertEqual(unpack_size(0x6c068000, 0, 1)['input_vectors'], 0)
    def test_fill_mode(self): self.assertEqual(unpack_size(0x6c068000, 2, 4)['input_vectors'], 4)
    def test_v4_5(self): self.assertEqual(unpack_size(0x6f038000, 1, 1)['padded_bytes'], 8)
    def test_reserved_format(self):
        with self.assertRaises(ValueError): unpack_size(0x63018000, 1, 1)
    def test_not_unpack(self):
        with self.assertRaises(ValueError): unpack_size(0x01000101, 1, 1)
    def test_cycle_bounds(self):
        with self.assertRaises(ValueError): unpack_size(0x6c068000, 256, 1)
    def block(self, count=1, size=144): return struct.pack('<5I', size, count, 159, 199, 187) + self.sample()
    def test_block_complete(self): self.assertEqual(packet_block(self.block(), 0, 148)['packet_count'], 1)
    def test_block_wrong_size(self):
        with self.assertRaises(ValueError): packet_block(self.block(size=145), 0, 148)
    def test_block_wrong_count(self):
        with self.assertRaises(ValueError): packet_block(self.block(count=2), 0, 148)
    def test_block_zero_count(self):
        with self.assertRaises(ValueError): packet_block(self.block(count=0), 0, 148)
    def test_block_truncated(self):
        with self.assertRaises(ValueError): packet_block(self.block()[:-1], 0, 147)
    def test_opaque_header_preserved(self): self.assertEqual(packet_block(self.block(), 0, 148)['opaque_header_words'], [159,199,187])
    def test_candidate_payload(self):
        data = self.sample(); r = self.row(data, 16, 4)
        z = annotate(data, [r], packet(data, 0, 128)['spans'])[0]
        self.assertEqual(z['category'], 'verified-vif-unpack-input'); self.assertFalse(z['editable'])
    def test_candidate_boundary(self):
        data = self.sample(); r = self.row(data, 14, 4)
        self.assertEqual(annotate(data, [r], packet(data,0,128)['spans'])[0]['category'], 'verified-vif-composite-boundary-context')
    def test_candidate_hash_mismatch(self):
        r = self.row(self.sample(), 16, 4); r['source_sha256'] = 'wrong'
        with self.assertRaises(ValueError): annotate(self.sample(), [r], packet(self.sample(),0,128)['spans'])
    def test_existing_category_preserved(self):
        r = self.row(self.sample(), 16, 4, 'existing')
        self.assertEqual(annotate(self.sample(), [r], packet(self.sample(),0,128)['spans'])[0], r)
    def test_uncovered_preserved(self):
        data = self.sample(); r = self.row(data,0,4)
        self.assertEqual(annotate(data,[r],[dict(start=8,end=128)])[0], r)
    def test_candidate_zero_length(self):
        with self.assertRaises(ValueError): annotate(self.sample(), [self.row(self.sample(),16,0)], [])


if __name__ == '__main__': unittest.main()
