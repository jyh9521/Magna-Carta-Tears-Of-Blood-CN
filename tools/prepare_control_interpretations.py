"""Derive source-bound literal dialogue rules for verified native text storage."""
from pathlib import Path
import argparse
import copy
import json
import struct
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('tools','lib','src')]
from font_poc import digest,archive_entries,require
from audit_literal_control_readings import audit
from audit_native_chat import source_match,validate_anchors as chat_anchors
from audit_native_fixed_dialogue import validate_field,validate_anchors as fixed_anchors
from audit_named_resource_data import SPECS,stride_address,item_lookup,validate_anchors as named_anchors
from research_native import ElfImage,ELF_SHA256
from localization.text import LITERAL_POLICY
from audit_literal_native_storage import validate_cdg,validate_tui,validate_native_anchors as literal_storage_anchors


def validate_binding(resource, entry, binding, original, image):
    kind = binding.get('kind')
    if kind == 'native-fpb-chat':
        require(resource['resource'].endswith('.fpb'), 'literal FPB kind mismatch')
        require(binding['source_resource'] == resource['resource']
                and binding['source_resource_sha256'] == resource['sha256']
                and all(binding[b] == entry[e] for b,e in [('id','id'),('source_offset','offset'),('source_bytes','source_bytes'),('source_sha256','source_sha256')]),
                'literal FPB source binding mismatch')
        return source_match(original,binding)
    if kind in ('native512-cht','native512-pod'):
        require(resource['resource'].endswith('.'+kind.removeprefix('native512-')), 'literal fixed kind mismatch')
        return validate_field(resource,entry,binding,original)
    if kind == 'native-cdg-description':
        return validate_cdg(resource,entry,binding,original,image)
    if kind == 'native-tui-main':
        return validate_tui(resource,entry,binding,original,image)
    require(kind == 'native-item-comment' and resource['resource'] == 'SHIP/00000953.itm', 'unsupported literal consumer')
    spec = SPECS['00000953.itm']
    require(digest(original) == resource['sha256'] == binding['resource_sha256'] == spec['sha256'], 'literal item resource mismatch')
    require(binding['resource'] == resource['resource'] and all(binding[k] == entry[k] for k in ('id','offset','source_bytes','source_sha256')), 'literal item span mismatch')
    require(len(original) == 8+spec['count']*spec['stride'] and struct.unpack_from('<II',original) == (spec['count'],spec['kind']), 'literal item geometry mismatch')
    i = binding['physical_index']
    require(type(i) is int and 0 <= i < spec['count'] and i == entry['record_index'] and entry['field_index'] == 1, 'literal item physical field mismatch')
    at = 8+i*594
    require(entry['offset'] == at+331 and binding['native_string_offset'] == 80, 'literal item Comment offset mismatch')
    key = struct.unpack_from('<I',original,at)[0]
    require(key == binding['record_key'] == entry['record_key'], 'literal item numeric key mismatch')
    slot = original[at+331:at+586];n = entry['source_bytes']
    require(0 < n < 255 and digest(slot[:n]) == entry['source_sha256'] and slot[n] == 0 and not any(slot[n:]), 'literal item source padding/hash mismatch')
    require(entry['slot_bytes'] == 255 and entry['slot_sha256'] == digest(slot), 'literal item full slot mismatch')
    require(image is not None, 'literal item native image missing')
    stride_address(image,'00000953.itm',i)
    keys = [struct.unpack_from('<I',original,8+j*594)[0] for j in range(spec['count'])]
    selected = max(j for j,k in enumerate(keys) if k == key)
    require(selected == i and item_lookup(image,keys,key) == 0xc000+100*i, 'literal item numeric lookup does not select field')
    return dict(native_string_offset=80,writable_bytes=255,numeric_key_verified=True,runtime_verified=False)


