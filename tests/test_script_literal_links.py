import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_script_literal_links import search_literal
class ScriptLiteralLinksTests(unittest.TestCase):
    def export(self,**kw):return dict(index=1,name='Fn',**{'class':'Function'},outer=2,offset=0,size=8,**kw)
    def test_hit(self):
        hits=search_literal(b'\x1fabc\0xyz',[self.export()],'abc','cp949')
        self.assertEqual(len(hits),1);self.assertEqual(hits[0]['preceding_byte'],31);self.assertFalse(hits[0]['instruction_boundary_verified'])
    def test_textbuffer_exclusion(self):
        e=self.export();e['class']='TextBuffer';self.assertEqual(search_literal(b'\x1fabc\0xyz',[e],'abc','cp949'),[])
    def test_boundary(self):
        e=self.export();e['size']=4;self.assertEqual(search_literal(b'\x1fabc\0xyz',[e],'abc','cp949'),[])
    def test_zero_empty(self):self.assertEqual(search_literal(b'\x1fabc\0xyz',[self.export()],'','cp949'),[])
    def test_wide(self):
        e=self.export();self.assertEqual(len(search_literal(b'A\0B\0\0\0xx',[e],'AB','utf-16-le')),1)
    def test_no_prefix(self):self.assertEqual(search_literal(b'abc\0xxxx',[self.export()],'abc','cp949')[0]['preceding_byte'],None)
    def test_bad_bounds(self):
        e=self.export();e['size']=9
        with self.assertRaises(ValueError):search_literal(b'abc\0xxxx',[e],'abc','cp949')
    def test_encoding(self):
        with self.assertRaises(UnicodeError):search_literal(bytes(8),[self.export()],'😀','cp949')
