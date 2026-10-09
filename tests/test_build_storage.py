import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from build_storage import inventory


class BuildStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'candidate.iso').write_bytes(b'candidate')
        (self.root / 'old.iso').write_bytes(b'old')
        self.manifest = dict(schema=1, protected=[dict(path='candidate.iso', size=9,
            sha256=hashlib.sha256(b'candidate').hexdigest(), role='pending')])

    def test_read_only_unreviewed(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        report = inventory(self.root, self.manifest)
        self.assertEqual(report['total_bytes'], 12)
        self.assertEqual(report['iso_count'], 2)
        self.assertFalse(report['deletion_authorized'])
        self.assertEqual(report['files'][1]['retention'], 'unreviewed')
        self.assertFalse(report['files'][0]['hash_verified'])
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})

    def test_hash_verified(self):
        self.assertTrue(inventory(self.root, self.manifest, verify_hash=True)['files'][0]['hash_verified'])

    def test_missing(self):
        self.manifest['protected'][0]['path'] = 'absent.iso'
        with self.assertRaisesRegex(ValueError, 'missing'): inventory(self.root, self.manifest)

    def test_wrong_size(self):
        self.manifest['protected'][0]['size'] = 8
        with self.assertRaisesRegex(ValueError, 'size mismatch'): inventory(self.root, self.manifest)

    def test_same_size_wrong_hash(self):
        (self.root / 'candidate.iso').write_bytes(b'changed!!')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'): inventory(self.root, self.manifest, verify_hash=True)

    def test_traversal(self):
        for path in ['../candidate.iso', '/candidate.iso', 'C:/candidate.iso', 'a\\candidate.iso', './candidate.iso', '']:
            with self.subTest(path=path):
                self.manifest['protected'][0]['path'] = path
                with self.assertRaisesRegex(ValueError, 'relative'): inventory(self.root, self.manifest)

    def test_duplicate_casefold(self):
        entry = copy.deepcopy(self.manifest['protected'][0]); entry['path'] = 'CANDIDATE.iso'
        self.manifest['protected'].append(entry)
        with self.assertRaisesRegex(ValueError, 'duplicate'): inventory(self.root, self.manifest)

    def test_invalid_hash(self):
        self.manifest['protected'][0]['sha256'] = 'g' * 64
        with self.assertRaisesRegex(ValueError, 'hash'): inventory(self.root, self.manifest)

    def test_bool_size(self):
        self.manifest['protected'][0]['size'] = True
        with self.assertRaisesRegex(ValueError, 'size'): inventory(self.root, self.manifest)

    def test_invalid_schema(self):
        self.manifest['schema'] = 2
        with self.assertRaisesRegex(ValueError, 'manifest'): inventory(self.root, self.manifest)
