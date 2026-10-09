import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_object_properties import Reader,property_block,string_value,HAS_STACK


class ObjectPropertiesTests(unittest.TestCase):
    def test_empty_prefix_retains_native_tail(self):
        r=property_block(b'\0native',['None'])
        self.assertEqual(r['native_tail_bytes'],6)
        self.assertFalse(r['native_semantics_verified'])

    def test_stack_u32_latent_and_optional_offset(self):
        raw=b'\x81\x81'+struct.pack('<QI',0xffffffffffffffff,120)+b'\0\0'
        r=property_block(raw,['None'],HAS_STACK)
        self.assertEqual(r['start'],15)
        self.assertEqual(r['stack']['latent_action'],120)
        self.assertEqual(r['native_tail_bytes'],0)

    def test_null_node_has_no_offset(self):
        r=property_block(b'\0\0'+bytes(12)+b'\0',['None'],HAS_STACK)
        self.assertEqual(r['start'],14)
        self.assertIsNone(r['stack']['code_offset'])

    def test_bool_flag_not_array_or_payload(self):
        r=property_block(b'\x01\x83\0',['None','Visible'])
        self.assertEqual(r['properties'][0]['value_bytes'],0)
        self.assertTrue(r['properties'][0]['bool_value'])

    def test_size_encodings(self):
        for code,size,encoded in [(0,1,b''),(1,2,b''),(2,4,b''),(3,12,b''),(4,16,b''),
                (5,7,b'\x07'),(6,257,struct.pack('<H',257)),(7,300,struct.pack('<I',300))]:
            raw=bytes((1,(code<<4)|1))+encoded+bytes(size)+b'\0'
            self.assertEqual(property_block(raw,['None','Data'])['properties'][0]['value_bytes'],size)

    def test_array_indices(self):
        for encoded,index in [(b'\x05',5),(b'\x81\x02',258),(b'\xc0\x01\x02\x03',66051)]:
            r=property_block(b'\x01\x81'+encoded+b'X\0',['None','Array'])
            self.assertEqual(r['properties'][0]['array_index'],index)

    def test_struct_name_precedes_size(self):
        r=property_block(b'\x01\x2a\x02'+bytes(4)+b'\0',['None','Location','Vector'])
        self.assertEqual(r['properties'][0]['structure'],'Vector')
        self.assertEqual(r['properties'][0]['value_offset'],3)

    def test_string_property_strict_cp949(self):
        raw='测试'.encode('utf-16-le')+b'\0\0';v=b'\x83'+raw
        r=property_block(b'\x01\x5d'+bytes([len(v)])+v+b'\0',['None','Caption'])
        self.assertEqual(r['properties'][0]['text'],'测试')
        v=b'\x05Test\0'
        self.assertEqual(string_value(v)['text'],'Test')

    def test_empty_string(self):
        self.assertEqual(string_value(b'\0')['text'],'')
        with self.assertRaises(ValueError):string_value(b'\0X')

    def test_malformed_inputs(self):
        for raw in [b'',b'\x01',b'\x01\x21X',b'\x02\0',b'\x01\0',b'\x01\x81\xc0']:
            with self.assertRaises(ValueError):property_block(raw,['None','Data'])
        for raw in [b'\x02X',b'\x02XY',b'\x83\0',b'\x02\xff\0']:
            with self.assertRaises((ValueError,UnicodeError)):string_value(raw)

    def test_reader_bounds(self):
        with self.assertRaises(ValueError):Reader(b'',1)
        with self.assertRaises(ValueError):Reader(b'').index()
        with self.assertRaises(ValueError):Reader(b'').take(-1)

if __name__=='__main__':unittest.main()
