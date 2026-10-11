from pathlib import Path
import copy,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
from rewrite_compiled_literals import rewrite_function,shifted,encode_target
from audit_compiled_scripts import body,compiled_script
from audit_object_properties import Reader
from font_poc import digest
TABLES=dict(version=118,names=['None','FunctionName'],imports=[{}],exports=[{}])
EXPORT=dict(flags=0,super_index=0,name='FunctionName',class_index=-1,**{'class':'Function'})
def make(script,virtual=None,flags=0):
 if virtual is None:virtual=len(script)
 return bytes(5)+b'\x01'+struct.pack('<iiII',1,2,0,virtual)+script+b'\x10'+struct.pack('<I',flags)+(b'\x07\0' if flags&0x40 else b'')
def rewrite(raw,replacements=None,tables=None,export=None,sha=None):
 return rewrite_function(raw,tables or TABLES,export or EXPORT,replacements or {0:b'abcdef'},expected_sha256=sha or digest(raw))

class CompiledRewriteTests(unittest.TestCase):
 def test_growth_and_nul_framing(self):
  raw=make(b'\x1fabc\0\x04\x0b');new,report=rewrite(raw);self.assertEqual(body(new,TABLES,EXPORT)['script']['strings'][0]['source_bytes'],6);self.assertEqual(report['new_size']-report['old_size'],3)
 def test_shrink(self):
  raw=make(b'\x1fabcdef\0');new,report=rewrite(raw,{0:b'xy'});self.assertEqual(report['new_virtual_bytes'],4);self.assertIn(b'\x1fxy\0',new)
 def test_absolute_jump_relocated(self):
  raw=make(b'\x06\x08\0\x1fabc\0\x0b');new,report=rewrite(raw);self.assertEqual(report['branches'][0]['new_value'],11);self.assertEqual(new[23:25],b'\x0b\0')
 def test_conditional_jump_relocated(self):
  raw=make(b'\x07\x09\0\x27\x1fabc\0\x0b');new,report=rewrite(raw);self.assertEqual(report['branches'][0]['new_value'],12)
 def test_case_relocation_and_default_sentinel(self):
  raw=make(b'\x0a\x08\0\x1fabc\0\x0a\xff\xff');new,report=rewrite(raw);self.assertEqual(len(report['branches']),1);self.assertEqual(report['branches'][0]['new_value'],11);self.assertIn(b'\x0a\xff\xff',new)
 def test_context_relative_length(self):
  script=b'\x19\x01\x01\x05\0\0\x1fabc\0';raw=make(script,14);new,report=rewrite(raw);self.assertEqual(report['branches'][0]['new_value'],8);self.assertEqual(report['new_virtual_bytes'],17)
 def test_original_short_context_distance_not_normalized(self):
  script=b'\x19\x01\x01\x05\0\0\x1b\x01\x1fabc\0\x16';raw=make(script,20);new,report=rewrite(raw);self.assertEqual(report['branches'][0]['new_value'],5);self.assertEqual(report['branches'][0]['old_target'],14)
 def test_assert_diagnostic_word_preserved(self):
  raw=make(b'\x09\x09\x03\x1fabc\0');new,report=rewrite(raw);self.assertEqual(new[23:25],raw[23:25]);self.assertEqual(report['branches'],[])
 def test_compact_reference_virtual_width_and_value(self):
  raw=make(b'\x47\x01\x1fabc\0',10);new,report=rewrite(raw);s=body(new,TABLES,EXPORT)['script'];self.assertEqual(s['references'][0]['value'],1);self.assertEqual(s['virtual_bytes'],13);self.assertEqual(s['disk_bytes'],10)
 def test_skip_original_plus_one_preserved(self):
  raw=make(b'\x18\x07\0\x47\x01\x16\x0b\x0b\x1fabc\0',16);new,report=rewrite(raw);self.assertEqual(report['branches'][0]['new_value'],7)
 def test_spans_end_before_parent_terminator(self):
  script=b'\x70\x19\x25\x01\0\0\x25\x16';s=compiled_script(Reader(script),len(script),TABLES,include_spans=True);context=s['tokens'][1];self.assertEqual(context['end'],7);self.assertEqual(context['virtual_end'],7);self.assertEqual(s['tokens'][0]['end'],8)
 def test_default_parser_inventory_unchanged(self):
  raw=make(b'\x1fabc\0');plain=body(raw,TABLES,EXPORT);spans=body(raw,TABLES,EXPORT,include_spans=True)
  for t in spans['script']['tokens']:t.pop('end');t.pop('virtual_end')
  self.assertEqual(plain,spans)
 def test_bad_hash_rejected(self):
  with self.assertRaises(ValueError):rewrite(make(b'\x1fabc\0'),sha='0'*64)
 def test_nul_replacement_rejected(self):
  with self.assertRaises(ValueError):rewrite(make(b'\x1fabc\0'),{0:b'a\0b'})
 def test_bad_literal_index_rejected(self):
  with self.assertRaises(ValueError):rewrite(make(b'\x1fabc\0'),{1:b'ab'})
 def test_replicated_function_rejected(self):
  with self.assertRaises(ValueError):rewrite(make(b'\x1fabc\0',flags=0x40))
 def test_non_function_rejected(self):
  e=dict(EXPORT);e['class']='NativeFunction'
  with self.assertRaises(ValueError):rewrite(make(b'\x1fabc\0'),export=e)
 def test_jump_inside_literal_rejected(self):
  with self.assertRaises(ValueError):rewrite(make(b'\x06\x05\0\x1fabc\0'))
 def test_context_inside_literal_rejected(self):
  with self.assertRaises(ValueError):rewrite(make(b'\x19\x25\x02\0\0\x1fabc\0'))
 def test_shifted_edges(self):
  edits=[dict(start=5,end=8,delta=3)];self.assertEqual([shifted(x,edits) for x in (0,5,8,9)],[0,5,11,12])
  with self.assertRaises(ValueError):shifted(6,edits)
 def test_mapping_and_ascii(self):self.assertEqual(encode_target('中1',dict(entries=[dict(character='中',bytes='D0A1')])),b'\xd0\xa11')
 def test_missing_mapping_rejected(self):
  with self.assertRaises(ValueError):encode_target('中',dict(entries=[]))
 def test_duplicate_mapping_rejected(self):
  with self.assertRaises(ValueError):encode_target('中',dict(entries=[dict(character='中',bytes='D0A1')]*2))
 def test_bad_double_byte_mapping_rejected(self):
  with self.assertRaises(ValueError):encode_target('中',dict(entries=[dict(character='中',bytes='00A1')]))
if __name__=='__main__':unittest.main()
