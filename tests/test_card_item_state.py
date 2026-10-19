import hashlib
from pathlib import Path
import struct
import sys
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from repair_card_item import compact, unpack_blocks, pack_blocks, remove_item


class CardItemTests(unittest.TestCase):
    def fixture(self, rows=None):
        rows = rows or [(3, 9), (497, 1), (11, 2)]
        inventory = b''.join(struct.pack('<ii', *r) for r in rows)
        raw = struct.pack('<I', 43)+b'FLAGS!'+compact(len(rows))+inventory+b'OTHER FIELDS'*2000
        blob = pack_blocks(raw)
        h = lambda b: hashlib.sha256(b).hexdigest()
        profile = dict(schema=1, save_sha256=h(blob), unpacked_sha256=h(raw),
                       version=43, count_offset=10, count=len(rows), index=1,
                       item_id=497, quantity=1, inventory_sha256=h(inventory))
        return blob, raw, profile

    def test_compact_boundaries(self):
        for number, expected in [(0,b'\0'),(63,b'\x3f'),(64,b'\x40\x01'),
                                 (287,b'\x5f\x04'),(288,b'\x60\x04')]:
            self.assertEqual(compact(number), expected)
        with self.assertRaises(ValueError): compact(-1)

    def test_block_roundtrip(self):
        for size in [1, 20480, 20481, 40960]:
            raw = bytes(range(256))*(size//256)+b'X'*(size%256)
            self.assertEqual(unpack_blocks(pack_blocks(raw)), raw)

    def test_removal_preserves_every_other_serialized_byte(self):
        blob, raw, profile = self.fixture()
        updated = unpack_blocks(remove_item(blob, profile))
        self.assertEqual(updated, raw[:10]+compact(2)+raw[11:19]+raw[27:])
        self.assertEqual(len(updated), len(raw)-8)

    def test_count_header_shrink(self):
        rows = [(j+1000,1) for j in range(64)]; rows[1]=(497,1)
        blob, raw, profile = self.fixture(rows)
        updated = unpack_blocks(remove_item(blob, profile))
        self.assertEqual(updated, raw[:10]+compact(63)+raw[12:20]+raw[28:])

    def test_wrong_input_hash(self):
        blob, _, profile = self.fixture(); profile['save_sha256']='0'*64
        with self.assertRaises(ValueError): remove_item(blob,profile)

    def test_wrong_quantity(self):
        blob, _, profile = self.fixture(); profile['quantity']=2
        with self.assertRaises(ValueError): remove_item(blob,profile)

    def test_duplicate_item(self):
        blob, _, profile = self.fixture([(497,1),(497,1)])
        with self.assertRaises(ValueError): remove_item(blob,profile)

    def test_truncated_or_trailing_stream(self):
        blob, _, _ = self.fixture()
        for bad in [b'',blob[:-1],blob+b'X']:
            with self.assertRaises((ValueError, zlib.error)): unpack_blocks(bad)

    def test_wrong_version_and_inventory_hash(self):
        blob, _, profile = self.fixture()
        for key, value in [('version',44),('inventory_sha256','0'*64)]:
            changed=dict(profile);changed[key]=value
            with self.assertRaises(ValueError): remove_item(blob,changed)


if __name__ == '__main__':
    unittest.main()
