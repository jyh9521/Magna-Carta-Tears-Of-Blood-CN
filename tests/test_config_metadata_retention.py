import copy, hashlib, sys, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','src','lib')]
import prepare_config_metadata_retention as m
from prepare_translation_scope import disposition, freeze

class Image:
    blob=bytes(range(64))
    def to_offset(self,va):return va-0x1000

class ConfigRetentionTests(unittest.TestCase):
    def setUp(self):
        self.raw=b'[URL]\r\nName=Player\r\n';h=m.digest(self.raw)
        self.e=dict(id='FILE/sample.ini/line/2',offset=12,source_bytes=6,source_sha256=m.digest(b'Player'),section='URL',key='Name',
            references={'und':'Player'},semantic='unresolved',editable=False,backend_eligible=False,decode='strict',controls='plain')
        self.r=dict(resource='FILE/sample.ini',sha256=h,entries=[self.e]);self.c={'resources':[self.r]}
        self.d=dict(id=self.e['id'],resource=self.r['resource'],resource_sha256=h,**{k:self.e[k] for k in ('offset','source_bytes','source_sha256','section','key')},source='Player',status='reviewed',role='default-player-identity',disposition='retain-config-metadata',import_approved=False,runtime_visibility_verified=False,reason='Preserve engine identity; no invisibility claim.',native_windows=[{'va':'0x1000','hex':Image.blob[:16].hex()}])
        self.p=dict(schema=1,elf_sha256=m.digest(Image.blob),entries=[self.d]);self.members={'sample.ini':self.raw}
    def derive(self):
        with patch.object(m,'ELF_SHA256',m.digest(Image.blob)):return m.derive(self.c,self.p,self.members,Image())
    def test_preserves_source_and_semantics(self):
        before=copy.deepcopy(self.c);out,proofs=self.derive();self.assertEqual(self.c,before);e=out['resources'][0]['entries'][0];p=e.pop('config_metadata_retention');self.assertEqual(e,self.e);self.assertEqual(len(proofs),1);self.assertFalse(p['import_approved'])
    def test_scope_explicit_retention(self):
        out,_=self.derive();e=out['resources'][0]['entries'][0];self.assertEqual(disposition(self.r,e)[0],'retain-config-metadata');rows,s=freeze(out,[]);self.assertTrue(rows[0]['source_retention_required']);self.assertEqual(s['unfilled_translation_candidates'],0);self.assertFalse(s['full_iso_ready'])
    def test_default_unresolved_unchanged(self):self.assertEqual(disposition(self.r,self.e)[0],'deferred-semantics')
    def test_wrong_native_bytes_rejected(self):
        self.d['native_windows'][0]['hex']='ff'*16
        with self.assertRaises(ValueError):self.derive()
    def test_source_hash_rejected(self):
        self.d['source_sha256']='0'*64
        with self.assertRaises(ValueError):self.derive()
    def test_archive_bytes_rejected(self):
        self.members['sample.ini']=self.raw.replace(b'Player',b'Other!')
        with self.assertRaises(ValueError):self.derive()
    def test_runtime_claim_rejected(self):
        self.d['runtime_visibility_verified']=True
        with self.assertRaises(ValueError):self.derive()
    def test_import_claim_rejected(self):
        self.d['import_approved']=True
        with self.assertRaises(ValueError):self.derive()
    def test_duplicate_rejected(self):
        self.p['entries'].append(copy.deepcopy(self.d))
        with self.assertRaises(ValueError):self.derive()
    def test_quarantine_rejected(self):
        self.e['controls']='quarantined'
        with self.assertRaises(ValueError):self.derive()
    def test_modified_proof_cannot_bypass_quarantine(self):
        out,_=self.derive();e=out['resources'][0]['entries'][0];e['controls']='quarantined'
        with self.assertRaises(ValueError):disposition(self.r,e)
    def test_editable_rejected(self):
        self.e['editable']=True
        with self.assertRaises(ValueError):self.derive()
    def test_retention_conflicts_with_translation(self):
        out,_=self.derive();b={'locale':'zh-CN','entries':[dict(id=self.e['id'],source_sha256=self.e['source_sha256'],status='reviewed',target='玩家')]}
        with self.assertRaises(ValueError):freeze(out,[b])
if __name__=='__main__':unittest.main()
