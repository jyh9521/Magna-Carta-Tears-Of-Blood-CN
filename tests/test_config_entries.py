import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_config_entries import parse_lines,exact_positions
class ConfigEntryTests(unittest.TestCase):
 def test_value(self):
  rows,entries=parse_lines(b'[S]\r\nKey=Value\r\n');self.assertEqual(entries[0]['value'],'Value');self.assertEqual(entries[0]['value_offset'],9)
 def test_empty(self):self.assertEqual(parse_lines(b'[S]\nKey=\n')[1][0]['value'],'')
 def test_duplicate_key_retained(self):self.assertEqual(len(parse_lines(b'[S]\nK=1\nK=2\n')[1]),2)
 def test_duplicate_section(self):self.assertEqual(parse_lines(b'[S]\nK=1\n[S]\nK=2')[1][-1]['section_occurrence'],2)
 def test_comment_blank(self):self.assertEqual([r['kind'] for r in parse_lines(b'; x\n# y\n\n')[0]],['comment','comment','blank'])
 def test_first_equals(self):self.assertEqual(parse_lines(b'[S]\nK=(X=1,Y=2)')[1][0]['value'],'(X=1,Y=2)')
 def test_space_preserved(self):self.assertEqual(parse_lines(b'[S]\n K = Value ')[1][0]['value'],' Value ')
 def test_placeholders(self):self.assertEqual(parse_lines(b'[S]\nK=%s %i %s')[1][0]['placeholder_candidates'],['%s','%i','%s'])
 def test_nonascii(self):
  with self.assertRaises(ValueError):parse_lines(b'[S]\nK=\xff')
 def test_nul(self):
  with self.assertRaises(ValueError):parse_lines(b'[S]\nK=A\0')
 def test_missing_section(self):
  with self.assertRaises(ValueError):parse_lines(b'K=V')
 def test_empty_key(self):
  with self.assertRaises(ValueError):parse_lines(b'[S]\n =V')
 def test_unknown_line(self):
  with self.assertRaises(ValueError):parse_lines(b'[S]\nunknown')
 def test_empty_section(self):
  with self.assertRaises(ValueError):parse_lines(b'[]')
 def test_exact_occurrences(self):self.assertEqual(exact_positions(b'AAAA',b'AA'),[0,1,2])
 def test_empty_needle(self):
  with self.assertRaises(ValueError):exact_positions(b'A',b'')
if __name__=='__main__':unittest.main()
