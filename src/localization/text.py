"""Strict mapped-byte encoding and anchored text edits, independent of locale."""
from __future__ import annotations
import hashlib
import re
import struct

from translate.fpb import parse_fpb_raw, build_fpb, synthesize_implicit_seq0

TOKEN = re.compile(r'\$(?:n|D\d{2}(?!\d))|%(?:%|(?:\d+\$)?[-+0 #]*\d*(?:\.\d+)?[sdifuxXoc])|\{\d+\}|</?[A-Za-z][A-Za-z0-9 _="\x27./:-]*>')


def protected_tokens(text: str) -> list[str]:
    tokens, pos = [], 0
    while pos < len(text):
        if text[pos] in "$%<>{}":
            match = TOKEN.match(text, pos)
            if match is None:
                raise ValueError(f"unknown control structure at character {pos}")
            tokens.append(match.group())
            pos = match.end()
        else:
            pos += 1
    return tokens


def validate_target(source: str, target: str) -> None:
    if not target or "\x00" in target or any(ord(c) < 32 for c in target):
        raise ValueError("empty target or unexpected control byte")
    if protected_tokens(source) != protected_tokens(target):
        raise ValueError("protected token values/count/order changed")


class MappedEncoder:
    def __init__(self, entries: list[dict], *, font_tables: dict | None = None):
        # Explicit serialized Font tables are required outside the legacy PoC.
        if font_tables is not None:
            ranges, bases, count = font_tables['ranges'], font_tables['bases'], font_tables['glyphs']
            if (len(ranges) < 2 or len(ranges) != len(bases)
                    or not all(isinstance(v, int) and 0 <= v <= 65535 for v in ranges + bases)
                    or not isinstance(count, int) or not 0 < count <= 65535
                    or ranges != sorted(set(ranges)) or bases != sorted(bases) or bases[-1] != count
                    or any(ranges[row] + bases[row + 1] - bases[row] > ranges[row + 1]
                           for row in range(len(ranges) - 1))):
                raise ValueError("invalid explicit font mapping tables")
        self.entries = entries
        self.table = {}
        used_bytes, used_glyphs = set(), set()
        for entry in entries:
            char, code, glyph = entry["character"], bytes.fromhex(entry["bytes"]), entry["glyph"]
            if len(char) != 1 or ord(char) < 128 or len(code) != 2:
                raise ValueError("map requires one non-ASCII character and one byte pair")
            if char in self.table or code in used_bytes or glyph in used_glyphs:
                raise ValueError("duplicate character/code/glyph in mapping")
            if font_tables is None:
                if not (0xB0 <= code[0] <= 0xC8 and 0xA1 <= code[1] <= 0xFE):
                    raise ValueError("byte pair outside observed KR Hangul ranges")
                expected = 317 + (code[0] - 0xB0) * 94 + code[1] - 0xA1
                limit = 2667
            else:
                if code[0] < 128 or code[1] == 0:
                    raise ValueError("invalid multibyte code")
                numeric = int.from_bytes(code, 'big')
                matches = [bases[row] + numeric - ranges[row] for row in range(len(ranges) - 1)
                           if ranges[row] <= numeric < ranges[row] + bases[row + 1] - bases[row]]
                if len(matches) != 1:
                    raise ValueError("byte pair outside explicit Font ranges")
                expected, limit = matches[0], count
            if not isinstance(glyph, int) or glyph != expected or glyph >= limit:
                raise ValueError("byte pair and glyph index disagree")
            self.table[char] = code
            used_bytes.add(code)
            used_glyphs.add(glyph)

    def encode(self, text: str) -> bytes:
        protected_tokens(text)
        result = bytearray()
        for char in text:
            if 32 <= ord(char) < 127:
                result.append(ord(char))
            elif char in self.table:
                result.extend(self.table[char])
            else:
                raise ValueError(f"unmapped or unsupported character U+{ord(char):04X}")
        return bytes(result)

    def validate_coverage(self, targets: list[str]) -> None:
        required = {c for text in targets for c in text if ord(c) > 127}
        if required != set(self.table):
            raise ValueError("map coverage must equal this PoC target character set")


