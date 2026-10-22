import sys,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from PIL import ImageFont,Image,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
from build_text_texture_overlays import clean_label,render_labels

def palette():
 a=np.zeros((256,4),np.uint8);a[1,:3]=4
 for i,v in enumerate([40,80,120,160,200,240],2):a[i,:3]=v
 a[8:,:3]=[240,50,150];a[:,3]=255;return a.tobytes()
class MaskTests(unittest.TestCase):
 def label(self,**kwargs):
  q=dict(text='TEST',size=18,ink=[240]*3,stroke=[4]*3,edge_guard=1,coverage_threshold=48);q.update(kwargs)
  face=ImageFont.load_default()
  with patch('build_text_texture_overlays.ImageFont.truetype',return_value=face):return clean_label((46,21),q,'fixture-font',palette())
 def test_transparent_edges(self):
  a=self.label();self.assertFalse(a[0].any() or a[-1].any() or a[:,0].any() or a[:,-1].any());self.assertTrue((a>1).any())
 def test_no_colored_palette(self):self.assertTrue(set(np.unique(self.label()))<=set(range(8)))
 def test_colored_palette_retains_support_guard(self):
  pal=np.frombuffer(palette(),np.uint8).reshape(256,4).copy()
  for j,v in enumerate(range(30,256,15),8):pal[j,:3]=[v,v//5,v*5//8]
  with patch(__name__+'.palette',return_value=pal.tobytes()):a=self.label(palette_mode='color',ink=[240,48,150])
  self.assertTrue((a>=8).any());self.assertFalse(a[0].any() or a[-1].any() or a[:,0].any() or a[:,-1].any())
 def test_unknown_palette_rejected(self):
  with self.assertRaises(ValueError):self.label(palette_mode='guess')
 def test_outline_local(self):
  a=self.label();support=Image.fromarray(np.where(a>1,255,0).astype(np.uint8));expanded=np.asarray(support.filter(ImageFilter.MaxFilter(3)))>0;self.assertFalse(((a==1)&~expanded).any())
 def test_guard_rejected(self):
  with self.assertRaises(ValueError):self.label(edge_guard=0)
 def test_threshold_rejected(self):
  with self.assertRaises(ValueError):self.label(coverage_threshold=0)
 def test_blank_rejected(self):
  with self.assertRaises(ValueError):self.label(text=' ')
 def test_non_target_pixels(self):
  raw=bytes([9])*65536;q=dict(text='A',size=18,ink=[240]*3,stroke=[4]*3,raster_mode='coverage-mask',rect=[10,20,56,41]);face=ImageFont.load_default()
  with patch('build_text_texture_overlays.ImageFont.truetype',return_value=face):new=render_labels(raw,palette(),[q],'fixture')
  a=np.frombuffer(raw,np.uint8).reshape(256,256);b=np.frombuffer(new,np.uint8).reshape(256,256);m=np.ones((256,256),bool);m[20:41,10:56]=False;self.assertTrue(np.array_equal(a[m],b[m]))
 def render_clear(self,rect):
  raw=bytes([9])*65536;q=dict(text='A',size=18,ink=[240]*3,stroke=[4]*3,raster_mode='coverage-mask',rect=[10,20,56,41],clear_rect=rect);face=ImageFont.load_default()
  with patch('build_text_texture_overlays.ImageFont.truetype',return_value=face):return np.frombuffer(render_labels(raw,palette(),[q],'fixture'),np.uint8).reshape(256,256)
 def test_clear_bottom_fringe(self):
  a=self.render_clear([10,20,56,42]);self.assertFalse(a[41,10:56].any());self.assertTrue((a[42,10:56]==9).all())
 def test_clear_non_target_preserved(self):
  a=self.render_clear([10,20,56,42]);self.assertEqual(a[41,9],9);self.assertEqual(a[41,56],9)
 def test_clear_outside_atlas_rejected(self):
  with self.assertRaises(ValueError):self.render_clear([10,20,56,257])
 def test_clear_missing_label_rejected(self):
  with self.assertRaises(ValueError):self.render_clear([11,20,56,42])
 def test_unknown_mode_rejected(self):
  with self.assertRaises(ValueError):render_labels(bytes(65536),palette(),[dict(rect=[0,0,46,21],raster_mode='unknown')],'fixture')
if __name__=='__main__':unittest.main()
