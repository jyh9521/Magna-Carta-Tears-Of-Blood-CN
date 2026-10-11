import copy,json,struct,sys,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib','src')]
from audit_literal_native_storage import cdg_records,check_span,CDG_ANCHORS,TUI_SPECS
from build_locale import validate_glyph_raster
from prepare_control_interpretations import derive
from font_poc import digest
class LiteralStorageTests(unittest.TestCase):
 def test_cdg526_not_old263_record_identity(self):
  blob=bytearray(struct.pack('<II',72,5)+bytes(72*526))
  for i in range(72):struct.pack_into('<II',blob,8+i*526,i,80+i)
  rows=cdg_records(bytes(blob));self.assertEqual(len(rows),72);self.assertEqual(rows[15],dict(physical_index=15,source_key=95,name_offset=7906,description_offset=8169))
 def test_cdg_header_and_size_mismatch_rejected(self):
  for raw in (struct.pack('<II',72,5)+bytes(72*526-1),struct.pack('<II',71,5)+bytes(72*526),struct.pack('<II',72,6)+bytes(72*526)):
   with self.subTest(size=len(raw)),self.assertRaisesRegex(ValueError,'geometry'):cdg_records(raw)
 def fixture(self):
  raw=b'20%'+bytes(252)+b'METAKEY!';entry=dict(id='x',offset=0,source_bytes=3,source_sha256=digest(b'20%'),observed_byte_capacity=254,trailer_bytes=8,slot_sha256=digest(raw));res=dict(resource='SHIP/sample.cdg',sha256=digest(raw));binding=dict(**{k:entry[k] for k in ('id','offset','source_bytes','source_sha256')},resource=res['resource'],resource_sha256=res['sha256']);return res,entry,binding,raw
 def test_full_hash_preserves_tail_outside255_write(self):
  res,e,b,raw=self.fixture();g=check_span(res,e,b,raw,digest(raw),255);self.assertEqual(g['writable_bytes'],255);self.assertEqual(g['preserved_tail_bytes'],8);self.assertEqual(g['preserved_tail_sha256'],digest(b'METAKEY!'))
 def test_wrong_span_capacity_rejected(self):
  res,e,b,raw=self.fixture();e['observed_byte_capacity']=255
  with self.assertRaisesRegex(ValueError,'full field'):check_span(res,e,b,raw,digest(raw),255)
 def test_dirty_slot_padding_rejected(self):
  res,e,b,raw=self.fixture();raw=raw[:50]+b'x'+raw[51:];res['sha256']=b['resource_sha256']=digest(raw)
  with self.assertRaisesRegex(ValueError,'padding'):check_span(res,e,b,raw,digest(raw),255)
 def test_source_identity_change_rejected(self):
  res,e,b,raw=self.fixture();b['offset']=1
  with self.assertRaisesRegex(ValueError,'source binding'):check_span(res,e,b,raw,digest(raw),255)
 def test_original_fingerprint_change_rejected(self):
  res,e,b,raw=self.fixture()
  with self.assertRaisesRegex(ValueError,'fingerprint'):check_span(res,e,b,raw,b'0'*64,255)
 def test_native_anchors_lock_key_plus4_and_fstring1c(self):
  self.assertEqual(CDG_ANCHORS[0x3140cc],0x0320f809);self.assertEqual(CDG_ANCHORS[0x3141ac],0x240600ff);self.assertEqual(CDG_ANCHORS[0x311228],0x26e5001c)
 def test_tui_spec_arrays_and_counts(self):
  self.assertEqual([(TUI_SPECS[n]['count'],TUI_SPECS[n]['array'],TUI_SPECS[n]['lookup']) for n in ('00001239.tui','00001249.tui')],[(34,0x148,0x312f60),(27,0x16c,0x3132f0)])
 def test_ten_bindings_and_true_store_key_not_ordinal(self):
  p=json.loads((ROOT/'locales/zh-CN/proofreading/literal-control-consumers-02.json').read_text('utf8'));self.assertEqual(len(p['bindings']),10);self.assertEqual(sum(b['kind']=='native-cdg-description' for b in p['bindings']),6);b=next(b for b in p['bindings'] if b['id']=='SHIP/00001239.tui/record/4/field/0/index/9');self.assertEqual((b['record_key'],b['physical_index'],b['native_string_offset']),(4,9,4))
 def test_language_subset_preserves_source_ids_targets(self):
  p=ROOT/'locales/zh-CN/proofreading';a=json.loads((p/'literal-control-readings.json').read_text('utf8'));b=json.loads((p/'literal-control-readings-02.json').read_text('utf8'));old={d['id']:d for d in a['entries']};self.assertEqual(len(b['entries']),10);self.assertTrue(all(old[d['id']]==d for d in b['entries']))
 def test_blank_unicode_separator_is_valid_glyph(self):
  image=Image.new('L',(19,19));validate_glyph_raster('　',image);validate_glyph_raster('\u2002',image)
 def test_blank_letters_and_replacement_still_rejected(self):
  for char in ('中','A','\ufffd'):
   with self.subTest(char=char),self.assertRaisesRegex(ValueError,'empty glyph'):validate_glyph_raster(char,Image.new('L',(19,19)))
 def test_blank_controls_and_line_separators_rejected(self):
  for char in ('\t','\n','\u2028','\u2029','\u200b'):
   with self.subTest(char=char),self.assertRaisesRegex(ValueError,'empty glyph'):validate_glyph_raster(char,Image.new('L',(19,19)))
 def test_nonempty_normal_glyph_valid(self):
  image=Image.new('L',(19,19));image.putpixel((8,8),255);validate_glyph_raster('中',image)
