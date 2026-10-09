import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from assemble_source_corpus import merge_resources,link_drafts


def resource(identity,start=4,sha='bytes'):
    return dict(resource='SHIP/fixture.fds',size=20,sha256='resource',
                entries=[dict(id=identity,offset=start,source_bytes=2,source_sha256=sha)])


class SourceCorpusTests(unittest.TestCase):
    def test_exact_alias_and_original_preserved(self):
        old,new=resource('old'),resource('new');saved=copy.deepcopy(old)
        merged,aliases,superseded=merge_resources([old],[new])
        self.assertEqual(aliases[0]['old_id'],'old')
        self.assertEqual(merged[0]['entries'][0]['source_aliases'],['old'])
        self.assertEqual(old,saved);self.assertEqual(superseded,[old])

    def test_same_text_hash_different_position_not_alias(self):
        self.assertEqual(merge_resources([resource('old')],[resource('new',5)])[1],[])

    def test_same_position_different_hash_not_alias(self):
        self.assertEqual(merge_resources([resource('old')],[resource('new',sha='different')])[1],[])

    def test_resource_identity_rejected(self):
        new=resource('new');new['sha256']='bad'
        with self.assertRaisesRegex(ValueError,'resource identity'):
            merge_resources([resource('old')],[new])

    def test_duplicate_resource_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate supplement'):
            merge_resources([resource('old')],[resource('new')]*2)

    def test_exact_draft_link_not_translation_copy(self):
        old=[resource('old')];merged,aliases,_=merge_resources(old,[resource('new')])
        link=link_drafts(old,merged,aliases,[dict(id='old',source_sha256='bytes')])[0]
        self.assertEqual(link['disposition'],'exact-byte-alias')
        self.assertFalse(link['translation_written'])

    def test_partial_draft_requires_remap(self):
        old=[resource('old')];merged,aliases,_=merge_resources(old,[resource('new',5)])
        link=link_drafts(old,merged,aliases,[dict(id='old',source_sha256='bytes')])[0]
        self.assertIsNone(link['new_id']);self.assertEqual(link['disposition'],'requires-source-remap')

    def test_bad_draft_hash_rejected(self):
        with self.assertRaisesRegex(ValueError,'draft source'):
            link_drafts([resource('old')],[resource('old')],[],[dict(id='old',source_sha256='bad')])

    def test_ambiguous_alias_rejected(self):
        aliases=[dict(old_id='old',new_id='a'),dict(old_id='old',new_id='b')]
        with self.assertRaisesRegex(ValueError,'ambiguous'):
            link_drafts([resource('old')],[],aliases,[dict(id='old',source_sha256='bytes')])


if __name__=='__main__':
    unittest.main()
