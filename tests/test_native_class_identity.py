import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_texture_mips import native_class_name
class NativeClassTests(unittest.TestCase):
 def fixture(self): return [dict(index=1,class_index=0,name='Texture',**{'class':'Class'})]
 def test_import(self):self.assertEqual(native_class_name(dict(class_index=-1,**{'class':'Texture'}),[]),'Texture')
 def test_local(self):self.assertEqual(native_class_name(dict(class_index=1,**{'class':'1'}),self.fixture()),'Texture')
 def test_class(self):self.assertEqual(native_class_name(dict(class_index=0,**{'class':'Class'}),[]),'Class')
 def test_bounds(self):
  with self.assertRaises(ValueError):native_class_name(dict(class_index=2),self.fixture())
 def test_wrong_index(self):
  ex=self.fixture();ex[0]['index']=2
  with self.assertRaises(ValueError):native_class_name(dict(class_index=1),ex)
 def test_non_class(self):
  ex=self.fixture();ex[0]['class_index']=-1
  with self.assertRaises(ValueError):native_class_name(dict(class_index=1),ex)
 def test_palette(self):
  ex=self.fixture();ex[0]['name']='Palette';self.assertEqual(native_class_name(dict(class_index=1),ex),'Palette')
if __name__=='__main__':unittest.main()
