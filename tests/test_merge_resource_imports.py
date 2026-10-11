import copy,sys,unittest
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/p) for p in ('tools','src','lib')]
from merge_resource_imports import merge_receipts

class MergeTests(unittest.TestCase):
    def fixture(self):
        base=dict(map_sha256='map',font_sha256='font',resources=[dict(resource='SHIP/a.fpb',modified_sha256='base',original_sha256='original',modified_bytes=100,selected_fields=1,fields=[dict(new_offset=10)])])
        overlay=dict(map_sha256='map',font_sha256='font',imported_header_fields=1,resources=[dict(resource='SHIP/a.fpb',base_sha256='base',original_sha256='original',modified_sha256='overlay',old_length=10,new_length=15,offset_delta=5)])
        return base,overlay
    def test_merge_and_no_mutation(self):
        b,h=self.fixture();old=copy.deepcopy(b);r=merge_receipts(b,h);self.assertEqual(b,old);self.assertEqual(r['resources'][0]['fields'][0]['new_offset'],15);self.assertEqual(r['total_selected_fields'],2)
    def test_wrong_base(self):
        b,h=self.fixture();h['resources'][0]['base_sha256']='bad'
        with self.assertRaisesRegex(ValueError,'fingerprint'):merge_receipts(b,h)
    def test_duplicate_overlay(self):
        b,h=self.fixture();h['resources']*=2
        with self.assertRaisesRegex(ValueError,'duplicate'):merge_receipts(b,h)
    def test_mapping_mismatch(self):
        b,h=self.fixture();h['map_sha256']='bad'
        with self.assertRaisesRegex(ValueError,'mapping'):merge_receipts(b,h)
    def test_inconsistent_delta(self):
        b,h=self.fixture();h['resources'][0]['offset_delta']=6
        with self.assertRaisesRegex(ValueError,'delta'):merge_receipts(b,h)
    def test_overlap(self):
        b,h=self.fixture();b['resources'][0]['fields'][0]['new_offset']=9
        with self.assertRaisesRegex(ValueError,'overlaps'):merge_receipts(b,h)
    def test_applied_twice(self):
        b,h=self.fixture();b['resources'][0]['header_fields']=[]
        with self.assertRaisesRegex(ValueError,'already'):merge_receipts(b,h)
    def test_count_mismatch(self):
        b,h=self.fixture();h['imported_header_fields']=2
        with self.assertRaisesRegex(ValueError,'count'):merge_receipts(b,h)

if __name__=='__main__':unittest.main()
