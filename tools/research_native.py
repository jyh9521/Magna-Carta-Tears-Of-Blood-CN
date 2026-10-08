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


def local_window(image: ElfImage, start_va: int, size: int = 0x300) -> dict:
    """Bounded numeric scan, explicitly not a recovered function boundary."""
    start = image.to_offset(start_va)
    segment = next(s for s in image.segments if s["type"] == 1 and s["offset"] <= start < s["offset"] + s["filesz"])
    end = min(start + size, segment["offset"] + segment["filesz"])
    calls, constants = [], []
    for offset in range(start, end - 3, 4):
        word = struct.unpack_from("<I", image.blob, offset)[0]
        va = image.to_va(offset)
        if word >> 26 == 3:
            calls.append(dict(va=va, target=((va + 4) & 0xf0000000) | ((word & 0x03ffffff) << 2)))
        elif word >> 26 == 9 and ((word >> 21) & 31) == 0 and word & 65535 in (256, 512, 516):
            constants.append(dict(va=va, destination_register=(word >> 16) & 31, immediate=word & 65535))
    return dict(start_va=start_va, span_bytes=end - start, direct_jal_candidates=calls,
                addiu_zero_size_candidates=constants, function_boundary_verified=False)


def analyze(blob: bytes) -> dict:
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
            "strings": strings,
            "evidence": "file-backed addresses and numeric candidates only; merged executable segment may contain data; no function boundaries or runtime execution proven"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=ROOT / "work/native-research")
    args = parser.parse_args()
    profile = json.loads((ROOT / "profiles/scka-20043.json").read_text("utf8"))
    before = core.file_digest(args.iso)
    core.require(before == profile["expected_iso_sha256"], "unknown ISO version/hash")
    blob = core.iso_files(args.iso, [profile["boot"]])[profile["boot"]]
    core.require(core.digest(blob) == ELF_SHA256, "ELF fingerprint mismatch")
    report = {"schema": 1, "iso_sha256": before, "elf_sha256": ELF_SHA256, **analyze(blob)}
    core.require(core.file_digest(args.iso) == before, "original ISO hash changed")
    out = core.output_directory(args.out)
    (out / "native-research.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(f"NATIVE AUDIT PASS symbols={report['symbol_entries']} strings={len(report['strings'])} address_candidates={sum(len(s['address_candidates']) for s in report['strings'])} pointer_words={sum(len(s['pointer_words']) for s in report['strings'])}")


if __name__ == "__main__":
    main()
