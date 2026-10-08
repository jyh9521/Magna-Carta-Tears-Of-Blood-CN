"""Build a three-string expanded-font PoC with upstream AFS/ISO writers."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'src')]
import font_poc as core
from build_locale import checked_archive, estimate_widths
from bundle_resource import overlay_segments
from localization.text import MappedEncoder,rewrite_fpb,rewrite_fixed_slot
from research_inventory import package_tables,font_data
from translate.celfid import decompress_chunked,recompress_chunked
from iso import patch_iso
from iso_validation import verify_iso_overlay
from udf_overlay import plan_udf_overlay,apply_udf_overlay
from name_slot_overlay import apply_name_slots


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--iso',type=Path,required=True)
    p.add_argument('--expansion-dir',type=Path,required=True)
    p.add_argument('--package-dir',type=Path,required=True)
    p.add_argument('--bundle-dir',type=Path,required=True)
    p.add_argument('--locale',type=Path,default=ROOT/'locales/zh-CN/poc-text.json')
    p.add_argument('--out',type=Path,default=ROOT/'build/expanded-text-poc')
    args=p.parse_args();locale=json.loads(args.locale.read_text('utf8'))
    game=json.loads((ROOT/locale['game_profile']).read_text('utf8'))
    core.require(core.file_digest(args.iso)==game['expected_iso_sha256'],'ISO fingerprint mismatch')
    out=core.output_directory(args.out)
    package_report=json.loads((args.package_dir/'font-package.json').read_text('utf8'))
    bundle_report=json.loads((args.bundle_dir/'font-bundle.json').read_text('utf8'))
    expansion=json.loads((args.expansion_dir/'font-expansion.json').read_text('utf8'))
    for report in (package_report,bundle_report,expansion):core.require(report['iso_sha256']==game['expected_iso_sha256'],'artifact ISO mismatch')
    engine=(args.package_dir/'MrtsEngine.modified.u').read_bytes()
    bundle=(args.bundle_dir/'bundle.modified.bin').read_bytes()
    core.require(core.digest(engine)==package_report['modified_sha256']==bundle_report['package_sha256'],'package identity mismatch')
    core.require(core.digest(bundle)==bundle_report['modified_sha256'],'bundle identity mismatch')
    mapping=json.loads((args.expansion_dir/'experimental-map.json').read_text('utf8'))
    fonts={e['name']:engine[e['offset']:e['offset']+e['size']] for e in package_tables(engine)['exports'] if e['class']=='Font' and e['name'] in game['fonts']}
    core.require(set(fonts)==set(game['fonts']),'expanded Fonts missing')
    encoder=None
    for name,serial in fonts.items():
        core.require(core.digest(serial)==expansion['fonts'][name]['modified_sha256'] and bundle.count(serial)==1,'expanded Font copy mismatch')
        encoder=MappedEncoder(mapping['entries'],font_tables=font_data(serial))
    core.require(len(locale['entries'])==3 and sorted(r['kind'] for r in locale['entries'])==['fixed-display-slot','fpb','fpb'],'unsupported PoC targets')
    core.require(len({r['id'] for r in locale['entries']})==3,'duplicate target IDs')
    for record in locale['entries']:
        expected=(f"SHIP/{game['fpb_resource']}/seq/{record['seq']}" if record['kind']=='fpb'
                  else f"SHIP/{game['ui_resource']}/record/{game['ui']['record_id']}")
        core.require(record['id']==expected,'target ID/profile mismatch')
    encoder.validate_coverage([r['target'] for r in locale['entries']])
    original=core.iso_files(args.iso,['FILE.AFS','SHIP.AFS'])
    for name,data in original.items():(out/('original-'+name)).write_bytes(data)
    _,fe=core.archive_entries(out/'original-FILE.AFS');_,se=core.archive_entries(out/'original-SHIP.AFS')
    files,ship=dict(fe),dict(se)
    core.require(core.digest(files['MrtsEngine.u'])==game['expected_engine_sha256'],'original engine mismatch')
    fpb,ui=ship[game['fpb_resource']],ship[game['ui_resource']]
    core.require(core.digest(fpb)==game['expected_fpb_sha256'] and core.digest(ui)==game['expected_ui_sha256'],'original text mismatch')
    targets={r['seq']:r['target'] for r in locale['entries'] if r['kind']=='fpb'}
    core.require(set(targets)=={0,2},'unexpected FPB target windows')
    new_fpb,fpb_info=rewrite_fpb(fpb,targets,encoder)
    core.require(len(new_fpb)>len(fpb),'FPB growth missing')
    ui_target=next(r['target'] for r in locale['entries'] if r['kind']=='fixed-display-slot')
    new_ui,ui_info=rewrite_fixed_slot(ui,game['ui'],ui_target,encoder)
    widths={name:estimate_widths(ui_target,encoder,serial) for name,serial in fonts.items()}
    budget=next(r['max_estimated_pixels'] for r in locale['entries'] if r['kind']=='fixed-display-slot')
    core.require(all(max(values)<=budget for values in widths.values()),'UI width budget exceeded')
    core.require(bundle.count(ui)==1,'UI bundle copy not unique')
    new_bundle,ui_segments=overlay_segments(bundle,[dict(label='ui',offset=bundle.index(ui),original=ui,modified=new_ui)],expected_sha256=bundle_report['modified_sha256'])
    name_overrides,new_bundle,name_info=apply_name_slots(ship,new_bundle,encoder,locale.get('name_slot_overlays',[]))
    compressed=recompress_chunked(new_bundle);core.require(decompress_chunked(compressed)==new_bundle,'compression round trip mismatch')
    fover={'mrtsengine.u':engine,'celfid.lix':compressed};sover={game['fpb_resource'].lower():new_fpb,game['ui_resource'].lower():new_ui}
    core.require(not set(sover).intersection(name_overrides),'name overlay collides with text target')
    sover.update(name_overrides)
    for entries,overrides in [(fe,fover),(se,sover)]:overrides[entries[0][0].lower()]=core.manifest_overlay(entries[0][1],{n:len(b) for n,b in overrides.items()})
    changes={n:checked_archive(out/('original-'+n),out/n,overrides) for n,overrides in [('FILE.AFS',fover),('SHIP.AFS',sover)]}
    replacements={'/FILE.AFS':out/'FILE.AFS','/SHIP.AFS':out/'SHIP.AFS'}
    udf_plan=plan_udf_overlay(args.iso,replacements)
    branches=patch_iso(args.iso,out/'MODIFIED_FILE.iso',replacements)
    apply_udf_overlay(out/'MODIFIED_FILE.iso',udf_plan)
    validation=verify_iso_overlay(args.iso,out/'MODIFIED_FILE.iso',replacements,udf_plan=udf_plan)
    core.require(branches==(validation['in_place'],validation['relocated']),'ISO branch mismatch')
    recovered=core.iso_files(out/'MODIFIED_FILE.iso',['FILE.AFS','SHIP.AFS'])
    for name,data in recovered.items():core.require(data==(out/name).read_bytes(),'ISO archive readback mismatch')
    counts={font_data(serial)['glyphs'] for serial in fonts.values()};core.require(len(counts)==1,'Font counts differ');count=counts.pop()
    udf_records=[dict(label=x['label'],offset=x['offset'],bytes=len(x['modified']),sha256=core.digest(x['modified'])) for x in udf_plan['patches']]
    report=dict(milestone='expanded-text-poc',source_sha256=game['expected_iso_sha256'],modified_sha256=core.file_digest(out/'MODIFIED_FILE.iso'),
                iso=validation,afs_changes=changes,package_sha256=core.digest(engine),bundle_sha256=core.digest(new_bundle),
                fpb_records=fpb_info,ui=ui_info,ui_segments=ui_segments,candidate_ui_widths=widths,map=mapping['entries'],
                glyphs_per_font=count,records=3,name_slots=name_info,udf_records=udf_records,runtime='unverified; cached-stream growth candidate',source_iso=str(args.iso.resolve()))
    (out/'DIFF_FILE.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    core.require(core.file_digest(args.iso)==game['expected_iso_sha256'],'original ISO changed')
    print(f"EXPANDED LOCALE STATIC PASS fonts=2 records=3 glyphs={count} in_place={branches[0]} relocated={branches[1]} iso_readback=true udf_synced={str(validation['udf_synced']).lower()} runtime=unverified")


if __name__=='__main__':main()
