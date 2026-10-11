import sys,struct,unittest
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/p) for p in ('tools','lib')]
from audit_native_method_registration import pointer,bind_inline
from audit_native_playbook import native_records,lookup


NAME='intUFixtureexecRead'
class Image:
    def __init__(self):
        self.blob=bytearray(4096)
        self.blob[0x100:0x100+len(NAME)+1]=NAME.encode()+b'\0'
        struct.pack_into('<I',self.blob,0x200,0x100)
        struct.pack_into('<3I',self.blob,0x300,0,0xffffffff,0x500)
        struct.pack_into('<10I',self.blob,0x400,0x3c040000,0x24840300,
            0x3c030000,0x24630204,0xc4820000,0xc4810004,0xc4800008,
            0xe4620000,0xe4610004,0xe4600008)
        struct.pack_into('<2I',self.blob,0x500,0x03e00008,0)
    def to_offset(self,v):
        if not 0<=v<len(self.blob):raise ValueError('bounds')
        return v
    to_va=to_offset


class RegistrationTests(unittest.TestCase):
    def test_exact_copy(self):self.assertEqual(bind_inline(Image(),NAME)['callback'],'0x500')
    def test_negative_low(self):self.assertEqual(pointer(0x3c040049,0x2484fc90,4),0x48fc90)
    def test_wrong_upper_register(self):
        with self.assertRaises(ValueError):pointer(0x3c030049,0x2484fc90,4)
    def test_nonzero_lui_rs(self):
        with self.assertRaises(ValueError):pointer(0x3c240049,0x2484fc90,4)
    def test_unqualified_name(self):
        with self.assertRaises(ValueError):bind_inline(Image(),'Read')
    def test_duplicate_string(self):
        i=Image();i.blob[0x800:0x800+len(NAME)+1]=NAME.encode()+b'\0'
        with self.assertRaisesRegex(ValueError,'ambiguous'):bind_inline(i,NAME)
    def test_duplicate_table(self):
        i=Image();struct.pack_into('<I',i.blob,0x900,0x100)
        with self.assertRaisesRegex(ValueError,'ambiguous'):bind_inline(i,NAME)
    def test_bad_copy_word(self):
        i=Image();struct.pack_into('<I',i.blob,0x410,0)
        with self.assertRaisesRegex(ValueError,'copy missing'):bind_inline(i,NAME)
    def test_bad_descriptor(self):
        i=Image();struct.pack_into('<I',i.blob,0x304,0)
        with self.assertRaisesRegex(ValueError,'descriptor'):bind_inline(i,NAME)
    def test_missing_return(self):
        i=Image();struct.pack_into('<I',i.blob,0x500,0)
        with self.assertRaisesRegex(ValueError,'return'):bind_inline(i,NAME)
    def test_callback_call(self):
        i=Image();struct.pack_into('<4I',i.blob,0x500,0x0c000200,0,0x03e00008,0)
        self.assertEqual(bind_inline(i,NAME)['bounded_callback_jals'],[{'va':'0x500','target':'0x800'}])

    def test_explicit_long_callback_bound(self):
        i=Image();struct.pack_into('<I',i.blob,0x500,0);struct.pack_into('<2I',i.blob,0x700,0x03e00008,0)
        with self.assertRaisesRegex(ValueError,'return'):bind_inline(i,NAME)
        result=bind_inline(i,NAME,callback_limit=1024);self.assertEqual(result['callback_end'],'0x708');self.assertEqual(result['callback_scan_limit'],1024)
    def test_invalid_callback_windows(self):
        for size in (0,4,9,-4,65540,True,512.0):
            with self.subTest(size=size),self.assertRaisesRegex(ValueError,'aligned'):bind_inline(Image(),NAME,callback_limit=size)
    def test_return_delay_slot_must_fit_bound(self):
        i=Image();struct.pack_into('<I',i.blob,0x500,0);struct.pack_into('<2I',i.blob,0x6fc,0x03e00008,0)
        with self.assertRaisesRegex(ValueError,'return'):bind_inline(i,NAME)
        self.assertEqual(bind_inline(i,NAME,callback_limit=516)['callback_end'],'0x704')


class HeaderRecordTests(unittest.TestCase):
    def fixture(self,header_key=13):
        return struct.pack('<7I',2,header_key,0,3,0,3,3)+struct.pack('<I',6)+b'abcdef'
    def test_header_is_actual_record(self):
        records,pool=native_records(self.fixture());self.assertEqual(records,[(13,0,3),(0,3,3)])
        self.assertEqual(pool,b'abcdef')
    def test_header_key_not_assumed_zero(self):self.assertEqual(lookup(native_records(self.fixture())[0],13),0)
    def test_explicit_zero_distinct(self):self.assertEqual(lookup(native_records(self.fixture())[0],0),1)
    def test_first_match(self):self.assertEqual(lookup(native_records(self.fixture(0))[0],0),0)
    def test_missing_key(self):self.assertIsNone(lookup(native_records(self.fixture())[0],99))
    def test_header_bounds(self):
        b=bytearray(self.fixture());struct.pack_into('<I',b,12,99)
        with self.assertRaisesRegex(ValueError,'bounds'):native_records(b)
    def test_no_explicit_records(self):
        records,pool=native_records(struct.pack('<5I',1,9,0,3,3)+b'abc')
        self.assertEqual(records,[(9,0,3)]);self.assertEqual(pool,b'abc')


if __name__=='__main__':unittest.main()
