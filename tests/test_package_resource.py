"""Synthetic package relocation tests; no proprietary package fixtures."""
from pathlib import Path
import hashlib
import struct
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from font_resource import encode_compact
from package_resource import export_records, replace_exports


def sha(data): return hashlib.sha256(data).hexdigest()


def fixture(payload=b'abc'):
    names = b'\x05test\0' + bytes(4)
    offset = 64 + len(names)
    prefix = bytes(11)
    table = prefix + encode_compact(len(payload)) + encode_compact(offset) + prefix + b'\0'
    header = struct.pack('<9I', 0x9e2a83c1, (15 << 16) | 118, 1, 1, 64, 2, offset + len(payload), 0, 0)
    return header + bytes(64 - len(header)) + names + payload + table


class PackageResourceTests(unittest.TestCase):
    def build(self, blob=None, replacements=None, **kw):
        blob = fixture() if blob is None else blob
        return replace_exports(blob, {1: b'expanded-resource'} if replacements is None else replacements,
                               expected_sha256=kw.get('hash', sha(blob)), expected_version=kw.get('version', (118, 15)))

    def test_relocated_payload(self):
        blob=fixture(); new, report=self.build(blob)
        records,end=export_records(new,expected_version=(118,15))
        self.assertEqual(new[records[0]['offset']:records[0]['offset']+records[0]['size']],b'expanded-resource')
        self.assertEqual(end,len(new));self.assertEqual(report['changed'][0]['old_offset'],74)

    def test_original_bytes_preserved(self):
        blob=fixture();new,_=self.build(blob)
        self.assertEqual(blob[:24],new[:24]);self.assertEqual(blob[28:],new[28:len(blob)])

    def test_empty_export_preserved(self):
        before,_=export_records(fixture(),expected_version=(118,15));new,_=self.build()
        after,_=export_records(new,expected_version=(118,15));self.assertEqual(before[1],after[1])

    def test_compact_size_growth(self):
        for count in (63,64,8191,8192):
            new,_=self.build(replacements={1:b'x'*count})
            entries,_=export_records(new,expected_version=(118,15));self.assertEqual(entries[0]['size'],count)

    def test_deterministic(self): self.assertEqual(self.build(),self.build())
    def test_bad_hash(self):
        with self.assertRaisesRegex(ValueError,'fingerprint'):self.build(hash='0'*64)
    def test_bad_version(self):
        with self.assertRaisesRegex(ValueError,'version'):self.build(version=(117,15))
    def test_unknown_index(self):
        for index in (0,3,-1,True,'1'):
            with self.assertRaises(ValueError):self.build(replacements={index:b'x'})
    def test_no_replacements(self):
        with self.assertRaises(ValueError):self.build(replacements={})
    def test_bad_payload(self):
        for payload in (b'',bytearray(b'x'),'x'):
            with self.assertRaises(ValueError):self.build(replacements={1:payload})
    def test_zero_size_target(self):
        with self.assertRaisesRegex(ValueError,'zero-size'):self.build(replacements={2:b'x'})
    def test_truncated_header(self):
        with self.assertRaises(ValueError):self.build(blob=fixture()[:35])
    def test_bad_signature(self):
        with self.assertRaises(ValueError):self.build(blob=b'xxxx'+fixture()[4:])
    def test_bad_export_offset(self):
        blob=bytearray(fixture());struct.pack_into('<I',blob,24,len(blob))
        with self.assertRaises(ValueError):self.build(blob=bytes(blob))
    def test_truncated_export(self):
        with self.assertRaises(ValueError):self.build(blob=fixture()[:-1])
    def test_payload_outside_package(self):
        blob=fixture();table=struct.unpack_from('<I',blob,24)[0]
        blob=blob[:table+11]+encode_compact(8192)+blob[table+12:]
        with self.assertRaises(ValueError):self.build(blob=blob)
    def test_unknown_flags(self):
        blob=bytearray(fixture());struct.pack_into('<I',blob,8,0x02000000)
        with self.assertRaisesRegex(ValueError,'flags'):self.build(blob=bytes(blob))


if __name__ == '__main__': unittest.main()
