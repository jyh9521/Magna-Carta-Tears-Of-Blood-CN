import importlib.util
from pathlib import Path
import struct
import unittest

spec = importlib.util.spec_from_file_location('frame_patch', Path(__file__).resolve().parents[1]/'tools/port_frame_limit_patch.py')
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)


class FramePatchTests(unittest.TestCase):
    def test_pnach_address(self):
        self.assertIn('patch=1,EE,201C69E4,extended,28410001', patch.pnach())

    def test_wrong_size(self):
        with self.assertRaisesRegex(ValueError, 'size'):
            patch.validate(b'')

    def test_wrong_elf(self):
        with self.assertRaisesRegex(ValueError, 'ELF32'):
            patch.validate(bytes(patch.SIZE))

    def test_missing_mapping(self):
        blob = bytearray(52)
        blob[:7] = b'\x7fELF\x01\x01\x01'
        struct.pack_into('<HH', blob, 42, 32, 0)
        with self.assertRaisesRegex(ValueError, 'file-backed'):
            patch.offset(blob, patch.VA)


if __name__ == '__main__':
    unittest.main()
