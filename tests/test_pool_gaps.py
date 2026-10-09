import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from extract_pool_gaps import uncovered

class PoolGapTests(unittest.TestCase):
    def test_full_partition(self):self.assertEqual(uncovered(5,[(0,2),(2,3)]),[])
    def test_prefix_not_synthetic_seq(self):self.assertEqual(uncovered(5,[(2,3)]),[(0,2)])
    def test_overlapping_union(self):self.assertEqual(uncovered(8,[(0,4),(2,4),(6,2)]),[])
    def test_interior_and_tail(self):self.assertEqual(uncovered(10,[(0,2),(4,2)]),[(2,2),(6,4)])
    def test_empty_pool(self):self.assertEqual(uncovered(0,[]),[])
    def test_unindexed_whole_pool(self):self.assertEqual(uncovered(3,[]),[(0,3)])
    def test_negative_bound_rejected(self):
        with self.assertRaisesRegex(ValueError,'bounds'):uncovered(5,[(-1,2)])
    def test_oversized_bound_rejected(self):
        with self.assertRaisesRegex(ValueError,'bounds'):uncovered(5,[(4,2)])

if __name__=='__main__':unittest.main()
