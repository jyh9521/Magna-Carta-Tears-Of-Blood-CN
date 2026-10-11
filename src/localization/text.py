"""Strict mapped-byte encoding and anchored text edits, independent of locale."""
from __future__ import annotations
import hashlib
import re
import struct

from translate.fpb import parse_fpb_raw, build_fpb, synthesize_implicit_seq0

TOKEN = re.compile(r'\$(?:n|D\d{2}(?!\d))|%(?:%|(?:\d+\$)?[-+0 #]*\d*(?:\.\d+)?[sdifuxXoc])|\{\d+\}|</?[A-Za-z][A-Za-z0-9 _="\x27./:-]*>')


LITERAL_POLICY = 'numeric-percent-nonascii-angle-arrow-v1'
TERMINAL_LF_POLICY = 'terminal-line-feed-v1'
SINGLE_TAB_POLICY = 'single-tab-byte-v1'
TERMINAL_NUL_POLICY = 'terminal-null-padding-v1'


def terminal_nul_body(text: str) -> str:
    body=text.rstrip('\x00')
    if not body or any(ord(c)<32 for c in body):
        raise ValueError('terminal NUL policy requires nonempty text and terminal-only NUL padding')
    return body


def single_tab_parts(text: str) -> list[str]:
    if text.count('\t') != 1 or not text.replace('\t', '') or any(ord(c) < 32 and c != '\t' for c in text):
        raise ValueError('single TAB policy requires one TAB and no other control bytes')
    return text.split('\t')


def terminal_lf_body(text: str) -> str:
    """An explicit storage policy preserves one original terminal byte 0A."""
    if not text.endswith('\n') or not text[:-1] or any(ord(c) < 32 for c in text[:-1]):
        raise ValueError('terminal LF policy requires one final LF and no other control bytes')
    return text[:-1]


def literal_structures(text: str) -> tuple[list[str], list[str]]:
    if any(ord(c) < 32 for c in text):
        raise ValueError('literal policy excludes control bytes')
    tokens, names, at = [], [], 0
    while at < len(text):
        if text.startswith('->', at):
            tokens.append('->'); at += 2; continue
        if text[at] not in '$%<>{}':
            at += 1; continue
        match = TOKEN.match(text, at)
        if match:
            tokens.append(match.group()); at = match.end(); continue
        if text[at] == '%':
            number = re.search(r'\d+(?:\.\d+)?$', text[:at])
            if number is None:
                raise ValueError('unbound literal percent')
            tokens.append(number.group() + '%'); at += 1; continue
        if text[at] == '<':
            end = text.find('>', at + 1)
            inside = text[at + 1:end] if end >= 0 else ''
            if (end < 0 or any(c in '$%<>{}' for c in inside)
                    or not any(ord(c) > 127 and c.isalpha() for c in inside)):
                raise ValueError('unreviewed literal angle content')
            tokens.extend(['<', '>']); names.append(inside); at = end + 1; continue
        raise ValueError('unknown literal control structure')
    return tokens, names


def protected_tokens(text: str, *, control_policy: str | None = None) -> list[str]:
    if control_policy == TERMINAL_NUL_POLICY:
        return protected_tokens(terminal_nul_body(text))
    if control_policy == SINGLE_TAB_POLICY:
        before,after=single_tab_parts(text)
        return protected_tokens(before) + ['\t'] + protected_tokens(after)
    if control_policy == TERMINAL_LF_POLICY:
        return protected_tokens(terminal_lf_body(text)) + ['\n']
    if control_policy is not None:
        if control_policy != LITERAL_POLICY:
            raise ValueError('unknown explicit control policy')
        return literal_structures(text)[0]
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


def validate_target(source: str, target: str, *, control_policy: str | None = None) -> None:
    body = terminal_lf_body(target) if control_policy == TERMINAL_LF_POLICY else target
    if control_policy == SINGLE_TAB_POLICY:
        body = ''.join(single_tab_parts(target))
    if not body or "\x00" in body or any(ord(c) < 32 for c in body):
        raise ValueError("empty target or unexpected control byte")
    if protected_tokens(source, control_policy=control_policy) != protected_tokens(target, control_policy=control_policy):
        raise ValueError("protected token values/count/order changed")
    if control_policy is not None and re.findall(r'\d+(?:\.\d+)?', source) != re.findall(r'\d+(?:\.\d+)?', target):
        raise ValueError('literal numeric values/count/order changed')
    if control_policy == SINGLE_TAB_POLICY:
        for before,after in zip(single_tab_parts(source),single_tab_parts(target)):
            if re.findall(r'\d+(?:\.\d+)?',before) != re.findall(r'\d+(?:\.\d+)?',after):
                raise ValueError('numeric value moved across TAB boundary')


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

    def encode(self, text: str, *, control_policy: str | None = None) -> bytes:
        protected_tokens(text, control_policy=control_policy)
        if control_policy == TERMINAL_LF_POLICY:
            return self.encode_characters(terminal_lf_body(text)) + b'\n'
        if control_policy == SINGLE_TAB_POLICY:
            before,after=single_tab_parts(text)
            return self.encode_characters(before) + b'\t' + self.encode_characters(after)
        return self.encode_characters(text)

    def encode_characters(self, text: str) -> bytes:
        """Encode characters after a caller's format-specific validation.

        No markup grammar is inferred here. The default encode() API retains
        its existing dialogue control validation; config templates use their
        own source-bound validator before calling this primitive.
        """
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


