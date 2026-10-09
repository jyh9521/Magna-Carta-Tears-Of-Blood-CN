"""Hash-bound containment of heuristic candidates in observed stream spans.

Containment is byte context, never visible-text classification or edit permission.
"""
from pathlib import Path
from bisect import bisect_right
from collections import Counter
import argparse,json,sys,struct
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from audit_container_payloads import unpack_chunks,probe_all_packages
from audit_bundle_contexts import BUNDLE_HASH
from extract_script_buffers import FILE_HASH
CORPUS_HASH='a9c7a9b0344cfebeda01014ffab83c00dd94e7e4b5de4d286eedc3447d031c18'
CORE_MAP_HASH='67be6726e872ed6952648c040467597cafa0f5cfc64edc51060db391d4b03f2a'
DEPENDENCY_MAP_HASH='2ced391d961ce51fc6ed97073b316f35aab3f94948d1f28e5c8ff8b2e49313de'

class SpanIndex:
    def __init__(self,rows):
        self.rows=sorted(rows,key=lambda x:x['start'])
        last=0
        for row in self.rows:
            core.require(type(row['start']) is int and type(row['end']) is int and 0<=row['start']<row['end'],'invalid span geometry')
            core.require(row['start']>=last,'overlapping oracle spans')
            last=row['end']
        self.starts=[r['start'] for r in self.rows]
    def containing(self,start,length):
        core.require(type(start) is int and type(length) is int and start>=0 and length>0,'invalid candidate geometry')
        i=bisect_right(self.starts,start)-1
        if i>=0 and start+length<=self.rows[i]['end']:return self.rows[i]
        return None

def build_spans(bundle,core_map,dependency_map,tables):
    rows=[]
    for package,data in [('Core.u',core_map),(None,dependency_map)]:
        pieces=list(data['chunks'])+(data.get('opaque',[]) if package else [])
        for piece in pieces:
            start=piece.get('start',piece['offset']);end=start+piece['bytes']
            core.require(0<=start<end<=len(bundle),'piece bounds')
            core.require(core.digest(bundle[start:end])==piece['sha256'],'piece hash mismatch')
            rows.append(dict(start=start,end=end,kind='bounded-script-prefix' if piece.get('part')=='bounded-prefix' else 'opaque-script' if 'semantic' in piece else 'source-identical-field',package=package or piece['package'],export=piece['export'],part=piece.get('part','opaque')))
    by_start={x['package_offset']-264:x for x in tables}
    for piece in dependency_map['embedded']:
        start,end=piece['start'],piece['end'];core.require(0<=start<end<=len(bundle),'embedded span bounds')
        kind=piece['kind']
        if kind=='stream-package-tables':
            core.require(start in by_start and by_start[start]['table_end']==end and by_start[start]['wrapper_path']==piece['path'],'table span identity')
        elif kind=='source-identical-ini':
            core.require(end-start==piece['bytes']+264 and core.digest(bundle[start+264:end])==piece['sha256'],'INI body mismatch')
        else:
            expected=piece.get('stream_sha256',piece.get('sha256'))
            core.require(expected and core.digest(bundle[start:end])==expected,'native span hash mismatch')
        rows.append(dict(start=start,end=end,kind=kind,identity_unique=piece.get('identity_unique',True)))
    index=SpanIndex(rows)
    core.require(core_map['root_complete'] and core_map['question'] is None and dependency_map['question'] is None,'oracle input incomplete at claimed boundary')
    core.require(core_map['stop_offset']==dependency_map['start'] and dependency_map['end']==3201448,'oracle boundary identity')
    return index

def wrapper_record(bundle,start,name,size):
    core.require(type(start) is int and 0<=start and start+132<=len(bundle),'wrapper record bounds')
    encoded=name.encode('ascii');core.require(0<len(encoded)<128 and type(size) is int and 0<size<=0xffffffff,'wrapper record identity')
    wanted=encoded+bytes(128-len(encoded))+struct.pack('<I',size)
    core.require(bundle[start:start+132]==wanted,'wrapper record mismatch')
    return dict(start=start,end=start+132,kind='source-wrapper-record')


