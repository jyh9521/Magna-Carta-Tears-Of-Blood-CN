"""Merge guarded ordinary Function copies, font copies, and observed cache mirrors.

Cache script prefixes use the all-alignment-consensus source oracle. This is
static consistency evidence, not independent stream decoding or runtime QA.
"""
from pathlib import Path
import argparse,json,struct,sys
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib')]
import font_poc as core
from package_resource import replace_exports,export_records
from research_inventory import package_tables
from audit_object_properties import ordinary_exports
from audit_compiled_scripts import body
from audit_stream_script_correspondence import align_prefix
from overlay_compiled_stream_prefix import unique_prefix
from bundle_resource import replace_cached_package,overlay_segments
from audit_container_payloads import unpack_chunks,probe_all_packages
from translate.celfid import recompress_chunked,decompress_chunked
from integrate_resource_copies import checked_archive


def metadata_segments(bundle,old,new,name):
    old_records,old_end=export_records(old,expected_version=(118,15));new_records,new_end=export_records(new,expected_version=(118,15))
    core.require(old_end==len(old) and new_end==len(new),'cached package export table must end at EOF')
    rows=[]
    for label,source,target in [('header',old[:64],new[:64]),('exports',old[struct.unpack_from('<I',old,24)[0]:],new[struct.unpack_from('<I',new,24)[0]:])]:
        core.require(bundle.count(source)==1,'cached package metadata not unique '+name+'/'+label)
        rows.append(dict(label=name+'/'+label,offset=bundle.index(source),original=source,modified=target))
    path=('../System/UFile/'+name).encode('ascii').ljust(128,b'\0');record=path+struct.pack('<I',len(old))
    core.require(bundle.count(record)==2,'cached package file-size record count mismatch '+name)
    at=0
    for i in range(2):
        at=bundle.index(record,at)+128;rows.append(dict(label=name+'/file-size-'+str(i),offset=at,original=record[-4:],modified=struct.pack('<I',len(new))));at+=4
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('base-archive','objects','compiled-dir','font-package-dir','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--base-sha256',required=True);a=p.parse_args()
    core.require(core.file_digest(a.base_archive)==a.base_sha256,'base integrated archive fingerprint mismatch')
    _,entries=core.archive_entries(a.base_archive);members=dict(entries);bundle,_=unpack_chunks(members['celfid.lix']);source_bundle=bundle
    report=json.loads((a.compiled_dir/'compiled-imports.json').read_text('utf8'));font=json.loads((a.font_package_dir/'font-package.json').read_text('utf8'));core.require(core.file_digest(a.objects)==report['objects_sha256'],'compiled object inventory fingerprint mismatch');objects={q['id']:q for q in json.loads(a.objects.read_text('utf8'))}
    font_engine=(a.font_package_dir/'MrtsEngine.modified.u').read_bytes();core.require(core.digest(font_engine)==font['modified_sha256'],'font package fingerprint mismatch')
    bundle,font_cache=replace_cached_package(bundle,members['MrtsEngine.u'],font_engine,{735,736},expected_bundle_sha256=core.digest(bundle),expected_package_sha256=core.digest(members['MrtsEngine.u']),cached_path='../System/UFile/MrtsEngine.u')
    bases=dict(members);bases['MrtsEngine.u']=font_engine;selected=defaultdict(dict);raws={};receipts={q['id']:q for q in report['function_receipts']}
    for row in report['packages']:
        name=row['package'];blob=(a.compiled_dir/name).read_bytes();core.require(core.digest(blob)==row['modified_sha256'],'compiled package fingerprint mismatch');tables=package_tables(blob);exports=ordinary_exports(blob,tables)
        for change in row['changed']:
            e=exports[change['index']-1];raw=blob[e['offset']:e['offset']+e['size']];oid='FILE/'+name+'/export/'+str(e['index']);core.require(oid in receipts and core.digest(raw)==receipts[oid]['modified_sha256'],'compiled Function receipt mismatch')
            selected[name][e['index']]=raw;raws[oid]=raw
    core.require(len(raws)==report['functions'] and sum(len(q['literals']) for q in receipts.values())==report['translated_fields'],'compiled selection count mismatch')
    out=core.output_directory(a.out);core.require(not any(out.iterdir()),'compiled integration output must be empty');segments=[];cache_proofs=[];new_packages={}
    for name,replacements in sorted(selected.items()):
        base=bases[name];new,proof=replace_exports(base,replacements,expected_sha256=core.digest(base),expected_version=(118,15));new_packages[name]=new
        segments.extend(metadata_segments(bundle,base,new,name));(out/name).write_bytes(new)
    for oid,new in sorted(raws.items()):
        o=objects[oid];e=o['export'];old=members[o['package']][e['offset']:e['offset']+e['size']];core.require(core.digest(old)==o['serial_sha256']==receipts[oid]['source_sha256'],'original Function in base archive changed')
        segment,proof=unique_prefix(bundle,old,new,o['script'],receipts[oid]['edits']);segment['label']=oid;segments.append(segment);cache_proofs.append(dict(id=oid,**proof))
    new_bundle,changes=overlay_segments(bundle,segments,expected_sha256=core.digest(bundle));by_label={q['label']:q for q in changes}
    for proof in cache_proofs:
        oid=proof['id'];q=by_label[oid];raw=raws[oid];o=objects[oid];s=body(raw,package_tables(new_packages[o['package']]),o['export'])['script'];alignment=align_prefix(new_bundle,q['modified_offset'],raw,s)
        core.require(alignment['matched'] and alignment['unique_end'] and alignment['ends'][0]['offset']==q['modified_offset']+q['modified_size'],'modified cached Function correspondence readback mismatch')
        proof.update(modified_offset=q['modified_offset'],modified_prefix_reparsed=True)
    streamed=probe_all_packages(new_bundle)
    for name,new in new_packages.items():
        t=[q for q in streamed if q['wrapper_path']=='../System/UFile/'+name];core.require(len(t)==1 and t[0]['original_package_size']==len(new),'modified cached package wrapper size mismatch')
        records,_=export_records(new,expected_version=(118,15));core.require(len(records)==len(t[0]['exports']),'cached export count changed')
        for rec,exp in zip(records,t[0]['exports'],strict=True):core.require(rec['offset']==exp['declared_offset'] and rec['size']==exp['declared_size'],'cached export metadata readback mismatch')
    compressed=recompress_chunked(new_bundle);core.require(decompress_chunked(compressed)==new_bundle,'compiled cache compression roundtrip mismatch')
    overrides={name.lower():blob for name,blob in new_packages.items()};overrides['celfid.lix']=compressed;overrides[entries[0][0].lower()]=core.manifest_overlay(entries[0][1],{name:len(blob) for name,blob in overrides.items()})
    archive_report=checked_archive(a.base_archive,out/'FILE.AFS',overrides)
    (out/'bundle.modified.bin').write_bytes(new_bundle);(out/'celfid.modified.lix').write_bytes(compressed)
    result=dict(schema=1,source_archive_sha256=a.base_sha256,modified_archive_sha256=core.file_digest(out/'FILE.AFS'),translated_fields=report['translated_fields'],functions=len(raws),packages=len(new_packages),source_bundle_sha256=core.digest(source_bundle),modified_bundle_sha256=core.digest(new_bundle),font_cache=font_cache,cache_prefixes=cache_proofs,cache_segments=changes,afs_changes=archive_report,all_alignment_outputs_identical=True,ordinary_and_cache_targets_synchronized=True,independent_stream_reader=False,compression_roundtrip=True,untargeted_archive_members_preserved=True,runtime_verified=False,final_iso_complete=False)
    path=out/'compiled-integration.json';path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');core.require(json.loads(path.read_text('utf8'))==result and core.file_digest(a.base_archive)==a.base_sha256,'integration/source reopen mismatch')
    print(f'COMPILED_CACHE_AFS_PASS fields={report["translated_fields"]} functions={len(raws)} packages={len(new_packages)} cache_prefixes={len(cache_proofs)} metadata_segments={len(changes)-len(cache_proofs)} fonts_updated=2 consensus=true untargeted_members_preserved=true runtime_verified=false ISO=false')
if __name__=='__main__':main()
