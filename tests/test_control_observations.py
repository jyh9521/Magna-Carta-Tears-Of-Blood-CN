import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_control_observations import observations
from localization.text import protected_tokens
class ControlObservationTests(unittest.TestCase):
 def test_known_tokens_not_unknown(self):self.assertEqual(observations('$n$D04%s{0}<Tag>',{}),[])
 def test_percent_candidate(self):self.assertEqual(observations('20% 할인',{})[0]['classification'],'numeric-percent-candidate')
 def test_exact_angle_link(self):self.assertEqual(observations('<천, 하늘>',{'천, 하늘':[dict(id='item')]})[0]['name_source_links'],[dict(id='item')])
 def test_no_trimmed_link(self):self.assertEqual(observations('< 천, 하늘 >',{'천, 하늘':[dict(id='item')]})[0]['name_source_links'],[])
 def test_arrow_candidate(self):self.assertEqual(observations('도장->유파',{})[0]['classification'],'arrow-candidate')
 def test_control_bytes_kept(self):self.assertEqual([x['codepoint'] for x in observations('a\t\n\0',{})],[9,10,0])
 def test_unknown_not_skipped(self):self.assertEqual(observations('$Z{bad}',{})[0]['classification'],'unknown-special')
 def test_validator_stays_strict(self):
  with self.assertRaises(ValueError):protected_tokens('20% 할인')
if __name__=='__main__':unittest.main()
