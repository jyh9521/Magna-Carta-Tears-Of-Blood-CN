import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_class_defaults import class_body


class ClassDefaultsTests(unittest.TestCase):
    def fixture(self,script=0,defaults=b'\0'):
        table=dict(version=118,names=['None','Sample','Config','Caption'],imports=[{}],exports=[{}])
        export=dict(name='Sample',super_index=0)
        # Super, next, script-text, children, friendly-name; line/text position;
        # observed u32 and virtual script length.
        header=b'\0\0\0\0\x01'+struct.pack('<iiII',-1,-1,0,script)
        metadata=bytes(22)+struct.pack('<I',0x112)+bytes(16)+b'\0\0\0\x02\0'
        return header+metadata+defaults,table,export

    def test_zero_script_exact_boundary(self):
        s,t,e=self.fixture();r=class_body(s,t,e)
        self.assertTrue(r['defaults_complete'])
        self.assertEqual(r['property_block']['end'],len(s))
        self.assertEqual(r['class_flags'],0x112)

    def test_nonzero_virtual_size_is_not_disk_skip(self):
        s,t,e=self.fixture(script=100000)
        r=class_body(s,t,e)
        self.assertEqual(r['status'],'nonzero-bytecode-pending')
        self.assertFalse(r['defaults_complete'])
        self.assertNotIn('property_block',r)

    def test_default_string_coordinates(self):
        s,t,e=self.fixture(defaults=b'\x03\x5d\x04\x03OK\0\0')
        r=class_body(s,t,e);p=r['property_block']['properties'][0]
        self.assertEqual(p['text'],'OK')
        self.assertEqual(s[p['value_offset']:p['value_offset']+p['value_bytes']],b'\x03OK\0')

    def test_unknown_word_not_named_flags(self):
        s,t,e=self.fixture();s=s[:13]+struct.pack('<I',123)+s[17:]
        r=class_body(s,t,e)
        self.assertEqual(r['header']['observed_pre_script_word'],123)
        self.assertEqual(r['header']['observed_pre_script_word_semantic'],'unverified')

    def test_reference_bounds(self):
        s,t,e=self.fixture();s=b'\x02'+s[1:]
        with self.assertRaises(ValueError):class_body(s,t,e)

    def test_super_and_friendly_agreement(self):
        s,t,e=self.fixture()
        for altered in [dict(e,super_index=-1),dict(e,name='Other')]:
            with self.assertRaises(ValueError):class_body(s,t,altered)

    def test_truncation_and_trailing_refused(self):
        s,t,e=self.fixture()
        for bad in [s[:4],s[:-1],s+b'X']:
            with self.assertRaises(ValueError):class_body(bad,t,e)

    def test_version_gate(self):
        s,t,e=self.fixture();t['version']=119
        with self.assertRaises(ValueError):class_body(s,t,e)

if __name__=='__main__':unittest.main()
