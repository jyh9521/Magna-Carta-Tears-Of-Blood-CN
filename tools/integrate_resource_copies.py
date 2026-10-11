"""Integrate fingerprinted resource copies and fonts into separate AFS candidates.

Whole, equal-size SHIP mirrors use the original conservative backend. Cached
configuration files additionally require explicit padded-name/count profiles.
Font package/bundle builders handle their explicit growing package fragments.
No ISO is generated and no runtime-role decision is inferred.
"""
from pathlib import Path
import argparse
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'src'),str(ROOT/'lib')]
import font_poc as core
from bundle_resource import overlay_segments,replace_cached_file
from build_locale import checked_archive
from translate.celfid import decompress_chunked,recompress_chunked


def validate_original_mirrors(bundle,owners,mirrors):
    for mirror in mirrors:
        prefix=mirror['resource'].split('/',1)[0]
        core.require(prefix in owners,'unsupported source mirror owner')
        name=Path(mirror['resource']).name
        core.require(name in owners[prefix],'source mirror member missing')
        old=owners[prefix][name]
        core.require(core.digest(old)==mirror['sha256'],'original cached source fingerprint mismatch')
        for at in mirror['decompressed_offsets']:
            core.require(type(at) is int and 0<=at<=len(bundle)-len(old),'original cache offset bounds')
            core.require(core.digest(bundle[at:at+len(old)])==mirror['sha256'],'original cache offset fingerprint mismatch')


