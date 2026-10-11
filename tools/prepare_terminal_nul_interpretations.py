"""Translate source-bound FPB prose while preserving terminal zero-byte padding."""
from pathlib import Path
import argparse,copy,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib','src')]
from font_poc import digest,archive_entries,require
from research_native import ElfImage,ELF_SHA256
from audit_native_playbook import native_evidence
from audit_native_chat import source_match,validate_anchors
from translate.fpb import parse_fpb_raw
from source_interpretation import source_text
from localization.text import TERMINAL_NUL_POLICY,terminal_nul_body,validate_target
from validate_translation_batch import validate,glossary_terms

def derive(corpus,profile,members):
    require(profile.get('schema')==1 and profile.get('locale')=='zh-CN','terminal NUL profile schema mismatch');out=copy.deepcopy(corpus);index={e['id']:(r,e) for r in out['resources'] for e in r['entries']};seen=set();batch=[];proofs=[]
    for d in profile['entries']:
        identity=d['id'];require(identity in index and identity not in seen,'terminal NUL duplicate/unknown source');seen.add(identity);r,e=index[identity]
        require(r['resource'].endswith('.fpb') and e.get('controls')=='quarantined' and e['decode']=='strict','terminal NUL requires strict quarantined FPB')
        require(d['resource']==r['resource'] and d['resource_sha256']==r['sha256'] and all(d[k]==e[k] for k in ('offset','source_bytes','source_sha256')),'terminal NUL source identity mismatch');original=members[Path(r['resource']).name];require(digest(original)==r['sha256'],'terminal NUL resource mismatch');pool=parse_fpb_raw(original)[2];span=pool[e['offset']:e['offset']+e['source_bytes']];source=span.decode('cp949');body=terminal_nul_body(source);n=len(source)-len(body)
        require(type(d['trailing_zero_bytes']) is int and n==d['trailing_zero_bytes'] and n>0,'terminal NUL padding count mismatch');require(digest(span)==e['source_sha256'] and source.encode('cp949')==span and source==d['source']==source_text(e) and digest(source.encode('utf8'))==d['reading_sha256'] and d['status']=='reviewed','terminal NUL source reading mismatch');validate_target(source,d['target'],control_policy=TERMINAL_NUL_POLICY);g=source_match(original,d['binding'])
        require(not any('가'<=ch<='힣' for ch in d['target']) and '—' not in d['target'] and '―' not in d['target'],'terminal NUL untranslated/dash target')
        e.update(controls='recognized',editable=True,backend_eligible=True,source_control_policy=TERMINAL_NUL_POLICY,source_control_interpretation=dict(schema=1,original_controls='quarantined',raw_sha256=e['source_sha256'],reading_sha256=d['reading_sha256'],target_sha256=digest(d['target'].encode('utf8')),native_binding_sha256=digest(json.dumps(d['binding'],sort_keys=True,separators=(',',':')).encode('utf8')),native_source_span_verified=True,runtime_control_semantics_verified=False,preserved_terminal_zero_bytes=n))
        batch.append(dict(id=identity,source_sha256=e['source_sha256'],target=d['target'],status='reviewed',reinsertion_policy='translate',context='Source-bound actual numeric FPB record; original terminal zero count retained in rebuilt record length. Target prose NUL-free; original source unchanged; event reachability/runtime layout not claimed.'));proofs.append(dict(id=identity,native=g,preserved_terminal_zero_bytes=n,runtime_verified=False))
    out['terminal_nul_interpretations']=dict(fields=len(batch),input_source_corpus_modified=False,runtime_verified=False);return out,dict(schema=1,locale=profile['locale'],entries=batch),proofs

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('corpus','profile','archive','elf','glossary','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();profile=json.loads(a.profile.read_text('utf8'));require(digest(a.corpus.read_bytes())==profile['source_corpus_sha256'],'terminal NUL input corpus fingerprint mismatch');require(digest(a.archive.read_bytes())=='09d2e4d1f72e40b5d12da7b872226c446a21dde12bf1601bb4dfe58887a5d33a','terminal NUL original archive mismatch');raw=a.elf.read_bytes();require(digest(raw)==ELF_SHA256,'terminal NUL original ELF mismatch');image=ElfImage(raw);native_evidence(image);validate_anchors(image)
    c,b,e=derive(json.loads(a.corpus.read_text('utf8')),profile,dict(archive_entries(a.archive)[1]));validate(c,b,glossary_terms(a.glossary));c['terminal_nul_interpretations']['input_sha256']={str(q):digest(q.read_bytes()) for q in (a.corpus,a.profile,a.archive,a.elf,a.glossary)};a.out.mkdir(parents=True,exist_ok=False)
    for name,data in [('source-corpus.json',c),('selected-batch.json',b),('native-bindings.json',e)]:
        q=a.out/name;q.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8');require(json.loads(q.read_text('utf8'))==data,'terminal NUL output reopen mismatch')
    print('TERMINAL_NUL_INTERPRETATION_PASS fields='+str(len(b['entries']))+' actual_numeric_key=true terminal_zero_count_preserved=true original_source_unchanged=true runtime_verified=false')
if __name__=='__main__':main()
