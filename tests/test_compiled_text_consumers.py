from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from compiled_text_consumers import matching_fields,array_reads
def token(offset,opcode,depth,**kw):return dict(offset=offset,opcode=opcode,depth=depth,**kw)
def literal(index=12):return [token(0,0x10,0),token(1,0x2c,1,int=index),token(3,0x19,1),token(4,0x48,2,field='DataManager'),token(8,0x48,2,field='CommonTextList')]
class CompiledConsumerTests(unittest.TestCase):
 def test_matching_fields_exact(self):self.assertEqual(matching_fields(literal(),['CommonTextList','FieldMenuTextList']),['CommonTextList'])
 def test_none_field_ignored(self):self.assertEqual(matching_fields([token(0,0,0,field=None)],['X']),[])
 def test_direct_index_is_physical_ordinal(self):self.assertEqual(array_reads(literal(),'CommonTextList')[0]['literal_physical_index'],12)
 def test_dynamic_index_not_inferred(self):
  ts=literal();ts[1].pop('int');ts[1]['field']='Index';self.assertIsNone(array_reads(ts,'CommonTextList')[0]['literal_physical_index'])
 def test_nearby_integer_not_key(self):
  ts=[token(-1,0x2c,0,int=99)]+literal(12);self.assertEqual(array_reads(ts,'CommonTextList')[0]['literal_physical_index'],12)
 def test_no_array_reference_ignored(self):self.assertFalse(array_reads([token(0,0x48,0,field='CommonTextList')],'CommonTextList'))
 def test_malformed_array_extra_children(self):
  ts=literal()+[token(10,0x2c,1,int=7)]
  with self.assertRaises(ValueError):array_reads(ts,'CommonTextList')
 def test_bounded_end_excludes_next_statement(self):
  ts=literal()+[token(10,0x2c,0,int=77)];q=array_reads(ts,'CommonTextList')[0];self.assertEqual(q['array_expression'],literal());self.assertEqual(q['index_expression'],[ts[1]])
if __name__=='__main__':unittest.main()
