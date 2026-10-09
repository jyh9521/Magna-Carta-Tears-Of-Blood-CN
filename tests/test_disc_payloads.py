import io,struct,sys,unittest,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_disc_payloads import stream_archive,hash_stream,BorrowedPath

def fixture(duplicate=False):
    first=b'data';second=b'other';names=[b'first.adx',b'first.adx' if duplicate else b'second.adx']
    toc=b''.join(n.ljust(48,b'\0') for n in names)
    return b'AFS\0'+struct.pack('<I',2)+struct.pack('<4I',32,4,36,5)+struct.pack('<II',41,96)+first+second+toc

class DiscPayloadTests(unittest.TestCase):
    def test_upstream_borrowed_archive_readers(self):
        raw=fixture();stream=io.BytesIO(raw);archive,names=stream_archive(stream,len(raw))
        self.assertEqual(names,['first.adx','second.adx'])
        self.assertEqual(archive.read_entry(1,stream),b'other')
        self.assertFalse(stream.closed)
    def test_archive_bounds(self):
        raw=bytearray(fixture());struct.pack_into('<I',raw,12,100000)
        with self.assertRaisesRegex(ValueError,'entry bounds'):stream_archive(io.BytesIO(raw),len(raw))
    def test_name_duplicates(self):
        raw=fixture(True)
        with self.assertRaisesRegex(ValueError,'filename inventory'):stream_archive(io.BytesIO(raw),len(raw))
    def test_count_bounds(self):
        with self.assertRaisesRegex(ValueError,'count bounds'):stream_archive(io.BytesIO(b'AFS\0'+struct.pack('<I',200)),8)
    def test_hash_stream_bounded(self):
        sha,prefix=hash_stream(io.BytesIO(b'helloXYZ'),5)
        self.assertEqual(sha,hashlib.sha256(b'hello').hexdigest());self.assertEqual(prefix,b'hello')
    def test_truncated_stream(self):
        with self.assertRaisesRegex(ValueError,'truncated'):hash_stream(io.BytesIO(b'a'),2)
    def test_borrowed_path_readonly(self):
        with self.assertRaisesRegex(ValueError,'read-only'):BorrowedPath(io.BytesIO()).open('wb')
    def test_empty_stream(self):
        self.assertEqual(hash_stream(io.BytesIO(),0),(hashlib.sha256(b'').hexdigest(),b''))

if __name__=='__main__':unittest.main()
