import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from audit_parser_operands import operand_role, review


def row(owner='ProcessSpecialWord', text='I', parent=0x0a, symbols=(), category='unresolved'):
    export = {'ProcessSpecialWord': 7196, 'GetTextNum': 6001, 'ParseAmpersand': 1260}[owner]
    package = 'UWindow.u' if owner == 'ParseAmpersand' else 'MrtsEngine.u'
    return dict(id=f'FILE/{package}/export/{export}/string/0', owner=owner, text=text,
                parent_opcode=parent, call_context=[dict(symbols=list(symbols))] if symbols else [],
                semantic_classification=category, sha256='original', offset=123)


class ParserOperandTests(unittest.TestCase):
    def test_switch(self):
        self.assertEqual(operand_role(row()), 'parser-switch-discriminator')

    def test_get_text_switch(self):
        self.assertEqual(operand_role(row(owner='GetTextNum')), 'parser-switch-discriminator')

    def test_search(self):
        self.assertEqual(operand_role(row(text='$', parent=0x1c, symbols=['InStrA'])), 'parser-delimiter-search')

    def test_ampersand_search(self):
        self.assertEqual(operand_role(row(owner='ParseAmpersand', text='&', parent=126, symbols=['InStr'])), 'parser-delimiter-search')

    def test_escape_compare(self):
        self.assertEqual(operand_role(row(owner='ParseAmpersand', text='&', parent=122, symbols=['EqualEqual_StrStr'])), 'parser-escape-comparison')

    def test_generated(self):
        self.assertEqual(operand_role(row(text='$W$E', parent=112, symbols=['Concat_StrStr'])), 'parser-generated-control-sequence')

    def test_wrong_scope(self):
        x=row(); x['id']='FILE/Other.u/export/7196/string/0'; self.assertIsNone(operand_role(x))

    def test_wrong_owner(self):
        x=row(); x['owner']='DrawText'
        with self.assertRaises(ValueError): operand_role(x)

    def test_other_categories_unchanged(self):
        x=row(category='visible-text-candidate'); self.assertEqual(review([x]), [x])

    def test_multichar_case_retained(self):
        self.assertIsNone(operand_role(row(text='Dialogue')))

    def test_unreviewed_call_retained(self):
        self.assertIsNone(operand_role(row(text='$', parent=0x1c, symbols=['DrawText'])))

    def test_nearest_call_only(self):
        x=row(text='$', parent=0x1c, symbols=['InStrA']); x['call_context'].append(dict(symbols=['DrawText']))
        self.assertIsNone(operand_role(x))

    def test_ui_concat_retained(self):
        self.assertIsNone(operand_role(row(owner='ParseAmpersand', text='_', parent=112, symbols=['Concat_StrStr'])))

    def test_generic_comparison_retained(self):
        self.assertIsNone(operand_role(row(text='I', parent=122, symbols=['EqualEqual_StrStr'])))

    def test_no_mutation_or_import(self):
        x=row(); y=review([x])[0]; self.assertEqual(x['semantic_classification'], 'unresolved')
        self.assertEqual(y['sha256'],x['sha256']);self.assertEqual(y['offset'],x['offset'])
        self.assertFalse(y['editable']);self.assertFalse(y['runtime_visibility_verified'])
        self.assertFalse(y['full_parser_semantics_verified'])

    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError): review([row(), row()])


if __name__ == '__main__': unittest.main()
