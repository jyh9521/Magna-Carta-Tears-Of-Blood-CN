import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_bundle_contexts import contexts,inventory
class BundleContextTests(unittest.TestCase):
    spans=[(10,20,'mirror','x'),(10,30,'table','y')]
    def test_contained(self):self.assertEqual(len(contexts(12,3,self.spans)),2)
    def test_end(self):self.assertEqual(len(contexts(19,1,self.spans)),2)
    def test_partial(self):self.assertEqual([r['kind'] for r in contexts(19,2,self.spans)],['table'])
    def test_before(self):self.assertEqual(contexts(9,3,self.spans),[])
    def test_after(self):self.assertEqual(contexts(31,1,self.spans),[])
    def test_negative(self):
        with self.assertRaises(ValueError):contexts(-1,3,self.spans)
    def test_negative_size(self):
        with self.assertRaises(ValueError):contexts(1,-1,self.spans)
    def test_version(self):
        with self.assertRaises(ValueError):inventory(b'unknown',{})