def rewrite_fpb(blob: bytes, targets: dict[int, str], encoder: MappedEncoder) -> tuple[bytes, list[dict]]:
    header, windows, pool = parse_fpb_raw(blob)
    if build_fpb(header, windows, pool) != blob:
        raise ValueError("FPB baseline round trip mismatch")
    views = synthesize_implicit_seq0(windows, len(pool))
    # This backend explicitly requires a partition. Overlapping views need another policy.
    cursor, seen = 0, set()
    for seq, offset, length in views:
        if offset != cursor or length < 0 or seq in seen:
            raise ValueError("FPB overlapping/non-partitioned/duplicate views unsupported")
        cursor += length
        seen.add(seq)
    if cursor != len(pool) or not set(targets).issubset(seen):
        raise ValueError("FPB views do not cover pool or target sequence missing")
    new_pool, relocated, report = bytearray(), {}, []
    for seq, offset, length in views:
        original = pool[offset:offset + length]
        data = original
        if seq in targets:
            validate_target(original.decode("cp949", errors="strict"), targets[seq])
            data = encoder.encode(targets[seq])
            report.append({"seq": seq, "old_offset": offset, "new_offset": len(new_pool),
                           "old_length": length, "new_length": len(data), "encoded_hex": data.hex()})
        relocated[seq] = (len(new_pool), len(data))
        new_pool.extend(data)
    new_windows = [(seq, *relocated[seq]) for seq, _, _ in windows]
    result = build_fpb(header, new_windows, bytes(new_pool))
    h, actual_windows, actual_pool = parse_fpb_raw(result)
    if actual_windows != new_windows or actual_pool != new_pool:
        raise ValueError("FPB rebuild changed intended views")
    for seq, offset, length in synthesize_implicit_seq0(actual_windows, len(actual_pool)):
        if seq not in targets:
            old_offset, old_length = next((o, n) for s, o, n in views if s == seq)
            if actual_pool[offset:offset + length] != pool[old_offset:old_offset + old_length]:
                raise ValueError("untargeted FPB dialogue changed")
    return result, report


def rewrite_fixed_slot(blob: bytes, profile: dict, target: str, encoder: MappedEncoder) -> tuple[bytes, dict]:
    count, kind = struct.unpack_from("<II", blob)
    if (count != profile["record_count"] or kind != profile["kind"]
            or len(blob) != profile["header_size"] + count * profile["record_size"]):
        raise ValueError("fixed record geometry mismatch")
    index = profile["record_index"]
    if not 0 <= index < count:
        raise ValueError("record index outside file")
    record = profile["header_size"] + index * profile["record_size"]
    if struct.unpack_from("<I", blob, record)[0] != profile["record_id"]:
        raise ValueError("fixed record identity mismatch")
    start = record + profile["text_offset"]
    end = start + profile["text_bytes"]
    if end > record + profile["record_size"]:
        raise ValueError("text field overruns record")
    slot = blob[start:end]
    if hashlib.sha256(slot).hexdigest() != profile["expected_slot_sha256"]:
        raise ValueError("fixed source slot mismatch")
    nul = slot.find(b"\0")
    if nul < 0 or any(slot[nul:]):
        raise ValueError("fixed slot has no clean null padding")
    validate_target(slot[:nul].decode("cp949", errors="strict"), target)
    encoded = encoder.encode(target)
    if len(encoded) >= len(slot):
        raise ValueError("fixed slot overflow including required NUL")
    result = blob[:start] + encoded.ljust(len(slot), b"\0") + blob[end:]
    return result, {"record_id": profile["record_id"], "offset": start,
                    "capacity": len(slot), "encoded_bytes": len(encoded), "encoded_hex": encoded.hex()}
