import copy
import json
from pathlib import Path
import struct
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('tools', 'lib', 'src')]
from audit_native_fixed_dialogue import ANCHORS, PATHS, validate_anchors, validate_field, pod_text_layout
from prepare_source_interpretations import derive
from import_audited_fields import fixed_extent, fingerprint_extent
from font_poc import digest


class Image:
    def __init__(self):
        self.blob = bytearray(); self.offsets = {}
        for va, word in ANCHORS.items():
            self.offsets[va] = len(self.blob); self.blob.extend(struct.pack('<I', word))
        for va, path in PATHS.items():
            self.offsets[va] = len(self.blob); self.blob.extend(path + b'\0')
    def to_offset(self, va): return self.offsets[va]


class FixedDialogueTests(unittest.TestCase):
    def fixture(self):
        source = '名前は？'; raw = source.encode('cp932')
        blob = struct.pack('<7I', 0xffffffff, 1, 5, 0, 0, 0, 0) + raw + bytes(512-len(raw)) + bytes(4)
        r = dict(resource='SHIP/fixture.cht', sha256=digest(blob))
        e = dict(id='fixture', slot=0, offset=28, source_bytes=len(raw), source_sha256=digest(raw),
                 raw_hex=raw.hex(), decode='failed', observed_byte_capacity=515,
                 slot_sha256=digest(blob[28:]), trailer_bytes=0, trailer_sha256=digest(b''),
                 semantic='leading-field-unverified')
        b = dict(id=e['id'], resource=r['resource'], resource_sha256=r['sha256'], offset=28,
                 source_bytes=len(raw), source_sha256=digest(raw), native_read_bytes=512,
                 record_index=0, numeric_metadata_hex=blob[12:28].hex(), runtime_verified=False)
        return r, e, b, blob

    def test_native_instruction_and_path_anchors(self): validate_anchors(Image())

    def test_changed_read_size_anchor_rejected(self):
        image=Image(); struct.pack_into('<I', image.blob, image.to_offset(0x3a3ac0), 0x24060204)
        with self.assertRaisesRegex(ValueError, 'instruction mismatch'): validate_anchors(image)

    def test_changed_path_rejected(self):
        image=Image(); image.blob[image.to_offset(0x4b7740)] = 0
        with self.assertRaisesRegex(ValueError, 'path mismatch'): validate_anchors(image)

    def test_cht_native_512_not_legacy_516_capacity(self):
        geometry=validate_field(*self.fixture())
        self.assertEqual(geometry['writable_bytes'],512)
        self.assertEqual(geometry['fingerprint_bytes'],516)
        self.assertEqual(geometry['preserved_tail_bytes'],4)

    def test_changed_numeric_metadata_rejected(self):
        r,e,b,blob=self.fixture(); b['numeric_metadata_hex']='01'+b['numeric_metadata_hex'][2:]
        with self.assertRaisesRegex(ValueError,'numeric record metadata'): validate_field(r,e,b,blob)

    def test_wrong_resource_and_span_bindings_rejected(self):
        for k,v in [('resource_sha256','0'*64),('source_sha256','0'*64),('source_bytes',999),('offset',0)]:
            r,e,b,blob=self.fixture(); b[k]=v
            with self.subTest(key=k),self.assertRaises(ValueError): validate_field(r,e,b,blob)

    def test_native_512_with_dirty_padding_rejected(self):
        r,e,b,blob=self.fixture(); changed=bytearray(blob);changed[e['offset']+510]=1
        r['sha256']=b['resource_sha256']=digest(changed)
        with self.assertRaisesRegex(ValueError,'padding'): validate_field(r,e,b,bytes(changed))

    def test_truncated_physical_record_rejected(self):
        r,e,b,blob=self.fixture();blob=blob[:-4];r['sha256']=b['resource_sha256']=digest(blob)
        with self.assertRaisesRegex(ValueError,'physical record'): validate_field(r,e,b,blob)

    def test_native_read_size_and_runtime_claim_rejected(self):
        for k,v in [('native_read_bytes',516),('runtime_verified',True)]:
            r,e,b,blob=self.fixture();b[k]=v
            with self.subTest(key=k),self.assertRaisesRegex(ValueError,'read proof'):validate_field(r,e,b,blob)

    def test_pod_layout_all24_strings_and_interleaved_words(self):
        rows=pod_text_layout();self.assertEqual(len(rows),24)
        self.assertEqual(rows[0],dict(index=0,offset=20,native_fstring_offset=0x18))
        self.assertEqual(rows[19],dict(index=19,offset=9756,native_fstring_offset=0xfc))
        self.assertEqual(rows[10]['offset'],5144);self.assertEqual(rows[15]['offset'],7708)
        self.assertEqual(rows[23]['offset']+512+12,12328)

    def test_pod_explicit_native_fstring_offset(self):
        r,e,b,old=self.fixture();raw=bytes.fromhex(e['raw_hex']);blob=bytearray(12328);blob[9756:9756+len(raw)]=raw
        r.update(resource='SHIP/fixture.pod',sha256=digest(blob))
        e.update(offset=9756,field_index=19,slot_bytes=512,slot_sha256=digest(blob[9756:10268]))
        b.update(resource=r['resource'],resource_sha256=r['sha256'],offset=9756,record_index=19,native_fstring_offset=0xfc)
        validate_field(r,e,b,bytes(blob));b['native_fstring_offset']=0x18
        with self.assertRaisesRegex(ValueError,'string geometry'):validate_field(r,e,b,bytes(blob))

    def test_fixed_profile_derives_narrow_slot_and_preserved_tail(self):
        r,e,b,blob=self.fixture();primary=dict(resources=[dict(r,entries=[e])]);before=copy.deepcopy(primary)
        d=dict(id=e['id'],resource=r['resource'],resource_sha256=r['sha256'],offset=e['offset'],
               source_bytes=e['source_bytes'],source_sha256=e['source_sha256'],source_encoding='cp932',
               reading_sha256=digest('名前は？'.encode('utf8')),target='你的名字？',status='reviewed',
               import_approved=False,runtime_encoding_verified=False)
        profile=dict(schema=1,locale='zh-CN',entries=[d])
        derived,batch=derive(primary,profile,{'fixture.cht':blob},dict(schema=1,bindings=[b]))
        de=derived['resources'][0]['entries'][0];span,_=fixed_extent(de)
        self.assertEqual(primary,before);self.assertEqual(span,512)
        self.assertEqual(fingerprint_extent(de,span),516)
        self.assertEqual(de['trailer_sha256'],digest(bytes(4)))
        self.assertEqual(len(batch['entries']),1)
        self.assertEqual(derive(primary,profile,{'fixture.cht':blob})[1]['entries'],[])

    def test_duplicate_fixed_source_binding_rejected(self):
        r,e,b,blob=self.fixture();primary=dict(resources=[dict(r,entries=[e])]);d=dict(id=e['id'],resource=r['resource'],resource_sha256=r['sha256'],offset=e['offset'],source_bytes=e['source_bytes'],source_sha256=e['source_sha256'],source_encoding='cp932',reading_sha256=digest('名前は？'.encode('utf8')),target='名字？',status='reviewed',import_approved=False,runtime_encoding_verified=False)
        with self.assertRaisesRegex(ValueError,'duplicate fixed'):
            derive(primary,dict(schema=1,locale='zh-CN',entries=[d]),{'fixture.cht':blob},dict(schema=1,bindings=[b,b]))

    def test_checked_in_fixed_batch_bindings_are_exact(self):
        profile=json.loads((ROOT/'locales/zh-CN/proofreading/alternate-fixed-consumers.json').read_text('utf8'))
        batch=json.loads((ROOT/'locales/zh-CN/alternate-fixed-review-01.json').read_text('utf8'))
        self.assertEqual(len(profile['bindings']),39);self.assertEqual(len(batch['entries']),39)
        self.assertEqual({b['id'] for b in profile['bindings']},{b['id'] for b in batch['entries']})
        self.assertEqual(sum('.cht/' in b['id'] for b in profile['bindings']),37)
        self.assertEqual(sum('.pod/' in b['id'] for b in profile['bindings']),2)


if __name__=='__main__':unittest.main()
