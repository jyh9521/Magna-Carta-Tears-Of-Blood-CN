import sys
from pathlib import Path
import struct
import unittest
import zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_container_payloads import unpack_chunks,package_probe,probe_all_packages,streamed_tables


def stream_fixture():
    names=b''.join(bytes([len(n)+1])+n+b'\0'+b'\0'*4 for n in [b'None',b'Class',b'Texture'])
    imports=b'\1\1'+b'\0'*4+b'\2'
    exports=b'\x81\0'+b'\0'*4+b'\2'+b'\0'*4+b'\3\x48\3'
    header=struct.pack('<9I',0x9e2a83c1,118|(14<<16),1,3,64,1,210,1,203)+b'\0'*28
    return b'../Textures/fixture.utx'.ljust(256,b'\0')+struct.pack('<II',0,240)+header+names+imports+exports+b'payload'


class ContainerPayloadTests(unittest.TestCase):
    def test_upstream_chunk_decompression_and_zero_padding(self):
        raw=b'text fixture';compressed=zlib.compress(raw)
        payload,count=unpack_chunks(struct.pack('<II',len(raw),len(compressed))+compressed+b'\0'*16)
        self.assertEqual((payload,count),(raw,1))

    def test_declared_length_checked(self):
        compressed=zlib.compress(b'abc')
        with self.assertRaisesRegex(ValueError,'mismatch'):
            unpack_chunks(struct.pack('<II',4,len(compressed))+compressed)

    def test_unconsumed_chunk_bytes_checked(self):
        compressed=zlib.compress(b'abc')+b'x'
        with self.assertRaisesRegex(ValueError,'mismatch'):
            unpack_chunks(struct.pack('<II',3,len(compressed))+compressed)

    def test_truncated_chunk_checked(self):
        with self.assertRaisesRegex(ValueError,'bounds'):
            unpack_chunks(struct.pack('<II',3,100)+b'x')

    def test_no_package_not_a_text_exclusion(self):
        self.assertIsNone(package_probe(b'not a package'))

    def test_bad_package_header_checked(self):
        with self.assertRaisesRegex(ValueError,'truncated'):
            package_probe(bytes.fromhex('c1832a9e'))

    def test_stream_tables_use_consecutive_not_original_offsets(self):
        row=probe_all_packages(stream_fixture())[0]
        self.assertEqual(row['names'],['None','Class','Texture'])
        self.assertEqual(row['exports'][0]['class'],'Texture')
        self.assertEqual(row['exports'][0]['declared_offset'],200)
        self.assertEqual(row['exports'][0]['serial_mapping'],'unresolved')
        self.assertNotIn('serial_sha256',row['exports'][0])

    def test_multiple_embedded_packages(self):
        self.assertEqual(len(probe_all_packages(stream_fixture()*2)),2)

    def test_pixels_magic_not_treated_as_package(self):
        self.assertEqual(probe_all_packages(b'pixels'+bytes.fromhex('c1832a9e')+b'\0'*100),[])

    def test_stream_original_size_bounds(self):
        blob=bytearray(stream_fixture());struct.pack_into('<I',blob,260,64)
        with self.assertRaisesRegex(ValueError,'original table bounds'):
            streamed_tables(blob,264)


if __name__=='__main__':unittest.main()
