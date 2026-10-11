"""Preserve original terminal LF bytes in version-bound native CHT text slots."""
from pathlib import Path
import argparse,copy,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('tools','lib','src')]
from font_poc import digest,archive_entries,require
from research_native import ElfImage,ELF_SHA256
from audit_native_fixed_dialogue import validate_field,validate_anchors
from source_interpretation import source_text
from localization.text import TERMINAL_LF_POLICY,validate_target,terminal_lf_body
from validate_translation_batch import validate,glossary_terms


def derive(corpus,profile,members,image):
    require(profile.get('schema')==1 and profile.get('locale')=='zh-CN','terminal LF profile schema mismatch')
    out=copy.deepcopy(corpus);index={e['id']:(r,e) for r in out['resources'] for e in r['entries']};seen=set();batch=[];proofs=[]
    for d in profile['entries']:
        identity=d['id'];require(identity in index and identity not in seen,'terminal LF duplicate/unknown source');seen.add(identity)
        r,e=index[identity];require(r['resource'].endswith('.cht') and e.get('controls')=='quarantined' and e['decode']=='strict','terminal LF requires quarantined native CHT')
        require(d['resource']==r['resource'] and d['resource_sha256']==r['sha256'] and all(d[k]==e[k] for k in ('offset','source_bytes','source_sha256')),'terminal LF source identity mismatch')
        original=members[Path(r['resource']).name];span=original[e['offset']:e['offset']+e['source_bytes']]
        source=span.decode('cp949');require(digest(span)==e['source_sha256'] and source.encode('cp949')==span and source==d['source']==source_text(e),'terminal LF source reading mismatch')
        require(d['reading_sha256']==digest(source.encode('utf8')) and d['status']=='reviewed','terminal LF reading fingerprint/status mismatch')
        validate_target(source,d['target'],control_policy=TERMINAL_LF_POLICY)
        body=terminal_lf_body(d['target']);require(not any('가'<=ch<='힣' for ch in body) and not any(ch in body for ch in ('—','―')) and body[0] not in '，。！？；：、）】》…','terminal LF target prose invalid')
        geometry=validate_field(r,e,d['binding'],original)
        e.update(observed_byte_capacity=511,trailer_bytes=geometry['preserved_tail_bytes'],trailer_sha256=geometry['preserved_tail_sha256'],controls='recognized',editable=True,backend_eligible=True,source_control_policy=TERMINAL_LF_POLICY,
            source_control_interpretation=dict(schema=1,original_controls='quarantined',raw_sha256=e['source_sha256'],reading_sha256=d['reading_sha256'],target_sha256=digest(d['target'].encode('utf8')),native_binding_sha256=digest(json.dumps(d['binding'],sort_keys=True,separators=(',',':')).encode('utf8')),native_source_span_verified=True,runtime_control_semantics_verified=False))
        batch.append(dict(id=identity,source_sha256=e['source_sha256'],target=d['target'],status='reviewed',reinsertion_policy='translate',context='Original terminal byte0A preserved exactly before NUL; native512 CHT storage/source hashes verified. No substitution to $n or deletion, runtime layout not claimed.'))
        proofs.append(dict(id=identity,geometry=geometry,source_terminal_byte='0A',target_terminal_byte='0A',runtime_verified=False))
    out['terminal_lf_interpretations']=dict(fields=len(batch),input_source_corpus_modified=False,runtime_verified=False)
    return out,dict(schema=1,locale=profile['locale'],entries=batch),proofs


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('corpus','profile','archive','elf','glossary','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();profile=json.loads(a.profile.read_text('utf8'));require(digest(a.corpus.read_bytes())==profile['source_corpus_sha256'],'terminal LF input corpus fingerprint mismatch')
    require(digest(a.archive.read_bytes())=='09d2e4d1f72e40b5d12da7b872226c446a21dde12bf1601bb4dfe58887a5d33a','terminal LF original archive mismatch');raw=a.elf.read_bytes();require(digest(raw)==ELF_SHA256,'terminal LF original ELF mismatch');image=ElfImage(raw);validate_anchors(image)
    c,b,e=derive(json.loads(a.corpus.read_text('utf8')),profile,dict(archive_entries(a.archive)[1]),image);validate(c,b,glossary_terms(a.glossary))
    c['terminal_lf_interpretations']['input_sha256']={str(q):digest(q.read_bytes()) for q in (a.corpus,a.profile,a.archive,a.elf,a.glossary)};a.out.mkdir(parents=True,exist_ok=False)
    for name,data in [('source-corpus.json',c),('selected-batch.json',b),('native-bindings.json',e)]:
        q=a.out/name;q.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8');require(json.loads(q.read_text('utf8'))==data,'terminal LF output reopen mismatch')
    print('TERMINAL_LF_INTERPRETATION_PASS fields='+str(len(b['entries']))+' native512=true terminal_0A_preserved=true input_corpus_unchanged=true runtime_verified=false')


if __name__=='__main__':main()
