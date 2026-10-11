import hashlib,struct,sys,unittest
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/p) for p in ('src','lib')]
from localization.text import rewrite_fpb_header
from translate.fpb import parse_fpb_raw

class Encoder:
    def encode(self,s):return s.encode('ascii')

class HeaderImportTests(unittest.TestCase):
    def fixture(self):return struct.pack('<7I',2,13,0,3,0,5,3)+struct.pack('<I',12)+b'abc!!defTAIL'
    def rewrite(self,b=None,key=13,digest=None,target='LONG'):
        return rewrite_fpb_header(b or self.fixture(),key,digest or hashlib.sha256(b'abc').hexdigest(),target,Encoder())
    def test_explicit_zero_and_tail_preserved(self):
        b,report=self.rewrite();h,w,p=parse_fpb_raw(b)
        self.assertEqual(struct.unpack_from('<III',h,4),(13,0,4));self.assertEqual(w,[(0,6,3)])
        self.assertEqual(p,b'LONG!!defTAIL');self.assertEqual(report['explicit_windows_preserved'],1)
    def test_shorter_prefix(self):self.assertEqual(parse_fpb_raw(self.rewrite(target='X')[0])[2],b'X!!defTAIL')
    def test_wrong_key(self):
        with self.assertRaisesRegex(ValueError,'identity'):self.rewrite(key=0)
    def test_wrong_hash(self):
        with self.assertRaisesRegex(ValueError,'hash'):self.rewrite(digest='0'*64)
    def test_no_empty_target(self):
        with self.assertRaises(ValueError):self.rewrite(target='')
    def test_header_overlap_rejected(self):
        b=bytearray(self.fixture());struct.pack_into('<I',b,20,2)
        with self.assertRaisesRegex(ValueError,'overlaps'):self.rewrite(b)
    def test_header_offset_rejected(self):
        b=bytearray(self.fixture());struct.pack_into('<I',b,8,1)
        with self.assertRaisesRegex(ValueError,'geometry'):self.rewrite(b)
    def test_header_bounds_rejected(self):
        b=bytearray(self.fixture());struct.pack_into('<I',b,12,99)
        with self.assertRaisesRegex(ValueError,'geometry'):self.rewrite(b)
    def test_only_header_no_windows(self):
        b=struct.pack('<5I',1,4,0,3,3)+b'abc';new,_=self.rewrite(b,key=4)
        self.assertEqual(parse_fpb_raw(new)[1],[]);self.assertEqual(parse_fpb_raw(new)[2],b'LONG')
    def test_control_order_preserved(self):
        b=struct.pack('<5I',1,13,0,3,3)+b'a$n'
        with self.assertRaisesRegex(ValueError,'protected'):self.rewrite(b,digest=hashlib.sha256(b'a$n').hexdigest())
    def test_existing_body_copy_supported(self):
        b=bytearray(self.fixture());b[-7:-4]=b'XYZ'
        new,_=self.rewrite(b);self.assertEqual(parse_fpb_raw(new)[2],b'LONG!!XYZTAIL')

if __name__=='__main__':unittest.main()
