import unittest
import sys
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/p) for p in ('tools','src','lib')]
from import_audited_fields import binding_index,resolve_source


class AliasTests(unittest.TestCase):
    def setUp(self):
        self.entry=dict(id='resource/canonical',source_sha256='hash',source_aliases=['resource/legacy'])
        self.corpus=dict(resources=[dict(resource='SHIP/example.cha',entries=[self.entry])])
    def resolve(self,identity='resource/legacy',hash='hash'):
        i,a=binding_index(self.corpus);return resolve_source(i,a,dict(id=identity,source_sha256=hash))
    def test_alias_keeps_external_id(self):
        _,e=self.resolve();self.assertEqual(e['id'],'resource/legacy');self.assertEqual(e['canonical_id'],self.entry['id']);self.assertEqual(self.entry['id'],'resource/canonical')
    def test_canonical(self):
        _,e=self.resolve('resource/canonical');self.assertEqual(e['canonical_id'],self.entry['id'])
    def test_alias_hash_mismatch(self):
        with self.assertRaisesRegex(ValueError,'source mismatch'):self.resolve(hash='other')
    def test_unknown(self):
        with self.assertRaisesRegex(ValueError,'missing'):self.resolve('other')
    def test_ambiguous_alias_even_if_hash_equal(self):
        self.corpus['resources'][0]['entries'].append(dict(self.entry,id='another'))
        with self.assertRaisesRegex(ValueError,'ambiguous'):self.resolve()
    def test_duplicate_canonical(self):
        self.corpus['resources'][0]['entries'].append(dict(self.entry))
        with self.assertRaisesRegex(ValueError,'duplicate'):binding_index(self.corpus)
    def test_canonical_alias_collision(self):
        self.corpus['resources'][0]['entries'].append(dict(self.entry,id='another',source_aliases=['resource/canonical']))
        with self.assertRaisesRegex(ValueError,'collides'):self.resolve('resource/canonical')
    def test_invalid_alias(self):
        self.entry['source_aliases']=[None]
        with self.assertRaisesRegex(ValueError,'invalid'):binding_index(self.corpus)


if __name__=='__main__':unittest.main()