def supplementary_spans(bundle,tables,configs):
    rows=[]
    for table in tables:
        start=table['package_offset']-264
        for offset in [start,start+132]:rows.append(wrapper_record(bundle,offset,table['wrapper_path'],table['original_package_size']))
    for name,raw in configs.items():
        core.require(bool(raw),'empty config mirror')
        start=0
        while True:
            offset=bundle.find(raw,start)
            if offset<0:break
            start=offset+1
            rows.append(wrapper_record(bundle,offset-264,name,len(raw)))
            rows.append(wrapper_record(bundle,offset-132,name,len(raw)))
            rows.append(dict(start=offset,end=offset+len(raw),kind='source-identical-config-body',resource='FILE/'+name,sha256=core.digest(raw)))
    for offset,name in [(0,'psx2game.ini'),(132,'psx2user.ini')]:
        core.require(name in configs,'missing initial manifest source')
        rows.append(wrapper_record(bundle,offset,name,len(configs[name])))
    return SpanIndex(rows)


def audit(archive,corpus_path,core_path,dependency_path,out):
    for path,wanted in [(archive,FILE_HASH),(corpus_path,CORPUS_HASH),(core_path,CORE_MAP_HASH),(dependency_path,DEPENDENCY_MAP_HASH)]:
        core.require(core.file_digest(path)==wanted,'input identity mismatch: '+str(path))
    afs=Afs.open(archive);names=filename_toc(afs)
    with archive.open('rb') as f:
        bundle,_=unpack_chunks(afs.read_entry(names.index('celfid.lix'),f))
        configs={name:afs.read_entry(i,f) for i,name in enumerate(names) if name.lower().endswith(('.ini','.int'))}
    core.require(core.digest(bundle)==BUNDLE_HASH,'bundle mismatch')
    corpus=json.loads(corpus_path.read_text('utf8'));tables=probe_all_packages(bundle)
    index=build_spans(bundle,json.loads(core_path.read_text('utf8')),json.loads(dependency_path.read_text('utf8')),tables)
    table_index=SpanIndex([dict(start=t['package_offset'],end=t['table_end'],kind='stream-package-table') for t in tables])
    resources={x['resource']:x for x in corpus['resources']};mirrors=[]
    for mirror in corpus['celfid_resource_mirrors']:
        resource=resources[mirror['resource']]
        for start in mirror['decompressed_offsets']:
            end=start+resource['size'];core.require(core.digest(bundle[start:end])==mirror['sha256'],'mirror mismatch')
            mirrors.append(dict(start=start,end=end,kind='resource-mirror',resource=mirror['resource']))
    mirror_index=SpanIndex(mirrors)
    extra_index=supplementary_spans(bundle,tables,configs)
    rows=[];counts=Counter();ids=set()
    for candidate in corpus['celfid_candidates']:
        ident=candidate['id'];core.require(ident not in ids,'duplicate candidate');ids.add(ident)
        start,size=candidate['offset'],candidate['source_bytes'];core.require(0<=start<start+size<=len(bundle),'candidate bounds')
        core.require(core.digest(bundle[start:start+size])==candidate['source_sha256'],'candidate hash')
        found=index.containing(start,size) or table_index.containing(start,size) or mirror_index.containing(start,size) or extra_index.containing(start,size)
        category=found['kind'] if found else 'unresolved-byte-context';counts[category]+=1
        rows.append(dict(id=ident,offset=start,bytes=size,source_sha256=candidate['source_sha256'],category=category,context=found,semantic_review='pending',editable=False))
    summary=dict(schema=1,candidates=len(rows),counts=dict(sorted(counts.items())),oracle_spans=len(index.rows),supplementary_spans=len(extra_index.rows),oracle_stop=3201448,all_candidate_hashes_checked=True,semantic_review_complete=False,complete_game_text=False,source_modified=False,translation_gate='coverage-audit-pending',corpus_sha256=CORPUS_HASH,core_map_sha256=CORE_MAP_HASH,dependency_map_sha256=DEPENDENCY_MAP_HASH)
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    for name,value in [('contexts.json',rows),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(value,indent=2)+'\n','utf8');core.require(json.loads(p.read_text('utf8'))==value,'JSON reopen')
    for path,wanted in [(archive,FILE_HASH),(corpus_path,CORPUS_HASH),(core_path,CORE_MAP_HASH),(dependency_path,DEPENDENCY_MAP_HASH)]:core.require(core.file_digest(path)==wanted,'input changed')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['archive','corpus','core-map','dependency-map','out']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.archive,a.corpus,a.core_map,a.dependency_map,a.out),sort_keys=True))
