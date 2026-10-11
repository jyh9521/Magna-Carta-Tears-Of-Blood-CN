"""Audit explicit alternate source readings without lifting import quarantine.

Profiles bind original corpus, resource, span and decoded-text fingerprints.
Codec round trips prove byte interpretation, not original runtime encoding.
Targets remain outside ordinary import registries until a separate import gate.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('tools', 'lib', 'src')]
from font_poc import archive_entries, digest, require
from audit_native_chat import source_match
from translate.fpb import parse_fpb_raw
from localization.text import protected_tokens, validate_target


def audit_field(resource, entry, decision, original):
    require(decision['resource'] == resource['resource'], 'resource identity mismatch')
    require(digest(original) == resource['sha256'] == decision['resource_sha256'], 'resource fingerprint mismatch')
    require(entry['decode'] == 'failed', 'alternate reading requires original decode quarantine')
    for key in ('id', 'offset', 'source_bytes', 'source_sha256'):
        require(decision.get(key) == entry.get(key), 'source binding mismatch: ' + key)
    require(decision.get('import_approved') is False and decision.get('runtime_encoding_verified') is False,
            'alternate reading cannot authorize imports or claim runtime encoding')
    require(decision.get('status') == 'reviewed', 'reading not reviewed')
    codec = decision['source_encoding']
    require(codec in ('cp932', 'cp949', 'utf-8'), 'unsupported explicit source codec')
    fpb = resource['resource'].endswith('.fpb')
    storage = parse_fpb_raw(original)[2] if fpb else original
    offset, length = entry['offset'], entry['source_bytes']
    require(type(offset) is int and type(length) is int and offset >= 0 and length > 0
            and offset + length <= len(storage), 'source span out of bounds')
    raw = storage[offset:offset + length]
    require(digest(raw) == entry['source_sha256'], 'source span fingerprint mismatch')
    require(bytes.fromhex(entry['raw_hex']) == raw, 'corpus original hex mismatch')
    text = raw.decode(codec, errors='strict')
    require(text.encode(codec, errors='strict') == raw, 'noncanonical codec round trip')
    require(digest(text.encode('utf-8')) == decision['reading_sha256'], 'decoded reading fingerprint mismatch')
    require(not any(ord(c) < 32 or 0xE000 <= ord(c) <= 0xF8FF for c in text), 'nontext/private-use reading')
    require(bool(re.search('[ぁ-ゖァ-ヺ]', text)), 'lexical reading evidence missing')
    tokens = protected_tokens(text)
    validate_target(text, decision['target'])
    require('—' not in decision['target'] and '―' not in decision['target'], 'dash forbidden in target')
    for segment in re.split(r'\$n', decision['target']):
        start = re.sub(r'^(?:\$D\d{2}|\s)+', '', segment)
        require(not start or start[0] not in '，。！？；：、）】》…', 'leading punctuation in target page')
    native = None
    if fpb:
        binding = decision['native_binding']
        require(binding['id'] == entry['id'] and binding['source_resource'] == resource['resource']
                and binding['source_resource_sha256'] == resource['sha256']
                and all(binding[b] == entry[e] for b, e in
                        [('source_offset', 'offset'), ('source_bytes', 'source_bytes'), ('source_sha256', 'source_sha256')]),
                'native binding does not match reading span')
        native = source_match(original, binding)
    return dict(id=entry['id'], source_encoding=codec, source=text, target=decision['target'],
                protected_tokens=tokens, native_source_binding=native,
                source_still_quarantined=True, import_approved=False,
                runtime_encoding_verified=False, runtime_verified=False)


def audit(corpus, profile, members):
    require(profile.get('schema') == 1, 'unsupported alternate reading profile')
    index = {e['id']: (r, e) for r in corpus['resources'] for e in r['entries']}
    seen, rows = set(), []
    for d in profile['entries']:
        identity = d['id']
        require(identity in index and identity not in seen, 'unknown/duplicate alternate identity')
        seen.add(identity)
        resource, entry = index[identity]
        rows.append(audit_field(resource, entry, d, members[Path(resource['resource']).name]))
    return dict(schema=1, fields=rows, summary=dict(readings=len(rows),
        native_fpb_bindings=sum(x['native_source_binding'] is not None for x in rows),
        ordinary_import_registry_changed=False, source_quarantine_retained=True,
        codec_roundtrip_not_runtime_proof=True, iso_generated=False))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ('corpus', 'profile', 'archive', 'out'):
        p.add_argument('--' + arg, type=Path, required=True)
    p.add_argument('--archive-sha256', required=True)
    a = p.parse_args()
    profile = json.loads(a.profile.read_text('utf8'))
    require(digest(a.corpus.read_bytes()) == profile['source_corpus_sha256'], 'corpus fingerprint mismatch')
    require(digest(a.archive.read_bytes()) == a.archive_sha256, 'archive fingerprint mismatch')
    result = audit(json.loads(a.corpus.read_text('utf8')), profile, dict(archive_entries(a.archive)[1]))
    result['input_sha256'] = {str(q): digest(q.read_bytes()) for q in (a.corpus, a.profile, a.archive)}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'utf8')
    require(digest(a.archive.read_bytes()) == a.archive_sha256, 'source archive changed')
    print('ALTERNATE_SOURCE_READINGS_PASS readings=' + str(len(result['fields']))
          + ' native_fpb_bindings=' + str(result['summary']['native_fpb_bindings'])
          + ' controls_preserved=true source_quarantine_retained=true import_approved=false runtime_encoding_verified=false')


if __name__ == '__main__':
    main()
