import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_object_properties import Reader
from audit_replication_defaults import replication_script


class ReplicationDefaultsTests(unittest.TestCase):
    table=dict(imports=[{}],exports=[{}]*63)
    def read(self,raw,size):return replication_script(Reader(raw),size,self.table)

    def test_reference_virtual_expansion(self):
        r=self.read(b'\x48\x01',5)
        self.assertEqual(r['disk_bytes'],2)
        self.assertEqual(r['virtual_bytes'],5)
        self.assertFalse(r['execution_verified'])

    def test_nested_native_with_parameter_end(self):
        r=self.read(b'\x82\x2d\x48\x01\x16',8)
        self.assertEqual([t['opcode'] for t in r['tokens']],[130,45,72,22])

    def test_direct_native_threshold(self):
        r=self.read(b'\x72\x48\x01\x2a\x16',8)
        self.assertEqual(r['references'][0]['value'],1)

    def test_context_and_cast(self):
        r=self.read(b'\x19\x48\x01\0\0\0\x2e\x01\x28',15)
        self.assertEqual(len(r['references']),2)

    def test_skip_and_conversion(self):
        r=self.read(b'\x18\x07\0\x39\x3a\x24\x04',7)
        self.assertEqual(len(r['tokens']),4)

    def test_exact_virtual_end(self):
        for size in [1,4,6]:
            with self.assertRaises(ValueError):self.read(b'\x48\x01',size)

    def test_unknown_and_bad_reference(self):
        for raw,size in [(b'\x69',1),(b'\x48\x40\x01',5),(b'\x82',2)]:
            with self.assertRaises(ValueError):self.read(raw,size)

    def test_recursion_bound(self):
        with self.assertRaises(ValueError):self.read(b'\x2d'*70+b'\x28',71)

if __name__=='__main__':unittest.main()
