import copy,json,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib','src')]
from localization.text import LITERAL_POLICY,protected_tokens,validate_target,rewrite_fpb,MappedEncoder
from source_interpretation import control_policy,encode_target
from prepare_control_interpretations import derive,validate_binding
from font_poc import digest
class LiteralPolicyImportTests(unittest.TestCase):
 def test_default_percent_still_quarantined(self):
  with self.assertRaisesRegex(ValueError,'unknown control'):protected_tokens('20%优惠')
 def test_default_angle_still_quarantined(self):
  with self.assertRaisesRegex(ValueError,'unknown control'):protected_tokens('<风>')
 def test_unknown_policy_rejected(self):
  with self.assertRaisesRegex(ValueError,'unknown explicit'):protected_tokens('20%',control_policy='anything')
 def test_explicit_numeric_percent_allowed(self):self.assertEqual(protected_tokens('20%优惠',control_policy=LITERAL_POLICY),['20%'])
 def test_known_printf_and_markup_stay_exact(self):self.assertEqual(protected_tokens('<b>%d %s %%</b>',control_policy=LITERAL_POLICY),['<b>','%d','%s','%%','</b>'])
 def test_numeric_percent_change_rejected(self):
  with self.assertRaisesRegex(ValueError,'protected token'):validate_target('20% 할인','优惠30%',control_policy=LITERAL_POLICY)
 def test_numeric_nonpercent_change_rejected(self):
  with self.assertRaisesRegex(ValueError,'numeric'):validate_target('10개 20%','买11件优惠20%',control_policy=LITERAL_POLICY)
 def test_known_token_order_change_rejected(self):
  with self.assertRaisesRegex(ValueError,'protected token'):validate_target('$D06가$n20%','$n20%甲$D06',control_policy=LITERAL_POLICY)
 def test_opaque_control_bytes_rejected(self):
  for c in ('\0','\n','\t'):
   with self.subTest(c=c),self.assertRaisesRegex(ValueError,'control bytes'):protected_tokens('20%'+c,control_policy=LITERAL_POLICY)
 def test_nonascii_angle_delimiters_retained(self):self.assertEqual(protected_tokens('<风>与<水>',control_policy=LITERAL_POLICY),['<','>','<','>'])
 def test_bad_angles_rejected(self):
  for text in ('<风','风>','<<风>','<123>','<风%>'):
   with self.subTest(text=text),self.assertRaises(ValueError):protected_tokens(text,control_policy=LITERAL_POLICY)
 def test_literal_arrow_order_preserved(self):
  validate_target('가->나','甲->乙',control_policy=LITERAL_POLICY)
  with self.assertRaisesRegex(ValueError,'protected token'):validate_target('가->나','甲到乙',control_policy=LITERAL_POLICY)
 def proof(self):
  text='20% 할인';target='20% reduction';e=dict(source_sha256=digest(text.encode('cp949')),references={'ko-KR':text},source_control_policy=LITERAL_POLICY);e['source_control_interpretation']=dict(schema=1,original_controls='quarantined',raw_sha256=e['source_sha256'],reading_sha256=digest(text.encode('utf8')),target_sha256=digest(target.encode('utf8')),native_binding_sha256='a'*64,native_source_span_verified=True,runtime_control_semantics_verified=False);return e,target
 def test_missing_field_proof_rejected(self):
  with self.assertRaisesRegex(ValueError,'bound'):control_policy(dict(source_control_policy=LITERAL_POLICY))
 def test_proof_bound_to_source_native_and_runtime(self):
  for key,value in [('raw_sha256','0'*64),('reading_sha256','0'*64),('native_source_span_verified',False),('runtime_control_semantics_verified',True),('native_binding_sha256','short')]:
   e,target=self.proof();e['source_control_interpretation'][key]=value
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,'bound'):control_policy(e,target)
 def test_proof_target_change_rejected(self):
  e,target=self.proof()
  with self.assertRaisesRegex(ValueError,'bound'):control_policy(e,'20% changed')
 def test_explicit_policy_encoding_default_unchanged(self):
  encoder=MappedEncoder([]);e,target=self.proof();self.assertEqual(encode_target(encoder,e,target),b'20% reduction')
  with self.assertRaises(ValueError):encoder.encode(target)
 def fixture(self):
  text='20% 할인';target='20% reduction';raw=text.encode('cp949');blob=struct.pack('<4I',1,77,0,len(raw))+struct.pack('<I',len(raw))+raw;res=dict(resource='SHIP/sample.fpb',sha256=digest(blob));e=dict(id='sample',offset=0,source_bytes=len(raw),source_sha256=digest(raw),decode='strict',controls='quarantined',semantic='dialogue-window',references={'ko-KR':text});d=dict(**{k:e[k] for k in ('id','offset','source_bytes','source_sha256')},resource=res['resource'],resource_sha256=res['sha256'],source=text,target=target,status='reviewed',source_encoding='cp949',reading_sha256=digest(text.encode('utf8')),import_approved=False,runtime_control_semantics_verified=False);b=dict(id='sample',kind='native-fpb-chat',source_resource=res['resource'],source_resource_sha256=res['sha256'],source_offset=0,source_bytes=len(raw),source_sha256=digest(raw),physical_index=0,native_record_key=77);return dict(resources=[dict(**res,entries=[e])]),dict(schema=1,locale='zh-CN',entries=[d]),dict(schema=1,bindings=[b]),{'sample.fpb':blob}
 def test_derive_native_fpb_keeps_input_and_selects_target(self):
  c,p,b,m=self.fixture();before=copy.deepcopy(c);out,batch,evidence=derive(c,p,b,m,{},None);self.assertEqual(c,before);e=out['resources'][0]['entries'][0];self.assertEqual(e['controls'],'recognized');self.assertEqual(control_policy(e,batch['entries'][0]['target']),LITERAL_POLICY);self.assertEqual(evidence[0]['geometry']['native_record_key'],77)
 def test_mismatched_fpb_binding_rejected(self):
  c,p,b,m=self.fixture();b['bindings'][0]['source_offset']=1
  with self.assertRaisesRegex(ValueError,'source binding'):derive(c,p,b,m,{},None)
 def test_duplicate_binding_rejected(self):
  c,p,b,m=self.fixture();b['bindings']*=2
  with self.assertRaisesRegex(ValueError,'duplicate'):derive(c,p,b,m,{},None)
 def test_rewrite_mixed_policies_requires_explicit_selection(self):
  c,p,b,m=self.fixture();blob=m['sample.fpb'];target={0:'20% reduction'};encoder=MappedEncoder([])
  with self.assertRaises(ValueError):rewrite_fpb(blob,target,encoder)
  new,rows=rewrite_fpb(blob,target,encoder,source_control_policies={0:LITERAL_POLICY});self.assertEqual(new[-13:],b'20% reduction');self.assertEqual(rows[0]['new_length'],13)
 def test_rewrite_unknown_or_unselected_policy_rejected(self):
  c,p,b,m=self.fixture()
  for policy in ({0:'anything'},{1:LITERAL_POLICY}):
   with self.subTest(policy=policy),self.assertRaisesRegex(ValueError,'invalid explicit'):rewrite_fpb(m['sample.fpb'],{0:'20% reduction'},MappedEncoder([]),source_control_policies=policy)
 def test_profile_has84_actual_native_bound_not_all94(self):
  p=json.loads((ROOT/'locales/zh-CN/proofreading/literal-control-consumers.json').read_text('utf8'));self.assertEqual(len(p['bindings']),84);self.assertEqual(sum(x['kind']=='native-fpb-chat' for x in p['bindings']),27);self.assertEqual(sum(x['kind']=='native512-pod' for x in p['bindings']),48);self.assertEqual(sum(x['kind']=='native512-cht' for x in p['bindings']),3);self.assertEqual(sum(x['kind']=='native-item-comment' for x in p['bindings']),6)

 def test_experience_unit_is_not_battle_system_kan(self):
  from validate_translation_batch import validate
  catalog=dict(source_locale='ko-KR',resources=[dict(entries=[dict(id='sample',source_sha256='a'*64,decode='strict',controls='recognized',references={'ko-KR':'경험치 칸 2개'})])]);batch=dict(schema=1,locale='zh-CN',entries=[dict(id='sample',source_sha256='a'*64,status='reviewed',target='2个经验值格')]);terms=[('경험치 칸','经验值格'),('경험치','经验值'),('칸','卡恩')];self.assertEqual(validate(catalog,batch,terms)['entries'],1)
