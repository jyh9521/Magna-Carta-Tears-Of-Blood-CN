import sys
import struct
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_stream_texture import stream_mips


def fixture(order='pixels-before-dimensions',lazy=122,width=4,height=4):
    pixels=bytes(range(16));dims=struct.pack('<IIBB',width,height,2,2)
    fields=bytes([16])+pixels
    return b'\x01'+struct.pack('<I',lazy)+(fields+dims if order=='pixels-before-dimensions' else dims+fields)


class StreamTextureTests(unittest.TestCase):
    def test_source_order(self):self.assertEqual(stream_mips(fixture(),0,100)[0]['order'],'pixels-before-dimensions')
    def test_projected_order(self):self.assertEqual(stream_mips(fixture('dimensions-before-pixels'),0,100)[0]['order'],'dimensions-before-pixels')
    def test_pixel_identity(self):self.assertEqual(stream_mips(fixture(),0,100)[0]['raw'],bytes(range(16)))
    def test_trailing(self):
        with self.assertRaises(ValueError):stream_mips(fixture()+b'\0',0,100)
    def test_lazy_mismatch(self):
        with self.assertRaises(ValueError):stream_mips(fixture(lazy=123),0,100)
    def test_dimension_mismatch(self):
        with self.assertRaises(ValueError):stream_mips(fixture(width=5),0,100)
    def test_truncated(self):
        with self.assertRaises(ValueError):stream_mips(fixture()[:-1],0,100)
    def test_zero_count(self):
        with self.assertRaises(ValueError):stream_mips(b'\0',0,100)
    def test_count_limit(self):
        with self.assertRaises(ValueError):stream_mips(b'\x11',0,100)
    def test_nonzero_start(self):self.assertEqual(stream_mips(b'prefix'+fixture(lazy=128),6,100)[0]['width'],4)


if __name__=='__main__':unittest.main()
