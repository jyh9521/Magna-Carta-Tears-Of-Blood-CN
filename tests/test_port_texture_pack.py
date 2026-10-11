import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from port_texture_pack import canonical_name, plan, materialize, texture_root_config


class TexturePackTests(unittest.TestCase):
    def test_old_region(self):
        self.assertEqual(canonical_name('abc-def-r100000001000000-00006a93.dds'), 'abc-def-r256x256-00002a93')

    def test_new_region(self):
        self.assertEqual(canonical_name('ABC-DEF-r256x256-00002a93.png'), 'abc-def-r256x256-00002a93')

    def test_direct(self):
        self.assertEqual(canonical_name('abc-80406a82.dds'), 'abc-80402a82')

    def test_palette_preserved(self):
        self.assertNotEqual(canonical_name('abc-def-00006a93.dds'), canonical_name('abc-aaa-00006a93.dds'))

    def test_reject_invalid(self):
        for name in ('../bad.dds', 'abc-r0x32-123.dds', 'abc-r1x0-123.dds', 'abc-100000000.dds', 'a-b-c-d.dds'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                canonical_name(name)

    def test_config_minimal(self):
        original = b'[Folders]\r\nTextures = old\r\nLogs = x\r\n[Other]\r\nTextures = unchanged\r\n'
        modified = texture_root_config(original, Path.cwd())
        self.assertEqual(modified.splitlines()[2:], original.splitlines()[2:])
        self.assertIn(b'\r\n', modified)

    def test_config_ambiguous(self):
        with self.assertRaises(ValueError):
            texture_root_config(b'[Folders]\nTextures=a\nTextures=b\n', Path.cwd())

    def fixture(self, root):
        source=root/'source';source.mkdir()
        header=bytearray(128);header[:4]=b'DDS '
        struct.pack_into('<I',header,4,124);struct.pack_into('<II',header,12,4,4)
        (source/'abc-def-r4000000040000-00006a93.dds').write_bytes(header+bytes(16))
        return source

    def test_plan_materialize_and_restore_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=self.fixture(root);manifest=plan(source)
            target=root/'target';self.assertEqual(materialize(manifest,target),1)
            self.assertEqual(next(target.glob('*.dds')).read_bytes(),next(source.glob('*.dds')).read_bytes())
            with self.assertRaises(ValueError):materialize(manifest,target)
            next(target.glob('*.dds')).unlink();target.rmdir()
            self.assertEqual(plan(source),manifest)

    def test_detect_source_change_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=self.fixture(root);manifest=plan(source)
            next(source.glob('*.dds')).write_bytes(b'changed')
            with self.assertRaises(ValueError):materialize(manifest,root/'target')
            self.assertFalse((root/'target').exists())

    def test_bad_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=self.fixture(root)
            next(source.glob('*.dds')).write_bytes(b'bad')
            with self.assertRaises(ValueError):plan(source)

    def test_duplicate_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=self.fixture(Path(tmp))
            (source/'abc-def-r4x4-00002a93.dds').write_bytes(next(source.glob('*.dds')).read_bytes())
            with self.assertRaises(ValueError):plan(source)

    def test_full_key_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=self.fixture(root);dumps=root/'dumps';dumps.mkdir()
            (dumps/'abc-def-r4x4-00002a93.png').write_bytes(b'not decoded by inventory')
            self.assertTrue(plan(source,dumps)['files'][0]['observed_full_key_match'])


if __name__ == '__main__':unittest.main()