def cache_overlay(bundle,originals,copies,mirrors):
    known={m['resource']:m for m in mirrors}
    core.require(len(known)==len(mirrors),'duplicate mirror resource identity')
    segments=[];summary=[]
    for resource,new in sorted(copies.items()):
        name=Path(resource).name
        core.require(name in originals,'import resource missing from source archive')
        old=originals[name];mirror=known.get(resource)
        expected=len(mirror['decompressed_offsets']) if mirror else 0
        if mirror:core.require(core.digest(old)==mirror['sha256'],'catalog mirror fingerprint mismatch')
        core.require(bundle.count(old)==expected,'unexpected cached copy count: '+resource)
        if not expected:continue
        core.require(len(old)==len(new),'cached resource resizing requires a separate backend')
        start=0
        for i in range(expected):
            at=bundle.index(old,start);start=at+len(old)
            segments.append(dict(label=resource+'#'+str(i),offset=at,original=old,modified=new))
        summary.append(dict(resource=resource,copies=expected,original_sha256=core.digest(old),modified_sha256=core.digest(new),bytes=len(new)))
    if segments:
        modified,details=overlay_segments(bundle,segments,expected_sha256=core.digest(bundle))
    else:modified,details=bundle,[]
    for row in details:
        core.require(core.digest(modified[row['modified_offset']:row['modified_offset']+row['modified_size']])==row['modified_sha256'],'cached mirror readback mismatch')
    return modified,dict(resources=summary,segments=details,cached_resources=len(summary),cached_copies=len(segments),unselected_bytes_preserved=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('file-archive','ship-archive','corpus','imports','font-package-dir','font-bundle-dir','out'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--file-sha256',required=True)
    p.add_argument('--config-imports',type=Path)
    p.add_argument('--cache-file-profile',type=Path)
    args=p.parse_args()
    corpus=json.loads(args.corpus.read_text('utf8'));imports=json.loads(args.imports.read_text('utf8'))
    package=json.loads((args.font_package_dir/'font-package.json').read_text('utf8'))
    bundle_report=json.loads((args.font_bundle_dir/'font-bundle.json').read_text('utf8'))
    core.require(core.file_digest(args.file_archive)==args.file_sha256,'original FILE.AFS fingerprint mismatch')
    core.require(core.file_digest(args.ship_archive)==imports['archive_sha256'],'original SHIP.AFS fingerprint mismatch')
    core.require(core.file_digest(args.corpus)==imports['corpus_sha256'],'import corpus fingerprint mismatch')
    core.require(corpus['iso_sha256']==package['iso_sha256']==bundle_report['iso_sha256'],'artifact source ISO mismatch')
    _,file_entries=core.archive_entries(args.file_archive);_,ship_entries=core.archive_entries(args.ship_archive)
    files=dict(file_entries);ship=dict(ship_entries)
    core.require(core.digest(files['MrtsEngine.u'])==package['original_sha256'],'original engine fingerprint mismatch')
    engine=(args.font_package_dir/'MrtsEngine.modified.u').read_bytes()
    core.require(core.digest(engine)==package['modified_sha256']==bundle_report['package_sha256'],'modified engine fingerprint mismatch')
    original_bundle=decompress_chunked(files['celfid.lix'])
    core.require(core.digest(original_bundle)==bundle_report['original_sha256'],'original bundle fingerprint mismatch')
    bundle=(args.font_bundle_dir/'bundle.modified.bin').read_bytes()
    core.require(core.digest(bundle)==bundle_report['modified_sha256'],'font bundle fingerprint mismatch')
    copies={}
    for row in imports['resources']:
        resource=row['resource'];name=Path(resource).name
        core.require(resource.startswith('SHIP/') and resource not in copies and name in ship,'invalid import resource identity')
        core.require(core.digest(ship[name])==row['original_sha256'],'import original resource mismatch')
        data=(args.imports.parent/name).read_bytes()
        core.require(core.digest(data)==row['modified_sha256'],'import modified resource mismatch')
        copies[resource]=data
    # Prove frozen mirror offsets against the original stream before locating
    # them in the font-grown stream. Never assume old physical offsets survived.
    validate_original_mirrors(original_bundle,{'SHIP':ship,'FILE':files},corpus['celfid_resource_mirrors'])
    modified_bundle,cache=cache_overlay(bundle,ship,copies,corpus['celfid_resource_mirrors'])
    config_overrides={};config_fields=0;file_cache=[]
    if args.config_imports:
        core.require(args.cache_file_profile is not None,'configuration cache profile required')
        config=json.loads(args.config_imports.read_text('utf8'))
        profile=json.loads(args.cache_file_profile.read_text('utf8'));rules={r['resource']:r for r in profile['files']}
        core.require(len(rules)==len(profile['files']),'duplicate cached file profile identity')
        core.require(config['archive_sha256']==args.file_sha256 and config['corpus_sha256']==imports['corpus_sha256'],'configuration source identity mismatch')
        core.require(config['map_sha256']==imports['map_sha256'] and config['font_sha256']==imports['font_sha256'],'configuration/SHIP font mapping mismatch')
        known={m['resource']:m for m in corpus['celfid_resource_mirrors']}
        for row in config['resources']:
            resource=row['resource'];name=Path(resource).name
            core.require(resource.startswith('FILE/') and name in files and name.lower() not in config_overrides,'invalid configuration member identity')
            original=files[name];data=(args.config_imports.parent/name).read_bytes()
            core.require(core.digest(original)==row['original_sha256'] and core.digest(data)==row['modified_sha256'],'configuration copy fingerprint mismatch')
            expected=len(known[resource]['decompressed_offsets']) if resource in known else 0
            core.require(modified_bundle.count(original)==expected,'unexpected configuration cached body count')
            if expected:
                core.require(resource in rules,'missing observed cached file profile')
                rule=rules[resource]
                core.require(rule['source_sha256']==row['original_sha256'] and rule['source_bytes']==len(original) and rule['expected_payloads']==expected,'cached file profile source/count mismatch')
                modified_bundle,details=replace_cached_file(modified_bundle,original,data,
                    cached_path=rule['cached_path'],expected_file_records=rule['expected_file_records'],expected_payloads=expected,
                    expected_bundle_sha256=core.digest(modified_bundle),expected_source_sha256=rule['source_sha256'])
                file_cache.append(dict(resource=resource,**details))
            config_overrides[name.lower()]=data;config_fields+=row['selected_fields']
    compressed=recompress_chunked(modified_bundle)
    core.require(decompress_chunked(compressed)==modified_bundle,'integrated bundle compression roundtrip mismatch')
    file_overrides={'mrtsengine.u':engine,'celfid.lix':compressed}
    core.require(not set(file_overrides)&set(config_overrides),'configuration override collides with package/bundle')
    file_overrides.update(config_overrides)
    ship_overrides={Path(resource).name.lower():data for resource,data in copies.items()}
    core.require(len(ship_overrides)==len(copies),'case-folded resource identity collision')
    for entries,overrides in [(file_entries,file_overrides),(ship_entries,ship_overrides)]:
        overrides[entries[0][0].lower()]=core.manifest_overlay(entries[0][1],{n:len(b) for n,b in overrides.items()})
    out=core.output_directory(args.out)
    changes={}
    for name,source,overrides in [('FILE.AFS',args.file_archive,file_overrides),('SHIP.AFS',args.ship_archive,ship_overrides)]:
        changes[name]=checked_archive(source,out/name,overrides)
    (out/'bundle.modified.bin').write_bytes(modified_bundle)
    (out/'celfid.modified.lix').write_bytes(compressed)
    report=dict(iso_sha256=package['iso_sha256'],import_report_sha256=core.file_digest(args.imports),font_package_sha256=core.digest(engine),
                integrated_bundle_sha256=core.digest(modified_bundle),integrated_compressed_sha256=core.digest(compressed),
                imported_resources=len(copies),imported_fields=sum(x['selected_fields'] for x in imports['resources']),
                cache=cache,afs_changes=changes,archive_sha256={n:core.file_digest(out/n) for n in changes},
                source_archive_sha256={'FILE.AFS':args.file_sha256,'SHIP.AFS':imports['archive_sha256']},
                iso_generated=False,runtime_verified=False,full_game_scope_complete=False)
    report.update(config_imported_resources=len(config_overrides),config_imported_fields=config_fields,
                  total_imported_resources=len(copies)+len(config_overrides),total_imported_fields=report['imported_fields']+config_fields,
                  file_cache=file_cache)
    if args.config_imports:
        report.update(config_import_report_sha256=core.file_digest(args.config_imports),cache_file_profile_sha256=core.file_digest(args.cache_file_profile))
    core.require(core.file_digest(args.file_archive)==args.file_sha256 and core.file_digest(args.ship_archive)==imports['archive_sha256'],'original archive changed')
    (out/'integration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print('RESOURCE_AFS_INTEGRATION_PASS resources='+str(len(copies))+' fields='+str(report['imported_fields'])+' config_resources='+str(len(config_overrides))+' config_fields='+str(config_fields)+' file_cache_resources='+str(len(file_cache))+' cached_resources='+str(cache['cached_resources'])+' compression_roundtrip=true iso_generated=false')


if __name__=='__main__':main()
