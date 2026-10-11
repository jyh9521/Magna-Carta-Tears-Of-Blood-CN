"""Build a version-locked test ISO from verified archives and accepted movies.

ISO9660/UDF views, unchanged source bytes and every replacement are verified
independently after writing. Game execution/visual acceptance are not claimed.
"""
from pathlib import Path
import argparse,json,re,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib')]
from font_poc import require,file_digest,digest,output_directory
from iso import patch_iso,_portable_metadata,SECTOR
from udf_overlay import plan_udf_overlay,apply_udf_overlay
from iso_validation import verify_iso_overlay
from movie_revision import validated_revision


def grouped_replacements(replacements):
    # Upstream patch_iso batches directories, rather than using global input
    # order. UDF planning and independent extent verification must use that
    # exact grouped order too, especially when a MOVIE99 entry precedes the
    # final MOVIE18 entry in the acceptance manifest.
    groups={}
    for name,path in replacements.items():groups.setdefault(name.rsplit('/',1)[0] or '/',{})[name]=path
    return {name:path for group in groups.values() for name,path in group.items()}


def checked_inputs(plan,movies,files):
    require(plan.get('schema')==1 and re.fullmatch(r'[a-zA-Z0-9-]+',plan.get('locale','')),'invalid test ISO plan')
    require({'FILE.AFS','SHIP.AFS'} <= set(plan['archives']) <= {'FILE.AFS','SHIP.AFS','LINEAR.AFS'},'test ISO requires supported complete archives')
    replacements={}
    for name,row in plan['archives'].items():
        require('/'+name in files,'archive absent from source ISO '+name)
        path=Path(row['path']);require(path.is_file() and file_digest(path)==row['sha256'],'archive input fingerprint mismatch '+name);replacements['/'+name]=path
    require(movies['selected_count']==len(movies['movies']) and movies['retained_original_count']>0,'movie selection counts mismatch')
    movie_files={name.rsplit('/',1)[1].removesuffix('.SFD'):name for name in files if name.endswith('.SFD')};seen=set();movie_proofs=[]
    require(len(movie_files)==movies['selected_count']+movies['retained_original_count'],'original movie inventory mismatch')
    for row in movies['movies']:
        name=row['movie'];require(name not in seen and name in movie_files,'duplicate/unknown movie')
        require(row['manual_movie_acceptance'] is True or validated_revision(row),'unaccepted movie');seen.add(name)
        path=Path(row['sfd_path']);review=Path(row['accepted_review_path'])
        require(path.stat().st_size==row['sfd_bytes'] and file_digest(path)==row['sfd_sha256'],'accepted SFD fingerprint mismatch '+name)
        require(file_digest(review)==row['accepted_review_sha256'],'accepted MP4 fingerprint mismatch '+name)
        replacements[movie_files[name]]=path;movie_proofs.append(dict(movie=name,iso_path=movie_files[name],source_sha256=row['original_sfd_sha256'],accepted_sfd_sha256=row['sfd_sha256'],accepted_review_sha256=row['accepted_review_sha256']))
    return grouped_replacements(replacements),movie_proofs,sorted(set(movie_files)-seen)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('iso','profile','input-plan','movies','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();game=json.loads(a.profile.read_text('utf8'));source_hash=file_digest(a.iso);require(source_hash==game['expected_iso_sha256'],'original ISO version/hash mismatch')
    plan=json.loads(a.input_plan.read_text('utf8'));require(file_digest(a.movies)==plan['movies_manifest_sha256'],'movie acceptance manifest fingerprint mismatch');movies=json.loads(a.movies.read_text('utf8'));files,_=_portable_metadata(a.iso)
    replacements,movie_proofs,retained=checked_inputs(plan,movies,files)
    with a.iso.open('rb') as source:
        for row in movie_proofs:
            lba,size=files[row['iso_path']];source.seek(lba*SECTOR);require(digest(source.read(size))==row['source_sha256'],'accepted movie original ISO identity mismatch '+row['movie'])
    udf=plan_udf_overlay(a.iso,replacements);out=output_directory(a.out);require(not any(out.iterdir()),'test ISO output must be empty');target=out/('Magna-Carta-'+plan['locale']+'-test.iso')
    counts=patch_iso(a.iso,target,replacements,verbose=True);apply_udf_overlay(target,udf);verification=verify_iso_overlay(a.iso,target,replacements,udf_plan=udf)
    require(tuple(counts)==(verification['in_place'],verification['relocated']),'ISO writer/independent verification count disagreement')
    require(file_digest(a.iso)==source_hash,'original ISO changed');target_hash=file_digest(target)
    serialized_udf={k:v for k,v in udf.items() if k!='patches'};serialized_udf['patches']=[{**q,'original':q['original'].hex(),'modified':q['modified'].hex()} for q in udf['patches']]
    result=dict(schema=1,source_iso=str(a.iso.resolve()),source_sha256=source_hash,modified_iso=str(target),modified_sha256=target_hash,input_plan_sha256=file_digest(a.input_plan),movies_manifest_sha256=file_digest(a.movies),replacements={name:dict(path=str(path.resolve()),bytes=path.stat().st_size,sha256=file_digest(path)) for name,path in replacements.items()},selected_movies=movie_proofs,retained_original_movies=retained,verification=verification,udf_plan=serialized_udf,translation_fields=plan['translation_fields'],font_characters=plan['font_characters'],glossary_terms=plan['glossary_terms'],runtime_verified=False,visual_layout_accepted=False,test_iso_generated=True)
    report=out/'test-iso.json';report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');require(json.loads(report.read_text('utf8'))==result,'test ISO report reopen mismatch')
    print(f'TEST_ISO_STATIC_PASS translated_fields={plan["translation_fields"]} archives={len(plan["archives"])} movies={len(movie_proofs)} originals={len(retained)} ISO9660_UDF_verified=true sha256={target_hash} runtime_verified=false')
if __name__=='__main__':main()