def derive(corpus, readings, bindings, members, terms, image):
    audit(corpus,readings,members,terms)
    require(bindings.get('schema') == 1, 'unsupported literal consumer schema')
    decisions = {e['id']:e for e in readings['entries']}
    derived = copy.deepcopy(corpus)
    index = {e['id']:(r,e) for r in derived['resources'] for e in r['entries']}
    selected,seen,evidence = [],set(),[]
    for b in bindings['bindings']:
        identity = b['id']
        require(identity in decisions and identity in index and identity not in seen, 'missing/duplicate literal binding identity')
        seen.add(identity);res,e = index[identity];d = decisions[identity]
        geometry = validate_binding(res,e,b,members[Path(res['resource']).name],image)
        if b['kind'] == 'native512-cht':
            e.update(observed_byte_capacity=511,trailer_bytes=geometry['preserved_tail_bytes'],trailer_sha256=geometry['preserved_tail_sha256'])
        e.update(controls='recognized',editable=True,backend_eligible=True,source_control_policy=LITERAL_POLICY,
            source_control_interpretation=dict(schema=1,original_controls='quarantined',raw_sha256=e['source_sha256'],
                reading_sha256=d['reading_sha256'],target_sha256=digest(d['target'].encode('utf8')),
                native_binding_sha256=digest(json.dumps(b,sort_keys=True,separators=(',',':')).encode('utf8')),
                native_source_span_verified=True,runtime_control_semantics_verified=False))
        selected.append(dict(id=identity,source_sha256=e['source_sha256'],target=d['target'],status='reviewed',reinsertion_policy='translate',
            context='Source-hashed literal structures and numeric values/order retained; bracket names canonical. Native text span bound independently; explicit field policy, default grammar unchanged. Runtime event/renderer layout not claimed.'))
        evidence.append(dict(id=identity,kind=b['kind'],geometry=geometry))
    previous = derived.get('literal_control_interpretations')
    derived['literal_control_interpretations'] = dict(fields=sum('source_control_policy' in e for r in derived['resources'] for e in r['entries']),
        input_source_corpus_modified=False,runtime_control_semantics_verified=False)
    if previous is not None:
        derived['literal_control_interpretations']['newly_selected_fields'] = len(selected)
        derived['literal_control_interpretations']['previous_interpretation_sha256'] = digest(json.dumps(previous,sort_keys=True,separators=(',',':')).encode('utf8'))
    return derived,dict(schema=1,locale=readings['locale'],entries=selected),evidence


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('corpus','readings','bindings','archive','elf','glossary','out'):
        p.add_argument('--'+name,type=Path,required=True)
    a = p.parse_args();readings = json.loads(a.readings.read_text('utf8'));bindings = json.loads(a.bindings.read_text('utf8'))
    require(digest(a.corpus.read_bytes()) == readings['source_corpus_sha256'] == bindings['source_corpus_sha256'], 'literal source corpus fingerprint mismatch')
    require(digest(a.archive.read_bytes()) == '09d2e4d1f72e40b5d12da7b872226c446a21dde12bf1601bb4dfe58887a5d33a', 'literal original archive mismatch')
    raw = a.elf.read_bytes();require(digest(raw) == ELF_SHA256, 'literal original ELF mismatch');image=ElfImage(raw)
    chat_anchors(image);fixed_anchors(image);named_anchors(image)
    if any(b['kind'] in ('native-cdg-description','native-tui-main') for b in bindings['bindings']):
        literal_storage_anchors(image)
    from validate_translation_batch import glossary_terms
    c,b,e = derive(json.loads(a.corpus.read_text('utf8')),readings,bindings,dict(archive_entries(a.archive)[1]),dict(glossary_terms(a.glossary)),image)
    c['literal_control_interpretations']['input_sha256'] = {str(q):digest(q.read_bytes()) for q in (a.corpus,a.readings,a.bindings,a.archive,a.elf,a.glossary)}
    a.out.mkdir(parents=True,exist_ok=False)
    for name,data in [('source-corpus.json',c),('selected-batch.json',b),('native-bindings.json',e)]:
        path=a.out/name;path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8');require(json.loads(path.read_text('utf8'))==data,'literal output reopen mismatch')
    print('CONTROL_INTERPRETATION_PASS fields='+str(len(b['entries']))+' source_bound_policy=true default_grammar_unchanged=true native_spans_verified=true input_corpus_unchanged=true runtime_verified=false')


if __name__ == '__main__':main()
