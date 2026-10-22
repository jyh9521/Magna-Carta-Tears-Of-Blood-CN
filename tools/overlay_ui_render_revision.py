"""Fingerprint-bound font-padding and numeric VM overlays with startup mirrors."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib','src')]
import font_poc as core
from research_inventory import package_tables
from audit_object_properties import ordinary_exports
from audit_compiled_scripts import body
from apply_ui_layout_copies import same_size_overlay
from sanitize_font_padding import sanitize
from overlay_compiled_stream_prefix import unique_prefix
from audit_stream_script_correspondence import align_prefix
from bundle_resource import overlay_segments
from translate.celfid import decompress_chunked,recompress_chunked
from build_locale import checked_archive

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('file','profile','font-dir','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();profile=json.loads(a.profile.read_text('utf8'));core.require(core.file_digest(a.file)==profile['base_file_sha256'],'archive identity mismatch');_,entries=core.archive_entries(a.file);members=dict(entries);bundle=decompress_chunked(members['celfid.lix']);segments=[];overrides={};proof=[];alignments=[]
    engine=members['MrtsEngine.u'];edits=[]
    for e in package_tables(engine)['exports']:
        if e['class']!='Font' or e['name'] not in ('NormalFont','KatakanaFont'):continue
        old=engine[e['offset']:e['offset']+e['size']];new=(a.font_dir/(e['name']+'.modified.bin')).read_bytes();expected,receipt=sanitize(old);core.require(new==expected,'font is not padding-only sanitation');core.require(bundle.count(old)==1,'font cache not unique');edits.append(dict(offset=e['offset'],original=old,modified=new));segments.append(dict(label=e['name'],offset=bundle.index(old),original=old,modified=new));proof.append(dict(font=e['name'],**receipt))
    core.require(len(edits)==2,'expected two fonts');overrides['mrtsengine.u']=same_size_overlay(engine,edits)
    game=members['MrtsGame.u'];t=package_tables(game);es=ordinary_exports(game,t);edits=[]
    for q in profile['functions']:
        e=es[q['export_index']-1];old=game[e['offset']:e['offset']+e['size']];core.require(core.digest(old)==q['source_sha256'],'function identity mismatch');parsed=body(old,t,e);tokens={x['offset']:x for x in parsed['script']['tokens']};rows=[];cache_edits=[]
        for d in q['edits']:
            at=d['offset'];original=bytes.fromhex(d['old_hex']);modified=bytes.fromhex(d['new_hex']);core.require(tokens[at]['opcode']==0x2c and len(original)==2 and original[0]==modified[0]==0x2c,'not fixed-width integer operand');rows.append(dict(offset=at,original=original,modified=modified));cache_edits.append(dict(label=d['label'],old_offset=at+1,new_offset=at+1,old_bytes=1,new_bytes=1))
        new=same_size_overlay(old,rows);after=body(new,t,e);core.require(parsed['script']['tokens']==after['script']['tokens'] and parsed['script']['virtual_bytes']==after['script']['virtual_bytes'],'VM topology changed');edits.append(dict(offset=e['offset'],original=old,modified=new));seg,cp=unique_prefix(bundle,old,new,parsed['script'],cache_edits);seg['label']='UI-'+str(e['index']);segments.append(seg);alignments.append((cp['original_offset'],new,parsed['script']));proof.append(dict(export_index=e['index'],source_sha256=core.digest(old),modified_sha256=core.digest(new),operands=q['edits'],cache=cp))
    overrides['mrtsgame.u']=same_size_overlay(game,edits);new_bundle,cache_report=overlay_segments(bundle,segments,expected_sha256=core.digest(bundle))
    for at,new,script in alignments:
        check=align_prefix(new_bundle,at,new,script);core.require(check['matched'] and check['unique_end'],'cache parse mismatch')
    overrides['celfid.lix']=recompress_chunked(new_bundle);core.require(decompress_chunked(overrides['celfid.lix'])==new_bundle,'cache compression mismatch');overrides[entries[0][0].lower()]=core.manifest_overlay(entries[0][1],{n:len(b) for n,b in overrides.items()});a.out.mkdir(parents=True,exist_ok=True);core.require(not any(a.out.iterdir()),'output not empty');changes=checked_archive(a.file,a.out/'FILE.AFS',overrides);(a.out/'ui-render-integration.json').write_text(json.dumps(dict(proofs=proof,cache=cache_report,changes=changes,runtime_verified=False),indent=2)+'\n','utf8');print('UI_RENDER_AFS_PASS fonts=2 VM_functions='+str(len(edits))+' cache_synced=true unselected_resources_preserved=true')
if __name__=='__main__':main()
