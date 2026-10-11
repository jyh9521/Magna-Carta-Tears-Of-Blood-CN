"""Source-bound linguistic review of quarantined literal structures, not import approval."""
from pathlib import Path
import argparse
import json
import re
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('tools', 'lib', 'src')]
from font_poc import archive_entries, digest, require
from source_interpretation import source_text
from localization.text import TOKEN
from translate.fpb import parse_fpb_raw


def structures(text):
    require(not any(ord(c) < 32 for c in text), 'literal review excludes control bytes')
    tokens, angles, at = [], [], 0
    while at < len(text):
        if text.startswith('->', at):
            tokens.append('->'); at += 2; continue
        c = text[at]
        if c not in '$%<>{}':
            at += 1; continue
        match = TOKEN.match(text, at)
        if match:
            tokens.append(match.group()); at = match.end(); continue
        if c == '%':
            number = re.search(r'\d+(?:\.\d+)?$', text[:at])
            require(number is not None, 'unbound literal percent')
            tokens.append(number.group() + '%'); at += 1; continue
        if c == '<':
            end = text.find('>', at + 1)
            require(end >= 0, 'unclosed literal angle')
            inside = text[at + 1:end]
            require(not any(ch in '$%<>{}' for ch in inside)
                    and re.search('[가-힣ぁ-ヿ一-鿿]', inside) is not None,
                    'unreviewed angle content')
            tokens.extend(['<', '>']); angles.append(inside); at = end + 1; continue
        raise ValueError('unknown literal review structure')
    return tokens, angles


def validate_reading(source, target, terms):
    require(bool(target) and not re.search('[가-힣]', target), 'untranslated or empty literal target')
    require('—' not in target and '―' not in target, 'dash forbidden')
    before, names = structures(source); after, translated_names = structures(target)
    require(before == after, 'literal structures values/count/order changed')
    require(re.findall(r'\d+(?:\.\d+)?', source) == re.findall(r'\d+(?:\.\d+)?', target),
            'numeric values/count/order changed')
    require(len(names) == len(translated_names), 'angle count mismatch')
    for name, translated in zip(names, translated_names):
        if name.strip() == '공지사항':
            require(translated.strip() == '公告', 'notice label mismatch')
        else:
            require(name in terms and translated == terms[name], 'canonical bracket name mismatch')
    for page in target.split('$n'):
        require(bool(page.strip()) and page.lstrip()[0] not in '，。！？；：、）】》…',
                'empty page or leading punctuation')
    return dict(structures=before, canonical_bracket_names=len(names))


def audit(corpus, profile, members, terms):
    require(profile.get('schema') == 1 and profile.get('locale') == 'zh-CN', 'unsupported literal profile')
    index = {e['id']: (r, e) for r in corpus['resources'] for e in r['entries']}
    seen, result = set(), []
    for d in profile['entries']:
        identity = d['id']
        require(identity in index and identity not in seen, 'unknown/duplicate literal identity')
        seen.add(identity); resource, entry = index[identity]
        require(entry['decode'] == 'strict' and entry['controls'] == 'quarantined', 'literal review requires strict control quarantine')
        require(d['status'] == 'reviewed' and d['import_approved'] is False
                and d['runtime_control_semantics_verified'] is False, 'literal review cannot approve import/runtime')
        require(d['resource'] == resource['resource'] and d['resource_sha256'] == resource['sha256'], 'resource binding mismatch')
        require(all(d[k] == entry[k] for k in ('id','offset','source_bytes','source_sha256')), 'source binding mismatch')
        raw = members[Path(resource['resource']).name]
        require(digest(raw) == resource['sha256'], 'resource fingerprint mismatch')
        storage = parse_fpb_raw(raw)[2] if resource['resource'].endswith('.fpb') else raw
        at, n = entry['offset'], entry['source_bytes']
        require(type(at) is int and type(n) is int and at >= 0 and n > 0 and at + n <= len(storage), 'source span bounds')
        span = storage[at:at+n]
        require(digest(span) == entry['source_sha256'], 'source fingerprint mismatch')
        require(d['source_encoding'] == 'cp949', 'literal codec mismatch')
        text = span.decode('cp949')
        require(text.encode('cp949') == span and text == source_text(entry) == d['source'], 'source text mismatch')
        require(digest(text.encode('utf8')) == d['reading_sha256'], 'reading fingerprint mismatch')
        result.append(dict(id=identity, **validate_reading(text, d['target'], terms),
                           source_quarantine_retained=True, import_approved=False, runtime_verified=False))
    return dict(schema=1, fields=result, summary=dict(reviewed=len(result),
        ordinary_import_registry_changed=False, source_quarantine_retained=True, iso_generated=False))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('corpus','profile','archive','glossary','out'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    profile = json.loads(a.profile.read_text('utf8'))
    require(digest(a.corpus.read_bytes()) == profile['source_corpus_sha256'], 'corpus fingerprint mismatch')
    require(digest(a.archive.read_bytes()) == '09d2e4d1f72e40b5d12da7b872226c446a21dde12bf1601bb4dfe58887a5d33a', 'original archive fingerprint mismatch')
    from validate_translation_batch import glossary_terms
    result = audit(json.loads(a.corpus.read_text('utf8')), profile, dict(archive_entries(a.archive)[1]), dict(glossary_terms(a.glossary)))
    result['input_sha256'] = {str(q): digest(q.read_bytes()) for q in (a.corpus,a.profile,a.archive,a.glossary)}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    require(json.loads(a.out.read_text('utf8')) == result, 'result reopen mismatch')
    print('LITERAL_CONTROL_READINGS_PASS fields='+str(len(result['fields']))+' values_order_names_preserved=true source_quarantine_retained=true import_approved=false runtime_verified=false')


if __name__ == '__main__':
    main()
