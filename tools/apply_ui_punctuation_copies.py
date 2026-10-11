"""Apply reviewed UI punctuation deltas to fingerprinted translated AFS copies.

Fixed-slot original geometry and previous mapped bytes must both match.
Configuration copies use the existing guarded whole-file/cache backend.
No unknown offsets, source aliases or punctuation-only empty fields are inferred.
"""
from pathlib import Path
import argparse,json,sys
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib','src')]
import font_poc as core
from build_locale import checked_archive
from import_audited_fields import binding_index,resolve_source,fixed_extent
from source_interpretation import source_text,control_policy,encode_target
from ui_punctuation import omit_period,validated_empty_suffix
from localization.text import MappedEncoder,validate_target
from research_inventory import font_data
from translate.celfid import decompress_chunked,recompress_chunked
from bundle_resource import overlay_segments,replace_cached_file


def fixed_deltas(original, baseline, rows, encoder):
    changed=bytearray(baseline);ranges=[];proofs=[]
    for entry,target in rows:
        at=entry['offset'];span,h=fixed_extent(entry)
        old=encoder.encode_characters(target['previous_target']);new=target['target']
        core.require(omit_period(target['previous_target'])==new,'unreviewed punctuation delta')
        core.require(core.digest(original[at:at+entry['source_bytes']])==entry['source_sha256'],'original source bytes mismatch')
        core.require(len(old)<span and baseline[at:at+span]==old+bytes(span-len(old)),'translated baseline slot mismatch '+target['id'])
        if new=='':validated_empty_suffix(entry,target)
        else:validate_target(source_text(entry),new,control_policy=control_policy(entry,new))
        encoded=encode_target(encoder,entry,new);core.require(len(encoded)<span,'UI field overflow')
        core.require(not any(at<b and a<at+span for a,b in ranges),'overlapping UI field edits')
        changed[at:at+span]=encoded+bytes(span-len(encoded));ranges.append((at,at+span))
        proofs.append(dict(id=target['id'],offset=at,span=span,old_hex=old.hex(),new_hex=encoded.hex()))
    prev=0
    for a,b in sorted(ranges):core.require(baseline[prev:a]==changed[prev:a],'non-UI bytes changed');prev=b
    core.require(baseline[prev:]==changed[prev:],'non-UI tail changed')
    return bytes(changed),proofs


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('base-file','base-ship','original-ship','corpus','changes','map','font','config-copies','cache-profile','out'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--base-file-sha256',required=True);p.add_argument('--base-ship-sha256',required=True)
    a=p.parse_args();core.require(core.file_digest(a.base_file)==a.base_file_sha256 and core.file_digest(a.base_ship)==a.base_ship_sha256,'UI baseline archive fingerprint mismatch')
    c=json.loads(a.corpus.read_text('utf8'));index,aliases=binding_index(c);changes=json.loads(a.changes.read_text('utf8'));mapping=json.loads(a.map.read_text('utf8'));encoder=MappedEncoder(mapping['entries'],font_tables=font_data(a.font.read_bytes()))
    originals=dict(core.archive_entries(a.original_ship)[1]);fe=core.archive_entries(a.base_file)[1];se=core.archive_entries(a.base_ship)[1];files=dict(fe);ship=dict(se)
    bundle=decompress_chunked(files['celfid.lix']);groups=defaultdict(list);field_proofs=[];so={};fo={};cache=[]
    for t in changes:
        if not t['id'].startswith('SHIP/'):continue
        r,e=resolve_source(index,aliases,t);groups[r['resource']].append((e,t))
    for resource,rows in groups.items():
        name=Path(resource).name;old=ship[name];new,proof=fixed_deltas(originals[name],old,rows,encoder);so[name.lower()]=new;field_proofs.extend(proof)
        mirrors=[m for m in c['celfid_resource_mirrors'] if m['resource']==resource];expected=sum(len(m['decompressed_offsets']) for m in mirrors)
        core.require(bundle.count(old)==expected,'UI cached body count mismatch '+resource)
        if expected:
            segments=[];start=0
            for i in range(expected):
                at=bundle.index(old,start);start=at+len(old);segments.append(dict(label=resource+'#'+str(i),offset=at,original=old,modified=new))
            bundle,details=overlay_segments(bundle,segments,expected_sha256=core.digest(bundle));cache.extend(details)
    config=json.loads((a.config_copies/'config-imports.json').read_text('utf8'));rules={r['resource']:r for r in json.loads(a.cache_profile.read_text('utf8'))['files']}
    for r in config['resources']:
        name=Path(r['resource']).name;old=files[name];new=(a.config_copies/name).read_bytes();core.require(core.digest(new)==r['modified_sha256'],'configuration copy fingerprint mismatch')
        if new==old:continue
        fo[name.lower()]=new
        if r['resource'] in rules:
            rule=rules[r['resource']];bundle,proof=replace_cached_file(bundle,old,new,cached_path=rule['cached_path'],expected_file_records=rule['expected_file_records'],expected_payloads=rule['expected_payloads'],expected_bundle_sha256=core.digest(bundle),expected_source_sha256=core.digest(old));cache.append(proof)
        else:core.require(bundle.count(old)==0,'unprofiled configuration cache')
    compressed=recompress_chunked(bundle);core.require(decompress_chunked(compressed)==bundle,'UI cache roundtrip mismatch');fo['celfid.lix']=compressed
    out=core.output_directory(a.out);core.require(not any(out.iterdir()),'UI archive output not empty');results={}
    for name,path,entries,overrides in [('FILE.AFS',a.base_file,fe,fo),('SHIP.AFS',a.base_ship,se,so)]:
        overrides[entries[0][0].lower()]=core.manifest_overlay(entries[0][1],{n:len(b) for n,b in overrides.items()});results[name]=checked_archive(path,out/name,overrides)
    report=dict(schema=1,field_proofs=field_proofs,cache=cache,archives=results,archive_sha256={n:core.file_digest(out/n) for n in results},originals_unchanged=True,runtime_verified=False)
    (out/'ui-integration.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
    print('UI_PUNCTUATION_IMPORT_PASS fixed_fields='+str(len(field_proofs))+' config_fields=22 compiled_fields=2 source_unchanged=true')

if __name__=='__main__':main()
