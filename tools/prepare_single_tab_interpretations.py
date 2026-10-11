"""Preserve one original TAB in version-bound TUI main text slots."""
from pathlib import Path
import argparse,copy,json,struct,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib','src')]
from font_poc import digest,archive_entries,require
from research_native import ElfImage,ELF_SHA256
from audit_native_text_loaders import loader
from audit_native_field_text import native_binding,run_lookup as field_lookup
from audit_native_text_index import run_lookup
from source_interpretation import source_text
from localization.text import SINGLE_TAB_POLICY,validate_target
from validate_translation_batch import validate,glossary_terms

SPECS={'SHIP/00000682.tui':dict(sha='2b3d6613e01e1d62f750ef1261f8223e7bb804b39225951af4381c69aaf1e0a5',loader=0x308600,path=0x4b7830,array=0x160,lookup=0x3131c0),
       'SHIP/00001240.tui':dict(sha='e51d42d096a485949f27d23b8549eb0f56049099214ad688cb225590662e7a83')}

def geometry(res,e,d,original,image):
    require(res['resource'] in SPECS,'unsupported single TAB resource');spec=SPECS[res['resource']]
    require(digest(original)==res['sha256']==d['resource_sha256']==spec['sha'],'single TAB original resource fingerprint mismatch')
    count,kind=struct.unpack_from('<II',original);require(kind==2 and len(original)==8+count*516,'single TAB TUI geometry mismatch')
    i=e['record_index'];require(type(i) is int and 0<=i<count and i==d['physical_index'] and e['half']==0 and e['offset']==12+i*516,'single TAB main record mismatch')
    keys=[struct.unpack_from('<I',original,8+j*516)[0] for j in range(count)];require(keys[i]==e['record_id']==d['record_key'],'single TAB numeric source key mismatch')
    slot=original[e['offset']:e['offset']+256];n=e['source_bytes'];require(0<n<256 and slot[n]==0 and not any(slot[n:]) and digest(slot[:n])==e['source_sha256'] and digest(slot)==e['slot_sha256'],'single TAB source slot/padding mismatch')
    if res['resource']=='SHIP/00001240.tui':native=native_binding(image);selected=field_lookup(image,keys,keys[i])
    else:native=loader(image,spec['loader'],spec['path'],spec['array'],Path(res['resource']).name);selected=run_lookup(image,spec['lookup'],spec['array'],keys,keys[i])
    require(selected['found'] and selected['index']==i,'single TAB actual key lookup mismatch')
    return dict(native=native,actual_key_lookup=selected,writable_bytes=256,source_tab_byte='09',runtime_verified=False)

def derive(corpus,profile,members,image):
    require(profile.get('schema')==1 and profile.get('locale')=='zh-CN','single TAB profile schema mismatch');out=copy.deepcopy(corpus);index={e['id']:(r,e) for r in out['resources'] for e in r['entries']};seen=set();batch=[];proofs=[]
    for d in profile['entries']:
        identity=d['id'];require(identity in index and identity not in seen,'single TAB duplicate/unknown source');seen.add(identity);r,e=index[identity]
        require(e.get('controls')=='quarantined' and e['decode']=='strict','single TAB requires strict quarantined source')
        require(d['resource']==r['resource'] and all(d[k]==e[k] for k in ('offset','source_bytes','source_sha256')),'single TAB source identity mismatch');original=members[Path(r['resource']).name];span=original[e['offset']:e['offset']+e['source_bytes']];source=span.decode('cp949')
        require(source.encode('cp949')==span and source==d['source']==source_text(e) and digest(source.encode('utf8'))==d['reading_sha256'] and d['status']=='reviewed','single TAB source reading mismatch');validate_target(source,d['target'],control_policy=SINGLE_TAB_POLICY);g=geometry(r,e,d,original,image)
        require(not any('가'<=ch<='힣' for ch in d['target']) and '—' not in d['target'] and '―' not in d['target'],'single TAB untranslated/dash target')
        e.update(controls='recognized',editable=True,backend_eligible=True,source_control_policy=SINGLE_TAB_POLICY,source_control_interpretation=dict(schema=1,original_controls='quarantined',raw_sha256=e['source_sha256'],reading_sha256=d['reading_sha256'],target_sha256=digest(d['target'].encode('utf8')),native_binding_sha256=digest(json.dumps(d,sort_keys=True,separators=(',',':')).encode('utf8')),native_source_span_verified=True,runtime_control_semantics_verified=False))
        batch.append(dict(id=identity,source_sha256=e['source_sha256'],target=d['target'],status='reviewed',reinsertion_policy='translate',context='Original TAB byte09 preserved; numeric values stay on original side of TAB.256byte TUI main native storage and actual numeric lookup bound. Runtime layout not claimed.'));proofs.append(dict(id=identity,geometry=g))
    out['single_tab_interpretations']=dict(fields=len(batch),input_source_corpus_modified=False,runtime_verified=False);return out,dict(schema=1,locale=profile['locale'],entries=batch),proofs

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('corpus','profile','archive','elf','glossary','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();profile=json.loads(a.profile.read_text('utf8'));require(digest(a.corpus.read_bytes())==profile['source_corpus_sha256'],'single TAB input corpus fingerprint mismatch');require(digest(a.archive.read_bytes())=='09d2e4d1f72e40b5d12da7b872226c446a21dde12bf1601bb4dfe58887a5d33a','single TAB original archive mismatch');raw=a.elf.read_bytes();require(digest(raw)==ELF_SHA256,'single TAB original ELF mismatch')
    c,b,e=derive(json.loads(a.corpus.read_text('utf8')),profile,dict(archive_entries(a.archive)[1]),ElfImage(raw));validate(c,b,glossary_terms(a.glossary));c['single_tab_interpretations']['input_sha256']={str(q):digest(q.read_bytes()) for q in (a.corpus,a.profile,a.archive,a.elf,a.glossary)};a.out.mkdir(parents=True,exist_ok=False)
    for name,data in [('source-corpus.json',c),('selected-batch.json',b),('native-bindings.json',e)]:
        q=a.out/name;q.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8');require(json.loads(q.read_text('utf8'))==data,'single TAB output reopen mismatch')
    print('SINGLE_TAB_INTERPRETATION_PASS fields='+str(len(b['entries']))+' native256=true actual_numeric_keys=true original_byte09_preserved=true runtime_verified=false')
if __name__=='__main__':main()
