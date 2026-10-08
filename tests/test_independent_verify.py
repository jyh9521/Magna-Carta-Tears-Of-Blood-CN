"""Synthetic independent Font derivation and version-gate tests."""
from pathlib import Path
import hashlib
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import verify_expanded_locale as target
from font_resource import encode_compact
from research_inventory import font_data


def sha(data):return hashlib.sha256(data).hexdigest()
def font_fixture(count=2):
    return bytes(3)+struct.pack('<6I',1,1,count,2,3,1)+encode_compact(count*2)+b'\x55'*(count*2)+encode_compact(count)+bytes([2])*count+encode_compact(2)+struct.pack('<2H',0x8000,0x8000+count)+encode_compact(2)+struct.pack('<2H',0,count)


class Face:
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def getBestCmap(self):return {ord('测'):'glyph'}


class IndependentVerifyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.font=self.root/'font.ttf';self.font.write_bytes(b'synthetic-font')
        self.one=font_fixture();self.two=font_fixture();self.engine=self.one+self.two
        self.game=dict(expected_engine_sha256=sha(self.engine),fonts={'NormalFont':sha(self.one),'KatakanaFont':sha(self.two)})
        self.locale=dict(font_input={'sha256':sha(b'synthetic-font')},alignment_reference='测',advance=2)
        self.exports=[dict(index=1,class_='Font',name='NormalFont',offset=0,size=len(self.one)),dict(index=2,class_='Font',name='KatakanaFont',offset=len(self.one),size=len(self.two))]
    def tearDown(self):self.temp.cleanup()
    def build(self,start=0xD0A1,exports=None):
        exports=self.exports if exports is None else exports
        tables={'exports':[dict(index=e['index'],name=e['name'],offset=e['offset'],size=e['size'],**{'class':e['class_']}) for e in exports]}
        with patch.object(target,'package_tables',return_value=tables),patch('fontTools.ttLib.TTFont',return_value=Face()),patch.object(target,'patch_font',side_effect=lambda serial,*args:serial):
            return target.expected_fonts(self.engine,self.game,self.locale,[{'character':'测'}],self.font,start)
    def test_derives_both_fonts(self):
        fonts,exports,encoder=self.build();self.assertEqual(set(exports),{1,2});self.assertEqual(encoder.encode('测'),bytes.fromhex('d0a1'))
        self.assertEqual({font_data(f)['glyphs'] for f in fonts.values()},{3})
    def test_deterministic_derivation(self):
        self.assertEqual(self.build()[0],self.build()[0])
    def test_original_glyphs_preserved(self):
        fonts,_,_=self.build();old=font_data(self.one)
        for serial in fonts.values():
            new=font_data(serial);self.assertEqual(serial[new['bitmap_start']:new['bitmap_start']+4],self.one[old['bitmap_start']:old['bitmap_start']+4])
    def test_bad_engine_hash(self):
        self.game['expected_engine_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'engine'):self.build()
    def test_bad_font_hash(self):
        self.locale['font_input']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'font input'):self.build()
    def test_bad_original_font_hash(self):
        self.game['fonts']['NormalFont']='0'*64
        with self.assertRaisesRegex(ValueError,'Font fingerprint'):self.build()
    def test_missing_expected_font(self):
        with self.assertRaisesRegex(ValueError,'missing'):self.build(exports=self.exports[:1])
    def test_range_overlap_rejected(self):
        with self.assertRaisesRegex(ValueError,'overlap'):self.build(start=0x8001)
    def test_source_candidate_alias_rejected(self):
        p=self.root/'same.iso';p.write_bytes(b'fixture')
        with patch.object(target,'load_config',return_value=({}, {}, None)):
            with self.assertRaisesRegex(ValueError,'differ'):target.verify_candidate(p,p,self.font,self.root/'locale.json',self.root/'out')
    def test_unknown_source_rejected_before_output(self):
        p=self.root/'source.iso';p.write_bytes(b'fixture');q=self.root/'candidate.iso';q.write_bytes(b'candidate')
        out=self.root/'untouched'
        with patch.object(target,'load_config',return_value=({}, {'expected_iso_sha256':'0'*64}, None)):
            with self.assertRaisesRegex(ValueError,'source ISO'):target.verify_candidate(p,q,self.font,self.root/'locale.json',out)
        self.assertFalse(out.exists())


if __name__=='__main__':unittest.main()
