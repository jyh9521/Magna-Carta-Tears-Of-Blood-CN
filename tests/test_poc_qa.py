from pathlib import Path
import copy
import json
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from validate_poc_qa import validate_receipt,RUNTIME_CASES
from build_poc_pipeline import write_qa

class QaReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.config={'locale':'test-LC','entries':[dict(id='ui',kind='fixed-display-slot',target='测试')]}
        self.sha='a'*64;write_qa(self.root,self.config,{'candidate_sha256':self.sha})
        self.path=self.root/'QA_CHECKLIST.json';self.receipt=json.loads(self.path.read_text('utf8'))
        (self.root/'screen.png').write_bytes(b'synthetic evidence; not a runtime screenshot')
    def tearDown(self):self.temp.cleanup()
    def check(self):return validate_receipt(self.receipt,self.config,self.sha,self.path)
    def mark_tested(self,status='pass'):
        self.receipt.update(pcsx2_version='test-version',bios_identifier='test-bios',renderer='test-backend')
        self.receipt['cases'][0].update(status=status,evidence=['screen.png'])
    def test_generated_pending(self):
        result=self.check();self.assertEqual(result['record_state'],'pending');self.assertEqual(len(result['pending_cases']),7)
    def test_partial_manual_pass_stays_pending(self):
        self.mark_tested();self.assertEqual(self.check()['record_state'],'pending')
    def test_complete_not_verified(self):
        self.mark_tested()
        for c in self.receipt['cases']:c.update(status='pass',evidence=['screen.png'])
        result=self.check();self.assertEqual(result['record_state'],'recorded-complete');self.assertIn('not independently verified',result['runtime'])
    def test_failure_priority(self):
        self.mark_tested('fail');self.assertEqual(self.check()['record_state'],'recorded-failure')
    def test_old_candidate_rejected(self):
        self.receipt['candidate_sha256']='b'*64
        with self.assertRaisesRegex(ValueError,'hash mismatch'):self.check()
    def test_invalid_hash(self):
        with self.assertRaisesRegex(ValueError,'invalid candidate'):validate_receipt(self.receipt,self.config,'x',self.path)
    def test_duplicate_case(self):
        self.receipt['cases'].append(copy.deepcopy(self.receipt['cases'][0]))
        with self.assertRaisesRegex(ValueError,'inventory'):self.check()
    def test_missing_case(self):
        self.receipt['cases'].pop()
        with self.assertRaisesRegex(ValueError,'inventory'):self.check()
    def test_unknown_case(self):
        self.receipt['cases'][-1]['id']='unknown'
        with self.assertRaisesRegex(ValueError,'inventory'):self.check()
    def test_wrong_expected(self):
        self.receipt['cases'][0]['expected']='changed'
        with self.assertRaisesRegex(ValueError,'text mismatch'):self.check()
    def test_wrong_kind(self):
        self.receipt['cases'][0]['kind']='fpb'
        with self.assertRaisesRegex(ValueError,'text mismatch'):self.check()
    def test_unknown_status(self):
        self.receipt['cases'][0]['status']='verified'
        with self.assertRaisesRegex(ValueError,'status'):self.check()
    def test_pass_without_evidence(self):
        self.mark_tested();self.receipt['cases'][0]['evidence']=[]
        with self.assertRaisesRegex(ValueError,'requires'):self.check()
    def test_pass_without_environment(self):
        self.mark_tested();self.receipt['renderer']=None
        with self.assertRaisesRegex(ValueError,'requires'):self.check()
    def test_empty_environment(self):
        self.receipt['renderer']=' '
        with self.assertRaisesRegex(ValueError,'environment'):self.check()
    def test_untested_with_evidence(self):
        self.receipt['cases'][0]['evidence']=['screen.png']
        with self.assertRaisesRegex(ValueError,'untested'):self.check()
    def test_missing_evidence(self):
        self.mark_tested();self.receipt['cases'][0]['evidence']=['absent.png']
        with self.assertRaisesRegex(ValueError,'missing'):self.check()
    def test_empty_evidence(self):
        self.mark_tested();(self.root/'screen.png').write_bytes(b'')
        with self.assertRaisesRegex(ValueError,'empty'):self.check()
    def test_directory_evidence(self):
        self.mark_tested();self.receipt['cases'][0]['evidence']=[str(self.root)]
        with self.assertRaisesRegex(ValueError,'missing'):self.check()
    def test_proprietary_evidence_rejected(self):
        self.mark_tested();(self.root/'original.iso').write_bytes(b'fixture');self.receipt['cases'][0]['evidence']=['original.iso']
        with self.assertRaisesRegex(ValueError,'type'):self.check()
    def test_duplicate_evidence(self):
        self.mark_tested();self.receipt['cases'][0]['evidence']=['screen.png','./screen.png']
        with self.assertRaisesRegex(ValueError,'duplicate'):self.check()
    def test_evidence_snapshot(self):
        self.mark_tested();result=self.check();entry=result['cases'][0]['evidence'][0]
        self.assertEqual(entry['path'],str((self.root/'screen.png').resolve()));self.assertEqual(len(entry['sha256']),64)
    def test_invalid_case_shape(self):
        self.receipt['cases']=[None]
        with self.assertRaisesRegex(ValueError,'cases'):self.check()
    def test_invalid_environment_type(self):
        self.receipt['pcsx2_version']=123
        with self.assertRaisesRegex(ValueError,'environment'):self.check()
    def test_nonlist_evidence(self):
        self.receipt['cases'][0]['evidence']='screen.png'
        with self.assertRaisesRegex(ValueError,'list'):self.check()

if __name__=='__main__':unittest.main()
