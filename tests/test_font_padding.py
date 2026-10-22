import sys,unittest
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'tools')]
from sanitize_font_padding import sanitize
from research_inventory import font_data
from overlay_font_resources import check_font_compatibility

class PaddingTests(unittest.TestCase):
    def setUp(self):
        # Existing fixture builder retains real custom Font geometry.
        import struct
        from font_resource import encode_compact as compact_encode
        self.raw=b'\0\0\0'+struct.pack('<6I',0,0,2667,2,19,5)+compact_encode(2667*10)+bytes([255])*(2667*10)+compact_encode(2667)+bytes([11])*2667+compact_encode(1)+b'\0\0'+compact_encode(1)+b'\0\0'
    def test_only_padding_changes(self):
        new,proof=sanitize(self.raw);i=font_data(new)
        self.assertEqual(i,font_data(self.raw));self.assertTrue(proof['effective_ink_preserved'])
        at=i['bitmap_start'];self.assertEqual(new[at:at+5],b'\xff\xff\x3f\0\0')
    def test_idempotent(self):
        new,_=sanitize(self.raw);again,p=sanitize(new);self.assertEqual(new,again);self.assertEqual(p['cleared_padding_pixels'],0)
    def test_strict_rejects_padding_changes(self):
        new,_=sanitize(self.raw)
        with self.assertRaises(ValueError):check_font_compatibility(self.raw,new)
        check_font_compatibility(self.raw,new,padding_cleanup=True)
    def test_effective_ink_tampering_rejected(self):
        new,_=sanitize(self.raw);new=bytearray(new);new[font_data(new)['bitmap_start']]=0
        with self.assertRaises(ValueError):check_font_compatibility(self.raw,bytes(new),padding_cleanup=True)
    def test_metric_bounds(self):
        i=font_data(self.raw);bad=bytearray(self.raw);bad[i['metrics_start']]=20
        with self.assertRaises(ValueError):sanitize(bytes(bad))
