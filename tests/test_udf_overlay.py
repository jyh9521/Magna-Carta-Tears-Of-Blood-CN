"""Synthetic ISO/UDF dual-view overlay and descriptor integrity tests."""
from pathlib import Path
import io
import struct
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
from iso import patch_iso,SECTOR
from udf_overlay import plan_udf_overlay,apply_udf_overlay,validate_tag,retag
from iso_validation import verify_iso_overlay


class UdfOverlayTests(unittest.TestCase):
    def setUp(self):
        import pycdlib
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.source=self.root/'source.iso';self.modified=self.root/'modified.iso'
        cd=pycdlib.PyCdlib();cd.new(udf='2.60')
        for name,data in [('FILE',b'original-file'),('SHIP',b'original-ship'),('KEEP',b'unchanged')]:
            cd.add_fp(io.BytesIO(data),len(data),iso_path='/'+name+'.AFS;1',udf_path='/'+name.title()+'.afs')
        cd.write(str(self.source));cd.close()
    def tearDown(self):self.temp.cleanup()
    def build(self,grow=True):
        replacements={}
        for name,data in [('FILE',b'X'*4097 if grow else b'new'),('SHIP',b'new-ship')]:
            p=self.root/(name+'.afs');p.write_bytes(data);replacements['/'+name+'.AFS']=p
        plan=plan_udf_overlay(self.source,replacements)
        patch_iso(self.source,self.modified,replacements,verbose=False)
        apply_udf_overlay(self.modified,plan)
        return replacements,plan
    def test_growth_both_views(self):
        replacements,plan=self.build();report=verify_iso_overlay(self.source,self.modified,replacements,udf_plan=plan)
        self.assertTrue(report['udf_synced']);self.assertEqual(report['relocated'],1)
    def test_shrink_both_views(self):
        replacements,plan=self.build(False);report=verify_iso_overlay(self.source,self.modified,replacements,udf_plan=plan)
        self.assertEqual(report['relocated'],0);self.assertEqual(plan['extra_sectors'],0)
    def test_new_anchor_location(self):
        replacements,plan=self.build();anchor=next(p for p in plan['patches'] if p['label']=='new-tail-anchor')
        self.assertEqual(anchor['offset'],self.modified.stat().st_size-SECTOR)
        self.assertEqual(struct.unpack_from('<I',anchor['modified'],12)[0],anchor['offset']//SECTOR)
        validate_tag(anchor['modified'])
    def test_partition_integrity_sizes(self):
        import pycdlib
        self.build();cd=pycdlib.PyCdlib();cd.open(str(self.modified))
        try:
            self.assertEqual(cd.udf_main_descs.partitions[0].part_length,cd.udf_reserve_descs.partitions[0].part_length)
            self.assertEqual(cd.udf_logical_volume_integrity.size_tables,[cd.udf_main_descs.partitions[0].part_length])
        finally:cd.close()
    def test_descriptor_checksums(self):
        _,plan=self.build()
        for patch in plan['patches']:validate_tag(patch['modified'])
    def test_descriptor_tamper(self):
        _,plan=self.build();block=bytearray(plan['patches'][0]['modified']);block[100]^=1
        with self.assertRaisesRegex(ValueError,'CRC'):validate_tag(bytes(block))
    def test_tag_tamper(self):
        _,plan=self.build();block=bytearray(plan['patches'][0]['modified']);block[4]^=1
        with self.assertRaisesRegex(ValueError,'checksum'):validate_tag(bytes(block))
    def test_retag_preserves_payload(self):
        _,plan=self.build();block=bytearray(plan['patches'][0]['modified']);block[100]^=1
        fixed=retag(bytes(block));self.assertEqual(fixed[16:],block[16:]);validate_tag(fixed)
    def test_udf_patch_tamper(self):
        replacements,plan=self.build();p=plan['patches'][0]
        with self.modified.open('r+b') as f:f.seek(p['offset']+100);f.write(b'X')
        with self.assertRaises(Exception):verify_iso_overlay(self.source,self.modified,replacements,udf_plan=plan)
    def test_unknown_replacement(self):
        p=self.root/'x';p.write_bytes(b'x')
        with self.assertRaisesRegex(ValueError,'unknown'):plan_udf_overlay(self.source,{'/UNKNOWN':p})
    def test_metadata_precondition(self):
        replacements,plan=self.build(False)
        with self.assertRaisesRegex(ValueError,'before overlay'):apply_udf_overlay(self.modified,plan)
    def test_crc_bounds(self):
        block=bytearray(SECTOR);struct.pack_into('<H',block,10,2040)
        with self.assertRaisesRegex(ValueError,'outside'):retag(bytes(block))


if __name__=='__main__':unittest.main()
