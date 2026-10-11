"""Derive a mixed-source catalog for audited native text spans, never alter primary input."""
from pathlib import Path
import argparse
import copy
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('tools', 'lib', 'src')]
from audit_alternate_source_readings import audit
from audit_native_chat import validate_anchors
from research_native import ElfImage, ELF_SHA256
from font_poc import digest, archive_entries, require
from audit_native_fixed_dialogue import validate_field,validate_anchors as validate_fixed_anchors


def derive(corpus, profile, members, fixed_profile=None):
    result = audit(corpus, profile, members)
    readings = {e['id']: e for e in result['fields']}
    fixed = {}
    if fixed_profile is not None:
        require(fixed_profile.get('schema') == 1, 'unsupported fixed interpretation profile')
        for b in fixed_profile['bindings']:
            require(b['id'] in readings and b['id'] not in fixed, 'missing/duplicate fixed interpretation identity')
            require(readings[b['id']]['native_source_binding'] is None, 'fixed binding overlaps FPB binding')
            fixed[b['id']] = b
    derived = copy.deepcopy(corpus)
    selected = []
    decisions = {e['id']: e for e in profile['entries']}
    for resource in derived['resources']:
        for entry in resource['entries']:
            identity = entry['id']
            if identity not in readings:
                continue
            reading, d = readings[identity], decisions[identity]
            if reading['native_source_binding'] is not None:
                require(resource['resource'].endswith('.fpb') and entry['semantic'] == 'dialogue-window',
                        'alternate native import role not supported')
            elif identity in fixed:
                geometry = validate_field(resource, entry, fixed[identity], members[Path(resource['resource']).name])
                if resource['resource'].endswith('.cht'):
                    entry.update(observed_byte_capacity=511, trailer_bytes=geometry['preserved_tail_bytes'],
                                 trailer_sha256=geometry['preserved_tail_sha256'])
                entry['semantic'] = 'native-text-storage-candidate'
            else:
                continue
            entry.update(source_locale='ja-JP', source_encoding=d['source_encoding'],
                         references=dict(entry.get('references', {}), **{'ja-JP': reading['source']}),
                         decode='strict', controls='recognized', editable=True, backend_eligible=True,
                         source_interpretation=dict(original_decode='failed', raw_sha256=entry['source_sha256'],
                             reading_sha256=d['reading_sha256'], native_source_span_verified=True,
                             runtime_encoding_verified=False, specific_event_execution_verified=False))
            selected.append(dict(id=identity, source_sha256=entry['source_sha256'], target=d['target'],
                                 status='reviewed', reinsertion_policy='translate',
                                 context=('Source-hashed alternate reading and actual FPB numeric-key chat payload. Source locale/codec explicit in derived catalog; primary corpus unchanged. Event reachability/layout not claimed.' if reading['native_source_binding'] is not None else 'Source-hashed alternate reading and native512-byte fixed text read to FString, numeric metadata preserved. Source locale/codec explicit in derived catalog; primary corpus unchanged. Event reachability/UI layout not claimed.')))
    derived['alternate_source_interpretations'] = dict(fields=len(selected),
        primary_corpus_modified=False, original_runtime_encoding_verified=False)
    return derived, dict(schema=1, locale=profile['locale'], entries=selected)


def merge_profiles(profiles, member='entries', locale_required=True):
    require(bool(profiles), 'interpretation profiles missing')
    first = profiles[0]
    require(first.get('schema') == 1, 'unsupported interpretation profile schema')
    require(bool(first.get('source_corpus_sha256')), 'interpretation corpus fingerprint missing')
    if locale_required:
        require(bool(first.get('locale')), 'interpretation locale missing')
    merged = copy.deepcopy(first)
    merged[member] = []
    seen = set()
    for profile in profiles:
        require(profile.get('schema') == first['schema'], 'interpretation profile schema mismatch')
        require(profile.get('source_corpus_sha256') == first['source_corpus_sha256'], 'interpretation profile corpus mismatch')
        require(profile.get('locale') == first.get('locale'), 'interpretation profile locale mismatch')
        for row in profile[member]:
            require(row['id'] not in seen, 'duplicate interpretation identity')
            seen.add(row['id'])
            merged[member].append(copy.deepcopy(row))
    return merged


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ('corpus', 'archive', 'elf', 'out'):
        p.add_argument('--' + arg, type=Path, required=True)
    p.add_argument('--profile', type=Path, action='append', required=True)
    p.add_argument('--fixed-profile', type=Path, action='append')
    a = p.parse_args()
    profile = merge_profiles([json.loads(q.read_text('utf8')) for q in a.profile])
    require(digest(a.corpus.read_bytes()) == profile['source_corpus_sha256'], 'primary corpus fingerprint mismatch')
    require(digest(a.archive.read_bytes()) == '09d2e4d1f72e40b5d12da7b872226c446a21dde12bf1601bb4dfe58887a5d33a', 'original archive fingerprint mismatch')
    require(digest(a.elf.read_bytes()) == ELF_SHA256, 'original ELF fingerprint mismatch')
    validate_anchors(ElfImage(a.elf.read_bytes()))
    fixed = None
    if a.fixed_profile is not None:
        fixed = merge_profiles([json.loads(q.read_text('utf8')) for q in a.fixed_profile], 'bindings', False)
        require(fixed['source_corpus_sha256'] == profile['source_corpus_sha256'], 'fixed profile primary corpus mismatch')
        validate_fixed_anchors(ElfImage(a.elf.read_bytes()))
    c, b = derive(json.loads(a.corpus.read_text('utf8')), profile, dict(archive_entries(a.archive)[1]), fixed)
    if a.fixed_profile is not None:
        if len(a.fixed_profile) == 1:
            c['alternate_source_interpretations']['fixed_profile_sha256'] = digest(a.fixed_profile[0].read_bytes())
        else:
            c['alternate_source_interpretations']['fixed_profiles_sha256'] = {str(q): digest(q.read_bytes()) for q in a.fixed_profile}
    c['alternate_source_interpretations']['input_sha256'] = {str(q): digest(q.read_bytes()) for q in (a.corpus, *a.profile, a.archive, a.elf)}
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / 'source-corpus.json').write_text(json.dumps(c, ensure_ascii=False, indent=2) + '\n', 'utf8')
    (a.out / 'selected-batch.json').write_text(json.dumps(b, ensure_ascii=False, indent=2) + '\n', 'utf8')
    require(digest(a.corpus.read_bytes()) == profile['source_corpus_sha256'], 'primary corpus changed')
    count = sum('.fpb/' in e['id'] for e in b['entries'])
    print('SOURCE_INTERPRETATION_PASS fields=' + str(len(b['entries'])) + ' native_fpb_fields=' + str(count)
          + ' native_fixed_fields=' + str(len(b['entries']) - count)
          + ' per_field_locale_codec=true primary_corpus_unchanged=true runtime_encoding_verified=false')


if __name__ == '__main__':
    main()
