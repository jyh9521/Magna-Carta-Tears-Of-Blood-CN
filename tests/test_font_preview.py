import unittest,sys
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from render_font_preview import compose
class PreviewTests(unittest.TestCase):
 def test_ignore_storage_tail(self):
  a=Image.new('L',(19,21));a.putpixel((14,15),255);b=Image.new('L',(19,21));c=compose(['2倍'],{'2':a,'倍':b},{'2':11,'倍':18},21);self.assertEqual(c.getpixel((22,21)),(25,29,33))
 def test_keep_visible_ink(self):
  a=Image.new('L',(19,21));a.putpixel((10,15),255);c=compose(['2'],{'2':a},{'2':11},21);self.assertEqual(c.getpixel((18,21)),(228,228,220))
 def test_overflow_fails(self):
  with self.assertRaises(ValueError):compose(['2'],{'2':Image.new('L',(19,21))},{'2':11},21,20)
if __name__=='__main__':unittest.main()
