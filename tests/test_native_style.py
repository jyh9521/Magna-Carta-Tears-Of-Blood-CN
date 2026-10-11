import json,struct,sys,unittest,copy
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools')]
from audit_native_style import record_address,expression_evidence,validate_anchors,ANCHORS
class StrideImage:
 def __init__(self):self.blob=b''.join(struct.pack('<I',ANCHORS[va]) for va in range(0x310aec,0x310b08,4))
 def to_offset(self,va):return va-0x310aec
class NativeStyleTests(unittest.TestCase):
 def test_original_stride_instructions(self):
  for i in range(249):self.assertEqual(record_address(StrideImage(),i),0x9000+100*i)
 def test_bounded_index(self):
  for i in (-1,10000):
   with self.assertRaises(ValueError):record_address(StrideImage(),i)
 def test_anchor_mutation_rejected(self):
  class Bad:
   blob=bytes(4)
   def to_offset(self,va):return 0
  with self.assertRaisesRegex(ValueError,'anchor mismatch'):validate_anchors(Bad())
 def test_same_named_member_other_receiver_not_selected(self):
  obj=dict(id='x',function='f',serial_sha256='s',tokens=[dict(offset=1,depth=0,opcode=15),dict(offset=2,depth=1,field='Name'),dict(offset=3,depth=2,field='ItemData')]);self.assertEqual(expression_evidence([obj]),[])
 def test_expression_subtree_does_not_include_next_statement(self):
  obj=dict(id='x',function='f',serial_sha256='s',tokens=[dict(offset=1,depth=0,opcode=15),dict(offset=2,depth=1,field='Name'),dict(offset=3,depth=2,field='StyleData'),dict(offset=4,depth=0,opcode=15),dict(offset=5,depth=1,field='Caption')]);rows=expression_evidence([obj]);self.assertEqual(len(rows),1);self.assertEqual(rows[0]['kind'],'other');self.assertEqual([t['offset'] for t in rows[0]['tokens']],[1,2,3])
 def test_all_translated_name_equality_classes_preserved(self):
  p=json.loads((R/'locales/zh-CN/proofreading/style-name-consumers.json').read_text('utf8'));rows=p['all_name_bindings'];self.assertEqual(len(rows),249)
  def target(row):return ('translated',row['target'].casefold()) if row['target'] is not None else ('original',bytes.fromhex(row['source_hex']).lower())
  for i,a in enumerate(rows):
   for b in rows[i+1:]:self.assertEqual(bytes.fromhex(a['source_hex']).lower()==bytes.fromhex(b['source_hex']).lower(),target(a)==target(b),(a['id'],b['id']))
 def test_hanja_label_collision_regression(self):
  p=json.loads((R/'locales/zh-CN/proofreading/style-name-consumers.json').read_text('utf8'));rows=p['all_name_bindings'];corrections=p['orthographic_label_corrections'];self.assertEqual(len(corrections),8)
  for base,variant in [(7,157),(7,158),(15,159),(15,160),(21,161),(21,162),(26,163),(31,164)]:
   self.assertNotEqual(rows[base]['source_hex'],rows[variant]['source_hex']);self.assertNotEqual(rows[base]['target'],rows[variant]['target']);self.assertEqual(rows[variant]['target'],rows[base]['target']+'（汉字名）')
 def test_profile_source_key_and_numbered_identifier_retained(self):
  p=json.loads((R/'locales/zh-CN/proofreading/style-name-consumers.json').read_text('utf8'));self.assertFalse(p['runtime_verified'])
  for x in p['bindings']:self.assertIsInstance(x['source_record_key'],int);self.assertIn(x['field'],(0,1));self.assertRegex(x['source_sha256'],r'^[0-9a-f]{64}$')
 def test_description_policy_has_distinct_help_binding(self):
  p=json.loads((R/'locales/zh-CN/proofreading/style-name-consumers.json').read_text('utf8'));self.assertEqual(sum(x['field']==1 for x in p['bindings']),40);self.assertTrue(p['description_help_consumer_closed_statically'])
if __name__=='__main__':unittest.main()
