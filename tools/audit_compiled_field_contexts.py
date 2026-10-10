"""Reparse compiled constants and bind assignment targets to bounded field uses.

Static field-reference context is not a reaching-definition or execution proof.
Only same-function single-target string assignments with reviewed consumers
gain a role; cross-function uses are retained as research evidence only.
"""
from pathlib import Path
from collections import Counter, defaultdict
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from research_inventory import package_tables
from audit_object_properties import ordinary_exports
from audit_literal_contexts import audit as literal_audit, ancestry, symbolic
from extract_script_buffers import FILE_HASH

HASHES = dict(objects='8f2b6a8c7fe5fe7b58efa89d54655e757644582b145f9a447d56f4ec59dd2ae7',
              strings='11e46f9c1461945ece7e08bbdfe5c27ba09068e0cd429e2e35410bb741706617',
              classifications='4c7235a3917763a0ef82efd488542c2a2ed21266377aad2c90e0a2ecba6b19d6')
FIELD_OPCODES = {0, 1, 2, 0x47, 0x48}
DISPLAY = {'DrawText', 'SetText', 'ClipText', 'AddTextMessage', 'Message', 'SetMessage'}
LOOKUP = {'FindObject', 'DynamicLoadObject', 'ConsoleCommand', 'GetItemName', 'Localize'}


def subtree(tokens, index):
    end = index + 1
    while end < len(tokens) and tokens[end]['depth'] > tokens[index]['depth']:
        end += 1
    return tokens[index:end]


def field_reference(token, references, exports, imports=()):
    if token['opcode'] not in FIELD_OPCODES:
        return None
    matches = [r for r in references if r['offset'] == token['offset'] + 1 and r['kind'] == 'object']
    core.require(len(matches) == 1, 'field token reference mismatch')
    value = matches[0]['value']
    core.require(-len(imports) <= value <= len(exports), 'field reference bounds')
    if value <= 0:
        return dict(reference=value, name=imports[-value-1]['name'] if value else None,
                    field_class='unresolved-import-or-null', outer=None,
                    opcode=token['opcode'], token_offset=token['offset'])
    e = exports[value - 1]
    return dict(reference=value, name=e['name'], field_class=e['class'], outer=e['outer'],
                opcode=token['opcode'], token_offset=token['offset'])


def assignment_target(row, tokens, parents, references, exports, imports=()):
    lets = [t for t in parents[row['token_offset']] if t['opcode'] == 0x0f]
    if not lets:
        return None
    let = lets[-1]
    ix = next(i for i, t in enumerate(tokens) if t['offset'] == let['offset'])
    core.require(ix + 1 < len(tokens), 'assignment lacks target')
    left = subtree(tokens, ix + 1)
    core.require(left[0]['depth'] == let['depth'] + 1, 'assignment target depth')
    right_ix = ix + 1 + len(left)
    core.require(right_ix < len(tokens) and tokens[right_ix]['depth'] == let['depth'] + 1,
                 'assignment lacks RHS')
    right = subtree(tokens, right_ix)
    core.require(any(t['offset'] == row['token_offset'] for t in right), 'literal not in assignment RHS')
    fields = [f for t in left if (f := field_reference(t, references, exports, imports))]
    # Complex array/member lvalues preserve all references but do not gain roles.
    return dict(assignment_offset=let['offset'], lhs_start=left[0]['offset'], lhs_tokens=len(left),
                fields=fields, simple_field=len(left) == 1 and len(fields) == 1)


def classify_assignment(row, target, uses):
    if row['semantic_classification'] != 'unresolved':
        return dict(row)
    item = dict(row, assignment_target=target, field_uses=uses,
                reaching_definition_verified=False, runtime_visibility_verified=False,
                editable=False, backend_eligible=False)
    if not target or not target['simple_field'] or target['fields'][0]['field_class'] != 'StrProperty':
        return item
    local = [u for u in uses if u['object_id'] == row['id'].split('/string/')[0] and not u['assignment_lhs']]
    symbols = {s for u in local for call in u['calls'] for s in call.get('symbols', [])}
    display, lookup = symbols & DISPLAY, symbols & LOOKUP
    if display and lookup:
        item['semantic_reason'] = 'mixed-display-and-lookup-field-uses-retained'
    elif display:
        category = 'diagnostic-text-candidate' if row['owner'] == 'DisplayDebug' else 'visible-text-candidate'
        item.update(semantic_classification=category,
                    semantic_reason='same-function-string-field-display-context-not-reaching-definition',
                    field_consumer_symbols=sorted(display))
    elif lookup:
        item.update(semantic_classification='internal-lookup-or-command-candidate',
                    semantic_reason='same-function-string-field-lookup-context-not-reaching-definition',
                    field_consumer_symbols=sorted(lookup))
    return item


