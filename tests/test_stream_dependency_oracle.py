import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from audit_stream_dependencies import resolve_reference, equivalent_native_span

class DependencyIdentityTests(unittest.TestCase):
    def packs(self):
        imports = [dict(name='Core', outer=0), dict(name='Owner', outer=-1), dict(name='Scale', outer=-2)]
        exports = [dict(name='Scale',outer=0,index=1),dict(name='Owner',outer=0,index=2),dict(name='Scale',outer=2,index=3)]
        return {'Engine.u': (b'', {'imports': imports}, []), 'Core.u': (b'', {'imports': []}, exports)}
    def test_null(self): self.assertIsNone(resolve_reference({}, 'missing', 0))
    def test_scoped_import(self): self.assertEqual(resolve_reference(self.packs(),'Engine.u',-3),('Core.u',3))
    def test_positive(self): self.assertEqual(resolve_reference(self.packs(),'Core.u',2),('Core.u',2))
    def test_positive_bounds(self):
        with self.assertRaises(ValueError): resolve_reference(self.packs(),'Core.u',4)
    def test_import_bounds(self):
        with self.assertRaises(ValueError): resolve_reference(self.packs(),'Engine.u',-4)
    def test_import_cycle(self):
        p=self.packs();p['Engine.u'][1]['imports'][1]['outer']=-3
        with self.assertRaises(ValueError): resolve_reference(p,'Engine.u',-3)
    def test_outer_bounds(self):
        p=self.packs();p['Core.u'][2][2]['outer']=4
        with self.assertRaises(ValueError): resolve_reference(p,'Engine.u',-3)
    def test_outer_cycle(self):
        p=self.packs();p['Core.u'][2][1]['outer']=3
        with self.assertRaises(ValueError): resolve_reference(p,'Engine.u',-3)
    def test_missing_target(self):
        p=self.packs();del p['Core.u']
        with self.assertRaises(ValueError): resolve_reference(p,'Engine.u',-3)
    def test_duplicate_identity(self):
        p=self.packs();p['Core.u'][2].append(dict(name='Scale',outer=2,index=4))
        with self.assertRaises(ValueError): resolve_reference(p,'Engine.u',-3)
    def test_missing_identity(self):
        p=self.packs();p['Core.u'][2][2]['name']='Other'
        with self.assertRaises(ValueError): resolve_reference(p,'Engine.u',-3)
    def test_invalid_import_scope(self):
        p=self.packs();p['Engine.u'][1]['imports'][2]['outer']=1
        with self.assertRaises(ValueError): resolve_reference(p,'Engine.u',-3)
    def test_missing_source(self):
        with self.assertRaises(ValueError): resolve_reference({},'Missing.u',1)

class NativeEquivalenceTests(unittest.TestCase):
    def test_empty(self): self.assertIsNone(equivalent_native_span([]))
    def test_unique(self): self.assertEqual(equivalent_native_span([(('Core.u',1),b'A'*16)]),([('Core.u',1)],b'A'*16))
    def test_identity_ambiguity_retained(self):
        ids, raw=equivalent_native_span([(('Core.u',1),b'A'*16),(('Other.u',2),b'A'*16)])
        self.assertEqual(ids,[('Core.u',1),('Other.u',2)]);self.assertEqual(raw,b'A'*16)
    def test_different_bytes(self): self.assertIsNone(equivalent_native_span([(('Core.u',1),b'A'*16),(('Core.u',2),b'B'*16)]))
    def test_different_lengths(self): self.assertIsNone(equivalent_native_span([(('Core.u',1),b'A'*16),(('Core.u',2),b'A'*17)]))
    def test_short_rejected(self):
        with self.assertRaises(ValueError): equivalent_native_span([(('Core.u',1),b'A')])
    def test_duplicate_identity(self):
        with self.assertRaises(ValueError): equivalent_native_span([(('Core.u',1),b'A'*16),(('Core.u',1),b'A'*16)])

if __name__=='__main__': unittest.main()
