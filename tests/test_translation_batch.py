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


if __name__=='__main__':unittest.main()
