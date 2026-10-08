from pathlib import Path
import copy
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import font_poc as core
from name_slot_overlay import apply_name_slots,name_cases
from build_poc_pipeline import write_qa
from validate_poc_qa import validate_receipt
import json

class Encoder:
    def encode(self,text):return text.encode('ascii')

def source():return bytes(12)+(b'Name'+bytes(294)+b'\x01')*2+(b'Other'+bytes(294))
def plan():return dict(resource='test.cha',expected_sha256=core.digest(source()),source_text='Name',source_encoding='ascii',expected_slots=[0,1],targets=[dict(slot=0,target='Test')])

class NameOverlayTests(unittest.TestCase):
    def setUp(self):self.plan=plan();self.ship={'test.cha':source()};self.bundle=b'prefix'+source()+b'suffix'
    def apply(self):return apply_name_slots(self.ship,self.bundle,Encoder(),[self.plan])
    def test_one_selected_only(self):
        over,bundle,report=self.apply();new=over['test.cha'];self.assertEqual(new[12:16],b'Test');self.assertEqual(new[311:],source()[311:]);self.assertEqual(bundle,b'prefix'+new+b'suffix');self.assertEqual(len(report[0]['selected']),1)
    def test_trailer_preserved(self):
        over,_,_=self.apply();self.assertEqual(over['test.cha'][310],1)
    def test_no_names_unchanged(self):
        over,bundle,report=apply_name_slots(self.ship,self.bundle,Encoder(),[]);self.assertEqual((over,bundle,report),({},self.bundle,[]))
    def test_two_distinct_targets(self):
        self.plan['targets'].append(dict(slot=1,target='LongName'));over,_,_=self.apply();self.assertEqual(over['test.cha'][311:319],b'LongName')
    def test_wrong_fingerprint(self):
        self.plan['expected_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'fingerprint'):self.apply()
    def test_unknown_resource(self):
        self.plan['resource']='missing.cha'
        with self.assertRaisesRegex(ValueError,'resource'):self.apply()
    def test_duplicate_resource(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):apply_name_slots(self.ship,self.bundle,Encoder(),[self.plan,self.plan])
    def test_wrong_inventory(self):
        self.plan['expected_slots']=[0,2]
        with self.assertRaisesRegex(ValueError,'inventory'):self.apply()
    def test_count_mismatch(self):
        self.plan['expected_slots']=[0]
        with self.assertRaisesRegex(ValueError,'count'):self.apply()
    def test_duplicate_expected_slots(self):
        self.plan['expected_slots']=[0,0]
        with self.assertRaisesRegex(ValueError,'expected'):self.apply()
    def test_negative_slot(self):
        self.plan['expected_slots']=[-1,1]
        with self.assertRaisesRegex(ValueError,'expected'):self.apply()
    def test_bool_slot(self):
        self.plan['targets'][0]['slot']=False
        with self.assertRaisesRegex(ValueError,'targets'):self.apply()
    def test_duplicate_targets(self):
        self.plan['targets'].append(copy.deepcopy(self.plan['targets'][0]))
        with self.assertRaisesRegex(ValueError,'duplicate'):self.apply()
    def test_target_outside_group(self):
        self.plan['targets'][0]['slot']=2
        with self.assertRaisesRegex(ValueError,'unexpected'):self.apply()
    def test_no_targets(self):
        self.plan['targets']=[]
        with self.assertRaisesRegex(ValueError,'targets'):self.apply()
    def test_token_change_rejected(self):
        self.plan['targets'][0]['target']='Test$n'
        with self.assertRaisesRegex(ValueError,'token'):self.apply()
    def test_encoding_failure(self):
        self.plan['targets'][0]['target']='测'
        with self.assertRaises(UnicodeEncodeError):self.apply()
    def test_duplicate_cached_copy(self):
        self.bundle+=source()
        with self.assertRaisesRegex(ValueError,'unique'):self.apply()
    def test_experimental_case_identity(self):
        cases=name_cases({'name_slot_overlays':[self.plan]});self.assertEqual(cases[0]['id'],'SHIP/test.cha/slot/0');self.assertEqual(cases[0]['status'],'untested')
    def test_generated_qa_accepts_extra_name_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);config=dict(locale='test',entries=[dict(id='ui',kind='fixed-display-slot',target='Test')],name_slot_overlays=[self.plan]);sha='a'*64
            write_qa(root,config,{'candidate_sha256':sha});receipt=json.loads((root/'QA_CHECKLIST.json').read_text('utf8'))
            result=validate_receipt(receipt,config,sha,root/'QA_CHECKLIST.json');self.assertEqual(len(result['pending_cases']),8)
    def test_missing_name_case_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);config=dict(locale='test',entries=[dict(id='ui',kind='fixed-display-slot',target='Test')],name_slot_overlays=[self.plan]);sha='a'*64
            write_qa(root,config,{'candidate_sha256':sha});receipt=json.loads((root/'QA_CHECKLIST.json').read_text('utf8'));receipt['cases']=[r for r in receipt['cases'] if r.get('kind')!='name-slot-experiment']
            with self.assertRaisesRegex(ValueError,'inventory'):validate_receipt(receipt,config,sha,root/'QA_CHECKLIST.json')

if __name__=='__main__':unittest.main()
