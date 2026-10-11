"""Preserve explicitly reviewed configuration metadata with exact static bindings.

Retention is an engineering decision, not proof of runtime invisibility. Original
semantic classifications, encoding and import eligibility remain unchanged.
"""
from pathlib import Path
import argparse, copy, hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('tools','lib','src')]
from font_poc import archive_entries, require, digest
from research_native import ElfImage, ELF_SHA256

def verified_retention(entry):
    p=entry.get('config_metadata_retention')
    if p is None:return False
    require(p.get('schema')==1 and p.get('source_sha256')==entry['source_sha256']
        and p.get('semantic')==entry.get('semantic') and p.get('source_bytes_verified') is True
        and p.get('native_binding_verified') is True and p.get('import_approved') is False
        and p.get('runtime_visibility_verified') is False and entry.get('editable') is False
        and entry.get('decode')=='strict' and entry.get('controls')!='quarantined'
        and entry.get('backend_eligible') is not True
        and p.get('role') in ('default-player-identity','protocol-description-metadata')
        and len(p.get('decision_sha256',''))==64,'configuration retention proof mismatch')
    return True

def derive(corpus,profile,members,image):
    require(profile.get('schema')==1,'configuration retention schema mismatch')
    require(digest(image.blob)==ELF_SHA256==profile['elf_sha256'],'configuration ELF mismatch')
    out=copy.deepcopy(corpus);index={e['id']:(r,e) for r in out['resources'] for e in r['entries']};seen=set();proofs=[]
    for d in profile['entries']:
        require(d['id'] in index and d['id'] not in seen,'duplicate/missing configuration identity');seen.add(d['id'])
        r,e=index[d['id']];raw=members[Path(r['resource']).name]
        require(r['resource'].startswith('FILE/') and Path(r['resource']).suffix=='.ini'
            and digest(raw)==r['sha256']==d['resource_sha256'],'configuration resource mismatch')
        require(all(d[k]==e[k] for k in ('offset','source_bytes','source_sha256','section','key'))
            and d['resource']==r['resource'] and d['source']==e['references']['und'],'configuration source binding mismatch')
        span=raw[e['offset']:e['offset']+e['source_bytes']]
        require(digest(span)==e['source_sha256'] and span.decode('ascii')==d['source'],'configuration source bytes mismatch')
        require(e.get('semantic')=='unresolved' and e.get('decode')=='strict'
            and e.get('controls')!='quarantined' and e.get('editable') is False
            and e.get('backend_eligible') is not True,'configuration retention cannot bypass quarantine/import eligibility')
        require(d['status']=='reviewed' and d['import_approved'] is False
            and d['runtime_visibility_verified'] is False and d['disposition']=='retain-config-metadata'
            and bool(d['reason'].strip()),'configuration retention decision mismatch')
        require(d['role'] in ('default-player-identity','protocol-description-metadata') and bool(d['native_windows']),'configuration role/binding missing')
        for w in d['native_windows']:
            va=int(w['va'],16);expected=bytes.fromhex(w['hex']);at=image.to_offset(va)
            require(len(expected)>=16 and len(expected)%4==0 and image.blob[at:at+len(expected)]==expected,'configuration native instruction mismatch')
        p=dict(schema=1,source_sha256=e['source_sha256'],semantic=e['semantic'],role=d['role'],
            source_bytes_verified=True,native_binding_verified=True,import_approved=False,
            runtime_visibility_verified=False,reason=d['reason'],
            decision_sha256=digest(json.dumps(d,sort_keys=True,separators=(',',':')).encode('utf8')))
        e['config_metadata_retention']=p;verified_retention(e);proofs.append(dict(id=e['id'],**p))
    require(bool(seen),'empty configuration retention profile')
    return out,proofs

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('corpus','profile','archive','elf','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();profile=json.loads(a.profile.read_text('utf8'))
    require(digest(a.corpus.read_bytes())==profile['source_corpus_sha256'],'configuration input corpus mismatch')
    require(digest(a.archive.read_bytes())==profile['archive_sha256'],'configuration input archive mismatch')
    out,proofs=derive(json.loads(a.corpus.read_text('utf8')),profile,dict(archive_entries(a.archive)[1]),ElfImage(a.elf.read_bytes()))
    a.out.mkdir(parents=True,exist_ok=False)
    for n,v in [('source-corpus.json',out),('config-retention.json',dict(fields=proofs,original_semantics_unchanged=True,runtime_visibility_verified=False))]:
        q=a.out/n;q.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8');require(json.loads(q.read_text('utf8'))==v,'configuration output reopen mismatch')
    print('CONFIG_METADATA_RETENTION_PASS fields='+str(len(proofs))+' original_semantics_unchanged=true source_bytes_preserved=true import_approved=false runtime_visibility_verified=false')
if __name__=='__main__':main()
