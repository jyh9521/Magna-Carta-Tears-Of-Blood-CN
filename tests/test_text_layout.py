import unittest,sys,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','src','lib')]
from text_layout import wrap,atoms,CLOSING
from apply_text_layout import rewrite_bound
class LayoutTests(unittest.TestCase):
 def test_long_name(self):self.assertEqual(atoms('艾尔泽诺尔·罗伊德·理查德·萨·格拉诺夫',['艾尔泽诺尔·罗伊德·理查德·萨·格拉诺夫']),['艾尔泽诺尔·罗伊德·理查德·萨·格拉诺夫'])
 def test_paragraph_punctuation(self):self.assertEqual(wrap('甲乙。$n$n……丙丁。',len,6,[]),'甲乙。……$n$n丙丁。')
 def test_numeric(self):self.assertEqual(atoms('100%2倍30%',[]),['100%','2倍','30%'])
 def test_terms(self):self.assertEqual(atoms('三位一体驱动', ['三位一体','三位一体驱动']),['三位一体驱动'])
 def test_term_rejoin(self):self.assertEqual(wrap('三位$n一体',len,4,['三位一体']),'三位一体')
 def test_commas(self):self.assertEqual(wrap('一二三，四五。',len,4,[]),'一二三，$n四五。')
 def test_sentence(self):self.assertEqual(wrap('一二。三四。',len,5,[]),'一二。$n三四。')
 def test_paragraphs(self):self.assertEqual(wrap('甲$n$n乙',len,4,[]),'甲$n$n乙')
 def test_numeric_wrap(self):self.assertEqual(wrap('达到100%，2倍。',len,7,[]),'达到100%，$n2倍。')
 def test_long_term_fail(self):
  with self.assertRaises(ValueError):wrap('三位一体',len,3,['三位一体'])
 def test_invalid_width(self):
  with self.assertRaises(ValueError):wrap('甲',len,0,[])
 def test_trailing_exclaim(self):self.assertNotIn('$n！',wrap('甲乙。！丙丁。',len,5,[]))
 def test_ellipsis(self):self.assertNotIn('$n…',wrap('甲乙。……丙丁。',len,7,[]))
 def fixture(self):
  pool=b'ab\0gapcd\0tail';return struct.pack('<I6II',2,0,0,3,42,6,3,len(pool))+pool+b'opaque'
 def entry(self):return dict(record_index=0,key=0,offset=0,length=3,old_hex='616200',new_hex='6162246e00',previous_target='甲乙',target='甲$n乙')
 def test_header_record_and_tail(self):
  new=rewrite_bound(self.fixture(),[self.entry()]);self.assertEqual(struct.unpack_from('<III',new,16),(42,8,3));self.assertTrue(new.endswith(b'tailopaque'));self.assertIn(b'ab$n\0gapcd',new)
 def test_wrong_bytes_fail(self):
  q=self.entry();q['old_hex']='626300'
  with self.assertRaises(ValueError):rewrite_bound(self.fixture(),[q])
 def test_changed_content_fail(self):
  q=self.entry();q['target']='甲丙'
  with self.assertRaises(ValueError):rewrite_bound(self.fixture(),[q])
 def test_duplicate_fail(self):
  with self.assertRaises(ValueError):rewrite_bound(self.fixture(),[self.entry(),self.entry()])
if __name__=='__main__':unittest.main()
