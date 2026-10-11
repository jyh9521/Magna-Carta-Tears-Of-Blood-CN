import json,struct,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/p) for p in ('tools','src')]
from audit_named_resource_data import SPECS,ANCHORS,validate_anchors,stride_address,item_lookup,item_hash_fixture,compiled_roles
from audit_text_slicing import scalar
ITEM_WORDS=[0x8c860818,0x8c830814,0x24c6ffff,0xc53024,0x63080,0x661821,0x8c670000,0x1000000c,0x2402ffff,0x8c830808,0x73040,0xc73021,0x63080,0x663021,0x8cc30004,0x14a30003,0,0x10000005,0x24c20008,0x8cc70000,0x14e2fff4,0,0x102d,0x1040000a,0,0x8c450000,0x8c820094,0x51880,0x652021,0x41880,0x831821,0x31880,0x10000002,0x431021,0x24820564]
class Image:
 def __init__(self,start,words):self.start=start;self.blob=b''.join(struct.pack('<I',w) for w in words)
 def to_offset(self,va):return va-self.start
class NamedNativeTests(unittest.TestCase):
 def test_all1138_actual_stride_instructions(self):
  cases={'00000460.cha':Image(0x310190,[0x8e220028,0x718c0,0x671823,0x318c0,0x438021]),'00000466.abi':Image(0x31049c,[0x8e22004c,0x51840,0x651821,0x31900,0x43a821]),'00000953.itm':Image(0x2fe510,ITEM_WORDS)}
  for name,image in cases.items():
   for i in range(SPECS[name]['count']):self.assertEqual(stride_address(image,name,i),0x9000+SPECS[name]['native_stride']*i)
 def test_native_item_hash_collision_and_last_duplicate(self):
  self.assertEqual(item_lookup(Image(0x2fe510,ITEM_WORDS),[9,17,9],9),0xc000+200);self.assertEqual(item_lookup(Image(0x2fe510,ITEM_WORDS),[9,17,9],17),0xc000+100)
 def test_native_missing_item_uses_original_fallback(self):self.assertEqual(item_lookup(Image(0x2fe510,ITEM_WORDS),[9,17],25),0x8564)
 def test_large_fixture_bucket_and_node_regions_do_not_overlap(self):
  image=Image(0x2fe510,ITEM_WORDS);keys=list(range(479))
  for i in range(479):self.assertEqual(item_lookup(image,keys,i),0xc000+100*i)
 def test_item_unsigned_key_validation(self):
  for keys in [[-1],[2**32],[True]]:
   with self.assertRaises(ValueError):item_hash_fixture(keys)
 def test_stride_rejects_out_of_range_or_boolean(self):
  for name in SPECS:
   for i in [-1,SPECS[name]['count'],True]:
    with self.assertRaises(ValueError):stride_address(None,name,i)
 def test_native_anchor_mutation_rejected(self):
  class Bad:
   blob=bytes(4)
   def to_offset(self,va):return 0
  with self.assertRaisesRegex(ValueError,'anchor mismatch'):validate_anchors(Bad())
 def test_register_and_executes_64bit_scalar_bits(self):
  image=Image(0x100,[0xc53024]);q=scalar(image,0x100,0x104,{6:0x123456789abcdef0,5:0xfedcba9876543210},{})
  self.assertEqual(q['registers'][6],0x123456789abcdef0 & 0xfedcba9876543210)
class NamedLanguageTests(unittest.TestCase):
 def rows(self):return json.loads((R/'locales/zh-CN/latin-named-data-review-01.json').read_text('utf8'))['entries']
 def bindings(self):return json.loads((R/'locales/zh-CN/proofreading/latin-named-data-consumers.json').read_text('utf8'))['bindings']
 def test_64_exact_source_targets_and_typed_fields(self):
  ix={e['id']:e for e in self.rows()};self.assertEqual(len(ix),64);self.assertEqual(len(self.bindings()),64)
  for b in self.bindings():self.assertEqual((b['source_sha256'],b['target']),(ix[b['id']]['source_sha256'],ix[b['id']]['target']));self.assertFalse(b['runtime_verified']);self.assertIsInstance(b['source_record_key'],int);self.assertEqual(b['native_string_offset'],SPECS[Path(b['source_resource']).name]['fields'][b['field']][2])
 def test_protected_underscores_abbreviations_and_numbers(self):
  for b in self.bindings():self.assertEqual(b['source'].count('_'),b['target'].count('_'));self.assertNotIn('—',b['target'])
 def test_source_variants_do_not_silently_merge_actors(self):
  ix={e['id']:e['target'] for e in self.rows()};self.assertIn('罗蒂',ix['SHIP/00000466.abi/record-index/322/field/0']);self.assertEqual(ix['SHIP/00000460.cha/record-index/292/field/0'],'T.罗蒂');self.assertEqual(ix['SHIP/00000460.cha/record-index/176/field/0'],'winmain');self.assertTrue(all('她' not in v and '他' not in v for v in ix.values()))
 def test_frost_worm_and_item_key_canonical_names(self):
  ix={e['id']:e['target'] for e in self.rows()};self.assertEqual(ix['SHIP/00000460.cha/record-index/286/field/0'],'T.霜龙');self.assertEqual(ix['SHIP/00000953.itm/record-index/451/field/0'],'宝箱钥匙');self.assertIn('翁戈利安特',ix['SHIP/00000466.abi/record-index/113/field/0'])
if __name__=='__main__':unittest.main()
