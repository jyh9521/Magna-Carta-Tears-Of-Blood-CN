"""Synthetic append-only Font resource tests; no original game fixtures."""
from pathlib import Path
import hashlib
import struct
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'src')]
from font_resource import append_font, encode_compact, parts, verify_append
from research_inventory import compact
from localization.text import MappedEncoder


def fixture():
    return bytes(3) + struct.pack('<6I',1,1,2,2,3,1) + encode_compact(4) + b'\x12\x23\x34\x45' + encode_compact(2) + b'\x02\x03' + encode_compact(2) + struct.pack('<2H',0x8000,0x8002) + encode_compact(2) + struct.pack('<2H',0,2) + b'opaque-tail'


def sha(data): return hashlib.sha256(data).hexdigest()


class FontResourceTests(unittest.TestCase):
    def build(self, serial=None, bitmap=b'\x55\x55', metrics=b'\x03', start=0x9001):
        serial = fixture() if serial is None else serial
        return append_font(serial,bitmap,metrics,start,expected_sha256=sha(serial))
    def test_compact_boundaries(self):
        for value in (0,1,63,64,8191,8192,0x7fffffff):
            blob=encode_compact(value);self.assertEqual(compact(blob,0),(value,len(blob)))
    def test_compact_invalid(self):
        for value in (-1,0x80000000,'1'):
            with self.assertRaises(ValueError):encode_compact(value)
    def test_append_arrays(self):
        info,b,m,t=parts(self.build());self.assertEqual(info['glyphs'],3)
        self.assertEqual(b,b'\x12\x23\x34\x45\x55\x55');self.assertEqual(m,b'\x02\x03\x03');self.assertEqual(t,b'opaque-tail')
    def test_mapping_and_empty_gap(self):
        info,*_=parts(self.build());self.assertEqual(info['ranges'],[0x8000,0x8002,0x9001,0x9002]);self.assertEqual(info['bases'],[0,2,2,3])
    def test_multi_glyph_append(self):
        info,*_=parts(self.build(bitmap=b'\x55'*4,metrics=b'\x01\x02'));self.assertEqual(info['glyphs'],4)
    def test_fingerprint_required(self):
        with self.assertRaisesRegex(ValueError,'fingerprint'):append_font(fixture(),b'\x55\x55',b'\x03',0x9001,expected_sha256='0'*64)
    def test_bitmap_cardinality(self):
        with self.assertRaisesRegex(ValueError,'count mismatch'):self.build(bitmap=b'\x55')
    def test_empty_append(self):
        with self.assertRaises(ValueError):self.build(bitmap=b'',metrics=b'')
    def test_metric_overflow(self):
        with self.assertRaisesRegex(ValueError,'metric'):self.build(metrics=b'\x04')
    def test_code_overlap(self):
        for start in (0x7fff,0x8000,0x8002):
            with self.assertRaises(ValueError):self.build(start=start)
    def test_code_overflow(self):
        with self.assertRaises(ValueError):self.build(start=65535)
    def test_code_nul(self):
        with self.assertRaisesRegex(ValueError,'NUL'):self.build(start=0x9000)
    def test_truncated_input(self):
        with self.assertRaises(ValueError):self.build(serial=fixture()[:20])
    def test_original_metric_tampering(self):
        result=bytearray(self.build());info,*_=parts(result);result[info['metrics_start']]=1
        with self.assertRaisesRegex(ValueError,'original'):verify_append(fixture(),bytes(result),1,0x9001)
    def test_unknown_tail_tampering(self):
        result=self.build()[:-1]+b'X'
        with self.assertRaisesRegex(ValueError,'tail'):verify_append(fixture(),result,1,0x9001)
    def test_uint16_glyph_capacity(self):
        n=65535;serial=bytes(3)+struct.pack('<6I',1,1,n,1,1,1)+encode_compact(n)+bytes(n)+encode_compact(n)+bytes(n)+encode_compact(2)+struct.pack('<2H',0,65535)+encode_compact(2)+struct.pack('<2H',0,65535)
        with self.assertRaisesRegex(ValueError,'capacity'):self.build(serial=serial,bitmap=b'\x00',metrics=b'\x01')
    def test_explicit_mapping_encoder(self):
        info,*_=parts(self.build());entries=[dict(character='测',bytes='9001',glyph=2)]
        self.assertEqual(MappedEncoder(entries,font_tables=info).encode('测$nABC'),b'\x90\x01$nABC')
    def test_legacy_encoder_stays_strict(self):
        with self.assertRaises(ValueError):MappedEncoder([dict(character='测',bytes='9001',glyph=2)])
    def test_explicit_mapping_wrong_index(self):
        info,*_=parts(self.build())
        with self.assertRaises(ValueError):MappedEncoder([dict(character='测',bytes='9001',glyph=1)],font_tables=info)
    def test_explicit_mapping_gap(self):
        info,*_=parts(self.build())
        with self.assertRaises(ValueError):MappedEncoder([dict(character='测',bytes='9002',glyph=3)],font_tables=info)
    def test_explicit_mapping_bad_table(self):
        info,*_=parts(self.build());info['bases'][-1]=4
        with self.assertRaises(ValueError):MappedEncoder([],font_tables=info)
    def test_geometry_preserved(self):
        result=self.build();self.assertEqual(result[:11],fixture()[:11]);self.assertEqual(result[15:27],fixture()[15:27])


if __name__ == '__main__':unittest.main()
