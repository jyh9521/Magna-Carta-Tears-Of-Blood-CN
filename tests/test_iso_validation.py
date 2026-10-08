"""Synthetic ISO checks for upstream patcher in-place and relocation branches."""
from pathlib import Path
import io
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
from iso import patch_iso,_portable_metadata,SECTOR
from iso_validation import verify_iso_overlay,require_iso_overlay_layout


class IsoValidationTests(unittest.TestCase):
    def setUp(self):
        import pycdlib
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.source=self.root/'source.iso';self.modified=self.root/'modified.iso'
        cd=pycdlib.PyCdlib();cd.new()
        for name,data in [('FILE.AFS',b'original-file'),('SHIP.AFS',b'original-ship'),('KEEP.DAT',b'unchanged')]:
            cd.add_fp(io.BytesIO(data),len(data),iso_path='/'+name+';1')
        cd.write(str(self.source));cd.close()
    def tearDown(self): self.temp.cleanup()
    def build(self,large=False):
        replacements={}
        for name,data in [('FILE.AFS',b'X'*4097 if large else b'new'),('SHIP.AFS',b'new-ship')]:
            path=self.root/name;path.write_bytes(data);replacements['/'+name]=path
        patch_iso(self.source,self.modified,replacements,verbose=False)
        return replacements
    def test_in_place(self):
        report=verify_iso_overlay(self.source,self.modified,self.build())
        self.assertEqual((report['in_place'],report['relocated']),(2,0))
    def test_relocation(self):
        report=verify_iso_overlay(self.source,self.modified,self.build(True))
        self.assertEqual((report['in_place'],report['relocated']),(1,1))
        self.assertGreater(report['modified_bytes'],report['original_bytes'])
    def test_untargeted_tamper(self):
        replacements=self.build();files,_=_portable_metadata(self.modified)
        with self.modified.open('r+b') as f:f.seek(files['/KEEP.DAT'][0]*SECTOR);f.write(b'X')
        with self.assertRaisesRegex(ValueError,'untargeted'):verify_iso_overlay(self.source,self.modified,replacements)
    def test_payload_tamper(self):
        replacements=self.build();files,_=_portable_metadata(self.modified)
        with self.modified.open('r+b') as f:f.seek(files['/FILE.AFS'][0]*SECTOR);f.write(b'X')
        with self.assertRaisesRegex(ValueError,'payload'):verify_iso_overlay(self.source,self.modified,replacements)
    def test_old_relocation_slot(self):
        replacements=self.build(True);files,_=_portable_metadata(self.source)
        with self.modified.open('r+b') as f:f.seek(files['/FILE.AFS'][0]*SECTOR);f.write(b'X')
        with self.assertRaisesRegex(ValueError,'cleared'):verify_iso_overlay(self.source,self.modified,replacements)
    def test_append_padding(self):
        replacements=self.build(True);files,_=_portable_metadata(self.modified)
        with self.modified.open('r+b') as f:f.seek(files['/FILE.AFS'][0]*SECTOR+4097);f.write(b'X')
        with self.assertRaisesRegex(ValueError,'padding'):verify_iso_overlay(self.source,self.modified,replacements)
    def test_extra_output(self):
        replacements=self.build(True)
        with self.modified.open('ab') as f:f.write(bytes(SECTOR))
        with self.assertRaisesRegex(ValueError,'length'):verify_iso_overlay(self.source,self.modified,replacements)
    def test_unknown_replacement(self):
        replacements=self.build();replacements['/UNKNOWN.AFS']=self.root/'FILE.AFS'
        with self.assertRaisesRegex(ValueError,'unknown'):verify_iso_overlay(self.source,self.modified,replacements)
    def test_plain_iso_preflight(self):
        require_iso_overlay_layout(self.source,self.build(True))
    def test_udf_growth_preflight(self):
        import pycdlib
        source=self.root/'udf.iso';replacement=self.root/'grown.afs';replacement.write_bytes(b'X'*4097)
        cd=pycdlib.PyCdlib();cd.new(udf='2.60')
        cd.add_fp(io.BytesIO(b'original'),8,iso_path='/FILE.AFS;1',udf_path='/File.afs')
        cd.write(str(source));cd.close()
        with self.assertRaisesRegex(ValueError,'UDF'):require_iso_overlay_layout(source,{'/FILE.AFS':replacement})


if __name__=='__main__':unittest.main()
