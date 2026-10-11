import copy
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'src'),str(ROOT/'lib')]
from validate_translation_batch import validate,glossary_terms
from extract_strings import field


class TranslationBatchTests(unittest.TestCase):
    def setUp(self):
        source=field('test','유파$n'.encode('cp949'),0)
        self.catalog=dict(source_locale='ko-KR',resources=[dict(entries=[source])])
        self.batch=dict(schema=1,locale='zh-CN',entries=[dict(id='test',source_sha256=source['source_sha256'],target='流派$n',status='draft')])
        self.terms=[('유파','流派')]

    def test_valid_batch(self):
        self.assertEqual(validate(self.catalog,self.batch,self.terms)['entries'],1)

    def test_source_hash(self):
        self.batch['entries'][0]['source_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'identity'):validate(self.catalog,self.batch,self.terms)

    def test_duplicate_id(self):
        self.batch['entries']*=2
        with self.assertRaisesRegex(ValueError,'duplicate'):validate(self.catalog,self.batch,self.terms)

    def test_unknown_id(self):
        self.batch['entries'][0]['id']='other'
        with self.assertRaisesRegex(ValueError,'unknown'):validate(self.catalog,self.batch,self.terms)

    def test_unique_source_alias_keeps_original_binding(self):
        self.catalog['resources'][0]['entries'][0]['source_aliases']=['legacy']
        self.batch['entries'][0]['id']='legacy'
        self.assertEqual(validate(self.catalog,self.batch,self.terms)['entries'],1)
        self.assertEqual(self.batch['entries'][0]['id'],'legacy')
        self.batch['entries'][0]['source_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'identity'):validate(self.catalog,self.batch,self.terms)

    def test_alias_and_canonical_target_are_duplicate(self):
        self.catalog['resources'][0]['entries'][0]['source_aliases']=['legacy']
        row=copy.deepcopy(self.batch['entries'][0]);row['id']='legacy'
        self.batch['entries'].append(row)
        with self.assertRaisesRegex(ValueError,'duplicate'):validate(self.catalog,self.batch,self.terms)

    def test_ambiguous_alias_rejected(self):
        first=self.catalog['resources'][0]['entries'][0];first['source_aliases']=['legacy']
        second=copy.deepcopy(first);second['id']='second'
        self.catalog['resources'][0]['entries'].append(second)
        self.batch['entries'][0]['id']='legacy'
        with self.assertRaisesRegex(ValueError,'ambiguous'):validate(self.catalog,self.batch,self.terms)

    def test_token_protection(self):
        self.batch['entries'][0]['target']='流派'
        with self.assertRaisesRegex(ValueError,'token'):validate(self.catalog,self.batch,self.terms)

    def test_glossary_consistency(self):
        self.batch['entries'][0]['target']='门派$n'
        with self.assertRaisesRegex(ValueError,'glossary'):validate(self.catalog,self.batch,self.terms)

    def test_font_missing(self):
        with self.assertRaisesRegex(ValueError,'missing font'):validate(self.catalog,self.batch,self.terms,{})

    def test_empty_target(self):
        self.batch['entries'][0]['target']=''
        with self.assertRaisesRegex(ValueError,'empty'):validate(self.catalog,self.batch,self.terms)

    def test_quarantine(self):
        self.catalog['resources'][0]['entries'][0]['controls']='quarantined'
        with self.assertRaisesRegex(ValueError,'quarantined'):validate(self.catalog,self.batch,self.terms)

    def test_glossary_md(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'terms.md';p.write_text('| 유파 | 流派 | 系统 | 暂定统一 | 来源 |\n','utf8')
            self.assertEqual(glossary_terms(p),self.terms)
            p.write_text(p.read_text('utf8')*2,'utf8')
            with self.assertRaisesRegex(ValueError,'duplicate'):glossary_terms(p)

    def test_longest_name_wins(self):
        source=field('test','크리스 아크웨이와 리스'.encode('cp949'),0)
        self.catalog['resources'][0]['entries']=[source]
        self.batch['entries'][0].update(source_sha256=source['source_sha256'],target='克里斯·阿克韦和莉丝')
        terms=[('리스','莉丝'),('크리스 아크웨이','克里斯·阿克韦')]
        self.assertEqual(validate(self.catalog,self.batch,terms)['entries'],1)

    def test_list_not_short_name(self):
        source=field('test','리스트'.encode('cp949'),0)
        self.catalog['resources'][0]['entries']=[source]
        self.batch['entries'][0].update(source_sha256=source['source_sha256'],target='列表')
        self.assertEqual(validate(self.catalog,self.batch,[('리스','莉丝'),('리스트','列表')])['entries'],1)

    def test_separate_short_name_still_checked(self):
        source=field('test','크리스 아크웨이와 리스'.encode('cp949'),0)
        self.catalog['resources'][0]['entries']=[source]
        self.batch['entries'][0].update(source_sha256=source['source_sha256'],target='克里斯·阿克韦')
        with self.assertRaisesRegex(ValueError,'리스'):
            validate(self.catalog,self.batch,[('리스','莉丝'),('크리스 아크웨이','克里斯·阿克韦')])

    def test_exact_source_homonym_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'terms.md';p.write_text('| 사과 | 苹果 | 道具 | 已统一 | [match=exact-source] |\n','utf8')
            terms=glossary_terms(p);self.assertEqual(terms,[('사과','苹果')]);self.assertEqual(terms.exact_only,{'사과'})
            for original,target,accepted in [('사과','苹果',True),('사과','道歉',False),('사과 드립니다','向您道歉',True)]:
                source=field('test',original.encode('cp949'),0);self.catalog['resources'][0]['entries']=[source]
                self.batch['entries'][0].update(source_sha256=source['source_sha256'],target=target)
                if accepted:self.assertEqual(validate(self.catalog,self.batch,terms)['entries'],1)
                else:
                    with self.assertRaisesRegex(ValueError,'glossary'):validate(self.catalog,self.batch,terms)


if __name__=='__main__':unittest.main()
