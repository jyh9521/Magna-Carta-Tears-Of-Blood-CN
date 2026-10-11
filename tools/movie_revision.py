"""Validate a text-only subtitle revision without claiming renewed human acceptance."""
import json
from pathlib import Path
import argparse
import subprocess

from font_poc import require, file_digest, digest


def name_only_ass(before, after, terms):
    require(bool(terms), 'empty subtitle revision')
    expected = before
    for term in terms:
        old,new = term['previous'],term['target']
        require(old and new and old != new, 'invalid subtitle term revision')
        require(not any(c in old+new for c in '\\{}\n\r'), 'subtitle revision control injection')
        expected = expected.replace(old,new)
    require(after == expected and after != before, 'subtitle edit changes layout/timing or unrelated text')
    return True


def validated_revision(row):
    revision = row.get('validated_revision')
    require(isinstance(revision,dict), 'movie lacks manual acceptance or validated revision')
    baseline = Path(revision['baseline_manifest'])
    proof_path = Path(revision['proof'])
    require(file_digest(baseline) == revision['baseline_manifest_sha256'], 'baseline movie manifest mismatch')
    require(file_digest(proof_path) == revision['proof_sha256'], 'movie revision proof mismatch')
    proof = json.loads(proof_path.read_text('utf8'))
    old = next(q for q in json.loads(baseline.read_text('utf8'))['movies'] if q['movie'] == row['movie'])
    require(old['manual_movie_acceptance'] is True, 'revision baseline was not accepted')
    require(old['sfd_sha256'] == proof['baseline_sfd_sha256'] and
            row['sfd_sha256'] == proof['candidate_sfd_sha256'], 'movie revision identity mismatch')
    require(file_digest(Path(old['sfd_path'])) == old['sfd_sha256'], 'accepted baseline SFD changed')
    before = Path(old['sfd_path']).parent/'subtitle.ass'
    after = Path(row['sfd_path']).parent/'subtitle.ass'
    require(file_digest(before) == old['ass_sha256'] and file_digest(after) == row['ass_sha256'], 'subtitle identity mismatch')
    name_only_ass(before.read_text('utf8'),after.read_text('utf8'),proof['terms'])
    from sfd_muxer import SFD
    old_audio = SFD.from_file(Path(old['sfd_path'])).extract_audio()
    new_audio = SFD.from_file(Path(row['sfd_path'])).extract_audio()
    require(old_audio == new_audio and digest(new_audio) == proof['adx_sha256'], 'revision audio changed')
    require(proof['full_decode_exit'] == 0 and proof['decoded_frames'] > 0 and
            proof['manual_revision_acceptance'] is False, 'revision decode/acceptance proof invalid')
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline-manifest','candidate','terms-profile','decoder','proof'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--movie',required=True)
    args = parser.parse_args()
    old = next(q for q in json.loads(args.baseline_manifest.read_text('utf8'))['movies']
               if q['movie'] == args.movie)
    require(old['manual_movie_acceptance'] is True,'baseline not manually accepted')
    baseline = Path(old['sfd_path'])
    require(file_digest(baseline) == old['sfd_sha256'],'baseline SFD fingerprint mismatch')
    before,after = baseline.parent/'subtitle.ass',args.candidate.parent/'subtitle.ass'
    require(file_digest(before) == old['ass_sha256'],'baseline ASS fingerprint mismatch')
    terms = json.loads(args.terms_profile.read_text('utf8'))['terms']
    name_only_ass(before.read_text('utf8'),after.read_text('utf8'),terms)
    from sfd_muxer import SFD
    a,b = SFD.from_file(baseline).extract_audio(),SFD.from_file(args.candidate).extract_audio()
    require(a == b,'movie audio changed')
    records = []
    for path in (baseline,args.candidate):
        cmd = [str(args.decoder),'-nostdin','-v','error','-i',str(path),
               '-map','0:v:0','-an','-fps_mode','passthrough','-f','framehash','-']
        result = subprocess.run(cmd,capture_output=True)
        frames = sum(bool(line) and not line.startswith(b'#') for line in result.stdout.splitlines())
        require(frames > 0,'empty movie revision')
        from audit_movie_ocr import decoder_outcome
        expected_frames = records[0]['frames'] if records else frames
        outcome = decoder_outcome(result.returncode,result.stderr.decode('utf8'),frames,expected_frames)
        require(outcome['complete'],'movie revision full decode failed')
        records.append(dict(command=cmd,exit_status=result.returncode,frames=frames,
                            stderr=result.stderr.decode('utf8'),decoder_outcome=outcome))
    require(records[0]['frames'] == records[1]['frames'],'movie frame count changed')
    proof = dict(movie=args.movie,baseline_sfd_sha256=old['sfd_sha256'],
                 candidate_sfd_sha256=file_digest(args.candidate),terms=terms,adx_sha256=digest(b),
                 full_decode_exit=0,decoded_frames=records[1]['frames'],manual_revision_acceptance=False,
                 layout_timing_styles_identical_except_names=True,container_timing_verified=False,
                 decode_records=records)
    args.proof.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n','utf8')
    print('MOVIE_REVISION_PASS movie='+args.movie+' name_only=true audio_identical=true full_decode=2 manual_revision_acceptance=false')


if __name__ == '__main__':main()
