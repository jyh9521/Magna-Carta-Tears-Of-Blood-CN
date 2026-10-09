import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from audit_elf_strings import spans, candidates, audit

class ElfStringsTests(unittest.TestCase):
    def test_nul_only(self):
        self.assertEqual(list(spans(b'abc\0tail')), [(0, b'abc')])
    def test_utf16_alignment(self):
        self.assertEqual(list(spans(b'xA\0B\0\0\0', 2, 1)), [(1, b'A\0B\0')])
    def test_invalid_alignment(self):
        with self.assertRaises(ValueError): list(spans(b'', 2, 2))
    def test_cp949(self):
        rows=candidates('테스트'.encode('cp949') + b'\0')
        row=next(r for r in rows if r['encoding']=='cp949')
        self.assertEqual(row['text'], '테스트'); self.assertFalse(row['editable'])
    def test_unicode_both_orders(self):
        for codec in ('utf-16-le','utf-16-be'):
            rows=candidates('테스트'.encode(codec)+b'\0\0')
            self.assertTrue(any(r['text']=='테스트' and r['encoding']==codec for r in rows))
    def test_nonprintable(self):
        self.assertFalse(any(r['encoding']=='cp949' for r in candidates(b'a\x01b\0')))
    def test_short_and_tail(self):
        self.assertEqual(candidates(b'A\0unterminated'), [])
    def test_identity(self):
        with self.assertRaises(ValueError): audit(b'not ELF')
