from pathlib import Path
import copy,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','src','lib')]
from validate_compiled_translations import validate_language
class CompiledInterfaceTests(unittest.TestCase):
 def setUp(self):
  self.b=json.loads((ROOT/'locales/zh-CN/compiled-interface-review-01.json').read_text('utf8'));self.p=json.loads((ROOT/'locales/zh-CN/proofreading/compiled-interface-consumers.json').read_text('utf8'))
 def test_all57_reviewed_function_backend(self):
  self.assertEqual(len(validate_language(self.b,self.p)),57);self.assertTrue(all(e['reinsertion_policy']=='translate-compiled-function' for e in self.b['entries']))
 def test_frontier66_fully_decided(self):self.assertEqual(len(self.p['bindings']),66);self.assertEqual(len(self.p['retained']),9);validate_language(self.b,self.p)
 def test_six_returned_interface_fallbacks(self):
  rows=[e for e in self.b['entries'] if e['id'].startswith('FILE/MrtsEngine.u/export/678') and e['source']=='None'];self.assertEqual(len(rows),6);self.assertTrue(all(e['target']=='无' for e in rows))
 def test_four_version_prefixes_preserve_numeric_tail(self):
  rows=[e for e in self.b['entries'] if e['id'].startswith('FILE/MrtsGame.u/export/8906/')];self.assertEqual(len(rows),4);self.assertTrue(all(e['target']=='版本 '+e['source'][4:] for e in rows))
 def test_mode_aliases_canonical(self):
  ix={e['source']:e['target'] for e in self.b['entries']};self.assertEqual([ix[n] for n in ('sura','nachal','yacha')],['修罗','罗刹','夜叉'])
 def test_all_currency_labels_canonical(self):
  for e in self.b['entries']:
   if e['source'].strip()=='Sid':self.assertEqual(e['target'].strip(),'希德币')
 def test_memory_slots_preserve_numbers(self):
  for e in self.b['entries']:
   if e['source'].startswith('SLOT '):self.assertEqual(e['target'],'插槽'+e['source'][-1])
 def test_machine_class_paths_not_translated(self):
  paths=[e for e in self.p['retained'] if e['source'].startswith('MrtsGame.')];self.assertEqual(len(paths),4);self.assertTrue(all(e['decision']=='retain-original' for e in paths))
 def test_duplicate_translation_rejected(self):
  self.b['entries'].append(copy.deepcopy(self.b['entries'][0]))
  with self.assertRaises(ValueError):validate_language(self.b,self.p)
 def test_wrong_source_rejected(self):
  self.b['entries'][0]['source_sha256']='0'*64
  with self.assertRaises(ValueError):validate_language(self.b,self.p)
 def test_import_claim_rejected(self):
  self.p['import_approved']=True
  with self.assertRaises(ValueError):validate_language(self.b,self.p)
 def test_unresolved_frontier_gap_rejected(self):
  self.p['retained'].pop()
  with self.assertRaises(ValueError):validate_language(self.b,self.p)
if __name__=='__main__':unittest.main()
