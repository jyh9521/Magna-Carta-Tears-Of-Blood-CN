import sys,tempfile,unittest,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from PIL import Image
from audit_mip_views import sheets,audit
class MipViewTests(unittest.TestCase):
 def test_empty(self):
  with tempfile.TemporaryDirectory() as d:self.assertEqual(sheets([],Path(d)),[])
 def test_native(self):
  with tempfile.TemporaryDirectory() as d:
   result=sheets([('one',Image.new('RGB',(128,64),'red'))],Path(d));self.assertFalse(result[0]['resized'])
   with Image.open(Path(d)/result[0]['image']) as im:self.assertEqual(im.getpixel((3,34)),(255,0,0))
 def test_batches(self):
  with tempfile.TemporaryDirectory() as d:self.assertEqual([r['count'] for r in sheets([('x',Image.new('RGB',(1,1)))]*25,Path(d))],[24,1])
 def test_too_wide(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):sheets([('x',Image.new('RGB',(129,1)))],Path(d))
 def test_too_high(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):sheets([('x',Image.new('RGB',(1,129)))],Path(d))
 def test_unknown_archive(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'bad.afs';p.write_bytes(b'unknown')
   with self.assertRaises(ValueError):audit(p,Path(d)/'manifest',Path(d)/'out')
 def test_reopened_sheet(self):
  with tempfile.TemporaryDirectory() as d:
   rows=sheets([('x',Image.new('RGB',(1,1)))],Path(d));self.assertEqual(len(rows[0]['sha256']),64)
if __name__=='__main__':unittest.main()
