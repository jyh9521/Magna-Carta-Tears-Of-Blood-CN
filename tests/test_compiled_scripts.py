import sys,struct,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_compiled_scripts import compiled_script,body
from audit_object_properties import Reader

TABLES=dict(version=118,names=['None','FunctionName','+'],imports=[{}],exports=[{}])

class CompiledScriptTests(unittest.TestCase):
 def parse(self,raw,size):return compiled_script(Reader(raw),size,TABLES)
 def test_reference_virtual_width(self):self.assertEqual(self.parse(b'\x47\x01',5)['disk_bytes'],2)
 def test_string_constant(self):self.assertEqual(self.parse(b'\x1fabc\0',5)['strings'][0]['text'],'abc')
 def test_wide_string(self):self.assertEqual(self.parse(b'\x34\x2d\x4e\0\0',5)['strings'][0]['text'],'中')
 def test_native_parameters(self):self.assertEqual(len(self.parse(b'\x70\x25\x16',3)['tokens']),3)
 def test_extended_native(self):self.assertEqual(self.parse(b'\x60\x80\x16',3)['virtual_bytes'],3)
 def test_unknown_fails(self):
  with self.assertRaises(ValueError):self.parse(b'\x03',1)
 def test_reference_bounds(self):
  with self.assertRaises(ValueError):self.parse(b'\x47\x02',5)
 def test_missing_terminator(self):
  with self.assertRaises(ValueError):self.parse(b'\x1fabc',5)
 def test_virtual_overflow(self):
  with self.assertRaises(ValueError):self.parse(b'\x47\x01',2)
 def test_recursion(self):
  with self.assertRaises(ValueError):self.parse(b'\x37'*65+b'\x25',66)
 def test_operator_friendly_name(self):
  raw=bytes(5)+b'\x02'+struct.pack('<iiII',1,2,0,2)+b'\x04\x0b'+b'\x10'+struct.pack('<I',0x20003)
  exp=dict(flags=0,super_index=0,name='FunctionName',class_index=-1)
  exp['class']='Function'
  self.assertEqual(body(raw,TABLES,exp)['header']['friendly_name'],'+')
 def test_native_suffix(self):
  raw=bytes(5)+b'\x01'+struct.pack('<iiII',1,2,0,0)+b'\0'+struct.pack('<IH',0x20401,129)
  exp=dict(flags=0,super_index=0,name='FunctionName');exp['class']='NativeFunction'
  self.assertEqual(body(raw,TABLES,exp)['tail']['native_index'],129)
 def test_decode_failure_retained(self):self.assertIsNotNone(self.parse(b'\x1f\xff\0',3)['strings'][0]['decode_error'])
 def test_state_tail(self):
  raw=bytes(5)+b'\x01'+struct.pack('<iiII',1,2,0,0)+struct.pack('<QQHI',3,4,0,1)
  exp=dict(flags=0,super_index=0,name='FunctionName');exp['class']='State'
  self.assertEqual(body(raw,TABLES,exp)['tail']['probe_mask'],3)
 def test_struct_without_tail(self):
  raw=bytes(5)+b'\x01'+struct.pack('<iiII',1,2,0,0)
  exp=dict(flags=0,super_index=0,name='FunctionName');exp['class']='Struct'
  self.assertEqual(body(raw,TABLES,exp)['tail'],{})
 def test_function_net_field(self):
  raw=bytes(5)+b'\x01'+struct.pack('<iiII',1,2,0,0)+b'\0'+struct.pack('<IH',0x40,7)
  exp=dict(flags=0,super_index=0,name='FunctionName');exp['class']='Function'
  self.assertEqual(body(raw,TABLES,exp)['tail']['replication_offset'],7)
if __name__=='__main__':unittest.main()
