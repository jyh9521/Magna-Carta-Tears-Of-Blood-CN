import unittest
from pathlib import Path
import sys
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/x) for x in ('tools','lib','src')]
from import_audited_fields import rewrite_fields,fixed_extent
import font_poc as core


class Encoder:
    def encode(self,text):return text.encode('ascii')


class AuditedImportTests(unittest.TestCase):
    def setUp(self):
        self.original=b'HEADER'+b'abc'+bytes(5)+b'TAIL'
        self.entry=dict(id='id',source_sha256=core.digest(b'abc'),source_bytes=3,offset=6,slot_bytes=8,
                        slot_sha256=core.digest(self.original[6:14]),decode='strict',controls='recognized',references={'ko-KR':'abc'})
        self.target=dict(id='id',source_sha256=self.entry['source_sha256'],target='xyz',status='reviewed')
    def apply(self):return rewrite_fields(self.original,[self.entry],[self.target],Encoder())
    def test_preserves_outside_slot(self):self.assertEqual(self.apply()[0],b'HEADERxyz'+bytes(5)+b'TAIL')
    def test_missing_extent(self):
        with self.assertRaises(ValueError):fixed_extent({})
    def test_bad_slot_hash(self):
        self.entry['slot_sha256']='bad'
        with self.assertRaises(ValueError):self.apply()
    def test_byte_overflow(self):
        self.target['target']='12345678'
        with self.assertRaises(ValueError):self.apply()
    def test_outside_resource(self):
        self.entry['offset']=100
        with self.assertRaises(ValueError):self.apply()
    def test_unreviewed(self):
        self.target['status']='draft'
        with self.assertRaises(ValueError):self.apply()
    def test_quarantine(self):
        self.entry['controls']='quarantined'
        with self.assertRaises(ValueError):self.apply()
    def test_dirty_padding(self):
        self.original=b'HEADERabc\0\0X\0\0TAIL';self.entry['slot_sha256']=core.digest(self.original[6:14])
        with self.assertRaises(ValueError):self.apply()
    def test_overlap(self):
        with self.assertRaises(ValueError):rewrite_fields(self.original,[self.entry,self.entry],[self.target,self.target],Encoder())
    def test_bound_source_hash(self):
        self.target['source_sha256']='other'
        with self.assertRaises(ValueError):self.apply()
    def test_interpretation(self):
        self.entry['references']['ko-KR']='def'
        with self.assertRaises(ValueError):self.apply()
    def test_internal_role_not_overridden_by_review(self):
        self.entry['semantic']='internal-configuration'
        with self.assertRaises(ValueError):self.apply()
    def leading_entry(self):
        del self.entry['slot_bytes']
        self.entry.update(observed_byte_capacity=7,trailer_bytes=4,
                          trailer_sha256=core.digest(b'TAIL'),
                          slot_sha256=core.digest(self.original[6:]))
    def test_leading_field_hash_includes_preserved_trailer(self):
        self.leading_entry()
        changed,report=self.apply()
        self.assertEqual(changed,b'HEADERxyz'+bytes(5)+b'TAIL')
        self.assertEqual(report[0]['fingerprint_bytes'],12)
        self.assertEqual(report[0]['capacity_bytes'],7)
    def test_leading_trailer_mismatch_rejected(self):
        self.leading_entry();self.entry['trailer_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'trailer'):self.apply()
    def test_leading_full_segment_hash_rejected(self):
        self.leading_entry();self.entry['slot_sha256']=core.digest(self.original[6:14])
        with self.assertRaisesRegex(ValueError,'fingerprint'):self.apply()
    def test_leading_does_not_gain_trailer_capacity(self):
        self.leading_entry();self.target['target']='12345678'
        with self.assertRaisesRegex(ValueError,'overflow'):self.apply()


if __name__=='__main__':unittest.main()
