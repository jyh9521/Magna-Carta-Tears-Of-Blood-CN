"""Append-only builder for the observed KR packed Font resource layout.

This operates on serialized resources, not UE2 packages or runtime caches.
"""
from __future__ import annotations
import hashlib
import struct
from research_inventory import font_data


def require(condition: bool, message: str) -> None:
    if not condition: raise ValueError(message)


def encode_compact(value: int) -> bytes:
    """Nonnegative UE compact index, restricted to signed 32-bit lengths."""
    require(isinstance(value, int) and 0 <= value <= 0x7fffffff, 'invalid compact length')
    first = value & 63; value >>= 6
    result = bytearray([first | (64 if value else 0)])
    while value:
        byte = value & 127; value >>= 7
        result.append(byte | (128 if value else 0))
    return bytes(result)


def parts(serial: bytes) -> tuple[dict, bytes, bytes, bytes]:
    try: info = font_data(serial)
    except (IndexError, struct.error) as exc: raise ValueError('truncated Font resource') from exc
    require(info['glyphs'] > 0 and info['height'] > 0 and 0 < info['width'] <= info['row_stride'] * 4,
            'invalid font geometry')
    require(info['glyphs'] <= 65535, 'glyph count exceeds uint16 base capacity')
    ranges, bases = info['ranges'], info['bases']
    require(len(ranges) >= 2 and ranges == sorted(set(ranges)) and bases == sorted(bases)
            and bases[-1] == info['glyphs'], 'invalid font mapping geometry')
    require(all(ranges[row] + bases[row + 1] - bases[row] <= ranges[row + 1]
                for row in range(len(ranges) - 1)), 'overlapping code ranges')
    bitmap = serial[info['bitmap_start']:info['bitmap_start'] + info['bitmap_bytes']]
    metrics = serial[info['metrics_start']:info['metrics_start'] + info['metrics_bytes']]
    require(len(bitmap) == info['bitmap_bytes'] and len(metrics) == info['glyphs'], 'truncated font arrays')
    return info, bitmap, metrics, bytes.fromhex(info['remaining_hex'])


def append_font(serial: bytes, bitmaps: bytes, metrics: bytes, start_code: int, *, expected_sha256: str) -> bytes:
    require(hashlib.sha256(serial).hexdigest() == expected_sha256, 'source Font fingerprint mismatch')
    info, old_bitmap, old_metrics, tail = parts(serial)
    added, stride, height = len(metrics), info['row_stride'], info['height']
    require(added > 0 and len(bitmaps) == added * height * stride, 'new bitmap/metric count mismatch')
    require(all(value <= info['width'] for value in metrics), 'new metric exceeds glyph width')
    require(info['glyphs'] + added <= 65535, 'glyph count exceeds uint16 base capacity')
    require(isinstance(start_code, int) and 0x8000 <= start_code and info['ranges'][-1] < start_code
            and start_code + added <= 65535, 'new code range overlaps or exceeds uint16')
    require(all(code & 255 for code in range(start_code, start_code + added)), 'new code range contains NUL byte')
    ranges = info['ranges'] + [start_code, start_code + added]
    bases = info['bases'] + [info['glyphs'], info['glyphs'] + added]
    header = bytearray(serial[:27]); struct.pack_into('<I', header, 11, info['glyphs'] + added)
    bitmap, widths = old_bitmap + bitmaps, old_metrics + metrics
    result = bytes(header) + encode_compact(len(bitmap)) + bitmap + encode_compact(len(widths)) + widths
    result += encode_compact(len(ranges)) + struct.pack(f'<{len(ranges)}H', *ranges)
    result += encode_compact(len(bases)) + struct.pack(f'<{len(bases)}H', *bases) + tail
    verify_append(serial, result, added, start_code)
    return result


def verify_append(original: bytes, modified: bytes, added: int, start_code: int) -> dict:
    before, bitmap, metrics, tail = parts(original)
    after, new_bitmap, new_metrics, new_tail = parts(modified)
    require(added > 0 and after['glyphs'] == before['glyphs'] + added, 'expanded glyph count mismatch')
    require(modified[:11] == original[:11] and modified[15:27] == original[15:27], 'header geometry changed')
    require(new_bitmap[:len(bitmap)] == bitmap and new_metrics[:len(metrics)] == metrics, 'original glyphs or metrics changed')
    require(new_tail == tail, 'unknown Font tail changed')
    require(after['ranges'] == before['ranges'] + [start_code, start_code + added]
            and after['bases'] == before['bases'] + [before['glyphs'], after['glyphs']], 'expanded mapping changed')
    return dict(original_glyphs=before['glyphs'], expanded_glyphs=after['glyphs'], added_glyphs=added,
                original_bitmap_preserved=True, original_metrics_preserved=True, unknown_tail_preserved=True)


def code_chunks(count: int, start: int) -> list[tuple[int, int]]:
    """Use bounded nonzero trail-byte bands, with a sentinel between bands."""
    require(type(count) is int and count > 0 and type(start) is int, 'invalid expansion count/start')
    chunks = []
    while count:
        require(0x8000 <= start <= 0xFFFE and 1 <= (start & 255) <= 254, 'invalid expansion code band')
        size = min(count, 255 - (start & 255))
        chunks.append((start, size)); count -= size
        start = (((start >> 8) + 1) << 8) | 0xA1
    return chunks


def expanded_entries(characters: list[dict], first: int, start: int) -> list[dict]:
    result = []
    for code, count in code_chunks(len(characters), start):
        for value in range(code, code + count):
            result.append(dict(character=characters[len(result)]['character'], bytes=f'{value:04X}', glyph=first + len(result)))
    return result


def append_slots(serial: bytes, count: int, start: int, *, expected_sha256: str) -> bytes:
    require(hashlib.sha256(serial).hexdigest() == expected_sha256, 'source Font fingerprint mismatch')
    result = serial
    for code, size in code_chunks(count, start):
        info = font_data(result)
        result = append_font(result, bytes(size * info['height'] * info['row_stride']), bytes(size), code,
                             expected_sha256=hashlib.sha256(result).hexdigest())
    return result


def verify_slots(original: bytes, modified: bytes, count: int, start: int) -> dict:
    before, bitmap, metrics, tail = parts(original)
    after, new_bitmap, new_metrics, new_tail = parts(modified)
    ranges, bases, total = list(before['ranges']), list(before['bases']), before['glyphs']
    for code, size in code_chunks(count, start):
        ranges.extend([code, code + size]); bases.extend([total, total + size]); total += size
    require(after['glyphs'] == total and after['ranges'] == ranges and after['bases'] == bases, 'expanded slot mapping mismatch')
    require(modified[:11] == original[:11] and modified[15:27] == original[15:27], 'header geometry changed')
    require(new_bitmap[:len(bitmap)] == bitmap and new_metrics[:len(metrics)] == metrics and new_tail == tail,
            'original Font data changed')
    return dict(original_glyphs=before['glyphs'], expanded_glyphs=total, added_glyphs=count,
                original_bitmap_preserved=True, original_metrics_preserved=True, unknown_tail_preserved=True)
