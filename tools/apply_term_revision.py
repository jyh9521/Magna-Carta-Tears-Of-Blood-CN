"""Apply fingerprint-bound, same-size terminology edits to translated AFS copies.

Offsets and old/new bytes must be explicitly reviewed in a revision profile.
This backend does not infer text locations or change encodings/engine code.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/p) for p in ('tools', 'lib', 'src')]
import font_poc as core
from build_locale import checked_archive
from bundle_resource import overlay_segments
from translate.celfid import decompress_chunked, recompress_chunked


def patch_bound_bytes(blob, record):
    core.require(core.digest(blob) == record['baseline_sha256'], 'resource baseline mismatch')
    result = bytearray(blob)
    end = 0
    for edit in sorted(record['edits'], key=lambda q: q['offset']):
        at = edit['offset']; old = bytes.fromhex(edit['old_hex']); new = bytes.fromhex(edit['new_hex'])
        core.require(old and len(old) == len(new), 'revision must preserve encoded length')
        core.require(end <= at and at+len(old) <= len(blob), 'invalid/overlapping revision offsets')
        core.require(blob[at:at+len(old)] == old, 'revision old bytes mismatch')
        core.require(any(a <= at and at+len(old) <= b for a,b in record['allowed_spans']),
                     'revision outside audited text span')
        core.require(blob[end:at] == result[end:at], 'non-target bytes changed')
        result[at:at+len(old)] = new; end = at+len(old)
    core.require(blob[end:] == result[end:], 'non-target tail changed')
    core.require(core.digest(result) == record['modified_sha256'], 'revision output mismatch')
    return bytes(result)


def apply(file, ship, profile, out):
    core.require(profile['schema'] == 1, 'unsupported revision schema')
    for name,path in [('FILE.AFS',file),('SHIP.AFS',ship)]:
        core.require(core.file_digest(path) == profile['archives'][name]['sha256'], 'archive baseline mismatch')
    _,fe = core.archive_entries(file); _,se = core.archive_entries(ship)
    f,s = dict(fe),dict(se); bundle = decompress_chunked(f['celfid.lix'])
    overrides,segments = {},[]
    for row in profile['resources']:
        name = row['resource'];old = s[name];new = patch_bound_bytes(old,row);overrides[name.lower()] = new
    for row in profile['cache']:
        name = row['resource']; old = s[name]; new = overrides[name.lower()]
        for offset in row['offsets']:
            segments.append(dict(label=name,offset=offset,original=old,modified=new))
    core.require(core.digest(bundle) == profile['bundle_sha256'], 'cache baseline mismatch')
    if segments:
        bundle,cache = overlay_segments(bundle,segments,expected_sha256=profile['bundle_sha256'])
    else:
        cache = []
    core.require(core.digest(bundle) == profile['modified_bundle_sha256'], 'cache output mismatch')
    for term in profile['terms']:
        old = bytes.fromhex(term['old_hex'])
        core.require(old not in bundle, 'old term remains in cache')
        core.require(all(old not in overrides.get(n.lower(),b) for n,b in se), 'old term remains in SHIP')
        core.require(all(old not in b for n,b in fe if n != 'celfid.lix'), 'unhandled FILE term')
    compressed = recompress_chunked(bundle)
    core.require(decompress_chunked(compressed) == bundle, 'cache recompression mismatch')
    fo = {'celfid.lix':compressed}
    out = core.output_directory(out);core.require(not any(out.iterdir()), 'output not empty')
    reports = {}
    for name,path,entries,edits in [('FILE.AFS',file,fe,fo),('SHIP.AFS',ship,se,overrides)]:
        edits[entries[0][0].lower()] = core.manifest_overlay(entries[0][1],{n:len(b) for n,b in edits.items()})
        reports[name] = checked_archive(path,out/name,edits)
    report = dict(schema=1,resources=len(profile['resources']),occurrences=sum(len(r['edits']) for r in profile['resources']),
                  cache_copies=len(cache),archives=reports,archive_sha256={n:core.file_digest(out/n) for n in reports},
                  residual_old_terms=0,encoding_changed=False,runtime_verified=False)
    (out/'term-revision.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
    print('TERM_REVISION_PASS resources='+str(report['resources'])+' occurrences='+str(report['occurrences'])+
          ' cache_copies='+str(report['cache_copies'])+' residual_old_terms=0')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('file','ship','profile','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();apply(a.file,a.ship,json.loads(a.profile.read_text('utf8')),a.out)


if __name__ == '__main__':main()
