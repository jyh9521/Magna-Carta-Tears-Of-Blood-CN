from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from audit_compiled_field_contexts import field_reference, assignment_target, classify_assignment, subtree
from audit_literal_contexts import ancestry
from audit_stream_native_strings import compact_strings


class NativeStringsTests(unittest.TestCase):
    def test_sequence(self):
        r=compact_strings(b'\x02A\0\0\x02B\0\0',0,8,4)
        self.assertEqual([x['text'] for x in r], ['A','','B',''])
    def test_exact_offsets(self):
        r=compact_strings(b'xx\x02A\0',2,5,1)[0]
        self.assertEqual((r['start'],r['text_start'],r['end']), (2,3,5))
    def test_utf16(self): self.assertEqual(compact_strings(b'\x82A\0\0\0',0,5,1)[0]['text'], 'A')
    def test_missing_terminator(self):
        with self.assertRaises(ValueError): compact_strings(b'\x02AB',0,3,1)
    def test_string_overrun(self):
        with self.assertRaises(ValueError): compact_strings(b'\x03A\0',0,3,1)
    def test_extra_bytes(self):
        with self.assertRaises(ValueError): compact_strings(b'\0x',0,2,1)
    def test_negative_start(self):
        with self.assertRaises(ValueError): compact_strings(b'\0',-1,1,1)
    def test_past_eof(self):
        with self.assertRaises(ValueError): compact_strings(b'\0',0,2,1)
    def test_zero_count(self):
        with self.assertRaises(ValueError): compact_strings(b'\0',0,1,0)
    def test_count_overrun(self):
        with self.assertRaises(ValueError): compact_strings(b'\0',0,1,2)
    def test_count_limit(self):
        with self.assertRaises(ValueError): compact_strings(bytes(33),0,33,33)


class FieldContextTests(unittest.TestCase):
    def row(self, owner='Paint', classification='unresolved'):
        return dict(id='FILE/test.u/export/3/string/0',owner=owner,semantic_classification=classification,
                    semantic_reason='old',sha256='original',editable=False,backend_eligible=False)
    def target(self, simple=True, cls='StrProperty'):
        return dict(simple_field=simple,fields=[dict(reference=1,name='text',field_class=cls)])
    def use(self,symbol='SetText',local=True,lhs=False):
        return dict(object_id='FILE/test.u/export/'+('3' if local else '4'),assignment_lhs=lhs,calls=[dict(symbols=[symbol])])
    def tokens(self):
        return [dict(offset=0,depth=0,opcode=15,parent_opcode=None),
                dict(offset=1,depth=1,opcode=71,parent_opcode=15),
                dict(offset=3,depth=1,opcode=31,parent_opcode=15)]
    def exports(self): return [dict(name='text',class_='StrProperty',outer=3,**{'class':'StrProperty'})]
    def refs(self,value=1): return [dict(offset=2,value=value,kind='object')]
    def test_reference(self): self.assertEqual(field_reference(self.tokens()[1],self.refs(),self.exports())['name'],'text')
    def test_null_kept_unknown(self): self.assertEqual(field_reference(self.tokens()[1],self.refs(0),[])['field_class'],'unresolved-import-or-null')
    def test_import_kept_unknown(self):
        r=field_reference(self.tokens()[1],self.refs(-1),[],[dict(name='inherited')]); self.assertEqual(r['name'],'inherited')
    def test_reference_bounds(self):
        with self.assertRaises(ValueError): field_reference(self.tokens()[1],self.refs(2),self.exports())
    def test_import_bounds(self):
        with self.assertRaises(ValueError): field_reference(self.tokens()[1],self.refs(-2),[],[dict(name='one')])
    def test_missing_reference(self):
        with self.assertRaises(ValueError): field_reference(self.tokens()[1],[],self.exports())
    def test_duplicate_reference(self):
        with self.assertRaises(ValueError): field_reference(self.tokens()[1],self.refs()*2,self.exports())
    def test_nonfield_token(self): self.assertIsNone(field_reference(self.tokens()[2],[],[]))
    def test_simple_target(self):
        ts=self.tokens();r=assignment_target(dict(token_offset=3),ts,ancestry(ts),self.refs(),self.exports());self.assertTrue(r['simple_field'])
    def test_no_assignment(self):
        ts=[dict(offset=0,depth=0,opcode=31,parent_opcode=None)]
        self.assertIsNone(assignment_target(dict(token_offset=0),ts,ancestry(ts),[],[]))
    def test_literal_on_lhs_rejected(self):
        ts=self.tokens()
        with self.assertRaises(ValueError): assignment_target(dict(token_offset=1),ts,ancestry(ts),self.refs(),self.exports())
    def test_subtree(self):
        ts=[dict(depth=x) for x in (0,1,2,1,0)];self.assertEqual(len(subtree(ts,1)),2)
    def test_display_candidate(self):
        self.assertEqual(classify_assignment(self.row(),self.target(),[self.use()])['semantic_classification'],'visible-text-candidate')
    def test_debug_candidate(self):
        self.assertEqual(classify_assignment(self.row('DisplayDebug'),self.target(),[self.use('DrawText')])['semantic_classification'],'diagnostic-text-candidate')
    def test_lookup_candidate(self):
        self.assertEqual(classify_assignment(self.row(),self.target(),[self.use('FindObject')])['semantic_classification'],'internal-lookup-or-command-candidate')
    def test_mixed_retained(self):
        self.assertEqual(classify_assignment(self.row(),self.target(),[self.use(),self.use('FindObject')])['semantic_classification'],'unresolved')
    def test_cross_function_not_promoted(self):
        self.assertEqual(classify_assignment(self.row(),self.target(),[self.use(local=False)])['semantic_classification'],'unresolved')
    def test_lhs_not_consumer(self):
        self.assertEqual(classify_assignment(self.row(),self.target(),[self.use(lhs=True)])['semantic_classification'],'unresolved')
    def test_measurement_not_display(self):
        self.assertEqual(classify_assignment(self.row(),self.target(),[self.use('TextSize')])['semantic_classification'],'unresolved')
    def test_unknown_call_retained(self):
        self.assertEqual(classify_assignment(self.row(),self.target(),[self.use('Other')])['semantic_classification'],'unresolved')
    def test_integer_sink_retained(self):
        self.assertEqual(classify_assignment(self.row(),self.target(cls='IntProperty'),[self.use()])['semantic_classification'],'unresolved')
    def test_complex_lhs_retained(self):
        self.assertEqual(classify_assignment(self.row(),self.target(simple=False),[self.use()])['semantic_classification'],'unresolved')
    def test_no_target_retained(self):
        self.assertEqual(classify_assignment(self.row(),None,[])['semantic_classification'],'unresolved')
    def test_original_category_preserved(self):
        r=self.row(classification='diagnostic-text-candidate');self.assertEqual(classify_assignment(r,self.target(),[self.use()]),r)
    def test_input_unchanged(self):
        r=self.row();classify_assignment(r,self.target(),[self.use()]);self.assertNotIn('assignment_target',r)
    def test_not_runtime_or_import_proof(self):
        r=classify_assignment(self.row(),self.target(),[self.use()]);self.assertFalse(r['editable']);self.assertFalse(r['runtime_visibility_verified']);self.assertFalse(r['reaching_definition_verified']);self.assertEqual(r['sha256'],'original')


if __name__=='__main__': unittest.main()
