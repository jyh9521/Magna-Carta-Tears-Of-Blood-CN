"""Version-locked, read-only ELF mapping and bounded MIPS address candidates."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import font_poc as core

ELF_SHA256 = "35cc6048f0e1f68d06bf3e515b99de3263e5092be62d6215cff5e74aa0ea15f0"


class ElfImage:
    def __init__(self, blob: bytes):
        core.require(len(blob) >= 52 and blob[:7] == b"\x7fELF\x01\x01\x01", "ELF32 little-endian version1 required")
        self.blob = blob
        h = struct.unpack_from("<HHIIIIIHHHHHH", blob, 16)
        kind, machine, version, self.entry, phoff, shoff, flags, ehsize, phsize, phnum, shsize, shnum, names_idx = h
        core.require((kind, machine, version, ehsize) == (2, 8, 1, 52), "unsupported ELF header")
        core.require(phsize == 32 and phoff + phnum * 32 <= len(blob), "program table bounds")
        core.require(shnum == 0 or (shsize == 40 and shoff + shnum * 40 <= len(blob)), "section table bounds")
        self.flags, self.segments, self.sections = flags, [], []
        for i in range(phnum):
            values = struct.unpack_from("<8I", blob, phoff + i * 32)
            typ, offset, va, pa, size, memory, permissions, align = values
            core.require(offset + size <= len(blob) and size <= memory, "segment bounds")
            self.segments.append(dict(type=typ, offset=offset, va=va, filesz=size, memsz=memory, flags=permissions))
        for i in range(shnum):
            s = struct.unpack_from("<10I", blob, shoff + i * 40)
            core.require(s[1] == 8 or s[4] + s[5] <= len(blob), "section bounds")
            self.sections.append(dict(name_offset=s[0], type=s[1], va=s[3], offset=s[4], size=s[5], entsize=s[9]))
        if shnum:
            core.require(names_idx < shnum, "section name table missing")
            names = self.sections[names_idx]
            strings = blob[names["offset"]:names["offset"] + names["size"]]
            for s in self.sections:
                off = s.pop("name_offset")
                core.require(off < len(strings) and b"\0" in strings[off:], "section name bounds")
                s["name"] = strings[off:].split(b"\0", 1)[0].decode("ascii")

    def to_va(self, offset: int) -> int:
        found = [s["va"] + offset - s["offset"] for s in self.segments
                 if s["type"] == 1 and s["offset"] <= offset < s["offset"] + s["filesz"]]
        core.require(len(found) == 1, "file offset not uniquely file-backed")
        return found[0]

    def to_offset(self, va: int) -> int:
        found = [s["offset"] + va - s["va"] for s in self.segments
                 if s["type"] == 1 and s["va"] <= va < s["va"] + s["filesz"]]
        core.require(len(found) == 1, "VA not uniquely file-backed (possibly BSS)")
        return found[0]


def pair_candidates(words: list[int], targets: set[int], max_gap: int = 8) -> list[dict]:
    """Limited instruction whitelist; never scan past unknown ops or branches.

    JAL permits its immediately following delay slot only. No reachability claim.
    """
    hits = []
    for i, upper in enumerate(words):
        base = (upper >> 16) & 31
        if upper >> 26 != 15 or (upper >> 21) & 31 or not base:
            continue
        delay_only = False
        for j in range(i + 1, min(len(words), i + max_gap + 1)):
            word = words[j]
            op, rs, rt, rd = word >> 26, (word >> 21) & 31, (word >> 16) & 31, (word >> 11) & 31
            if op in (9, 13) and rs == base:
                low = word & 65535
                value = (upper & 65535) << 16
                value = (value + (low if low < 32768 else low - 65536)) & 0xffffffff if op == 9 else value | low
                if value in targets:
                    hits.append(dict(upper_word=i, lower_word=j, address=value,
                                     operation="ADDIU" if op == 9 else "ORI", delay_slot=delay_only))
            if delay_only:
                break
            if op == 3 and base != 31:
                delay_only = True
                continue
            if word == 0 or op in (40, 41, 43, 63):
                continue  # NOP or SB/SH/SW/SD, no GPR destination.
            if op in (8, 9, 10, 11, 12, 13, 14, 15, 32, 33, 35, 36, 37, 55):
                if rt != base:
                    continue
            elif op == 0 and word & 63 in (0, 2, 3, 4, 6, 7, 0x21, 0x23, 0x24, 0x25, 0x26, 0x27, 0x2a, 0x2b, 0x2d, 0x2f):
                if rd != base:
                    continue
            break
    return hits


def _transfer(word: int) -> bool:
    return word >> 26 in (1, 2, 3, 4, 5, 6, 7, 20, 21, 22, 23) or (word >> 26 == 0 and word & 63 in (8, 9))


def _supported_effect(word: int) -> bool:
    op, rs, rt = word >> 26, (word >> 21) & 31, (word >> 16) & 31
    return (word == 0 or op in (9, 13, 32, 33, 35, 36, 37, 40, 41, 43, 63) or (op == 15 and rs == 0)
            or (op == 0 and (word >> 6) & 31 == 0 and (word & 63 == 0x21 or (word & 63 == 0x2d and (rs == 0 or rt == 0)))))


def trace_call(image: ElfImage, call_va: int, max_back: int = 8) -> dict:
    """Local low-32-bit symbolic state at JAL/JALR, including the delay slot.

    No memory dereference, ABI preservation, path execution or function claim.
    Unknown instructions and earlier transfers delimit the starting unknown state.
    """
    core.require(call_va % 4 == 0 and 1 <= max_back <= 32, "invalid call trace bound/alignment")
    offset = image.to_offset(call_va)
    image.to_offset(call_va + 7)  # complete instruction and complete delay slot
    word, delay = struct.unpack_from("<II", image.blob, offset)
    op, rs, rd = word >> 26, (word >> 21) & 31, (word >> 11) & 31
    direct = op == 3
    indirect = op == 0 and word & 63 == 9 and ((word >> 16) & 31) == 0 and ((word >> 6) & 31) == 0 and rd == 31 and rs not in (0, 31)
    core.require(direct or indirect, "only direct JAL or canonical JALR ra supported")
    segment = next(s for s in image.segments if s["type"] == 1 and s["offset"] <= offset < s["offset"] + s["filesz"])
    core.require(offset + 8 <= segment["offset"] + segment["filesz"], "delay slot crosses load segment")
    start, boundary, barrier_va = offset, "bounded_window", None
    for pos in range(offset - 4, max(segment["offset"], offset - 4 * max_back) - 1, -4):
        previous = struct.unpack_from("<I", image.blob, pos)[0]
        if _transfer(previous):
            start, boundary, barrier_va = min(offset, pos + 8), "earlier_transfer_and_delay_excluded", image.to_va(pos)
            break
        if not _supported_effect(previous):
            start, boundary, barrier_va = pos + 4, "unsupported_instruction", image.to_va(pos)
            break
        start = pos
    if start == segment["offset"] and barrier_va is None:
        boundary = "segment_start"
    def value(expression, constant=None, definitions=()):
        return dict(expression=expression, known_u32=constant, definitions=list(definitions))
    regs = {r: value(f"entry_r{r}") for r in range(32)}
    regs[0] = value("0", 0)
    def effect(w, va):
        opcode, a, b, dest = w >> 26, (w >> 21) & 31, (w >> 16) & 31, (w >> 11) & 31
        if w == 0 or opcode in (40, 41, 43, 63):
            return
        source = regs[a]
        immediate = w & 65535
        signed = immediate if immediate < 32768 else immediate - 65536
        defs = sorted(set(source["definitions"] + [va]))
        constant = source["known_u32"]
        if opcode == 15:
            result, b = value(hex(immediate << 16), immediate << 16, [va]), b
        elif opcode in (9, 13):
            n = ((constant + signed) & 0xffffffff if opcode == 9 else constant | immediate) if constant is not None else None
            result = value(f"({source['expression']} {'+' if opcode == 9 else '|'} {signed if opcode == 9 else immediate})", n, defs)
        elif opcode in (32, 33, 35, 36, 37):
            label = {32: 'load8s', 33: 'load16s', 35: 'load32', 36: 'load8u', 37: 'load16u'}[opcode]
            result = value(f"{label}({source['expression']} + {signed})", definitions=defs)
        else:  # ADDU or DADDU move (only zero-source forms accepted for DADDU)
            other, b = regs[b], dest
            n = (constant + other['known_u32']) & 0xffffffff if constant is not None and other['known_u32'] is not None else None
            expr = other['expression'] if a == 0 else source['expression'] if ((w >> 16) & 31) == 0 else f"({source['expression']} + {other['expression']})"
            result = value(expr, n, sorted(set(defs + other['definitions'])))
        if b:
            regs[b] = result
    for pos in range(start, offset, 4):
        effect(struct.unpack_from("<I", image.blob, pos)[0], image.to_va(pos))
    target = value(hex(((call_va + 4) & 0xf0000000) | ((word & 0x03ffffff) << 2)), ((call_va + 4) & 0xf0000000) | ((word & 0x03ffffff) << 2)) if direct else dict(regs[rs])
    regs[31] = value(hex(call_va + 8), (call_va + 8) & 0xffffffff, [call_va])
    supported_delay = _supported_effect(delay)
    if supported_delay:
        effect(delay, call_va + 4)
    return dict(call_va=call_va, kind="JAL" if direct else "JALR", target_before_delay=target,
                start_va=image.to_va(start), boundary=boundary, barrier_va=barrier_va,
                delay_va=call_va + 4, delay_supported=supported_delay,
                argument_registers={str(r): regs[r] for r in range(4, 8)} if supported_delay else {},
                evidence="conditional straight-line low32 state; memory values, function boundaries and execution unverified")


def local_window(image: ElfImage, start_va: int, size: int = 0x300) -> dict:
    """Bounded numeric scan, explicitly not a recovered function boundary."""
    start = image.to_offset(start_va)
    segment = next(s for s in image.segments if s["type"] == 1 and s["offset"] <= start < s["offset"] + s["filesz"])
    end = min(start + size, segment["offset"] + segment["filesz"])
    calls, constants, traces = [], [], []
    for offset in range(start, end - 3, 4):
        word = struct.unpack_from("<I", image.blob, offset)[0]
        va = image.to_va(offset)
        if word >> 26 == 3:
            calls.append(dict(va=va, target=((va + 4) & 0xf0000000) | ((word & 0x03ffffff) << 2)))
        elif word >> 26 == 9 and ((word >> 21) & 31) == 0 and word & 65535 in (256, 512, 516):
            constants.append(dict(va=va, destination_register=(word >> 16) & 31, immediate=word & 65535))
        if offset + 8 <= end and (word >> 26 == 3 or (word >> 26 == 0 and word & 63 == 9 and (word >> 11) & 31 == 31 and (word >> 21) & 31 not in (0, 31) and (word >> 16) & 31 == 0 and (word >> 6) & 31 == 0)):
            traces.append(trace_call(image, va))
    return dict(start_va=start_va, span_bytes=end - start, direct_jal_candidates=calls,
                addiu_zero_size_candidates=constants, call_argument_candidates=traces, function_boundary_verified=False)


def classify_va(image: ElfImage, va: int) -> str:
    found = [s for s in image.segments if s['type'] == 1 and s['va'] <= va < s['va'] + s['memsz']]
    if len(found) != 1:
        return 'unmapped_or_ambiguous'
    s = found[0]
    return 'file_backed' if va < s['va'] + s['filesz'] else 'memory_only'


def read_u32(image: ElfImage, va: int) -> int:
    core.require(va % 4 == 0, 'unaligned table word')
    off = image.to_offset(va)
    core.require(image.to_offset(va + 3) == off + 3, 'table word crosses file mapping')
    return struct.unpack_from('<I', image.blob, off)[0]


def reginfo_gp(image: ElfImage) -> int | None:
    sections = [s for s in image.sections if s['type'] == 0x70000006]
    core.require(len(sections) <= 1, 'ambiguous MIPS reginfo')
    if not sections:
        return None
    s = sections[0]
    core.require(s['size'] == 24, 'unsupported MIPS reginfo size')
    return struct.unpack_from('<6I', image.blob, s['offset'])[5]


def constant_store_candidates(words: list[int], targets: set[int], max_gap: int = 32) -> list[dict]:
    """Numeric LUI/lower/SW chains only; no object identity or path assertion."""
    core.require(1 <= max_gap <= 32, 'invalid store scan bound')
    result = []
    for pair in pair_candidates(words, targets):
        if pair['delay_slot']:
            continue  # never carry a constructed value across a call
        lower = pair['lower_word']
        reg = (words[lower] >> 16) & 31
        if reg == 0:
            continue
        for i in range(lower + 1, min(len(words), lower + max_gap + 1)):
            w = words[i]
            op, rs, rt, rd = w >> 26, (w >> 21) & 31, (w >> 16) & 31, (w >> 11) & 31
            if _transfer(w) or not _supported_effect(w):
                break
            if op == 43 and rt == reg:
                displacement = w & 65535
                result.append(dict(**pair, store_word=i, base_register=rs, value_register=rt,
                                   displacement=displacement if displacement < 32768 else displacement - 65536))
            if w == 0 or op in (40, 41, 43, 63):
                continue
            destination = rd if op == 0 else rt
            if destination == reg:
                break
    return result


def table_audit(image: ElfImage, tables: list[int], displacements: list[int]) -> dict:
    core.require(len(tables) <= 16 and len(displacements) <= 16, 'too many research selections')
    core.require(all(-32768 <= d <= 32767 for d in displacements), 'GP displacement outside signed16')
    gp = reginfo_gp(image)
    core.require(gp is not None or not displacements, 'GP metadata required for selected slots')
    reports = [{ 'base_va': va, 'words': [dict(offset=i * 4, value=read_u32(image, va + i * 4),
                  value_region=classify_va(image, read_u32(image, va + i * 4))) for i in range(16)],
                  'constant_store_candidates': []} for va in sorted(set(tables))]
    slots = [dict(displacement=d, slot_va=(gp + d) & 0xffffffff,
                  region=classify_va(image, (gp + d) & 0xffffffff), load_candidates=[], store_candidates=[])
             for d in sorted(set(displacements))]
    for slot in slots:
        if slot['region'] == 'file_backed':
            slot['initial_file_word'] = read_u32(image, slot['slot_va'])
            slot['initial_word_region'] = classify_va(image, slot['initial_file_word'])
        else:
            slot['initial_file_word'] = None  # no synthetic zero or implicit dereference
    for segment in image.segments:
        if segment['type'] != 1 or not segment['flags'] & 1:
            continue
        start, size = segment['offset'], segment['filesz']
        core.require(start % 4 == 0, 'unaligned scan segment')
        words = list(struct.unpack_from(f'<{size // 4}I', image.blob, start))
        for h in constant_store_candidates(words, set(tables)):
            record = {k.replace('_word', '_va'): image.to_va(start + v * 4) if k.endswith('_word') else v for k, v in h.items()}
            next(t for t in reports if t['base_va'] == h['address'])['constant_store_candidates'].append(record)
        for i, word in enumerate(words):
            if (word >> 21) & 31 != 28 or word >> 26 not in (35, 43):
                continue
            low = word & 65535
            d = low if low < 32768 else low - 65536
            for slot in slots:
                if slot['displacement'] == d:
                    key = 'load_candidates' if word >> 26 == 35 else 'store_candidates'
                    slot[key].append(dict(va=image.to_va(start + 4 * i), register=(word >> 16) & 31))
    return dict(declared_gp=gp, tables=reports, gp_slots=slots,
                evidence='initial file words and numeric candidates only; GP runtime value, mutable pointers, object identity and execution unverified')


def analyze(blob: bytes, tables: list[int] | None = None, displacements: list[int] | None = None) -> dict:
    image = ElfImage(blob)
    strings = []
    for match in re.finditer(rb"[ -~]{4,128}\x00", blob):
        text = match.group()[:-1].decode("ascii")
        if not ("\\UIText\\" in text or text in ("UFontObj", "DrawText: No font", "DrawTextClipped: No font")
                or text.startswith(("intUFontObjexec", "intUCanvasexecStrLen", "intUCanvasexecDrawText", "intUObjectexecUnicodeStringConst", "intUMrtsDynamicTextAreaexecMrtsDrawTextLine"))):
            continue
        strings.append(dict(identifier=text, offset=match.start(), va=image.to_va(match.start()),
                            pointer_words=[], address_candidates=[]))
    targets = {s["va"]: s for s in strings}
    for segment in image.segments:
        if segment["type"] != 1 or not segment["filesz"]:
            continue
        start, end = segment["offset"], segment["offset"] + segment["filesz"]
        core.require(start % 4 == 0, "unaligned load segment")
        words = list(struct.unpack_from(f"<{(end - start) // 4}I", blob, start))
        for i, word in enumerate(words):
            if word in targets:
                targets[word]["pointer_words"].append(image.to_va(start + i * 4))
        if segment["flags"] & 1:
            for hit in pair_candidates(words, set(targets)):
                targets[hit["address"]]["address_candidates"].append(
                    {"upper_va": image.to_va(start + hit["upper_word"] * 4),
                     "lower_va": image.to_va(start + hit["lower_word"] * 4),
                     "operation": hit["operation"], "delay_slot": hit["delay_slot"]})
    for s in strings:
        if "\\UIText\\" in s["identifier"]:
            s["local_windows"] = [local_window(image, h["upper_va"]) for h in s["address_candidates"]]
    return {"entry": image.entry, "flags": image.flags, "segments": image.segments,
            "sections": image.sections, "symbol_entries": sum(s["size"] // s["entsize"] for s in image.sections if s["type"] in (2, 11) and s["entsize"]),
            "strings": strings, "table_audit": table_audit(image, tables or [], displacements or []),
            "evidence": "file-backed addresses and numeric candidates only; merged executable segment may contain data; no function boundaries or runtime execution proven"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=ROOT / "work/native-research")
    parser.add_argument("--table-va", type=lambda x: int(x, 0), action='append', default=[], help='bounded 16-word table candidate (repeatable)')
    parser.add_argument("--gp-displacement", type=lambda x: int(x, 0), action='append', default=[], help='signed16 GP-relative slot candidate (repeatable)')
    args = parser.parse_args()
    profile = json.loads((ROOT / "profiles/scka-20043.json").read_text("utf8"))
    before = core.file_digest(args.iso)
    core.require(before == profile["expected_iso_sha256"], "unknown ISO version/hash")
    blob = core.iso_files(args.iso, [profile["boot"]])[profile["boot"]]
    core.require(core.digest(blob) == ELF_SHA256, "ELF fingerprint mismatch")
    report = {"schema": 3, "iso_sha256": before, "elf_sha256": ELF_SHA256, **analyze(blob, args.table_va, args.gp_displacement)}
    core.require(core.file_digest(args.iso) == before, "original ISO hash changed")
    out = core.output_directory(args.out)
    (out / "native-research.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    traces = sum(len(w['call_argument_candidates']) for s in report['strings'] for w in s.get('local_windows', []))
    print(f"NATIVE AUDIT PASS symbols={report['symbol_entries']} strings={len(report['strings'])} address_candidates={sum(len(s['address_candidates']) for s in report['strings'])} pointer_words={sum(len(s['pointer_words']) for s in report['strings'])} call_traces={traces} tables={len(report['table_audit']['tables'])} gp_slots={len(report['table_audit']['gp_slots'])}")


if __name__ == "__main__":
    main()
