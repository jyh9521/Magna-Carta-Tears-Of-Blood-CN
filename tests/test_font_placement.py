import unittest,sys,struct,json
from pathlib import Path
from unittest.mock import patch
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','src','lib')]
from rebuild_mapped_font import rebuild
from font_resource import encode_compact
from research_inventory import font_data

def fixture():
 n=2669;h=6;w=5;s=2
 return bytes(3)+struct.pack('<6I',1,1,n,h,w,s)+encode_compact(n*h*s)+bytes(n*h*s)+encode_compact(n)+bytes([5])*n+encode_compact(2)+struct.pack('<2H',0x8000,0x8000+n)+encode_compact(2)+struct.pack('<2H',0,n)+b'tail'

def ink(ch,*args):
 im=Image.new('L',(96,96));top=29 if ch=='甲' else 30
 for y in range(top,33):im.putpixel((32,y),255)
 return im,im.getbbox(),None

class PlacementTests(unittest.TestCase):
 def run_build(self,**kw):
  s=dict(raster_size=4,reference='乙',body_top=0,original_glyphs=2667,advance=5,advance_overrides={},raster_options={'supersample':4},placement='shared-origin-guarded',edge_guard=1);s.update(kw)
  m={'entries':[{'character':ch,'glyph':2667+j,'bytes':f'{0x8000+2667+j:04X}'} for j,ch in enumerate('甲乙')]}
  with patch('rebuild_mapped_font.ImageFont.truetype'),patch('font_rasterization.render_ink',side_effect=ink):return rebuild(fixture(),m,'fixture.otf',s)
 def test_single_origin(self):
  new,p=self.run_build();self.assertEqual(p[0]['origin_y'],p[1]['origin_y']);self.assertEqual(p[1]['ink_box'][1]-p[0]['ink_box'][1],1)
 def test_empty_boundary(self):
  new,p=self.run_build();i=font_data(new)
  for g in (2667,2668):
   raw=new[i['bitmap_start']+g*12:i['bitmap_start']+(g+1)*12];self.assertEqual(raw[:2]+raw[-2:],bytes(4))
 def test_preserve_metrics_originals(self):
  old=fixture();new,p=self.run_build();i=font_data(old);self.assertEqual(old[:i['bitmap_start']+2667*12],new[:i['bitmap_start']+2667*12]);self.assertEqual(old[i['metrics_start']:],new[i['metrics_start']:])
 def test_guard_overflow_rejected(self):
  with self.assertRaises(ValueError):self.run_build(edge_guard=2)
 def test_invalid_mode_rejected(self):
  with self.assertRaises(ValueError):self.run_build(placement='guess')
 def test_zero_guard_rejected(self):
  with self.assertRaises(ValueError):self.run_build(edge_guard=0)
 def test_horizontal_guard(self):
  new,p=self.run_build(horizontal_guard=1)
  for q in p:self.assertGreaterEqual(q['ink_box'][0],1);self.assertLessEqual(q['ink_box'][2],q['advance']-1)
 def test_wide_ink_fitted_not_clipped(self):
  def wide(ch,*args):
   im=Image.new('L',(96,96))
   for y in range(29,33):
    for x in range(32,37):im.putpixel((x,y),255)
   return im,im.getbbox(),None
  with patch('font_rasterization.render_ink',side_effect=wide):
   # run_build installs its own renderer patch; construct equivalent direct input.
   s=dict(raster_size=4,reference='乙',body_top=0,original_glyphs=2667,advance=5,advance_overrides={},raster_options={'supersample':4},placement='shared-origin-guarded',edge_guard=1,horizontal_guard=1)
   m={'entries':[{'character':ch,'glyph':2667+j,'bytes':f'{0x8000+2667+j:04X}'} for j,ch in enumerate('甲乙')]}
   with patch('rebuild_mapped_font.ImageFont.truetype'):new,proof=rebuild(fixture(),m,'fixture.otf',s)
  for q in proof:self.assertTrue(q['horizontally_fitted']);self.assertEqual(q['ink_box'][2]-q['ink_box'][0],3)
 def test_horizontal_guard_reject_negative(self):
  with self.assertRaises(ValueError):self.run_build(horizontal_guard=-1)
 def test_horizontal_guard_reject_legacy(self):
  with self.assertRaises(ValueError):self.run_build(placement='legacy-clamped',horizontal_guard=1)
 def test_horizontal_guard_no_area(self):
  with self.assertRaises(ValueError):self.run_build(horizontal_guard=3)
 def test_profile_parameters_unchanged(self):
  p=json.loads((ROOT/'locales/zh-CN/full-font-profile.json').read_text('utf8'))
  for s in p['fonts'].values():self.assertEqual(s['placement'],'shared-origin-guarded');self.assertEqual(s['edge_guard'],1)
  self.assertEqual(p['fonts']['NormalFont']['raster_options'],{'supersample':4});self.assertNotIn('raster_options',p['fonts']['KatakanaFont'])
if __name__=='__main__':unittest.main()
