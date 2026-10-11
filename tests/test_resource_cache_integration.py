import unittest
import sys
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/p) for p in ('tools','src','lib')]
from integrate_resource_copies import cache_overlay,validate_original_mirrors
import font_poc as core


class CacheTests(unittest.TestCase):
    def mirror(self,name='SHIP/a.cha',old=b'abcdef',offsets=None):
        return dict(resource=name,sha256=core.digest(old),decompressed_offsets=offsets or [1])
    def test_unique_cache(self):
        b,r=cache_overlay(b'!abcdef?',{'a.cha':b'abcdef'},{'SHIP/a.cha':b'ABCDEF'},[self.mirror()]);self.assertEqual(b,b'!ABCDEF?');self.assertEqual(r['cached_copies'],1)
    def test_uncached_resource(self):
        b,r=cache_overlay(b'other',{'a.cha':b'abcdef'},{'SHIP/a.cha':b'longer123'},[]);self.assertEqual(b,b'other');self.assertEqual(r['cached_resources'],0)
    def test_unexpected_cache_rejected(self):
        with self.assertRaisesRegex(ValueError,'copy count'):cache_overlay(b'abcdef',{'a.cha':b'abcdef'},{'SHIP/a.cha':b'ABCDEF'},[])
    def test_missing_declared_cache(self):
        with self.assertRaisesRegex(ValueError,'copy count'):cache_overlay(b'other',{'a.cha':b'abcdef'},{'SHIP/a.cha':b'ABCDEF'},[self.mirror()])
    def test_cached_resize_rejected(self):
        with self.assertRaisesRegex(ValueError,'resizing'):cache_overlay(b'abcdef',{'a.cha':b'abcdef'},{'SHIP/a.cha':b'longer123'},[self.mirror()])
    def test_multiple_explicit_mirrors(self):
        b,r=cache_overlay(b'abcdef!abcdef',{'a.cha':b'abcdef'},{'SHIP/a.cha':b'ABCDEF'},[self.mirror(offsets=[0,7])]);self.assertEqual(b,b'ABCDEF!ABCDEF');self.assertEqual(r['cached_copies'],2)
    def test_overlapping_resources_rejected(self):
        with self.assertRaisesRegex(ValueError,'overlapping'):
            cache_overlay(b'abcdef',{'a.cha':b'abcdef','b.cha':b'cde'},{'SHIP/a.cha':b'ABCDEF','SHIP/b.cha':b'CDE'},[self.mirror(),self.mirror('SHIP/b.cha',b'cde')])
    def test_duplicate_catalog_identity(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):cache_overlay(b'abcdef',{'a.cha':b'abcdef'},{'SHIP/a.cha':b'ABCDEF'},[self.mirror(),self.mirror()])
    def test_file_owned_original_mirror(self):
        validate_original_mirrors(b'!abcdef',{'SHIP':{},'FILE':{'a.cha':b'abcdef'}},[self.mirror('FILE/a.cha')])
    def test_unsupported_owner(self):
        with self.assertRaisesRegex(ValueError,'owner'):validate_original_mirrors(b'!abcdef',{'SHIP':{}},[self.mirror('UNKNOWN/a.cha')])
    def test_original_offset_bounds(self):
        with self.assertRaisesRegex(ValueError,'bounds'):validate_original_mirrors(b'!abcdef',{'SHIP':{'a.cha':b'abcdef'}},[self.mirror(offsets=[-1])])
    def test_original_source_hash(self):
        with self.assertRaisesRegex(ValueError,'source fingerprint'):validate_original_mirrors(b'!abcdef',{'SHIP':{'a.cha':b'ABCDEF'}},[self.mirror()])


if __name__=='__main__':unittest.main()
