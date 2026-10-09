"""Independently derive and verify a PoC ISO from source ISO/font/locale.

No build report, extracted build archive, or intermediate Font is trusted.
The candidate is read-only; derived assets go into a fresh ignored directory.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'src')]
import font_poc as core
from build_locale import load_config,patch_font,checked_archive,estimate_widths
from bundle_resource import replace_cached_package,overlay_segments
from font_resource import append_slots, expanded_entries
from display_resources import apply_display_resources, character_entries, display_cases
from localization.text import MappedEncoder,rewrite_fpb,rewrite_fixed_slot
from package_resource import replace_exports
from research_inventory import package_tables,font_data
from translate.celfid import decompress_chunked,recompress_chunked
from udf_overlay import plan_udf_overlay
from iso_validation import verify_iso_overlay
from name_slot_overlay import apply_name_slots


def fresh_output(path: Path, inputs: list[Path], *, root: Path=ROOT) -> Path:
    """Never clear an existing directory or allow an input below output."""
    path=path.resolve();roots=[(root/name).resolve() for name in ('work','build')]
    core.require(any(path!=base and path.is_relative_to(base) for base in roots),'fresh output must be below work/build')
    core.require(all(not p.resolve().is_relative_to(path) for p in inputs),'input overlaps output directory')
    core.require(not path.exists() or path.is_dir() and not any(path.iterdir()),'output directory must be empty')
    path.mkdir(parents=True,exist_ok=True);return path


def expected_fonts(engine: bytes, game: dict, locale: dict, old_entries: list[dict], font: Path, start: int) -> tuple[dict,dict,MappedEncoder]:
    from fontTools.ttLib import TTFont
    core.require(core.digest(engine)==game['expected_engine_sha256'],'original engine fingerprint mismatch')
    core.require(core.file_digest(font)==locale['font_input']['sha256'],'font input fingerprint mismatch')
    with TTFont(font) as face:
        cmap=face.getBestCmap()
        core.require(all(cmap.get(ord(item['character'])) not in (None,'.notdef') for item in old_entries),'missing font glyph')
    originals={}
    for export in package_tables(engine)['exports']:
        if export['class']=='Font' and export['name'] in game['fonts']:
            name=export['name'];serial=engine[export['offset']:export['offset']+export['size']]
            core.require(core.digest(serial)==game['fonts'][name],'original Font fingerprint mismatch')
            originals[name]=(export['index'],serial)
    core.require(set(originals)==set(game['fonts']) and len(originals)==2,'expected Fonts missing')
    counts={font_data(serial)['glyphs'] for _,serial in originals.values()}
    core.require(len(counts)==1,'original Font counts differ');first=counts.pop();count=len(old_entries)
    entries=expanded_entries(old_entries,first,start)
    fonts={};replacements={};encoder=None
    for name,(index,serial) in originals.items():
        info=font_data(serial)
        expanded=append_slots(serial,count,start,
                             expected_sha256=game['fonts'][name])
        encoder=MappedEncoder(entries,font_tables=font_data(expanded))
        fonts[name]=patch_font(expanded,encoder,font,locale['alignment_reference'],locale['advance'])
        replacements[index]=fonts[name]
    return fonts,replacements,encoder


def verify_candidate(source: Path, candidate: Path, font: Path, locale_path: Path, out: Path, start: int=0xD0A1) -> dict:
    locale,game,old_encoder=load_config(locale_path)
    core.require(source.resolve()!=candidate.resolve() and not source.samefile(candidate),'source and candidate must differ')
    core.require(core.file_digest(source)==game['expected_iso_sha256'],'source ISO fingerprint mismatch')
    candidate_hash=core.file_digest(candidate)
    out=fresh_output(out,[source,candidate,font,locale_path])
    contents=core.iso_files(source,['FILE.AFS','SHIP.AFS'])
    for name,data in contents.items():(out/('original-'+name)).write_bytes(data)
    _,file_entries=core.archive_entries(out/'original-FILE.AFS');_,ship_entries=core.archive_entries(out/'original-SHIP.AFS')
    files,ship=dict(file_entries),dict(ship_entries);original_engine=files['MrtsEngine.u']
    fonts,replacements,encoder=expected_fonts(original_engine,game,locale,character_entries(locale,ROOT),font,start)
    if 'text_resources' not in locale: encoder.validate_coverage([r['target'] for r in locale['entries']])
    engine,_=replace_exports(original_engine,replacements,expected_sha256=game['expected_engine_sha256'],expected_version=(118,15))
    original_bundle=decompress_chunked(files['celfid.lix'])
    bundle,_=replace_cached_package(original_bundle,original_engine,engine,set(replacements),
        expected_bundle_sha256=game['expected_bundle_sha256'],expected_package_sha256=game['expected_engine_sha256'],
        cached_path='../System/UFile/MrtsEngine.u')
    if 'text_resources' in locale:
        text_overrides,bundle,text_info=apply_display_resources(ship,bundle,encoder,locale['text_resources'],fonts,estimate_widths)
    else:
        fpb,ui=ship[game['fpb_resource']],ship[game['ui_resource']]
        core.require(core.digest(fpb)==game['expected_fpb_sha256'] and core.digest(ui)==game['expected_ui_sha256'],'original text fingerprint mismatch')
        targets={r['seq']:r['target'] for r in locale['entries'] if r['kind']=='fpb'}
        core.require(set(targets)=={0,2},'unexpected FPB target windows')
        new_fpb,_=rewrite_fpb(fpb,targets,encoder);core.require(len(new_fpb)>len(fpb),'FPB growth missing')
        record=next(r for r in locale['entries'] if r['kind']=='fixed-display-slot')
        new_ui,_=rewrite_fixed_slot(ui,game['ui'],record['target'],encoder)
        for serial in fonts.values():core.require(max(estimate_widths(record['target'],encoder,serial))<=record['max_estimated_pixels'],'UI width budget exceeded')
        core.require(bundle.count(ui)==1,'UI cached copy not unique')
        bundle,_=overlay_segments(bundle,[dict(label='ui',offset=bundle.index(ui),original=ui,modified=new_ui)],expected_sha256=core.digest(bundle))
        text_overrides={game['fpb_resource'].lower():new_fpb,game['ui_resource'].lower():new_ui};text_info=[]
    name_overrides,bundle,name_info=apply_name_slots(ship,bundle,encoder,locale.get('name_slot_overlays',[]))
    compressed=recompress_chunked(bundle);core.require(decompress_chunked(compressed)==bundle,'compression round trip mismatch')
    overrides={'FILE.AFS':{'mrtsengine.u':engine,'celfid.lix':compressed},
               'SHIP.AFS':text_overrides}
    core.require(not set(overrides['SHIP.AFS']).intersection(name_overrides),'name overlay collides with text target')
    overrides['SHIP.AFS'].update(name_overrides)
    for name,entries in [('FILE.AFS',file_entries),('SHIP.AFS',ship_entries)]:
        edits=overrides[name];edits[entries[0][0].lower()]=core.manifest_overlay(entries[0][1],{n:len(data) for n,data in edits.items()})
        checked_archive(out/('original-'+name),out/('expected-'+name),edits)
    recovered=core.iso_files(candidate,['FILE.AFS','SHIP.AFS'])
    paths={}
    for name,data in recovered.items():
        expected=out/('expected-'+name)
        core.require(data==expected.read_bytes(),'independent archive mismatch: '+name);paths['/'+name]=expected
    udf_plan=plan_udf_overlay(source,paths)
    iso=verify_iso_overlay(source,candidate,paths,udf_plan=udf_plan)
    core.require(core.file_digest(source)==game['expected_iso_sha256'] and core.file_digest(candidate)==candidate_hash,
                 'verification input changed')
    result=dict(schema=1,locale=locale['locale'],source_sha256=game['expected_iso_sha256'],candidate_sha256=candidate_hash,
                font_sha256=core.file_digest(font),range_start=f'{start:04X}',font_characters=len(encoder.entries),records=len(display_cases(locale)) if 'text_resources' in locale else len(locale['entries']),
                iso=iso,name_slots=name_info,text_resources=text_info,independent_inputs='source ISO + font + locale; no build reports',
                checks=['font raster/metrics/map','all export identities/payloads','cached fragments and UI copy',
                        'FPB/fixed-slot tokens and payloads','full AFS bytes/metadata/manifest','ISO9660/UDF views','untargeted ISO bytes'],
                runtime='unverified')
    (out/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return result


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--font',type=Path,required=True);p.add_argument('--locale',type=Path,required=True)
    p.add_argument('--range-start',type=lambda x:int(x,0),default=0xD0A1);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();r=verify_candidate(a.source,a.candidate,a.font,a.locale,a.out,a.range_start)
    print(f"INDEPENDENT VERIFY PASS chars={r['font_characters']} records={r['records']} udf_synced={str(r['iso']['udf_synced']).lower()} reports_trusted=0 sha256={r['candidate_sha256']}")


if __name__=='__main__':main()
