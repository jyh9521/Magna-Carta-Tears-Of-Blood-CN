"""Fingerprint-gated cached package fragment overlay; not a general LIX parser.

The observed startup stream caches a package header, export table, payloads
and two file-size records. Runtime stream acceptance requires separate QA.
"""
from __future__ import annotations
import hashlib
import struct
from font_resource import require
from package_resource import export_records


def overlay_segments(blob: bytes, segments: list[dict], *, expected_sha256: str) -> tuple[bytes, list[dict]]:
    require(hashlib.sha256(blob).hexdigest() == expected_sha256, 'bundle fingerprint mismatch')
    require(bool(segments), 'no bundle segments')
    segments = sorted(segments, key=lambda item: item['offset'])
    output = bytearray(); end = 0; report = []
    for item in segments:
        start, old, new = item['offset'], item['original'], item['modified']
        require(type(start) is int and end <= start and old and type(new) is bytes and new,
                'invalid/overlapping bundle segment')
        require(start + len(old) <= len(blob) and blob[start:start + len(old)] == old,
                'bundle segment source mismatch')
        output += blob[end:start]; target = len(output); output += new
        report.append(dict(label=item['label'], original_offset=start, modified_offset=target,
                           original_size=len(old), modified_size=len(new),
                           original_sha256=hashlib.sha256(old).hexdigest(), modified_sha256=hashlib.sha256(new).hexdigest()))
        end = start + len(old)
    output += blob[end:]
    # Check every untargeted interval against its relocated output interval.
    before = after = 0
    for item in report:
        length = item['original_offset'] - before
        require(output[after:after + length] == blob[before:before + length], 'untargeted bundle bytes changed')
        before = item['original_offset'] + item['original_size']
        after = item['modified_offset'] + item['modified_size']
    require(output[after:] == blob[before:], 'bundle tail changed')
    return bytes(output), report


def replace_cached_package(bundle: bytes, original: bytes, modified: bytes, indices: set[int], *,
                           expected_bundle_sha256: str, expected_package_sha256: str,
                           cached_path: str, expected_file_records: int = 2) -> tuple[bytes, dict]:
    require(hashlib.sha256(original).hexdigest() == expected_package_sha256, 'package fingerprint mismatch')
    old_entries, old_end = export_records(original, expected_version=(118, 15))
    new_entries, new_end = export_records(modified, expected_version=(118, 15))
    require(len(old_entries) == len(new_entries) and old_end == len(original) and new_end == len(modified),
            'unsupported cached package table layout')
    require(indices and all(type(index) is int and 1 <= index <= len(old_entries) for index in indices), 'invalid cached export targets')
    segments = []

    def unique(label: str, old: bytes, new: bytes) -> None:
        require(old and bundle.count(old) == 1, 'cached fragment not unique: ' + label)
        segments.append(dict(label=label, offset=bundle.index(old), original=old, modified=new))

    unique('package-header', original[:64], modified[:64])
    old_table = struct.unpack_from('<I', original, 24)[0]
    new_table = struct.unpack_from('<I', modified, 24)[0]
    unique('export-table', original[old_table:old_end], modified[new_table:new_end])
    for old, new in zip(old_entries, new_entries, strict=True):
        require(old['prefix'] == new['prefix'], 'cached export identity changed')
        if old['index'] not in indices:
            require(old == new, 'unexpected cached export metadata change'); continue
        require(old['size'] > 0 and new['size'] > old['size'], 'cached target must grow')
        unique('export-' + str(old['index']), original[old['offset']:old['offset'] + old['size']],
               modified[new['offset']:new['offset'] + new['size']])
    path = cached_path.encode('ascii')
    require(path and b'\0' not in path and len(path) < 128, 'invalid cached filename')
    record = path.ljust(128, b'\0') + struct.pack('<I', len(original))
    require(expected_file_records > 0 and bundle.count(record) == expected_file_records, 'cached file record count mismatch')
    start = 0
    for row in range(expected_file_records):
        offset = bundle.index(record, start) + 128; start = offset + 4
        segments.append(dict(label='file-size-' + str(row), offset=offset,
                             original=record[-4:], modified=struct.pack('<I', len(modified))))
    result, changes = overlay_segments(bundle, segments, expected_sha256=expected_bundle_sha256)
    return result, dict(original_size=len(bundle), modified_size=len(result), segments=changes,
                        file_records=expected_file_records, export_targets=sorted(indices),
                        untargeted_bytes_preserved=True, runtime='unverified cached-stream overlay')