def audit(file, objects_path, strings_path, classifications_path, out):
    inputs = [(file, FILE_HASH), (objects_path, HASHES['objects']), (strings_path, HASHES['strings']),
              (classifications_path, HASHES['classifications'])]
    for p, h in inputs:
        core.require(core.file_digest(p) == h, 'input identity mismatch')
    out = core.output_directory(out)
    core.require(not any(out.iterdir()), 'output must be empty')
    literal_audit(file, objects_path, strings_path, out / 'reparsed-contexts')
    reparsed = {r['id']: r for r in json.loads((out / 'reparsed-contexts/contexts.json').read_text('utf8'))}
    rows = json.loads(classifications_path.read_text('utf8'))
    core.require(len({r['id'] for r in rows}) == len(rows) and set(reparsed) == {r['id'] for r in rows}, 'constant set mismatch')
    for row in rows:
        core.require(all(row[k] == v for k, v in reparsed[row['id']].items() if k != 'semantic_classification'),
                     'classification/source context mismatch')
    objects = json.loads(objects_path.read_text('utf8'))
    by_id = {o['id']: o for o in objects}
    natives = defaultdict(set)
    for o in objects:
        if 'native_index' in o['tail']:
            natives[o['tail']['native_index']].add(o['export']['name'])
    afs = Afs.open(file)
    names = filename_toc(afs)
    packages = {}
    targets = {}
    selected = set()
    with file.open('rb') as stream:
        def package(name):
            if name not in packages:
                blob = afs.read_entry(names.index(name), stream)
                tables = package_tables(blob)
                packages[name] = (blob, tables, ordinary_exports(blob, tables))
            return packages[name]
        for row in rows:
            if row['semantic_classification'] != 'unresolved':
                continue
            obj = by_id[row['id'].split('/string/')[0]]
            blob, tables, exports = package(obj['package'])
            target = assignment_target(row, obj['script']['tokens'], ancestry(obj['script']['tokens']),
                                       obj['script']['references'], exports, tables['imports'])
            targets[row['id']] = target
            if target:
                selected.update((obj['package'], f['reference']) for f in target['fields'])
        uses = defaultdict(list)
        for obj in objects:
            blob, tables, exports = package(obj['package'])
            tokens = obj['script']['tokens']
            parents = ancestry(tokens)
            e = obj['export']
            serial = blob[e['offset']:e['offset'] + e['size']]
            for i, t in enumerate(tokens):
                if t['opcode'] not in FIELD_OPCODES:
                    continue
                f = field_reference(t, obj['script']['references'], exports, tables['imports'])
                key = (obj['package'], f['reference'])
                if key not in selected:
                    continue
                calls = [symbolic(a, serial, tables, natives) for a in parents[t['offset']]]
                calls = [c for c in calls if 'reference_kind' in c]
                lhs = False
                for let in parents[t['offset']]:
                    if let['opcode'] != 0xf:
                        continue
                    ix = next(j for j, x in enumerate(tokens) if x['offset'] == let['offset'])
                    lhs |= any(x['offset'] == t['offset'] for x in subtree(tokens, ix + 1))
                uses[key].append(dict(object_id=obj['id'], function=e['name'], token_offset=t['offset'],
                                      serial_sha256=obj['serial_sha256'], assignment_lhs=lhs, calls=calls))
    updated = []
    for row in rows:
        if row['id'] not in targets:
            updated.append(dict(row))
            continue
        target = targets[row['id']]
        found = [u for f in (target['fields'] if target else []) for u in uses[(row['package'], f['reference'])]]
        updated.append(classify_assignment(row, target, found))
    summary = dict(schema=1, constants=len(rows), objects_reparsed=len(objects),
                   assignment_targets=sum(t is not None for t in targets.values()),
                   simple_assignment_targets=sum(t is not None and t['simple_field'] for t in targets.values()),
                   fields_with_use_index=len(selected), field_use_occurrences=sum(len(u) for u in uses.values()),
                   reclassified=sum(a['semantic_classification'] != b['semantic_classification'] for a,b in zip(rows,updated)),
                   counts=dict(sorted(Counter(r['semantic_classification'] for r in updated).items())),
                   reaching_definition_verified=False, full_vm_semantics_verified=False,
                   runtime_visibility_verified=False, source_modified=False, complete_game_text=False,
                   coverage_review_complete=False, translation_gate='coverage-audit-pending')
    for name, value in [('classifications.json', updated), ('summary.json', summary)]:
        p = out / name
        p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', 'utf8')
        core.require(json.loads(p.read_text('utf8')) == value, 'JSON reopen mismatch')
    for p, h in inputs:
        core.require(core.file_digest(p) == h, 'input changed')
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('file', 'objects', 'strings', 'classifications', 'out'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(audit(a.file, a.objects, a.strings, a.classifications, a.out), sort_keys=True))
