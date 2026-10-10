import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_config_semantics import role, members, reference_index, classify

class ConfigSemanticsTests(unittest.TestCase):
    def test_numeric(self):
        self.assertEqual(role('FILE/game.ini','Game','Rate','1.000')[0],'internal-configuration')
    def test_alias(self):
        self.assertEqual(role('FILE/game.ini','Engine.Input','Help','Talk | Fire')[1],'input-command-or-alias')
    def test_empty(self):
        self.assertEqual(role('FILE/Engine.int','Menu','HelpMessage','')[1],'empty-value-no-text')
    def test_default_identity_unknown(self):
        self.assertEqual(role('FILE/game.ini','URL','Name','Player')[0],'unresolved')
    def test_unknown_key(self):
        self.assertEqual(role('FILE/unknown.int','Arbitrary','Value','Hello')[0],'unresolved')
    def test_class_selection(self):
        self.assertEqual(role('FILE/game.ini','Engine.Engine','Canvas','Engine.Canvas')[0],'internal-configuration')
    def test_url_template(self):
        self.assertEqual(role('FILE/Engine.int','Progress','ConnectingURL','unreal://%s/%s')[0],'internal-configuration')
    def test_error(self):
        self.assertEqual(role('FILE/Core.int','Errors','Exec','Bad command')[0],'diagnostic-text')
    def test_query(self):
        self.assertEqual(role('FILE/Core.int','Query','Name','Name:')[0],'visible-text-candidate')
    def test_command_token(self):
        self.assertEqual(role('FILE/Editor.int','MakeCommandlet','HelpParm[0]','Silent')[0],'internal-configuration')
    def test_usage_protected(self):
        self.assertEqual(role('FILE/Editor.int','MakeCommandlet','HelpUsage','make [-x]')[1],'commandlet-help-with-protected-syntax')
    def test_descriptor(self):
        v='(Caption="Sound, Advanced",Parent="Options",Class=Audio.Driver)'
        fs=members(v)
        self.assertEqual([f['category'] for f in fs],['visible-text-candidate','internal-configuration','internal-configuration'])
        for f in fs:self.assertEqual(v[f['start']:f['end']],f['raw'])
    def test_bad_descriptor(self):
        for v in ['Caption="X"','(Caption="X)','(Class=)','(Class=X,Class=Y)']:
            with self.assertRaises(ValueError):members(v)
    def test_parent_protected(self):
        self.assertEqual(members('(Parent="Audio")')[0]['reason'],'hierarchy-or-object-lookup-protected')
    def test_caption_not_whole_descriptor_edit(self):
        self.assertEqual(role('FILE/Core.int','Public','Preferences','(Caption="Options",Parent="Root")')[1],'mixed-preference-descriptor')
    def test_registration(self):
        self.assertEqual(role('FILE/Core.int','Public','Object','(Name=Core.Test,Class=Class)')[0],'internal-configuration')
    def test_declaration_dedup(self):
        src=[dict(id='s',owner='Engine',serial_sha256='h',text='var config class<Language> Language;')]
        d,c=reference_index(src)
        self.assertEqual(len(d['Engine','Language']),1)
    def test_call(self):
        src=[dict(id='s',owner='Console',serial_sha256='h',text='Message(Localize("Errors", "Exec", "Core"));')]
        d,c=reference_index(src)
        self.assertEqual((c[0]['section'],c[0]['key'],c[0]['package']),('Errors','Exec','Core'))
    def test_no_authorization(self):
        e=dict(id='FILE/Core.int/line/1',references={'und':'%s'},section='Query',section_occurrence=2,key='Name',line=1,offset=10,source_sha256='h',source_bytes=2)
        c=classify(e,'FILE/Core.int',{},[])
        self.assertFalse(c['editable']);self.assertFalse(c['backend_eligible']);self.assertFalse(c['runtime_visibility_verified'])
        self.assertEqual(c['source_sha256'],'h');self.assertEqual(c['value'],'%s')
    def test_server_name_not_numeric(self):
        self.assertEqual(role('FILE/game.ini','Engine.GameReplicationInfo','ServerName','123')[0],'visible-text-candidate')

if __name__=='__main__':unittest.main()
