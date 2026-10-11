import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('tools','lib','src')]
from audit_literal_control_readings import structures,validate_reading,audit
from font_poc import digest
class LiteralControlReadingTests(unittest.TestCase):
 def test_numeric_percent_preserved(self):self.assertEqual(structures('20% 할인')[0],['20%'])
 def test_known_printf_remains_protected(self):self.assertEqual(structures('%d %s %%')[0],['%d','%s','%%'])
 def test_page_and_delay_preserved(self):self.assertEqual(structures('$D06가$n나')[0],['$D06','$n'])
 def test_canonical_names_in_brackets(self):self.assertEqual(validate_reading('<바람>과 <물>','<风>与<水>',{'바람':'风','물':'水'})['canonical_bracket_names'],2)
 def test_wrong_bracket_name_rejected(self):
  with self.assertRaisesRegex(ValueError,'canonical'):validate_reading('<바람>','<水>',{'바람':'风'})
 def test_percent_value_changed_rejected(self):
  with self.assertRaisesRegex(ValueError,'structures'):validate_reading('20% 할인','优惠30%',{})
 def test_numeric_order_changed_rejected(self):
  with self.assertRaisesRegex(ValueError,'numeric'):validate_reading('10개 20%','20%优惠，购买10件',{})
 def test_arrow_retained(self):self.assertEqual(structures('도장->유파')[0],['->'])
 def test_arrow_changed_rejected(self):
  with self.assertRaisesRegex(ValueError,'structures'):validate_reading('도장->유파','道场到流派',{})
 def test_unknown_markup_rejected(self):
  with self.assertRaisesRegex(ValueError,'unknown'):structures('$z')
 def test_control_bytes_rejected(self):
  for text in ('가\n','가\t','가\0'):
   with self.subTest(text=text),self.assertRaisesRegex(ValueError,'control bytes'):structures(text)
 def test_unbalanced_angles_rejected(self):
  for text in ('<가','가>','<<가>'):
   with self.subTest(text=text),self.assertRaises(ValueError):structures(text)
 def test_percent_without_number_rejected(self):
  with self.assertRaisesRegex(ValueError,'unbound'):structures('가%나')
 def test_leading_punctuation_rejected(self):
  with self.assertRaisesRegex(ValueError,'leading'):validate_reading('가$n나','甲$n，乙',{})
 def test_profile_has94_unique_reviewed_not_imported(self):
  p=json.loads((ROOT/'locales/zh-CN/proofreading/literal-control-readings.json').read_text('utf8'));self.assertEqual(len(p['entries']),94);self.assertEqual(len({e['id'] for e in p['entries']}),94);self.assertTrue(all(e['status']=='reviewed' and e['import_approved'] is False and e['runtime_control_semantics_verified'] is False for e in p['entries']));self.assertEqual(sum('.pod/' in e['id'] for e in p['entries']),48)
 def test_exact_original_source_hash_and_quarantine_gate(self):
  raw='20% 할인'.encode('cp949');res=dict(resource='SHIP/sample.cht',sha256=digest(raw));e=dict(id='x',offset=0,source_bytes=len(raw),source_sha256=digest(raw),decode='strict',controls='quarantined',references={'ko-KR':'20% 할인'});d=dict(**{k:e[k] for k in ('id','offset','source_bytes','source_sha256')},resource=res['resource'],resource_sha256=res['sha256'],source='20% 할인',target='优惠20%',status='reviewed',source_encoding='cp949',reading_sha256=digest('20% 할인'.encode('utf8')),import_approved=False,runtime_control_semantics_verified=False);p=dict(schema=1,locale='zh-CN',entries=[d]);c=dict(resources=[dict(**res,entries=[e])]);self.assertEqual(audit(c,p,{'sample.cht':raw},{})['summary']['reviewed'],1);e['controls']='recognized'
  with self.assertRaisesRegex(ValueError,'quarantine'):audit(c,p,{'sample.cht':raw},{})
