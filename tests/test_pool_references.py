import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from append_pool_references import append_fields

class PoolReferenceTests(unittest.TestCase):
 def setUp(self):
  self.resources=[dict(resource='SHIP/a.fpb',sha256='resource-hash',pool=dict(source_bytes=10),entries=[dict(id='old',offset=0,source_bytes=5,source_sha256='old-hash')])]
  self.row=dict(id='gap',resource='SHIP/a.fpb',resource_sha256='resource-hash',offset=5,source_bytes=5,source_sha256='gap-hash',coordinate='fpb-pool',sequence_id=None,editable=False,backend_eligible=False)
 def test_append_preserves_input(self):
  before=copy.deepcopy(self.resources);got=append_fields(self.resources,[self.row]);self.assertEqual(self.resources,before);self.assertEqual(len(got[0]['entries']),2)
 def test_duplicate(self):
  with self.assertRaises(ValueError):append_fields(self.resources,[self.row,self.row])
 def test_overlap(self):
  self.row['offset']=4
  with self.assertRaises(ValueError):append_fields(self.resources,[self.row])
 def test_bounds(self):
  self.row['source_bytes']=6
  with self.assertRaises(ValueError):append_fields(self.resources,[self.row])
 def test_hash(self):
  self.row['resource_sha256']='wrong'
  with self.assertRaises(ValueError):append_fields(self.resources,[self.row])
 def test_fabricated_sequence(self):
  self.row['sequence_id']=99
  with self.assertRaises(ValueError):append_fields(self.resources,[self.row])
 def test_not_editable(self):
  self.row['backend_eligible']=True
  with self.assertRaises(ValueError):append_fields(self.resources,[self.row])
 def test_zero_length(self):
  self.row['source_bytes']=0
  with self.assertRaises(ValueError):append_fields(self.resources,[self.row])
if __name__=='__main__':unittest.main()
