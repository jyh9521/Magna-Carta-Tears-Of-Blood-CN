"""Pure orchestration and output hygiene tests; no game inputs."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build_poc_pipeline import command_plan,run_steps,write_qa
from verify_expanded_locale import fresh_output


class PipelineTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def plan(self):return command_plan(Path('source.iso'),Path('font.ttf'),Path('locale.json'),Path('profile.json'),self.root,0xD0A1)
    def test_stage_order(self):self.assertEqual([name for name,_ in self.plan()],['fonts','package','bundle','image','verify'])
    def test_explicit_locale(self):
        for name,args in self.plan():
            if name in ('fonts','image','verify'):self.assertEqual(args[args.index('--locale')+1],'locale.json')
    def test_explicit_profile(self):
        for name,args in self.plan():
            if name in ('package','bundle'):self.assertEqual(args[args.index('--profile')+1],'profile.json')
    def test_range_start(self):
        for name,args in self.plan():
            if name in ('fonts','verify'):self.assertEqual(args[args.index('--range-start')+1],'0xd0a1')
    def test_no_hidden_intermediates(self):
        for _,args in self.plan():self.assertTrue(Path(args[args.index('--out')+1]).is_relative_to(self.root))
    def test_verify_points_at_built_iso(self):
        args=self.plan()[-1][1];self.assertEqual(args[args.index('--candidate')+1],str(self.root/'image/MODIFIED_FILE.iso'))
    def test_subprocess_argument_list(self):
        for _,args in self.plan():self.assertIsInstance(args,list);self.assertEqual(args[:3],[sys.executable,'-X','utf8'])
    def test_fresh_output(self):
        out=self.root/'build/run';self.assertEqual(fresh_output(out,[],root=self.root),out)
    def test_reuse_nonempty_rejected(self):
        out=self.root/'build/run';out.mkdir(parents=True);(out/'retained').write_text('unchanged')
        with self.assertRaisesRegex(ValueError,'empty'):fresh_output(out,[],root=self.root)
        self.assertEqual((out/'retained').read_text(),'unchanged')
    def test_input_overlap_rejected(self):
        out=self.root/'build/run'
        with self.assertRaisesRegex(ValueError,'overlaps'):fresh_output(out,[out/'input.iso'],root=self.root)
        self.assertFalse(out.exists())
    def test_output_root_rejected(self):
        for out in [self.root/'build',self.root/'work',self.root/'tracked',self.root/'build/../../escape']:
            with self.assertRaises(ValueError):fresh_output(out,[],root=self.root)
    def test_file_output_rejected(self):
        out=self.root/'build/run';out.parent.mkdir();out.write_text('retained')
        with self.assertRaises(ValueError):fresh_output(out,[],root=self.root)
    def test_success_receipt(self):
        receipt={};run_steps([('one',['fake']),('two',['fake'])],self.root,receipt,
                            runner=lambda *args,**kw:subprocess.CompletedProcess(args[0],0,'PASS\n'))
        self.assertEqual(receipt['status'],'static-pass');self.assertEqual(len(receipt['steps']),2)
        self.assertEqual(json.loads((self.root/'pipeline.json').read_text())['status'],'static-pass')
    def test_failure_stops_pipeline(self):
        calls=[]
        def fail(*args,**kw):calls.append(args[0]);return subprocess.CompletedProcess(args[0],2,'BAD\n')
        receipt={}
        with self.assertRaisesRegex(ValueError,'one'):run_steps([('one',['fake']),('two',['fake'])],self.root,receipt,runner=fail)
        self.assertEqual(len(calls),1);self.assertEqual(receipt['status'],'failed');self.assertEqual(receipt['steps'][0]['exit'],2)
    def test_exception_receipt(self):
        def fail(*args,**kw):raise OSError('launch failed')
        receipt={}
        with self.assertRaises(OSError):run_steps([('one',['fake'])],self.root,receipt,runner=fail)
        self.assertEqual(json.loads((self.root/'pipeline.json').read_text())['failed_step'],'one')
    def test_qa_states_unverified(self):
        write_qa(self.root,{'entries':[dict(id='ui',kind='fixed-display-slot',target='测试')]},{'candidate_sha256':'abc'})
        qa=json.loads((self.root/'QA_CHECKLIST.json').read_text('utf8'))
        self.assertTrue(all(item['status']=='untested' and not item['evidence'] for item in qa['cases']))
    def test_qa_contains_candidate_identity(self):
        write_qa(self.root,{'entries':[dict(id='ui',kind='fixed-display-slot',target='测试')]},{'candidate_sha256':'abc'})
        self.assertIn('abc',(self.root/'QA_CHECKLIST.md').read_text('utf8'))
        self.assertIsNone(json.loads((self.root/'QA_CHECKLIST.json').read_text('utf8'))['pcsx2_version'])


if __name__=='__main__':unittest.main()
