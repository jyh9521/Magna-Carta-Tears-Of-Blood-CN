import hashlib,struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from bundle_resource import replace_cached_file

class CachedFileOverlayTests(unittest.TestCase):
    def fixture(self):
        old=b'[T]\r\nName=old\r\n';record=b'Test.int'.ljust(128,b'\0')+struct.pack('<I',len(old));return b'HEAD'+record+record+old+b'TAIL',old
    def run_overlay(self,bundle=None,old=None,**kw):
        b,o=self.fixture();bundle=bundle if bundle is not None else b;old=old if old is not None else o
        args=dict(cached_path='Test.int',expected_file_records=2,expected_payloads=1,expected_bundle_sha256=hashlib.sha256(bundle).hexdigest(),expected_source_sha256=hashlib.sha256(old).hexdigest());args.update(kw)
        return replace_cached_file(bundle,old,b'[T]\r\nName=longer\r\n',**args)
    def test_resize_payload_and_two_size_records(self):
        new,rep=self.run_overlay();size=len(b'[T]\r\nName=longer\r\n');self.assertEqual(new.count(b'Test.int'.ljust(128,b'\0')+struct.pack('<I',size)),2);self.assertTrue(new.endswith(b'[T]\r\nName=longer\r\nTAIL'));self.assertEqual(rep['payloads'],1)
    def test_body_count_mismatch(self):
        with self.assertRaisesRegex(ValueError,'body count'):self.run_overlay(expected_payloads=2)
    def test_metadata_count_mismatch(self):
        with self.assertRaisesRegex(ValueError,'size record count'):self.run_overlay(expected_file_records=3)
    def test_wrong_path(self):
        with self.assertRaisesRegex(ValueError,'size record count'):self.run_overlay(cached_path='Other.int')
    def test_wrong_source_fingerprint(self):
        with self.assertRaisesRegex(ValueError,'source fingerprint'):self.run_overlay(expected_source_sha256='0'*64)
    def test_wrong_bundle_fingerprint(self):
        with self.assertRaisesRegex(ValueError,'bundle fingerprint'):self.run_overlay(expected_bundle_sha256='0'*64)
    def test_invalid_counts(self):
        with self.assertRaisesRegex(ValueError,'counts'):self.run_overlay(expected_file_records=0)
    def test_untargeted_prefix_tail(self):
        new,rep=self.run_overlay();self.assertTrue(new.startswith(b'HEAD'));self.assertTrue(new.endswith(b'TAIL'));self.assertTrue(rep['untargeted_bytes_preserved'])

if __name__=='__main__':unittest.main()
