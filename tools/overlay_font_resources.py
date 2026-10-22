"""Overlay same-format fonts and their unique startup copies, and nothing else."""
from pathlib import Path
import argparse, json, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('tools','lib','src')]
import font_poc as core
from research_inventory import font_data, package_tables
from apply_ui_layout_copies import same_size_overlay
from bundle_resource import overlay_segments
from translate.celfid import decompress_chunked, recompress_chunked
from build_locale import checked_archive


def check_font_compatibility(old, new, *, padding_cleanup=False):
    before=font_data(old);after=font_data(new)
    core.require(before['glyphs']>=2667,'original glyph prefix absent')
    core.require(before==after and len(old)==len(new),'font geometry/mapping/layout mismatch')
    at=before['bitmap_start'];stride=before['height']*before['row_stride']
    reference=old
    if padding_cleanup:
        from sanitize_font_padding import sanitize
        reference,_=sanitize(old)
    core.require(reference[:at+2667*stride]==new[:at+2667*stride],'original effective glyph bytes changed')
    end=at+before['bitmap_bytes']
    core.require(old[end:]==new[end:],'metrics/tables/tail changed')
    return before


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('file','font-dir','base-font-dir','out'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--expected-sha256',required=True);p.add_argument('--padding-cleanup',action='store_true');a=p.parse_args()
    core.require(core.file_digest(a.file)==a.expected_sha256,'archive fingerprint mismatch')
    _,entries=core.archive_entries(a.file);members=dict(entries);engine=members['MrtsEngine.u'];bundle=decompress_chunked(members['celfid.lix'])
    edits=[];cache=[];proof=[]
    for e in package_tables(engine)['exports']:
        if e['class']!='Font' or e['name'] not in ('NormalFont','KatakanaFont'):continue
        old=engine[e['offset']:e['offset']+e['size']];new=(a.font_dir/(e['name']+'.modified.bin')).read_bytes()
        core.require(old==(a.base_font_dir/(e['name']+'.modified.bin')).read_bytes(),'baseline font mismatch')
        info=check_font_compatibility(old,new,padding_cleanup=a.padding_cleanup)
        core.require(bundle.count(old)==1,'expected unique cached font')
        edits.append(dict(offset=e['offset'],original=old,modified=new));cache.append(dict(label=e['name'],offset=bundle.index(old),original=old,modified=new))
        proof.append(dict(name=e['name'],export_index=e['index'],offset=e['offset'],bytes=len(new),source_sha256=core.digest(old),modified_sha256=core.digest(new),glyphs=info['glyphs'],cache_copies=1))
    core.require(len(edits)==2,'expected exactly two Font exports')
    new_engine=same_size_overlay(engine,edits);new_bundle,cache_proof=overlay_segments(bundle,cache,expected_sha256=core.digest(bundle))
    compressed=recompress_chunked(new_bundle);core.require(decompress_chunked(compressed)==new_bundle,'cache recompression mismatch')
    overrides={'mrtsengine.u':new_engine,'celfid.lix':compressed}
    overrides[entries[0][0].lower()]=core.manifest_overlay(entries[0][1],{name:len(raw) for name,raw in overrides.items()})
    a.out.mkdir(parents=True,exist_ok=True);core.require(not any(a.out.iterdir()),'output not empty')
    changes=checked_archive(a.file,a.out/'FILE.AFS',overrides)
    report=dict(source_sha256=a.expected_sha256,modified_sha256=core.file_digest(a.out/'FILE.AFS'),fonts=proof,cache=cache_proof,changes=changes,translation_script_UI_changes=False,runtime_verified=False)
    (a.out/'font-integration.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
    print('FONT_ONLY_AFS_PASS fonts=2 cache_copies=2 original_effective_ink_metrics_mapping_preserved=true padding_cleanup='+str(a.padding_cleanup)+' scripts_UI_text_unchanged=true')

if __name__=='__main__':main()
