import sys
import struct
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from extract_record_fields import extract, layout


def fixture(ext,kind,stride,count=1):
    blob = bytearray(struct.pack('<II',count,kind)+bytes(stride*count))
    for i in range(count):
        struct.pack_into('<I',blob,8+i*stride,i)
    return blob


class RecordFieldTests(unittest.TestCase):
    def test_fds_fields_and_ids(self):
        blob = fixture('.fds',4,2052,2)
        blob[12:16] = b'ABCD'
        result = extract('fixture.fds',bytes(blob))
        self.assertEqual(len(result['entries']),8)
        self.assertEqual(result['entries'][4]['offset'],2064)
        self.assertEqual(result['entries'][4]['record_id'],1)
        self.assertFalse(result['entries'][0]['editable'])

    def test_gft_short_geometry(self):
        result = extract('fixture.gft',bytes(fixture('.gft',23,822)))
        self.assertEqual([r['field_span'] for r in result['entries']],[70]*11)
        self.assertEqual(result['entries'][0]['offset'],16)
        self.assertEqual(result['entries'][10]['offset'],756)

    def test_gft_long_geometry(self):
        result = extract('fixture.gft',bytes(fixture('.gft',23,10307)))
        self.assertEqual([r['field_span'] for r in result['entries']],[1000]*8+[255]+[1000]*2)
        self.assertEqual(result['entries'][9]['offset'],8307)

    def test_odd_geometry(self):
        result = extract('fixture.odd',bytes(fixture('.odd',12,560)))
        self.assertEqual([r['offset'] for r in result['entries']],[16,96,336])
        self.assertEqual([r['field_span'] for r in result['entries']],[80,240,200])

    def test_odd_metadata_only(self):
        result = extract('fixture.odd',bytes(fixture('.odd',4,20)))
        self.assertEqual(result['entries'],[])
        self.assertEqual(len(result['records'][0]['metadata'][0]['raw_hex']),40)

    def test_no_replacement_of_failed_decode(self):
        blob = fixture('.fds',4,2052);blob[12]=0xff
        result = extract('fixture.fds',bytes(blob))
        self.assertEqual(result['entries'][0]['decode'],'failed')
        self.assertEqual(result['entries'][0]['raw_hex'],'ff')

    def test_unknown_layout_rejected(self):
        for blob in [b'bad',struct.pack('<II',0,23),bytes(fixture('.gft',23,821)),bytes(fixture('.gft',24,822))]:
            with self.assertRaises(ValueError):
                layout(blob,'.gft')

    def test_duplicate_id_rejected(self):
        blob = fixture('.fds',4,2052,2);struct.pack_into('<I',blob,2060,0)
        with self.assertRaisesRegex(ValueError,'duplicate record id'):
            extract('fixture.fds',bytes(blob))

    def test_nonzero_padding_rejected(self):
        blob = fixture('.fds',4,2052);blob[14]=65
        with self.assertRaisesRegex(ValueError,'padding'):
            extract('fixture.fds',bytes(blob))

    def test_missing_nul_rejected(self):
        blob = fixture('.fds',4,2052);blob[12:524]=b'A'*512
        with self.assertRaisesRegex(ValueError,'unterminated'):
            extract('fixture.fds',bytes(blob))


if __name__ == '__main__':
    unittest.main()
