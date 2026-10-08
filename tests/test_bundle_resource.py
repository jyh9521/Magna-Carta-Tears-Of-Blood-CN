"""Synthetic cached-stream overlays without game assets."""
from pathlib import Path
import hashlib
import struct
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from bundle_resource import overlay_segments, replace_cached_package
from package_resource import replace_exports
from font_resource import encode_compact


def sha(blob): return hashlib.sha256(blob).hexdigest()


def fixture():
    names=b'\x05test\0'+bytes(4);payload=b'original-resource'
    offset=64+len(names);prefix=bytes(11)
    table=prefix+encode_compact(len(payload))+encode_compact(offset)+prefix+b'\0'
    header=struct.pack('<9I',0x9e2a83c1,(15<<16)|118,1,1,64,2,offset+len(payload),0,0)
    original=header+bytes(64-len(header))+names+payload+table
    modified,_=replace_exports(original,{1:b'expanded-resource-longer'},expected_sha256=sha(original),expected_version=(118,15))
    record=b'cache.u'.ljust(128,b'\0')+struct.pack('<I',len(original))
    bundle=record*2+original[:64]+b'GAP-A'+table+b'GAP-B'+payload+b'TAIL'
    return original,modified,bundle


class BundleResourceTests(unittest.TestCase):
    def build(self, bundle=None, **kwargs):
        old,new,default=fixture();bundle=default if bundle is None else bundle
        return replace_cached_package(bundle,old,new,kwargs.get('indices',{1}),
            expected_bundle_sha256=kwargs.get('bundle_hash',sha(bundle)),
            expected_package_sha256=kwargs.get('package_hash',sha(old)),
            cached_path=kwargs.get('path','cache.u'),expected_file_records=kwargs.get('records',2))
    def test_growth_and_payload(self):
        result,report=self.build();self.assertIn(b'expanded-resource-longer',result)
        self.assertNotIn(b'original-resource',result);self.assertEqual(len(report['segments']),5)
    def test_file_sizes(self):
        old,new,_=fixture();result,_=self.build()
        self.assertEqual(struct.unpack_from('<I',result,128)[0],len(new))
        self.assertEqual(struct.unpack_from('<I',result,260)[0],len(new))
    def test_untargeted_intervals(self):
        result,report=self.build();self.assertTrue(result.endswith(b'TAIL'))
        self.assertIn(b'GAP-A',result);self.assertIn(b'GAP-B',result);self.assertTrue(report['untargeted_bytes_preserved'])
    def test_bad_bundle_hash(self):
        with self.assertRaisesRegex(ValueError,'fingerprint'):self.build(bundle_hash='0'*64)
    def test_bad_package_hash(self):
        with self.assertRaisesRegex(ValueError,'fingerprint'):self.build(package_hash='0'*64)
    def test_record_count(self):
        for count in (0,1,3):
            with self.assertRaises(ValueError):self.build(records=count)
    def test_unknown_path(self):
        with self.assertRaises(ValueError):self.build(path='missing.u')
    def test_bad_indices(self):
        for indices in (set(),{0},{3},{True}):
            with self.assertRaises(ValueError):self.build(indices=indices)
    def test_duplicate_fragment(self):
        old,new,b=fixture()
        with self.assertRaisesRegex(ValueError,'not unique'):self.build(bundle=b+old[:64])
    def test_damaged_fragment(self):
        old,new,b=fixture()
        with self.assertRaisesRegex(ValueError,'not unique'):self.build(bundle=b.replace(b'original-resource',b'damaged-resource'))
    def test_overlay_growth_and_order(self):
        b=b'0123456789';result,report=overlay_segments(b,[dict(label='late',offset=7,original=b'78',modified=b'XYZ'),dict(label='early',offset=1,original=b'12',modified=b'ABCD')],expected_sha256=sha(b))
        self.assertEqual(result,b'0ABCD3456XYZ9');self.assertEqual(report[1]['modified_offset'],9)
    def test_overlay_overlap(self):
        b=b'abcdef'
        with self.assertRaisesRegex(ValueError,'overlapping'):overlay_segments(b,[dict(label='a',offset=1,original=b'bcd',modified=b'x'),dict(label='b',offset=2,original=b'cd',modified=b'y')],expected_sha256=sha(b))
    def test_overlay_source_bounds(self):
        b=b'abc'
        for offset,old in [(0,b'wrong'),(-1,b'a'),(3,b'x')]:
            with self.assertRaises(ValueError):overlay_segments(b,[dict(label='x',offset=offset,original=old,modified=b'new')],expected_sha256=sha(b))
    def test_overlay_empty(self):
        with self.assertRaises(ValueError):overlay_segments(b'abc',[],expected_sha256=sha(b'abc'))


if __name__ == '__main__': unittest.main()
