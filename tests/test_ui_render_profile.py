import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class RenderProfileTests(unittest.TestCase):
    def setUp(self):self.p=json.loads((ROOT/'locales/zh-CN/proofreading/ui-render-revision.json').read_text('utf8'))
    def test_button_ink_center(self):
        f=next(f for f in self.p['functions'] if f['export_index']==12210);c=f['centering_basis']
        self.assertEqual(c['caption_y']+(c['caption_ink_min_y']+c['caption_ink_max_y'])/2,c['button_height']/2)
        self.assertEqual(f['edits'][0]['new_hex'],'2c04')
    def test_attribute_shadows_shift_together(self):
        rows=[f for f in self.p['functions'] if f['export_index']!=12210];self.assertEqual(len(rows),3)
        for f in rows:
            self.assertEqual(len(f['edits']),20)
            for q in f['edits']:self.assertEqual(bytes.fromhex(q['old_hex'])[1]-bytes.fromhex(q['new_hex'])[1],2)
    def test_profile_keeps_font_raster_parameters(self):
        p=json.loads((ROOT/'locales/zh-CN/full-font-profile.json').read_text('utf8'))
        self.assertEqual(p['bitmap_padding'],'zero-outside-metric');self.assertEqual(p['fonts']['NormalFont']['raster_size'],18);self.assertEqual(p['fonts']['NormalFont']['raster_options'],{'supersample':4});self.assertEqual(p['fonts']['KatakanaFont']['raster_size'],15)
