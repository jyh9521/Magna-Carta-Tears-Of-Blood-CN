import sys
import struct
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_native_text_loaders import descriptor, chain, loader


class DescriptorTests(unittest.TestCase):
    def fixture(self, dimension=1):
        return b'\0\0\x02'+struct.pack('<II',dimension,0x400000)+b'\0'

    def test_exact_scalar(self):
        row=descriptor(self.fixture(),['None'],'StrProperty')
        self.assertEqual((row['next_reference'],row['dimension'],row['flags']),(2,1,0x400000))

    def test_truncated(self):
        with self.assertRaises(ValueError): descriptor(self.fixture()[:-1],['None'],'StrProperty')

    def test_extra_bytes(self):
        with self.assertRaisesRegex(ValueError,'unparsed'): descriptor(self.fixture()+b'\0',['None'],'StrProperty')

    def test_dimension(self):
        with self.assertRaisesRegex(ValueError,'dimension'): descriptor(self.fixture(2),['None'],'StrProperty')

    def test_defaults(self):
        with self.assertRaisesRegex(ValueError,'defaults'): descriptor(self.fixture(),['Something'],'StrProperty')

    def test_chain(self):
        rows={1:dict(outer=8,next_reference=2),2:dict(outer=8,next_reference=0)}
        self.assertEqual(chain(rows,1,8),[rows[1],rows[2]])

    def test_cycle(self):
        with self.assertRaisesRegex(ValueError,'cycle'): chain({1:dict(outer=8,next_reference=1)},1,8)

    def test_owner(self):
        with self.assertRaisesRegex(ValueError,'owner'): chain({1:dict(outer=9,next_reference=0)},1,8)

    def test_missing_reference(self):
        with self.assertRaisesRegex(ValueError,'missing'): chain({},1,8)

    def test_wrong_loader_word_rejected(self):
        class Image:
            blob=bytes(32)
            def to_offset(self,va):return va-0x1000
        with self.assertRaisesRegex(ValueError,'instruction mismatch'):
            loader(Image(),0x1000,0x4b7810,0x148,'00001239.tui')


if __name__=='__main__': unittest.main()
