import sys,struct,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_texture_mips import mips,palette,image_view

def sample(lazy=111,size=4,width=2,height=2,ub=1,vb=1):
 return b'\1'+struct.pack('<I',lazy)+bytes([size])+bytes(range(4))+struct.pack('<IIBB',width,height,ub,vb)

class TextureMipTests(unittest.TestCase):
 def test_mip(self):self.assertEqual(mips(sample(),0,101)[0]['width'],2)
 def test_lazy_bounds(self):
  with self.assertRaises(ValueError):mips(sample(lazy=110),0,101)
 def test_dimensions(self):
  with self.assertRaises(ValueError):mips(sample(width=3),0,101)
 def test_non_p8(self):
  with self.assertRaises(ValueError):mips(sample(width=4,ub=2),0,101)
 def test_trailing(self):
  with self.assertRaises(ValueError):mips(sample()+b'\0',0,101)
 def test_truncated(self):
  with self.assertRaises(ValueError):mips(sample()[:-1],0,101)
 def test_palette(self):self.assertEqual(len(palette(b'\x40\x04'+bytes(1024),0)),1024)
 def test_palette_trailing(self):
  with self.assertRaises(ValueError):palette(b'\x40\x04'+bytes(1025),0)
 def test_channel_view(self):
  colors=bytes([10,20,30,255])+bytes(1020)
  self.assertEqual(image_view(b'\0',1,1,colors).getpixel((0,0)),(30,20,10))
if __name__=='__main__':unittest.main()
