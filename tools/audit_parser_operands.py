"""Bind literal parser operands to reparsed switch/search contexts.

Operand classification is not execution, global grammar or visible-text proof.
Existing source constants and their contexts remain unchanged.
"""
from pathlib import Path
from collections import Counter
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'lib')]
import font_poc as core
from audit_literal_contexts import audit as reparse
from audit_compiled_field_contexts import HASHES
from extract_script_buffers import FILE_HASH

CLASSIFICATIONS_HASH = '6f0fd4358c2ef6ddb0552daf6e06b7f442d59c78a8dc6a44b8c79446e0a2378e'
SCOPES = {
    'FILE/MrtsEngine.u/export/6001': ('GetTextNum', {'InStrA', 'MidA', 'RemoveSpecialWordA'}),
    'FILE/MrtsEngine.u/export/7196': ('ProcessSpecialWord', {'InStrA', 'MidA', 'RemoveSpecialWord', 'SplitRowAt'}),
    'FILE/UWindow.u/export/1260': ('ParseAmpersand', {'InStr', 'Mid'}),
}


def operand_role(row):
    """Classify only evidenced operand positions inside reviewed parser scopes."""
    owner_id = row['id'].split('/string/')[0]
    if owner_id not in SCOPES:
        return None
    core.require(row['owner'] == SCOPES[owner_id][0], 'parser owner mismatch')
    if row['semantic_classification'] != 'unresolved':
        return None
    nearest = row['call_context'][-1].get('symbols', []) if row['call_context'] else []
    text = row['text']
    if row['parent_opcode'] == 0x0a and len(text) == 1 and row['owner'] != 'ParseAmpersand':
        return 'parser-switch-discriminator'
    if set(nearest) & {'InStrA', 'InStr'} and text in {'$', '&'}:
        return 'parser-delimiter-search'
    if row['owner'] == 'ParseAmpersand' and nearest == ['EqualEqual_StrStr'] and text == '&':
        return 'parser-escape-comparison'
    if row['owner'] == 'ProcessSpecialWord' and nearest == ['Concat_StrStr'] and text == '$W$E':
        return 'parser-generated-control-sequence'
    return None


def review(rows):
    ids = set()
    result = []
    for row in rows:
        core.require(row['id'] not in ids, 'duplicate compiled constant'); ids.add(row['id'])
        role = operand_role(row)
        item = dict(row)
        if role:
            item.update(semantic_classification='internal-parser-operand-candidate',
                        semantic_reason='reviewed-parser-bounded-literal-operand',
                        parser_operand_role=role, runtime_visibility_verified=False,
                        full_parser_semantics_verified=False, editable=False, backend_eligible=False)
        result.append(item)
    return result


def audit(file, objects, strings, classifications, out):
    inputs = [(file, FILE_HASH), (objects, HASHES['objects']), (strings, HASHES['strings']),
              (classifications, CLASSIFICATIONS_HASH)]
    for p, h in inputs: core.require(core.file_digest(p) == h, 'input identity mismatch')
    out = core.output_directory(out); core.require(not any(out.iterdir()), 'output must be empty')
    reparse(file, objects, strings, out / 'reparsed-contexts')
    original = json.loads(classifications.read_text('utf8'))
    contexts = {x['id']: x for x in json.loads((out / 'reparsed-contexts/contexts.json').read_text('utf8'))}
    core.require(len(original) == len(contexts) == 1207, 'compiled inventory mismatch')
    for row in original:
        core.require(all(row[k] == v for k, v in contexts[row['id']].items()
                         if k != 'semantic_classification'), 'reparsed source/context mismatch')
    obj = {x['id']: x for x in json.loads(objects.read_text('utf8'))}
    for owner, (_, required) in SCOPES.items():
        core.require(owner in obj, 'missing parser object')
        # Every required consumer appears as a resolved ancestor of a literal;
        # independent call inventory is collected from the complete script below.
        from cri_afs import Afs
        from afs import filename_toc
        from research_inventory import package_tables
        from audit_literal_contexts import symbolic
        from collections import defaultdict
        natives = defaultdict(set)
        for o in obj.values():
            if 'native_index' in o['tail']: natives[o['tail']['native_index']].add(o['export']['name'])
        afs = Afs.open(file); names = filename_toc(afs); o = obj[owner]
        with file.open('rb') as stream: blob = afs.read_entry(names.index(o['package']), stream)
        tables = package_tables(blob); e = o['export']; serial = blob[e['offset']:e['offset'] + e['size']]
        core.require(core.digest(serial) == o['serial_sha256'], 'parser serial mismatch')
        calls = [symbolic(t, serial, tables, natives) for t in o['script']['tokens']]
        symbols = {s for c in calls for s in c.get('symbols', [])}
        core.require(required <= symbols, 'parser required call set mismatch')
        (out / (str(e['index']) + '-parser.json')).write_text(json.dumps(dict(
            id=owner, serial_sha256=o['serial_sha256'], required_symbols=sorted(required),
            calls=calls, parser_semantics_complete=False), ensure_ascii=False, indent=2) + '\n', 'utf8')
    result = review(original)
    summary = dict(constants=len(result), objects_reparsed=len(obj), parser_scopes=len(SCOPES),
                   reclassified=sum(a != b for a, b in zip(original, result)),
                   counts=dict(sorted(Counter(x['semantic_classification'] for x in result).items())),
                   operand_roles=dict(sorted(Counter(x['parser_operand_role'] for x in result
                                                      if 'parser_operand_role' in x).items())),
                   full_parser_semantics_verified=False, runtime_visibility_verified=False,
                   source_modified=False, coverage_review_complete=False, complete_game_text=False)
    for name, value in [('classifications.json', result), ('summary.json', summary)]:
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', 'utf8')
        core.require(json.loads((out / name).read_text('utf8')) == value, 'output reopen mismatch')
    for p, h in inputs: core.require(core.file_digest(p) == h, 'input changed')
    for p in out.glob('*-parser.json'): json.loads(p.read_text('utf8'))
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for n in ('file', 'objects', 'strings', 'classifications', 'out'):
        p.add_argument('--' + n, type=Path, required=True)
    a = p.parse_args(); print(json.dumps(audit(a.file, a.objects, a.strings, a.classifications, a.out), sort_keys=True))
