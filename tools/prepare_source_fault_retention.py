"""Bind explicit original-byte retention of faulty native FPB windows, not imports."""
from pathlib import Path
import argparse,copy,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib','src')]
from font_poc import digest,archive_entries,require
from audit_native_playbook import native_records,lookup,native_evidence
from research_native import ElfImage,ELF_SHA256
from translate.fpb import parse_fpb_raw

CLASSIFICATIONS=('split-multibyte-native-window','opaque-script-fragment','all-zero-native-window')

def check_decision(res,e,d,raw):
    require(d['id']==e['id'] and d['resource']==res['resource'] and all(d[k]==e[k] for k in ('offset','source_bytes','source_sha256')),'source fault field identity mismatch')
    require(res['resource'].endswith('.fpb') and digest(raw)==res['sha256']==d['resource_sha256'],'source fault resource fingerprint mismatch')
    require(d['status']=='reviewed' and d['import_approved'] is False and d['runtime_visibility_verified'] is False and d['disposition']=='retain-source-fault','source fault decision cannot approve import/runtime')
    require(isinstance(d.get('reason'),str) and bool(d['reason'].strip()),'source fault reason missing')
    records,pool=native_records(raw);at,n=e['offset'],e['source_bytes'];span=pool[at:at+n];require(len(span)==n and digest(span)==e['source_sha256'] and span.hex()==d['raw_hex'],'source fault raw span mismatch')
    matches=[i for i,(key,a,size) in enumerate(records) if a==at and size==n];require(len(matches)==1,'source fault native span ambiguous');i=matches[0];key=records[i][0];require(i==d['physical_index'] and key==d['native_record_key'] and lookup(records,key)==i,'source fault actual numeric key mismatch')
    whole=pool.decode('cp949');require(whole.encode('cp949')==pool,'source fault pool roundtrip mismatch');boundaries={0};cursor=0
    for ch in whole:cursor+=len(ch.encode('cp949'));boundaries.add(cursor)
    category=d['classification'];require(category in CLASSIFICATIONS,'unknown source fault classification')
    if category=='split-multibyte-native-window':
        require(e['decode']=='failed' and (at not in boundaries or at+n not in boundaries),'source fault not a split character window')
        try:span.decode('cp949')
        except UnicodeDecodeError:pass
        else:raise ValueError('source fault split window unexpectedly decodes')
    elif category=='all-zero-native-window':
        require(e['decode']=='strict' and e.get('controls')=='quarantined' and n>0 and not any(span),'source fault nonzero empty window')
    else:
        require(e['decode']=='strict' and e.get('controls')=='quarantined' and any(span),'source fault opaque fragment not strict quarantined')
        require(d.get('source')==span.decode('cp949') and d.get('linguistic_review')=='non-grammatical-prototype-fragment','source fault opaque reading decision missing')
    return dict(schema=1,classification=category,raw_sha256=e['source_sha256'],resource_sha256=res['sha256'],native_record_key=key,physical_index=i,original_decode=e['decode'],original_controls=e.get('controls'),raw_span_verified=True,native_source_span_verified=True,runtime_visibility_verified=False,import_approved=False,reason=d['reason'],decision_sha256=digest(json.dumps(d,sort_keys=True,separators=(',',':')).encode('utf8')))

def derive(corpus,profile,members):
    require(profile.get('schema')==1,'source fault profile schema mismatch');out=copy.deepcopy(corpus);ix={e['id']:(r,e) for r in out['resources'] for e in r['entries']};seen=set();proofs=[]
    for d in profile['entries']:
        require(d['id'] in ix and d['id'] not in seen,'source fault duplicate/unknown identity');seen.add(d['id']);res,e=ix[d['id']];proof=check_decision(res,e,d,members[Path(res['resource']).name]);e['source_fault_retention']=proof;proofs.append(dict(id=e['id'],**proof))
    out['source_fault_retentions']=dict(fields=len(proofs),original_decode_control_quarantine_unchanged=True,input_source_corpus_modified=False,import_approved=False,runtime_visibility_verified=False);return out,proofs

def verified_retention(entry):
    proof=entry.get('source_fault_retention')
    if proof is None:return False
    require(proof.get('schema')==1 and proof.get('classification') in CLASSIFICATIONS and proof.get('raw_sha256')==entry['source_sha256'] and proof.get('original_decode')==entry['decode'] and proof.get('original_controls')==entry.get('controls') and proof.get('raw_span_verified') is True and proof.get('native_source_span_verified') is True and proof.get('runtime_visibility_verified') is False and proof.get('import_approved') is False and isinstance(proof.get('decision_sha256'),str) and len(proof['decision_sha256'])==64,'source fault retention proof mismatch')
    require(entry.get('editable') is False and entry.get('backend_eligible') is not True,'source fault cannot become editable/backend eligible')
    return True

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('corpus','profile','archive','elf','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();profile=json.loads(a.profile.read_text('utf8'));require(digest(a.corpus.read_bytes())==profile['source_corpus_sha256'],'source fault input corpus mismatch');require(digest(a.archive.read_bytes())=='09d2e4d1f72e40b5d12da7b872226c446a21dde12bf1601bb4dfe58887a5d33a','source fault original archive mismatch');raw=a.elf.read_bytes();require(digest(raw)==ELF_SHA256,'source fault original ELF mismatch');native=native_evidence(ElfImage(raw));c,e=derive(json.loads(a.corpus.read_text('utf8')),profile,dict(archive_entries(a.archive)[1]));c['source_fault_retentions']['input_sha256']={str(q):digest(q.read_bytes()) for q in (a.corpus,a.profile,a.archive,a.elf)};a.out.mkdir(parents=True,exist_ok=False)
    for name,data in [('source-corpus.json',c),('native-bindings.json',dict(fields=e,native_protocol=native))]:
        q=a.out/name;q.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8');require(json.loads(q.read_text('utf8'))==data,'source fault output reopen mismatch')
    print('SOURCE_FAULT_RETENTION_PASS fields='+str(len(e))+' original_decode_controls_unchanged=true native_byte_windows_verified=true imports_approved=false runtime_visibility_verified=false')
if __name__=='__main__':main()
