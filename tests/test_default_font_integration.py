import json, struct, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'src'),str(ROOT/'lib')]
from font_resource import encode_compact
from research_inventory import font_data
from overlay_font_resources import check_font_compatibility


def fixture():
    n=2668
    return bytes(3)+struct.pack('<6I',1,1,n,2,3,1)+encode_compact(n*2)+bytes(n*2)+encode_compact(n)+bytes([3])*n+encode_compact(2)+struct.pack('<2H',0x8000,0x8000+n)+encode_compact(2)+struct.pack('<2H',0,n)+b'opaque-tail'


class IntegrationTests(unittest.TestCase):
    def test_selected_default(self):
        p=json.loads((ROOT/'locales/zh-CN/full-font-profile.json').read_text('utf8'))
        self.assertEqual(p['selected_experiment'],'A-medium-mixed')
        self.assertEqual(p['font_input']['sha256'],'1df61d31687d04fd2f928a3bb6ca6cd61f0e988cc267cf317f32406edbb49f70')
        self.assertNotIn('path',p['font_input'])
    def test_exact_raster_parameters(self):
        p=json.loads((ROOT/'locales/zh-CN/full-font-profile.json').read_text('utf8'))
        n,k=p['fonts']['NormalFont'],p['fonts']['KatakanaFont']
        self.assertEqual((n['raster_size'],k['raster_size']),(18,15));self.assertEqual(n['raster_options'],{'supersample':4});self.assertNotIn('raster_options',k)
        for s in (n,k):self.assertEqual(s['advance'],18);self.assertEqual(s['advance_overrides']['，'],10);self.assertEqual(s['original_glyphs'],2667)
    def test_font_only_edit(self):
        old=fixture();new=bytearray(old);i=font_data(old);new[i['bitmap_start']+2667*2]=1;check_font_compatibility(old,bytes(new))
    def test_old_glyph_rejected(self):
        old=fixture();new=bytearray(old);new[font_data(old)['bitmap_start']]=1
        with self.assertRaises(ValueError):check_font_compatibility(old,bytes(new))
    def test_metrics_rejected(self):
        old=fixture();new=bytearray(old);new[font_data(old)['metrics_start']+2667]=2
        with self.assertRaises(ValueError):check_font_compatibility(old,bytes(new))
    def test_tail_rejected(self):
        old=fixture()
        with self.assertRaises(ValueError):check_font_compatibility(old,old[:-1]+b'X')
    def test_length_rejected(self):
        old=fixture()
        with self.assertRaises(ValueError):check_font_compatibility(old,old+b'X')
    def test_geometry_rejected(self):
        old=fixture();new=bytearray(old);struct.pack_into('<I',new,19,2)
        with self.assertRaises(ValueError):check_font_compatibility(old,bytes(new))

if __name__=='__main__':unittest.main()
