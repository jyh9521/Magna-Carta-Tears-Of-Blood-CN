import sys
import struct
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from audit_stream_resource_chain import parse_chain, attach_contexts
import font_poc as core


def fixture(name='a.val', body=b'payload'):
    path=('..\\ValueData\\'+name).encode('ascii')
    return path.ljust(128,b'\0')+struct.pack('<I',len(body))+body


class ResourceChainTests(unittest.TestCase):
    def test_exact_body(self):
        b=fixture();self.assertEqual(parse_chain(b,0,len(b),{'a.val':b'payload'})[0]['bytes'],7)
    def test_two_resources(self):
        b=fixture()+fixture('b.val');self.assertEqual(len(parse_chain(b,0,len(b),{'a.val':b'payload','b.val':b'payload'})),2)
    def test_missing_identity(self):
        b=fixture()
        with self.assertRaises(ValueError):parse_chain(b,0,len(b),{})
    def test_mismatch(self):
        b=fixture()
        with self.assertRaises(ValueError):parse_chain(b,0,len(b),{'a.val':b'PAYLOAD'})
    def test_duplicate_identity(self):
        b=fixture()*2
        with self.assertRaises(ValueError):parse_chain(b,0,len(b),{'a.val':b'payload'})
    def test_bad_padding(self):
        b=bytearray(fixture());b[127]=1
        with self.assertRaises(ValueError):parse_chain(bytes(b),0,len(b),{'a.val':b'payload'})
    def test_truncated(self):
        b=fixture()[:-1]
        with self.assertRaises(ValueError):parse_chain(b,0,len(b),{'a.val':b'payload'})
    def test_empty_body(self):
        b=fixture(body=b'')
        with self.assertRaises(ValueError):parse_chain(b,0,len(b),{'a.val':b''})
    def test_bad_path(self):
        b=fixture().replace(b'..\\',b'../',1)
        with self.assertRaises(ValueError):parse_chain(b,0,len(b),{'a.val':b'payload'})
    def context(self,b,start,length,category='unresolved-byte-context'):
        return dict(offset=start,bytes=length,source_sha256=core.digest(b[start:start+length]),category=category,editable=False)
    def test_body_context(self):
        b=fixture();chain=parse_chain(b,0,len(b),{'a.val':b'payload'});old=[self.context(b,132,7)]
        self.assertEqual(attach_contexts(old,b,chain)[0]['category'],'source-identical-resource-body');self.assertEqual(old[0]['category'],'unresolved-byte-context')
    def test_cross_boundary_not_assigned(self):
        b=fixture();chain=parse_chain(b,0,len(b),{'a.val':b'payload'})
        self.assertEqual(attach_contexts([self.context(b,131,2)],b,chain)[0]['category'],'unresolved-byte-context')
    def test_known_context_preserved(self):
        b=fixture();old=[self.context(b,132,7,'resource-mirror')]
        self.assertEqual(attach_contexts(old,b,parse_chain(b,0,len(b),{'a.val':b'payload'})),old)
    def test_wrapper_context(self):
        b=fixture();self.assertEqual(attach_contexts([self.context(b,0,10)],b,parse_chain(b,0,len(b),{'a.val':b'payload'}))[0]['category'],'source-resource-wrapper')
    def test_hash_guard(self):
        b=fixture();row=self.context(b,132,7);row['source_sha256']='0'*64
        with self.assertRaises(ValueError):attach_contexts([row],b,[])


if __name__ == '__main__':unittest.main()
