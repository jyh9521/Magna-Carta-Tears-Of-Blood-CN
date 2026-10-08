from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from prepare_name_slots import prepare_slots,mirror_resource

def fixture(raw=b'Name',trailer=b'\x01\x02'):
    slot=raw+bytes(299-len(trailer)-len(raw))+trailer
    return bytes(12)+slot+(b'Other'+bytes(294))

class NameSlotsTests(unittest.TestCase):
    def test_selected_only(self):
        original=fixture();modified,changes=prepare_slots(original,'.cha',b'Name',b'Test',1)
        self.assertEqual(changes[0]['slot'],0);self.assertEqual(modified[311:],original[311:])
    def test_growth_and_trailer(self):
        original=fixture();modified,_=prepare_slots(original,'.cha',b'Name',b'LongName',1)
        self.assertEqual(modified[309:311],b'\x01\x02');self.assertEqual(len(modified),len(original))
    def test_no_global_substring(self):
        modified,_=prepare_slots(fixture(b'NameExtra'),'.cha',b'Other',b'Test',1)
        self.assertEqual(modified[12:21],b'NameExtra')
    def test_wrong_count(self):
        with self.assertRaisesRegex(ValueError,'count'):prepare_slots(fixture(),'.cha',b'Name',b'Test',2)
    def test_missing(self):
        with self.assertRaisesRegex(ValueError,'count'):prepare_slots(fixture(),'.cha',b'Absent',b'Test',1)
    def test_overflow(self):
        with self.assertRaisesRegex(ValueError,'exceeds'):prepare_slots(fixture(),'.cha',b'Name',b'X'*297,1)
    def test_nul_target(self):
        with self.assertRaisesRegex(ValueError,'bytes'):prepare_slots(fixture(),'.cha',b'Name',b'X\x00',1)
    def test_empty_source(self):
        with self.assertRaisesRegex(ValueError,'bytes'):prepare_slots(fixture(),'.cha',b'',b'X',1)
    def test_invalid_count(self):
        with self.assertRaisesRegex(ValueError,'count'):prepare_slots(fixture(),'.cha',b'Name',b'X',0)
    def test_unterminated(self):
        with self.assertRaisesRegex(ValueError,'unterminated'):prepare_slots(bytes(12)+b'X'*299,'.cha',b'X',b'Y',1)
    def test_cached_mirror(self):
        old=fixture();new,_=prepare_slots(old,'.cha',b'Name',b'Test',1)
        result,offset=mirror_resource(b'prefix'+old+b'suffix',old,new)
        self.assertEqual(offset,6);self.assertEqual(result,b'prefix'+new+b'suffix')
    def test_duplicate_cache(self):
        old=fixture()
        with self.assertRaisesRegex(ValueError,'unique'):mirror_resource(old+old,old,old)
    def test_absent_cache(self):
        with self.assertRaisesRegex(ValueError,'unique'):mirror_resource(b'other',fixture(),fixture())

if __name__=='__main__':unittest.main()
