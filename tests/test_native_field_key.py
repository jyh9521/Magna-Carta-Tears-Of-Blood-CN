import sys,struct,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib')]
from audit_native_field_text import run_lookup,source_key_index,bind_calls,exact
from audit_text_slicing import scalar
class Image:
 def __init__(self,words,base=0x3127a0):self.base=base;self.blob=struct.pack('<'+'I'*len(words),*words)
 def to_offset(self,va):return va-self.base
WORDS=[0x8c870140,0x1000000d,0x0000402d,0x8c82013c,0x000818c0,0x00681823,0x00031880,0x00431021,0x8c420000,0x14a20004,0,0xacc80000,0x10000005,0x24020001,0x25080001,0x0107102a,0x1440fff2,0x0000102d,0x03e00008,0]
def entry(key,half,ordinal):return dict(record_id=key,half=half,record_index=ordinal,id=f'key/{key}/half/{half}',source_sha256='a'*64)
def corpus():return dict(resources=[dict(resource='SHIP/00001240.tui',entries=[entry(300,0,238),entry(300,1,238)])])
def call(key=300,depth=1):return dict(id='object/1',function='ShowRecordInfo',call=dict(symbols=['GetFieldTextData'],offset=10),tree=[dict(offset=10,depth=depth),dict(offset=11,depth=depth+1,int=key)])
class NativeFieldKeyTests(unittest.TestCase):
 def test_native_lookup_not_ordinal(self):self.assertEqual(run_lookup(Image(WORDS),[238,300,301],300)['index'],1)
 def test_native_first_match_duplicate_keys(self):self.assertEqual(run_lookup(Image(WORDS),[9,9,1],9)['index'],0)
 def test_native_missing_index_untouched(self):self.assertEqual(run_lookup(Image(WORDS),[1,2],9)['index'],0xffffffff)
 def test_native_empty_table(self):self.assertFalse(run_lookup(Image(WORDS),[],1)['found'])
 def test_literal_call_binds_key(self):
  rows,_=bind_calls([call()],source_key_index(corpus()));self.assertEqual(rows[0]['key'],300);self.assertEqual(rows[0]['physical_index'],238);self.assertTrue(rows[0]['key_differs_from_ordinal'])
 def test_wrong_ordinal_literal_rejected(self):
  with self.assertRaises(ValueError):bind_calls([call(238)],source_key_index(corpus()))
 def test_dynamic_argument_retained_not_assumed(self):
  q=call();q['tree'][1].pop('int');q['tree'][1]['field']='RequestedKey';rows,dynamic=bind_calls([q],source_key_index(corpus()));self.assertFalse(rows);self.assertEqual(len(dynamic),1)
 def test_duplicate_native_key_rejected(self):
  q=corpus();q['resources'][0]['entries'].append(entry(300,0,240))
  with self.assertRaises(ValueError):source_key_index(q)
 def test_missing_help_half_rejected(self):
  q=corpus();q['resources'][0]['entries'].pop()
  with self.assertRaises(ValueError):bind_calls([call()],source_key_index(q))
 def test_bad_argument_depth_rejected(self):
  q=call();q['tree'][1]['depth']=4
  with self.assertRaises(ValueError):bind_calls([q],source_key_index(corpus()))
 def test_exact_instruction_mismatch(self):
  with self.assertRaises(ValueError):exact(Image(WORDS),{0x3127a0:0})
 def test_exact_instruction_readback(self):self.assertEqual(exact(Image(WORDS),{0x3127a0:WORDS[0]})['0x3127a0'],hex(WORDS[0]))
 def test_scalar_store_outside_fixture_rejected(self):
  with self.assertRaises(ValueError):scalar(Image([0xacc80000]),0x3127a0,0x3127a4,{6:0x9000,8:1},{})
 def test_scalar_sll_store_value(self):
  image=Image([0x00081880,0xacc30000]);memory={0x9000+i:0 for i in range(4)};scalar(image,0x3127a0,0x3127a8,{6:0x9000,8:7},memory);self.assertEqual(bytes(memory.values()),struct.pack('<I',28))
if __name__=='__main__':unittest.main()