def rewrite_fpb(blob: bytes, targets: dict[int, str], encoder: MappedEncoder, *, source_encodings: dict[int, str] | None = None, source_control_policies: dict[int, str] | None = None) -> tuple[bytes, list[dict]]:
    codecs = {} if source_encodings is None else dict(source_encodings)
    policies = {} if source_control_policies is None else dict(source_control_policies)
    if not set(policies).issubset(targets) or any(v not in (LITERAL_POLICY, TERMINAL_NUL_POLICY) for v in policies.values()):
        raise ValueError('invalid explicit FPB control policy selection')
    if not set(codecs).issubset(targets) or any(v not in ('cp949', 'cp932', 'utf-8') for v in codecs.values()):
        raise ValueError('invalid explicit FPB source encoding selection')
    header, windows, pool = parse_fpb_raw(blob)
    if build_fpb(header, windows, pool) != blob:
        raise ValueError("FPB baseline round trip mismatch")
    views = synthesize_implicit_seq0(windows, len(pool))
    # Disjoint ordered views may leave opaque pool gaps. Preserve those bytes;
    # never invent a sequence identity or translate them as part of a neighbor.
    # Overlapping or duplicate views still need a separate explicit policy.
    cursor, seen = 0, set()
    for seq, offset, length in views:
        if offset < cursor or length < 0 or offset + length > len(pool) or seq in seen:
            raise ValueError("FPB overlapping/unsorted/out-of-bounds/duplicate views unsupported")
        cursor = offset + length
        seen.add(seq)
    if not set(targets).issubset(seen):
        raise ValueError("FPB target sequence missing")
    new_pool, relocated, report = bytearray(), {}, []
    cursor = 0
    for seq, offset, length in views:
        new_pool.extend(pool[cursor:offset])
        original = pool[offset:offset + length]
        data = original
        if seq in targets:
            codec = codecs.get(seq, 'cp949')
            source = original.decode(codec, errors='strict')
            if codec != 'cp949' and source.encode(codec) != original:
                raise ValueError('FPB alternate codec roundtrip mismatch')
            policy = policies.get(seq)
            validate_target(source, targets[seq], control_policy=policy)
            data = encoder.encode(targets[seq], control_policy=policy) if policy else encoder.encode(targets[seq])
            if policy == TERMINAL_NUL_POLICY:
                padding=len(source)-len(terminal_nul_body(source))
                if padding == 0:
                    raise ValueError('FPB terminal NUL policy requires original padding')
                data += bytes(padding)
            report.append({"seq": seq, "old_offset": offset, "new_offset": len(new_pool),
                           "old_length": length, "new_length": len(data), "encoded_hex": data.hex()})
        relocated[seq] = (len(new_pool), len(data))
        new_pool.extend(data)
        cursor = offset + length
    new_pool.extend(pool[cursor:])
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


def rewrite_fpb_header(blob: bytes, expected_key: int, expected_source_sha256: str,
                       target: str, encoder: MappedEncoder, *, source_encoding: str = 'cp949') -> tuple[bytes, dict]:
    """Rewrite only the actual header record, preserving explicit record identity.

    Works on a previously rebuilt copy if its header source bytes still match.
    No legacy catalog sequence alias is interpreted as a native record key.
    """
    header, windows, pool = parse_fpb_raw(blob)
    key, offset, length = struct.unpack_from('<III', header, 4)
    if key != expected_key or offset != 0 or length > len(pool):
        raise ValueError('FPB header identity/geometry mismatch')
    if any(o < length or o+n > len(pool) for _, o, n in windows):
        raise ValueError('FPB explicit window overlaps header or overruns pool')
    source = pool[:length]
    if hashlib.sha256(source).hexdigest() != expected_source_sha256:
        raise ValueError('FPB header source hash mismatch')
    text = source.decode(source_encoding, errors='strict')
    if text.encode(source_encoding, errors='strict') != source:
        raise ValueError('FPB header source encoding round trip mismatch')
    validate_target(text, target)
    encoded = encoder.encode(target)
    delta = len(encoded)-length
    moved = [(s, o+delta, n) for s, o, n in windows]
    new_pool = encoded+pool[length:]
    new_header = header[:12]+struct.pack('<I',len(encoded))
    # Build directly: legacy build_fpb derives header length from the first
    # explicit offset, which is not an authorization to consume any pool gap.
    result = new_header+b''.join(struct.pack('<III',*w) for w in moved)+struct.pack('<I',len(new_pool))+new_pool
    h, actual, actual_pool = parse_fpb_raw(result)
    if h != new_header or actual != moved or actual_pool != new_pool:
        raise ValueError('FPB header rebuild readback mismatch')
    for (_, old, n), (_, new, _) in zip(windows, moved):
        if pool[old:old+n] != actual_pool[new:new+n]:
            raise ValueError('FPB header rewrite changed explicit window bytes')
    return result, dict(native_key=key,old_length=length,new_length=len(encoded),
                        offset_delta=delta,encoded_hex=encoded.hex(),explicit_windows_preserved=len(windows))


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
