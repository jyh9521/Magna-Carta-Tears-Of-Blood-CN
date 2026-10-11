"""Rehome a user-supplied PCSX2 pack without inventing regional texture hashes.

Filename semantics follow PCSX2 v2.8.2 GSTextureReplacements/SourceRegion.
The manifest records byte identity; it does not claim full-game coverage.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def canonical_name(filename):
    stem = Path(filename).stem
    parts = stem.split('-')
    region = None
    if len(parts) > 2 and parts[-2].startswith('r'):
        region = parts.pop(-2)[1:]
    if len(parts) not in (2, 3):
        raise ValueError(f'Unsupported texture name: {filename}')
    if not all(re.fullmatch(r'[0-9a-fA-F]+', p) for p in parts):
        raise ValueError(f'Invalid texture hash: {filename}')
    hashes = [int(p, 16) for p in parts[:-1]]
    bits = int(parts[-1], 16)
    if any(h >= 2**64 for h in hashes) or bits >= 2**32:
        raise ValueError('Hash/format overflow')
    bits &= ~0x4000  # Old TCC, ignored by PCSX2 RemoveUnusedBits.
    result = [f'{h:x}' for h in hashes]
    if region is not None:
        if re.fullmatch(r'[0-9]+x[0-9]+', region):
            width, height = map(int, region.split('x'))
        elif re.fullmatch(r'[0-9a-fA-F]{1,16}', region):
            value = int(region, 16)
            coords = [(value >> (16*i)) & 65535 for i in range(4)]
            coords = [c if c < 32768 else c - 65536 for c in coords]
            width, height = coords[1]-coords[0], coords[3]-coords[2]
        else:
            raise ValueError('Invalid region')
        if not (0 < width <= 65535 and 0 < height <= 65535):
            raise ValueError('Invalid region dimensions')
        result.append(f'r{width}x{height}')
    return '-'.join(result + [f'{bits:08x}'])


def plan(source, dumps=None):
    source = Path(source).resolve()
    records, seen = [], set()
    observed = {canonical_name(p.name) for p in Path(dumps).glob('*.png')} if dumps else set()
    for path in sorted(source.glob('*.dds')):
        if path.is_symlink():
            raise ValueError('Symlink input is not supported')
        name = canonical_name(path.name)
        if name in seen:
            raise ValueError(f'Duplicate canonical texture key: {name}')
        seen.add(name)
        with path.open('rb') as stream:
            header = stream.read(128)
        if len(header) != 128 or header[:4] != b'DDS ' or struct.unpack_from('<I', header, 4)[0] != 124:
            raise ValueError(f'Invalid DDS header: {path}')
        height, width = struct.unpack_from('<II', header, 12)
        if not width or not height:
            raise ValueError('Empty DDS image')
        records.append(dict(source_name=path.name, target_name=name+'.dds',
                            sha256=digest(path), size=path.stat().st_size,
                            width=width, height=height,
                            observed_full_key_match=name in observed))
    if not records:
        raise ValueError('No DDS textures found')
    return dict(schema=1, source=str(source), files=records,
                observed_dump_count=len(observed), hash_aliases=0,
                iso_changes=False, full_game_verified=False)


def materialize(manifest, target, hardlink=False):
    target = Path(target).resolve()
    if target.exists():
        raise ValueError('Destination already exists; no overwrite or merge')
    # Check every source before creating any output.
    source = Path(manifest['source'])
    for row in manifest['files']:
        path = source / row['source_name']
        if path.parent.resolve() != source.resolve() or digest(path) != row['sha256']:
            raise ValueError('Source changed or invalid source path')
        if Path(row['target_name']).name != row['target_name']:
            raise ValueError('Invalid output path')
    target.mkdir(parents=True)
    for row in manifest['files']:
        src, dst = source/row['source_name'], target/row['target_name']
        if hardlink:
            os.link(src, dst)  # Explicit option, no silent fallback.
        else:
            shutil.copy2(src, dst)
        if digest(dst) != row['sha256']:
            raise ValueError('Output identity mismatch')
    return len(manifest['files'])


def texture_root_config(data, root):
    """Change only the unique Textures key within [Folders], preserving all bytes."""
    text = data.decode('utf-8-sig')
    lines = text.splitlines(keepends=True)
    section, hits = '', []
    for i, line in enumerate(lines):
        match = re.fullmatch(r'\[([^\]]+)\]\s*', line.strip())
        if match:
            section = match[1]
        elif section == 'Folders' and re.match(r'^Textures\s*=', line):
            hits.append(i)
    if len(hits) != 1:
        raise ValueError('Expected exactly one [Folders] Textures setting')
    i = hits[0]
    ending = '\r\n' if lines[i].endswith('\r\n') else '\n'
    value = str(Path(root).resolve())
    if '\n' in value or '\r' in value:
        raise ValueError('Invalid root path')
    lines[i] = f'Textures = {value}{ending}'
    prefix = b'\xef\xbb\xbf' if data.startswith(b'\xef\xbb\xbf') else b''
    return prefix + ''.join(lines).encode('utf8')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, required=True, help='US replacements directory')
    ap.add_argument('--dumps', type=Path)
    ap.add_argument('--manifest', type=Path, required=True)
    ap.add_argument('--target', type=Path, help='New target serial/replacements directory')
    ap.add_argument('--hardlink', action='store_true', help='Same-volume links; never edit linked DDS in place')
    args = ap.parse_args()
    manifest = plan(args.source, args.dumps)
    if args.target:
        materialize(manifest, args.target, args.hardlink)
        manifest.update(target=str(args.target.resolve()), storage='hardlink' if args.hardlink else 'copy')
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf8')
    print(f"PACK files={len(manifest['files'])} observed_matches={sum(r['observed_full_key_match'] for r in manifest['files'])} aliases=0")


if __name__ == '__main__':
    main()
