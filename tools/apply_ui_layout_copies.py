"""Guarded same-size font, UI field and VM operand overlays on verified copies."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib','src')]
import font_poc as core
from research_inventory import package_tables,font_data
from audit_object_properties import ordinary_exports
from audit_compiled_scripts import body
from overlay_compiled_stream_prefix import unique_prefix
from audit_stream_script_correspondence import align_prefix
from bundle_resource import overlay_segments
from translate.celfid import decompress_chunked,recompress_chunked
from localization.text import MappedEncoder,validate_target
from import_audited_fields import fixed_extent
from source_interpretation import source_text
from build_locale import checked_archive

def same_size_overlay(source,segments):
    data=bytearray(source);ranges=[]
    for q in segments:
        at=q['offset'];old=q['original'];new=q['modified'];core.require(0<=at<at+len(old)<=len(source) and len(old)==len(new) and source[at:at+len(old)]==old,'overlay identity/size mismatch');core.require(not any(at<b and a<at+len(old) for a,b in ranges),'overlapping edits');data[at:at+len(old)]=new;ranges.append((at,at+len(old)))
    prev=0
    for a,b in sorted(ranges):core.require(source[prev:a]==data[prev:a],'unselected bytes changed');prev=b
    core.require(source[prev:]==data[prev:],'unselected tail changed');return bytes(data)

def apply(file,ship,corpus,profile,mapping,font_dir,out):
    core.require(core.file_digest(file)==profile['base_file_sha256'] and core.file_digest(ship)==profile['base_ship_sha256'],'baseline archives mismatch')
    _,fe=core.archive_entries(file);_,se=core.archive_entries(ship);f=dict(fe);s=dict(se);bundle=decompress_chunked(f['celfid.lix']);segments=[];file_edits={};ship_edits={};proof=[]
    engine=f['MrtsEngine.u'];t=package_tables(engine);rows=[]
    for e in t['exports']:
        if e['class']=='Font' and e['name'] in ('NormalFont','KatakanaFont'):
            old=engine[e['offset']:e['offset']+e['size']];new=(font_dir/(e['name']+'.modified.bin')).read_bytes();report=json.loads((font_dir/'font-rebuild.json').read_text('utf8'))[e['name']]
            core.require(core.digest(old)==report['original_sha256'] and core.digest(new)==report['modified_sha256'],'font receipt mismatch');rows.append(dict(offset=e['offset'],original=old,modified=new));core.require(bundle.count(old)==1,'cached font not unique');segments.append(dict(label=e['name'],offset=bundle.index(old),original=old,modified=new));proof.append(dict(font=e['name'],source_sha256=core.digest(old),modified_sha256=core.digest(new)))
    core.require(len(rows)==2,'expected two fonts');file_edits['MrtsEngine.u']=same_size_overlay(engine,rows)
    q=profile['operand'];b=f[q['package']];t=package_tables(b);e=ordinary_exports(b,t)[q['export_index']-1];raw=b[e['offset']:e['offset']+e['size']];core.require(core.digest(raw)==q['source_function_sha256'],'VM source function mismatch');at=q['offset'];old=bytes.fromhex(q['old_hex']);new=bytes.fromhex(q['new_hex']);core.require(raw[at:at+len(old)]==old,'operand mismatch');parsed=body(raw,t,e);tokens=parsed['script']['tokens'];core.require(any(x['offset']==at and x['opcode']==0x2c for x in tokens),'not an IntConstByte token');modified=same_size_overlay(raw,[dict(offset=at,original=old,modified=new)]);after=body(modified,t,e);core.require(parsed['script']['tokens']==after['script']['tokens'] and parsed['script']['virtual_bytes']==after['script']['virtual_bytes'],'VM coordinates changed')
    function_modified=modified
    file_edits[q['package']]=same_size_overlay(b,[dict(offset=e['offset'],original=raw,modified=modified)])
    cache,cp=unique_prefix(bundle,raw,modified,parsed['script'],[dict(label='layout-operand',old_offset=at+1,new_offset=at+1,old_bytes=1,new_bytes=1)]);cache['label']='friendship-center';segments.append(cache);proof.append(cp)
    catalog={e['id']:(r,e) for r in corpus['resources'] for e in r['entries']};encoder=MappedEncoder(mapping['entries'],font_tables=font_data((font_dir/'NormalFont.modified.bin').read_bytes()))
    for row in profile['fields']:
        r,e=catalog[row['id']];core.require(e['source_sha256']==row['source_sha256'],'field source mismatch');validate_target(source_text(e),row['target']);name=Path(r['resource']).name;original=s[name];at=e['offset'];span,_=fixed_extent(e);old=encoder.encode(row['previous_target']);new=encoder.encode(row['target']);core.require(original[at:at+span]==old+bytes(span-len(old)) and len(new)<span,'field baseline/overflow mismatch');modified=same_size_overlay(original,[dict(offset=at,original=old+bytes(span-len(old)),modified=new+bytes(span-len(new)))]);ship_edits[name]=modified
        mirrors=[m for m in corpus['celfid_resource_mirrors'] if m['resource']==r['resource']];expected=sum(len(m['decompressed_offsets']) for m in mirrors);core.require(bundle.count(original)==expected,'field cache multiplicity mismatch');pos=0
        for i in range(expected):pos=bundle.index(original,pos);segments.append(dict(label=row['id']+'#'+str(i),offset=pos,original=original,modified=modified));pos+=len(original)
        proof.append(dict(id=row['id'],resource=name,offset=at,span=span,new_hex=new.hex(),cache_copies=expected))
    new_bundle,cache_report=overlay_segments(bundle,segments,expected_sha256=core.digest(bundle));alignment=align_prefix(new_bundle,cp['original_offset'],function_modified,parsed['script']);core.require(alignment['matched'] and alignment['unique_end'],'modified cached operand cannot be reparsed')
    file_edits['celfid.lix']=recompress_chunked(new_bundle);core.require(decompress_chunked(file_edits['celfid.lix'])==new_bundle,'cache recompression mismatch');out.mkdir(parents=True,exist_ok=True);core.require(not any(out.iterdir()),'output not empty');reports={}
    for name,source,entries,overrides in [('FILE.AFS',file,fe,file_edits),('SHIP.AFS',ship,se,ship_edits)]:
        normalized={n.lower():b for n,b in overrides.items()};normalized[entries[0][0].lower()]=core.manifest_overlay(entries[0][1],{n:len(b) for n,b in normalized.items()});reports[name]=checked_archive(source,out/name,normalized)
    result=dict(proofs=proof,cache=cache_report,archives=reports,archive_sha256={n:core.file_digest(out/n) for n in reports},runtime_verified=False);(out/'ui-layout-integration.json').write_text(json.dumps(result,indent=2)+'\n','utf8');print('UI_LAYOUT_AFS_PASS fonts=2 fields=2 VM_operands=1 cached_fonts_fields_operand_synced=true untargeted_bytes_preserved=true')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('file','ship','corpus','profile','map','font-dir','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();apply(a.file,a.ship,json.loads(a.corpus.read_text('utf8')),json.loads(a.profile.read_text('utf8')),json.loads(a.map.read_text('utf8')),a.font_dir,a.out)
if __name__=='__main__':main()
