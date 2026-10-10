import sys,struct,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_stream_tail_contexts import segment_candidate,map_properties,commandlet_oracle
from audit_numeric_resources import parse_words,word_context
from audit_compiled_semantics import classify

class StreamTailReviewTests(unittest.TestCase):
    def test_single_span(self):
        s=[dict(start=10,end=20,kind='known')]
        p=segment_candidate(dict(offset=12,bytes=4),s)
        self.assertEqual([(x['start'],x['end']) for x in p],[(12,16)])
    def test_cross_boundary(self):
        s=[dict(start=10,end=14),dict(start=14,end=20)]
        self.assertEqual(len(segment_candidate(dict(offset=12,bytes=6),s)),2)
    def test_gap_not_covered(self):
        self.assertIsNone(segment_candidate(dict(offset=12,bytes=6),[dict(start=10,end=14),dict(start=15,end=20)]))
    def test_outside_not_covered(self):
        self.assertIsNone(segment_candidate(dict(offset=9,bytes=6),[dict(start=10,end=20)]))
    def test_exact_endpoint(self):
        self.assertIsNotNone(segment_candidate(dict(offset=10,bytes=10),[dict(start=10,end=20)]))
    def test_partial_end_rejected(self):
        self.assertIsNone(segment_candidate(dict(offset=10,bytes=11),[dict(start=10,end=20)]))
    def test_map_truncated(self):
        with self.assertRaises(ValueError):map_properties(b'',{'exports':[dict(flags=0,declared_size=14)]*8,'names':['None']},0,14)
    def test_oracle_wrong_identity(self):
        with self.assertRaises(ValueError):commandlet_oracle(b'',b'',{},[dict(name='Other')]*8,0,10)

class NumericReviewTests(unittest.TestCase):
    def sample(self):return struct.pack('<6I',2,1,0,12,1,0xffffffff)
    def test_complete_word_geometry(self):
        rs=parse_words(self.sample(),'.val');self.assertEqual(len(rs),2);self.assertEqual(rs[-1]['s32'][-1],-1)
    def test_bad_kind(self):
        with self.assertRaises(ValueError):parse_words(struct.pack('<4I',1,2,0,1),'.val')
    def test_trailing_bytes(self):
        with self.assertRaises(ValueError):parse_words(self.sample()+b'x','.val')
    def test_truncated(self):
        with self.assertRaises(ValueError):parse_words(self.sample()[:-1],'.val')
    def test_unknown_extension(self):
        with self.assertRaises(ValueError):parse_words(self.sample(),'.bin')
    def test_word_containment(self):
        x=word_context(dict(offset=14,source_bytes=2),parse_words(self.sample(),'.val'));self.assertEqual(x['u32'],[12])
    def test_cross_word(self):
        x=word_context(dict(offset=11,source_bytes=3),parse_words(self.sample(),'.val'));self.assertEqual((x['first_word'],x['last_word']),(0,1))
    def test_cross_record_rejected(self):
        with self.assertRaises(ValueError):word_context(dict(offset=15,source_bytes=2),parse_words(self.sample(),'.val'))

class CompiledSemanticTests(unittest.TestCase):
    def row(self,symbols,text='hello',owner='Init',assignment=False):
        return dict(id='fixture',text=text,call_context=[dict(symbols=[s]) for s in symbols],owner=owner,assignment_context=assignment,sha256='unchanged')
    def test_display(self):self.assertEqual(classify(self.row(['SetCaption']))['semantic_classification'],'visible-text-candidate')
    def test_debug_display(self):self.assertEqual(classify(self.row(['DrawText'],owner='DisplayDebug'))['semantic_classification'],'diagnostic-text-candidate')
    def test_lookup_inside_display(self):self.assertEqual(classify(self.row(['Message','Localize']))['semantic_classification'],'internal-lookup-or-command-candidate')
    def test_concat_inside_display(self):self.assertEqual(classify(self.row(['SetText','Concat_StrStr']))['semantic_classification'],'visible-text-candidate')
    def test_diagnostic(self):self.assertEqual(classify(self.row(['Warn','Concat_StrStr']))['semantic_classification'],'diagnostic-text-candidate')
    def test_unreviewed_symbol(self):self.assertEqual(classify(self.row(['SomeCall']))['semantic_classification'],'unresolved')
    def test_comparison_not_excluded(self):self.assertEqual(classify(self.row(['EqualEqual_StrStr']))['semantic_classification'],'unresolved')
    def test_assignment_not_excluded(self):self.assertEqual(classify(self.row([],assignment=True))['semantic_classification'],'unresolved')
    def test_empty_preserved(self):self.assertEqual(classify(self.row(['SetText'],text=''))['semantic_classification'],'internal-empty-value')
    def test_not_editable(self):
        r=classify(self.row(['SetCaption']));self.assertFalse(r['editable']);self.assertFalse(r['backend_eligible']);self.assertFalse(r['runtime_visibility_verified']);self.assertEqual(r['sha256'],'unchanged')

class ReviewConsolidationTests(unittest.TestCase):
    def fixture(self):
        return dict(resources=[dict(resource='FILE/fixture.int',entries=[dict(id='x',source_sha256='h',source_bytes=2,offset=10,references={'und':'%s'},decode='strict',controls='research-unclassified',editable=False)])])
    def review(self):
        return dict(id='x',source_sha256='h',editable=False,category='visible-text-candidate',semantic_review='classified-candidate-not-runtime-proof',reason='label',evidence_level='high-confidence-deduction')
    def test_annotations_preserve_source(self):
        from audit_coverage_review import annotate
        c=self.fixture();r=annotate(c,[self.review()],[],[],[])
        self.assertEqual(r['resources'][0]['entries'][0]['references'],{'und':'%s'})
        self.assertNotIn('coverage_reviews',c['resources'][0]['entries'][0])
        self.assertFalse(r['complete_game_text'])
    def test_bad_hash(self):
        from audit_coverage_review import annotate
        row=self.review();row['source_sha256']='bad'
        with self.assertRaises(ValueError):annotate(self.fixture(),[row],[],[],[])
    def test_unknown_id(self):
        from audit_coverage_review import annotate
        row=self.review();row['id']='other'
        with self.assertRaises(ValueError):annotate(self.fixture(),[row],[],[],[])
    def test_duplicate_review(self):
        from audit_coverage_review import annotate
        with self.assertRaises(ValueError):annotate(self.fixture(),[self.review()]*2,[],[],[])
    def test_edit_authorization_rejected(self):
        from audit_coverage_review import annotate
        row=self.review();row['editable']=True
        with self.assertRaises(ValueError):annotate(self.fixture(),[row],[],[],[])
    def test_numeric_does_not_change_bytes(self):
        from audit_coverage_review import annotate
        row=dict(id='x',source_sha256='h',editable=False,category='fixed-word-payload-not-translatable',record=0,first_word=0,last_word=0)
        r=annotate(self.fixture(),[],[row],[],[])
        self.assertEqual(r['resources'][0]['entries'][0]['source_bytes'],2)
    def test_quarantine_kept(self):
        from audit_coverage_review import annotate
        c=self.fixture();c['resources'][0]['entries'][0]['controls']='quarantined'
        row=dict(id='x',source_sha256='h',editable=False,observations=[dict(classification='numeric-percent')])
        r=annotate(c,[],[],[],[row]);self.assertEqual(r['resources'][0]['entries'][0]['controls'],'quarantined')

if __name__=='__main__':unittest.main()
