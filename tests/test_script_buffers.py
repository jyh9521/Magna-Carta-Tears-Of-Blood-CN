import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from extract_script_buffers import text_buffer,literals,packed_cp949_view
class ScriptBuffersTests(unittest.TestCase):
    def test_narrow(self):self.assertEqual(text_buffer(bytes(9)+b'\x04abc\0')['text'],'abc')
    def test_wide(self):self.assertEqual(text_buffer(bytes(9)+b'\x82'+ '한\0'.encode('utf-16-le'))['text'],'한')
    def test_prefix(self):
        with self.assertRaises(ValueError):text_buffer(b'x'+bytes(10))
    def test_size(self):
        with self.assertRaises(ValueError):text_buffer(bytes(9)+b'\x04abc\0x')
    def test_terminator(self):
        with self.assertRaises(ValueError):text_buffer(bytes(9)+b'\x03abc')
    def test_zero(self):
        with self.assertRaises(ValueError):text_buffer(bytes(10))
    def test_comments_names_escapes(self):
        text='// "skip"\n/* "skip" */ \'Name\' "a\\\"b"'
        rows=literals(text);self.assertEqual(len(rows),1);self.assertEqual(rows[0]['raw_literal'],'"a\\\"b"');self.assertEqual(rows[0]['line'],2)
    def test_truncation(self):
        for text in ('/* foo','"foo'):
            with self.assertRaises(ValueError):literals(text)

    def test_packed_reference(self):
        self.assertEqual(packed_cp949_view('맙엁쎼'), '바탕체')
        self.assertEqual(packed_cp949_view('샌쇶 룰뗥'), '이지 모드')
    def test_packed_invalid(self):
        with self.assertRaises(ValueError):packed_cp949_view('é')
