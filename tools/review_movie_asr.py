"""Join ASR candidates to exact source fields and upstream reference timelines.

Whitespace folding is an explicit research comparison, not source identity.
ASS region labels describe tracks, not necessarily the language of their text.
"""
from pathlib import Path
from collections import defaultdict,Counter
import argparse,json,re,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import font_poc as core
from audit_movie_asr import segment_record,wave_identity
from audit_movie_frames import reference_cues


def folded(text):return ''.join(text.split())


def source_index(corpus):
    exact=defaultdict(list);space=defaultdict(list);ids=set()
    for resource in corpus['resources']:
        for row in resource['entries']:
            core.require(row['id'] not in ids,'duplicate source field');ids.add(row['id'])
            if row.get('decode')!='strict':continue
            text=row.get('references',{}).get('ko-KR')
            if not text:continue
            link=dict(id=row['id'],source_sha256=row['source_sha256'])
            exact[text].append(link);space[folded(text)].append(link)
    return exact,space


def overlaps(start,end,cue):
    return max(start,cue['start_centiseconds']/100)<min(end,cue['end_centiseconds']/100)


def review(segment,exact,space,cues):
    text=segment['text'];same=exact.get(text,[]);comparison=space.get(folded(text),[])
    refs=[dict(id=c['id'],source_sha256=c['source_sha256'],region=c['region']) for c in cues
          if overlaps(segment['start'],segment['end'],c)]
    flags=segment['uncertainty_flags']
    return dict(segment_id=segment['id'],start=segment['start'],end=segment['end'],text=text,
                exact_source_links=same,whitespace_folded_source_candidates=comparison,
                upstream_timeline_links=refs,uncertainty_flags=flags,
                targeted_ocr_requested=bool(flags),listen_review_required=bool(flags) or not comparison,
                source_dedup_verified=False,original_verbatim_verified=False,
                spoken_equals_displayed_verified=False,editable=False,backend_eligible=False)


def audit(asr,corpus,subs,out):
    before=core.file_digest(corpus);c=json.loads(corpus.read_text('utf8'))
    exact,space=source_index(c);movies=json.loads((asr/'movies.json').read_text('utf8'))
    summary=json.loads((asr/'summary.json').read_text('utf8'))
    core.require(len(movies)==summary['movies_requested']==46,'full ASR movie completion required')
    core.require(len({x['movie'] for x in movies})==46,'duplicate ASR movie')
    cue_by_movie=defaultdict(list);cue_files={}
    for region in ('korean','japanese'):
        for path in sorted((subs/region).glob('*.ass')):
            rows=reference_cues(path,region);cue_by_movie[path.stem].extend(rows)
            cue_files[str(path.relative_to(subs))]=core.file_digest(path)
    result=[];statuses=Counter();segments=0
    for movie in movies:
        statuses[movie['status']]+=1
        if movie['status']!='asr-candidates-complete':
            result.append(dict(movie=movie['movie'],status=movie['status'],visual_review_required=True,
                               no_text_verified=False));continue
        folder=asr/movie['movie'];audio=wave_identity(folder/'audio.wav')
        core.require(audio==movie['audio'],'PCM identity changed')
        rows=json.loads((folder/'segments.json').read_text('utf8'));core.require(len(rows)==movie['segments'],'ASR count mismatch')
        ids=set();records=[]
        for row in rows:
            core.require(row['id'] not in ids,'duplicate ASR segment');ids.add(row['id'])
            checked=segment_record(row,audio['duration_seconds']);core.require(checked==row,'ASR evidence changed')
            records.append(review(row,exact,space,cue_by_movie[movie['movie']]))
        segments+=len(records)
        result.append(dict(movie=movie['movie'],source_sha256=movie['source_sha256'],language=movie['language'],
                           segments=records,visual_review_required=True,
                           absent_asr_does_not_prove_absent_speech=True))
    stats=dict(movies=len(movies),statuses=dict(statuses),segments=segments,
               targeted_ocr_segments=sum(r['targeted_ocr_requested'] for m in result for r in m.get('segments',[])),
               exact_source_matches=sum(bool(r['exact_source_links']) for m in result for r in m.get('segments',[])),
               whitespace_folded_matches=sum(bool(r['whitespace_folded_source_candidates']) for m in result for r in m.get('segments',[])),
               upstream_ass_files=len(cue_files),upstream_ass_cues=sum(len(x) for x in cue_by_movie.values()),
               ass_text_not_assumed_track_language=True,source_fields_deleted=0,
               source_modified=False,coverage_review_complete=False,translation_gate='coverage-audit-pending')
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    for name,value in [('review.json',result),('summary.json',stats),('reference-hashes.json',cue_files)]:
        p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8')
        core.require(json.loads(p.read_text('utf8'))==value,'review reopen')
    core.require(core.file_digest(corpus)==before,'corpus changed')
    core.require(all(core.file_digest(subs/n)==h for n,h in cue_files.items()),'ASS changed')
    return stats


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('asr','corpus','subs','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.asr,a.corpus,a.subs,a.out),sort_keys=True))
