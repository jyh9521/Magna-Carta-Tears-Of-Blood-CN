import hashlib
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from repair_event_item_state import remove_bound_item


class EventItemStateTests(unittest.TestCase):
    def fixture(self, rows=None, selected=1):
        rows = rows or [(3, 9), (497, 1), (11, 2)]
        memory = bytearray(256)
        struct.pack_into('<III', memory, 16, 64, len(rows), 8)
        for j, row in enumerate(rows):
            struct.pack_into('<ii', memory, 64+j*8, *row)
        memory[200:204] = b'GSW!'
        memory = bytes(memory)
        profile = dict(schema=1, memory_sha256=hashlib.sha256(memory).hexdigest(),
                       inventory_array_offset=16, inventory_data_offset=64,
                       inventory_count=len(rows), inventory_index=selected,
                       item_id=497, expected_quantity=1)
        return memory, profile

    def test_remove_middle_and_preserve_flags(self):
        memory, profile = self.fixture()
        result = remove_bound_item(memory, profile)
        self.assertEqual(struct.unpack_from('<III', result, 16), (64, 2, 8))
        self.assertEqual(struct.unpack_from('<4i', result, 64), (3, 9, 11, 2))
        self.assertEqual(result[200:204], b'GSW!')
        self.assertEqual(result[80:], memory[80:])

    def test_remove_last(self):
        memory, profile = self.fixture([(3, 9), (497, 1)])
        result = remove_bound_item(memory, profile)
        self.assertEqual(result[64:], memory[64:])
        self.assertEqual(struct.unpack_from('<I', result, 20)[0], 1)

    def test_wrong_hash(self):
        memory, profile = self.fixture()
        profile['memory_sha256'] = '0'*64
        with self.assertRaises(ValueError): remove_bound_item(memory, profile)

    def test_duplicate_key_rejected(self):
        memory, profile = self.fixture([(497, 1), (497, 1)], 0)
        with self.assertRaises(ValueError): remove_bound_item(memory, profile)

    def test_wrong_quantity_rejected(self):
        memory, profile = self.fixture([(3, 9), (497, 2)])
        with self.assertRaises(ValueError): remove_bound_item(memory, profile)

    def test_wrong_array_rejected(self):
        memory, profile = self.fixture()
        profile['inventory_data_offset'] = 68
        with self.assertRaises(ValueError): remove_bound_item(memory, profile)

    def test_wrong_index_rejected(self):
        memory, profile = self.fixture()
        profile['inventory_index'] = 0
        with self.assertRaises(ValueError): remove_bound_item(memory, profile)

    def test_unknown_schema_rejected(self):
        memory, profile = self.fixture()
        profile['schema'] = 2
        with self.assertRaises(ValueError): remove_bound_item(memory, profile)


if __name__ == '__main__':
    unittest.main()
