"""Read-only build inventory; no deletion or automatic disposal classification."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat


def linked(path: Path) -> bool:
    info = path.lstat()
    return path.is_symlink() or bool(getattr(info, 'st_file_attributes', 0) & 0x400)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def inventory(root: Path, manifest: dict, *, verify_hash: bool = False) -> dict:
    if linked(root):
        raise ValueError('linked inventory root')
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError('inventory root must be a directory')
    if manifest.get('schema') != 1 or not isinstance(manifest.get('protected'), list):
        raise ValueError('invalid retention manifest')
    protected = {}
    for entry in manifest['protected']:
        name = entry['path']
        path = PurePosixPath(name)
        if not name or '\\' in name or ':' in name or path.is_absolute() or '..' in path.parts or path.as_posix() != name:
            raise ValueError('invalid relative protected path')
        if name.casefold() in protected:
            raise ValueError('duplicate protected path')
        if type(entry['size']) is not int or entry['size'] < 0:
            raise ValueError('invalid protected size')
        expected = entry['sha256']
        if not isinstance(expected, str) or len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected):
            raise ValueError('invalid protected hash')
        protected[name.casefold()] = entry
    files = []
    found = set()
    for directory, dirs, names in os.walk(root, followlinks=False):
        for name in dirs + names:
            if linked(Path(directory) / name):
                raise ValueError('linked build entry')
        for name in names:
            path = Path(directory) / name
            if not stat.S_ISREG(path.stat().st_mode):
                raise ValueError('non-regular build entry')
            relative = path.relative_to(root).as_posix()
            key = relative.casefold()
            size = path.stat().st_size
            entry = protected.get(key)
            row = dict(path=relative, size=size, retention='unreviewed')
            if entry:
                found.add(key)
                if size != entry['size']:
                    raise ValueError('protected size mismatch: ' + relative)
                row.update(retention='protected', role=entry['role'], expected_sha256=entry['sha256'], hash_verified=False)
                if verify_hash:
                    actual = sha256(path)
                    if actual != entry['sha256']:
                        raise ValueError('protected hash mismatch: ' + relative)
                    row.update(sha256=actual, hash_verified=True)
            files.append(row)
    missing = sorted(set(protected) - found)
    if missing:
        raise ValueError('missing protected file: ' + ', '.join(missing))
    files.sort(key=lambda row: (-row['size'], row['path']))
    return dict(schema=1, root=str(root), mode='read-only', deletion_authorized=False,
                files=files, total_bytes=sum(row['size'] for row in files),
                iso_count=sum(Path(row['path']).suffix.lower() == '.iso' for row in files),
                protected_count=len(found))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--verify-hash', action='store_true')
    args = parser.parse_args()
    print(json.dumps(inventory(args.root, json.loads(args.manifest.read_text(encoding='utf8')),
                               verify_hash=args.verify_hash), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
