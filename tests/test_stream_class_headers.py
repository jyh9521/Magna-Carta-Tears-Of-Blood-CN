import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_stream_class_headers import occurrences,check_tables,full_imports

class ClassHeaderTests(unittest.TestCase):
 def test_missing(self):self.assertEqual(occurrences(b'',b'x'*21),[])
 def test_exact(self):self.assertEqual(occurrences(b'abc'+b'x'*21+b'z',b'x'*21),[3])
 def test_overlapping(self):self.assertEqual(occurrences(b'x'*23,b'x'*21),[0,1,2])
 def test_short_rejected(self):
  with self.assertRaises(ValueError):occurrences(b'x'*20,b'x'*20)
 def fixture(self):
  e=dict(index=1,name='Object',class_index=0,outer=0,super_index=0,flags=1,size=50,offset=64)
  a=dict(names=['Object'],imports=[],exports=[e]);s=dict(names=['Object'],imports=[],exports=[dict(e,declared_size=50,declared_offset=64)])
  return a,s
 def test_tables(self):check_tables(*self.fixture())
 def test_name_change(self):
  a,s=self.fixture();s['names']=['Class']
  with self.assertRaises(ValueError):check_tables(a,s)
 def test_import_change(self):
  a,s=self.fixture();s['imports']=[dict(name='Other')]
  with self.assertRaises(ValueError):check_tables(a,s)
 def test_export_count(self):
  a,s=self.fixture();s['exports']=[]
  with self.assertRaises(ValueError):check_tables(a,s)
 def test_metadata_change(self):
  a,s=self.fixture();s['exports'][0]['super_index']=1
  with self.assertRaises(ValueError):check_tables(a,s)
 def test_coordinate_change(self):
  a,s=self.fixture();s['exports'][0]['declared_offset']=65
  with self.assertRaises(ValueError):check_tables(a,s)
 def test_full_import(self):
  b=bytearray(36);struct.pack_into('<II',b,28,1,36);b.extend(b'\0\1'+struct.pack('<i',0)+b'\2')
  tables=dict(names=['Core','Package','Other'],imports=[dict(**{'class':'Package'},name='Other',outer=0)])
  self.assertEqual(full_imports(bytes(b),tables),[dict(class_package='Core',class_name='Package',name='Other',outer=0)])
 def test_import_index_rejected(self):
  b=bytearray(36);struct.pack_into('<II',b,28,1,36);b.extend(b'\3\1'+struct.pack('<i',0)+b'\2')
  with self.assertRaises(ValueError):full_imports(bytes(b),dict(names=['Core','Package','Other'],imports=[]))

if __name__=='__main__':unittest.main()
