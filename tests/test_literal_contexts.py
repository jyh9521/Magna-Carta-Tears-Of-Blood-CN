import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_literal_contexts import ancestry,symbolic
T={'names':['None','SetCaption'],'imports':[{'name':'Log'}],'exports':[{'name':'SetText'}]}
def tok(off,op,depth,parent):return dict(offset=off,opcode=op,depth=depth,parent_opcode=parent)
class LiteralContextTests(unittest.TestCase):
 def test_tree(self):
  ts=[tok(0,15,0,None),tok(1,0,1,15),tok(2,31,1,15),tok(4,4,0,None)]
  self.assertEqual([t['offset'] for t in ancestry(ts)[2]],[0]);self.assertEqual(ancestry(ts)[4],[])
 def test_depth_jump(self):
  with self.assertRaises(ValueError):ancestry([tok(0,31,1,15)])
 def test_wrong_parent(self):
  with self.assertRaises(ValueError):ancestry([tok(0,15,0,None),tok(1,31,1,27)])
 def test_duplicate_offset(self):
  with self.assertRaises(ValueError):ancestry([tok(0,15,0,None),tok(0,31,1,15)])
 def test_named(self):self.assertEqual(symbolic(tok(0,27,0,None),b'\x1b\1',T,{})['symbols'],['SetCaption'])
 def test_final(self):self.assertEqual(symbolic(tok(0,28,0,None),b'\x1c\1',T,{})['symbols'],['SetText'])
 def test_import(self):self.assertEqual(symbolic(tok(0,28,0,None),b'\x1c\x81',T,{})['symbols'],['Log'])
 def test_native(self):self.assertEqual(symbolic(tok(0,97,0,None),b'\x61\2',T,{258:{'ClassIsChildOf'}})['symbols'],['ClassIsChildOf'])
 def test_name_bounds(self):
  with self.assertRaises(ValueError):symbolic(tok(0,27,0,None),b'\x1b\2',T,{})
 def test_missing_native(self):self.assertEqual(symbolic(tok(0,112,0,None),b'\x70',T,{})['symbols'],[])
if __name__=='__main__':unittest.main()
