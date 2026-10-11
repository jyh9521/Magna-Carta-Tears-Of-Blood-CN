import hashlib,sys,unittest
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/p) for p in ('tools','src','lib')]
from config_translation import template_tokens,validate_value,config_lines,rewrite_values

class Encoder:
    def encode_characters(self,s):return s.encode('ascii')

class ConfigTranslationTests(unittest.TestCase):
    def test_opaque_death_macros_preserved(self):self.assertTrue(validate_value('%o by %k %w','%o killed %k %w','localized-template'))
    def test_unknown_macro_rejected(self):
        with self.assertRaisesRegex(ValueError,'unknown'):template_tokens('%q')
    def test_macro_order_rejected(self):
        with self.assertRaisesRegex(ValueError,'tokens'):validate_value('%s %i','%i %s','localized-template')
    def test_literal_percentage_and_precision(self):self.assertEqual(template_tokens('%3.1f%%')['percent'],['%3.1f','%%'])
    def test_accelerator_letter(self):self.assertTrue(validate_value('E&xit','Exit(&x)','localized-template'))
    def test_accelerator_changed(self):
        with self.assertRaisesRegex(ValueError,'tokens'):validate_value('&Back','Back(&N)','localized-template')
    def test_backslash_newline_exact(self):
        with self.assertRaisesRegex(ValueError,'tokens'):validate_value(r'a\\n',r'b\n','localized-template')
    def test_path_exact(self):
        with self.assertRaisesRegex(ValueError,'tokens'):validate_value(r'C:\Folder',r'D:\Folder','localized-template')
    def test_quote_wrapper(self):
        with self.assertRaisesRegex(ValueError,'wrapper'):validate_value('"value"','value','localized-template')
    def test_ui_angle_tokens(self):self.assertTrue(validate_value('< &Back','< Back(&B)','localized-template'))
    def test_dollar_placeholder_added(self):
        with self.assertRaisesRegex(ValueError,'tokens'):validate_value('value','value $q','localized-template')
    def test_descriptor_labels_only(self):
        self.assertTrue(validate_value('(Caption="A",Parent="B",Class=Core.System,Immediate=True)','(Caption="C",Parent="D",Class=Core.System,Immediate=True)','preference-descriptor',parent_labels={'B':{'target':'D'}}))
    def test_unbound_parent_change_rejected(self):
        with self.assertRaisesRegex(ValueError,'unbound'):validate_value('(Caption="A",Parent="B")','(Caption="C",Parent="D")','preference-descriptor')
    def test_descriptor_class_change(self):
        with self.assertRaisesRegex(ValueError,'machine'):validate_value('(Caption="A",Class=Core.System)','(Caption="A",Class=New.System)','preference-descriptor')
    def test_descriptor_flag_change(self):
        with self.assertRaisesRegex(ValueError,'machine'):validate_value('(Caption="A",Immediate=True)','(Caption="A",Immediate=False)','preference-descriptor')
    def fixture(self):
        raw=b';comment\r\n[Test]\r\nLabel=old\r\nMachine=Class.Name\r\n';row=config_lines(raw)[0]
        e=dict(id='FILE/Test.int/line/3',source_sha256=hashlib.sha256(b'old').hexdigest(),source_bytes=3,**{k:row[k] for k in ('line','offset','section','section_occurrence','key')})
        t=dict(id=e['id'],source_sha256=e['source_sha256'],target='newlong',value_kind='localized-template')
        return raw,e,t
    def test_selected_value_only_and_newlines(self):
        raw,e,t=self.fixture();new,_=rewrite_values(raw,[e],[t],Encoder());self.assertEqual(new,raw.replace(b'Label=old',b'Label=newlong'))
    def test_source_hash_mismatch(self):
        raw,e,t=self.fixture();e['source_sha256']=t['source_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'geometry'):rewrite_values(raw,[e],[t],Encoder())
    def test_section_key_mismatch(self):
        raw,e,t=self.fixture();e['key']='Other'
        with self.assertRaisesRegex(ValueError,'section/key'):rewrite_values(raw,[e],[t],Encoder())
    def test_encoded_linebreak_rejected(self):
        raw,e,t=self.fixture()
        class BadEncoder:
            def encode_characters(self,s):return b'new\n'
        with self.assertRaisesRegex(ValueError,'delimiter'):rewrite_values(raw,[e],[t],BadEncoder())
    def test_duplicate_target_rejected(self):
        raw,e,t=self.fixture()
        with self.assertRaisesRegex(ValueError,'duplicate'):rewrite_values(raw,[e,e],[t,t],Encoder())
    def test_nonascii_value_structure(self):self.assertEqual(config_lines(b'[T]\r\nName=\xd0\xa1\r\n')[0]['value'],b'\xd0\xa1')
    def test_default_dialogue_encoder_still_rejects_opaque_macro(self):
        from localization.text import MappedEncoder
        with self.assertRaisesRegex(ValueError,'unknown control'):MappedEncoder([]).encode('%w')
    def test_character_primitive_preserves_literal_macro(self):
        from localization.text import MappedEncoder
        self.assertEqual(MappedEncoder([]).encode_characters('%w < &Back'),b'%w < &Back')
    def test_character_primitive_rejects_actual_control(self):
        from localization.text import MappedEncoder
        with self.assertRaisesRegex(ValueError,'unsupported'):MappedEncoder([]).encode_characters('\n')

if __name__=='__main__':unittest.main()
