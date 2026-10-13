from pathlib import Path
import json,sys,unittest,struct
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib','src')]
from ui_punctuation import single_sentence_period,omit_period,validated_empty_suffix
from localization.text import validate_target
from font_poc import digest
from patch_indexed_texture_pixels import patch_pixels
from build_indexed_texture_overlays import artwork


class UIPunctuationTests(unittest.TestCase):
 def test_plain_status(self):self.assertEqual(omit_period('没有存档。'),'没有存档')
 def test_comma_retained(self):self.assertEqual(omit_period('保存中，请稍候。'),'保存中，请稍候。')
 def test_ascii_comma_retained(self):self.assertFalse(single_sentence_period('保存中,请稍候。'))
 def test_two_sentences_retained(self):self.assertEqual(omit_period('保存中。请稍候。'),'保存中。请稍候。')
 def test_question_retained(self):self.assertEqual(omit_period('保存吗？'),'保存吗？')
 def test_embedded_question_retained(self):self.assertFalse(single_sentence_period('保存吗？请确认。'))
 def test_exclamation_retained(self):self.assertFalse(single_sentence_period('注意！请确认。'))
 def test_ellipsis_retained(self):self.assertFalse(single_sentence_period('稍等……保存中。'))
 def test_controls_preserved(self):self.assertEqual(omit_period('增加$n卡恩。'),'增加$n卡恩')
 def test_numeric_decimal_preserved(self):self.assertEqual(omit_period('经验提升至1.25倍。'),'经验提升至1.25倍')
 def test_trailing_space_preserved(self):self.assertEqual(omit_period('没有存档。 '),'没有存档 ')
 def test_default_empty_rejected(self):
  with self.assertRaises(ValueError):validate_target('suffix','')
 def test_unbound_empty_rejected(self):
  with self.assertRaises(ValueError):validated_empty_suffix({'id':'x','source_sha256':'0'*64},{'id':'x','source_sha256':'0'*64,'target':''})
 def test_bound_empty_only(self):
  row=next(q for q in self.review() if q['target']=='');source=dict(id=row['id'],source_sha256=row['source_sha256'],references={'ko-KR':'suffix'})
  self.assertTrue(validated_empty_suffix(source,row))
  for k,v in [('id','different'),('source_sha256','0'*64)]:
   with self.assertRaises(ValueError):validated_empty_suffix(dict(source,**{k:v}),row)
 def review(self):return json.loads((ROOT/'locales/zh-CN/proofreading/ui-punctuation-review.json').read_text('utf8'))
 def test_every_changed_field_has_reviewed_exact_delta(self):
  rows=self.review();self.assertEqual(len(rows),592);self.assertEqual(len({x['id'] for x in rows}),592)
  for q in rows:self.assertEqual(q['status'],'reviewed');self.assertEqual(q['target'],omit_period(q['previous_target']));self.assertRegex(q['source_sha256'],r'^[a-f0-9]{64}$')
 def test_save_empty_message(self):
  rows=json.loads((ROOT/'locales/zh-CN/opening-review-01.json').read_text('utf8'))['entries'];self.assertEqual(next(e['target'] for e in rows if '/record/176/' in e['id']),'没有存档')
 def test_all_original_movie_text_unchanged_by_ui_profile(self):self.assertFalse(any('.fpb/' in q['id'] or '.cht/' in q['id'] or '.ecd/' in q['id'] or '.fds/' in q['id'] or '00014107.tui' in q['id'] for q in self.review()))
 def test_composed_messages_retain_exact_fragments(self):
  rows=json.loads((ROOT/'locales/zh-CN/opening-review-01.json').read_text('utf8'))['entries'];by={e['id']:e for e in rows};p=json.loads((ROOT/'locales/zh-CN/proofreading/ui-punctuation-compositions.json').read_text('utf8'))
  self.assertEqual(len(p['groups']),7)
  for g in p['groups']:
   self.assertEqual(''.join(by[e['id']]['target'] for e in g['source_bound_fields']),g['composed_text']);self.assertFalse(p['runtime_verified'])


class IndexedTextureTests(unittest.TestCase):
 def fixture(self):
  pixels=bytes([0])*65536;serial=b'\x00\x01'+struct.pack('<I',66045)+b'\x40\x80\x08'+pixels+struct.pack('<IIBB',256,256,8,8);pal=bytes([255,255,255,255])*256;data=serial+pal
  table=dict(wrapper_path='../Textures/test.utx',names=['None'],exports=[dict(name='test',**{'class':'Texture'},flags=0,declared_size=len(serial),declared_offset=500)])
  profile=dict(payload_sha256=digest(data),textures=[dict(package=table['wrapper_path'],name='test',serial_offset=0,pixel_offset=9,pixel_sha256=digest(pixels),palette_offset=len(serial),palette_sha256=digest(pal),asset_key='test')]);return data,table,profile,pixels
 def test_only_pixels_change(self):
  b,t,p,pix=self.fixture()
  with patch('patch_indexed_texture_pixels.probe_all_packages',return_value=[t]):m,r=patch_pixels(b,p,{'test':bytes([1])*65536})
  self.assertEqual(b[:9],m[:9]);self.assertEqual(b[65545:],m[65545:]);self.assertEqual(len(b),len(m));self.assertEqual(len(r),1)
 def test_wrong_payload_hash(self):
  b,t,p,pix=self.fixture();p['payload_sha256']='0'*64
  with self.assertRaises(ValueError):patch_pixels(b,p,{'test':pix})
 def test_wrong_pixel_hash(self):
  b,t,p,pix=self.fixture();p['textures'][0]['pixel_sha256']='0'*64
  with patch('patch_indexed_texture_pixels.probe_all_packages',return_value=[t]),self.assertRaises(ValueError):patch_pixels(b,p,{'test':pix})
 def test_wrong_palette_hash(self):
  b,t,p,pix=self.fixture();p['textures'][0]['palette_sha256']='0'*64
  with patch('patch_indexed_texture_pixels.probe_all_packages',return_value=[t]),self.assertRaises(ValueError):patch_pixels(b,p,{'test':pix})
 def test_size_change_rejected(self):
  b,t,p,pix=self.fixture()
  with patch('patch_indexed_texture_pixels.probe_all_packages',return_value=[t]),self.assertRaises(ValueError):patch_pixels(b,p,{'test':pix[:-1]})
 def test_ambiguous_package_rejected(self):
  b,t,p,pix=self.fixture()
  with patch('patch_indexed_texture_pixels.probe_all_packages',return_value=[t,t]),self.assertRaises(ValueError):patch_pixels(b,p,{'test':pix})
 def test_artwork_hash_guard(self):
  p=json.loads((ROOT/'locales/zh-CN/images/title-texture-profile.json').read_text('utf8'))['canvases'][0]['patches'][0];p['image_sha256']='0'*64
  with self.assertRaises(ValueError):artwork(p)
 def test_three_source_streams_not_alternate_variant(self):
  p=json.loads((ROOT/'locales/zh-CN/images/title-texture-profile.json').read_text('utf8'));self.assertEqual(set(p['streams']),{'00013133.lin','00015559.lin','00000624.lin'})
 def test_menu_five_states(self):
  p=json.loads((ROOT/'locales/zh-CN/images/title-texture-profile.json').read_text('utf8'));self.assertEqual([q['position'][1] for q in p['canvases'][1]['patches']],[1,23,45,67,89])

if __name__=='__main__':unittest.main()
