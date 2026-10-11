"""Version-locked native CHT/POD 512-byte text reads and source span binding.

Static FString storage and numeric metadata separation do not prove runtime UI
initialization, branch/event reachability or full consumer enumeration.
"""
from pathlib import Path
import argparse
import json
import struct
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('tools', 'lib', 'src')]
from font_poc import digest, archive_entries, require
from research_native import ElfImage, ELF_SHA256
from import_audited_fields import fixed_extent, fingerprint_extent

ANCHORS = {
    0x2ffb38: 0x3c05004b, 0x2ffb48: 0x24a57740,
    0x2ffc44: 0x24060200, 0x2ffc68: 0x0c069530,
    0x3a39ac: 0x3c05004c, 0x3a39b8: 0x24a5b7e0,
    0x3a3ac0: 0x24060200, 0x3a3ae4: 0x0c069530,
    0x3a3bb0: 0x0c0e8c50, 0x3a3bb4: 0x27a80378,
    0x3a3280: 0x26240008, 0x3a32c8: 0x0c045b1c,
    0x3a01fc: 0x0c06cd10, 0x3a0200: 0xafa200a4,
    0x3a0208: 0x0c06cd10, 0x3a020c: 0x26450014,
    0x3a0214: 0x0c06cd10, 0x3a0218: 0x26450020,
    0x329ec0: 0x3c05004c, 0x329ed0: 0x24a59070,
    0x32a0c4: 0x24060200, 0x32a100: 0x0c069530,
    0x32a0dc: 0xae000018, 0x32a0e0: 0x26110018,
    0x32a158: 0x0c045b1c,
    0x32a470: 0x24060200, 0x32a474: 0xae8000fc,
    0x32a478: 0x268400fc, 0x32a494: 0x0c069530,
    0x32a4e8: 0x0c045b1c,
}
PATHS = {0x4b7740: b'..\\ChatingData\\%08d.cht',
         0x4bb7e0: b'..\\ChatingData\\%08d.cht',
         0x4b9070: b'..\\PhoneData\\%08d.pod'}


def validate_anchors(image):
    for va, word in ANCHORS.items():
        require(struct.unpack_from('<I', image.blob, image.to_offset(va))[0] == word,
                'fixed dialogue native instruction mismatch ' + hex(va))
    for va, path in PATHS.items():
        at = image.to_offset(va)
        require(image.blob[at:at + len(path) + 1] == path + b'\0', 'fixed dialogue native path mismatch')


def pod_text_layout():
    # The native reader first consumes five u32 words, then ten strings,
    # a u32, five strings, a u32, nine strings and three final u32 words.
    rows, at = [], 20
    native = [v for i in range(5) for v in (0x18 + 12 * i, 0x54 + 12 * i)]
    native += [0x90] + [0x9c + 12 * i for i in range(4)]
    native += [0xcc + 12 * i for i in range(4)] + [0xfc]
    native += [0x108 + 12 * i for i in range(4)]
    for index, location in enumerate(native):
        if index in (10, 15): at += 4
        rows.append(dict(index=index, offset=at, native_fstring_offset=location))
        at += 512
    require(at + 12 == 12328, 'POD native geometry disagreement')
    return rows


def validate_field(resource, entry, binding, original):
    require(binding['id'] == entry['id'] and binding['resource'] == resource['resource'], 'fixed native identity mismatch')
    require(digest(original) == resource['sha256'] == binding['resource_sha256'], 'fixed native resource fingerprint mismatch')
    for key in ('offset', 'source_bytes', 'source_sha256'):
        require(binding[key] == entry[key], 'fixed native source binding mismatch')
    require(binding.get('native_read_bytes') == 512 and binding.get('runtime_verified') is False,
            'invalid fixed native read proof')
    if resource['resource'].endswith('.cht'):
        count = struct.unpack_from('<I', original, 4)[0]
        require(len(original) == 12 + count * 532, 'CHT physical record geometry mismatch')
        index = entry['slot']
        require(0 <= index < count and entry['offset'] == 28 + index * 532,
                'CHT native slot offset mismatch')
        require(binding['record_index'] == index, 'CHT record identity mismatch')
        require(binding['numeric_metadata_hex'] == original[12 + index * 532:28 + index * 532].hex(),
                'CHT numeric record metadata mismatch')
    elif resource['resource'].endswith('.pod'):
        require(len(original) == 12328, 'POD original physical size mismatch')
        index = entry['field_index']; row = pod_text_layout()[index]
        require(entry['offset'] == row['offset'] and binding['record_index'] == index
                and binding['native_fstring_offset'] == row['native_fstring_offset'], 'POD native string geometry mismatch')
    else:
        raise ValueError('unsupported fixed native text format')
    at = entry['offset']; slot = original[at:at + 512]; n = entry['source_bytes']
    require(0 < n < 512 and digest(slot[:n]) == entry['source_sha256'], 'fixed native source span mismatch')
    require(slot[n] == 0 and not any(slot[n:]), 'fixed native text padding not clean')
    span, whole_sha = fixed_extent(entry); hashed = fingerprint_extent(entry, span)
    require(hashed >= 512 and digest(original[at:at + hashed]) == whole_sha, 'fixed original segment fingerprint mismatch')
    return dict(id=entry['id'], native_read_bytes=512, writable_bytes=512,
                fingerprint_bytes=hashed, preserved_tail_bytes=hashed - 512,
                preserved_tail_sha256=digest(original[at + 512:at + hashed]),
                native_fstring_storage_verified=True, runtime_verified=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ('elf', 'archive', 'corpus', 'profile', 'out'):
        p.add_argument('--' + arg, type=Path, required=True)
    a = p.parse_args()
    require(digest(a.elf.read_bytes()) == ELF_SHA256, 'original ELF fingerprint mismatch')
    require(digest(a.archive.read_bytes()) == '09d2e4d1f72e40b5d12da7b872226c446a21dde12bf1601bb4dfe58887a5d33a', 'original SHIP fingerprint mismatch')
    validate_anchors(ElfImage(a.elf.read_bytes()))
    c = json.loads(a.corpus.read_text('utf8')); profile = json.loads(a.profile.read_text('utf8'))
    require(profile['source_corpus_sha256'] == digest(a.corpus.read_bytes()), 'fixed primary corpus fingerprint mismatch')
    ix = {e['id']: (r, e) for r in c['resources'] for e in r['entries']}
    ship = dict(archive_entries(a.archive)[1]); rows = []; seen = set()
    for binding in profile['bindings']:
        require(binding['id'] not in seen, 'duplicate native fixed source identity'); seen.add(binding['id'])
        r, e = ix[binding['id']]
        rows.append(validate_field(r, e, binding, ship[Path(r['resource']).name]))
    result = dict(elf_sha256=ELF_SHA256, bindings=rows, anchors={hex(k): hex(v) for k, v in ANCHORS.items()},
        protocol='source512byte buffer->identity conversion1a54c0->FString byte copy116c70; numeric metadata separate',
        runtime_verified=False, all_other_consumers_enumerated=False)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2) + '\n', 'utf8')
    print('NATIVE_FIXED_DIALOGUE_PASS fields=' + str(len(rows))
          + ' native_text_bytes=512 numeric_metadata_separate=true source_geometry_hashes=true runtime_verified=false')


if __name__ == '__main__': main()
