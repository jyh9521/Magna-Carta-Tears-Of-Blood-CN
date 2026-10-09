"""Attach verified byte-range context to celfid candidates, not semantic labels."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from audit_container_payloads import unpack_chunks,probe_all_packages
from extract_script_buffers import FILE_HASH
BUNDLE_HASH='04ed29c9c4e65b1f14c4c2ae4b8578ad147af42b7dbaecdc62f57a3af56e3536'
CORPUS_HASH='3e92c5dcb2dcb5fe9ca2d513dcadf15bf37886e8eb0c080d9047a0265e6b816c'


def contexts(start,length,intervals):
    core.require(start>=0 and length>=0,'invalid candidate span')
    return [dict(kind=kind,identity=identity,start=low,end=high)
            for low,high,kind,identity in intervals if low<=start and start+length<=high]


def inventory(bundle,corpus):
    core.require(core.digest(bundle)==BUNDLE_HASH,'bundle identity mismatch')
    resources={r['resource']:r for r in corpus['resources']};intervals=[];mirrors=[]
    for mirror in corpus['celfid_resource_mirrors']:
        resource=resources[mirror['resource']]
        core.require(resource['sha256']==mirror['sha256'],'mirror resource identity mismatch')
        for start in mirror['decompressed_offsets']:
            end=start+resource['size'];core.require(end<=len(bundle),'mirror bounds')
            core.require(core.digest(bundle[start:end])==resource['sha256'],'mirror bytes mismatch')
            intervals.append((start,end,'exact-resource-mirror',resource['resource']))
            mirrors.append(dict(resource=resource['resource'],start=start,end=end,sha256=resource['sha256']))
    tables=probe_all_packages(bundle)
    for table in tables:
        intervals.append((table['package_offset'],table['table_end'],'stream-package-tables',table['wrapper_path']))
    counts=Counter();rows=[];ids=set()
    for candidate in corpus['celfid_candidates']:
        core.require(candidate['id'] not in ids,'duplicate candidate');ids.add(candidate['id'])
        start=candidate['offset'];length=candidate['source_bytes']
        core.require(0<=start<=start+length<=len(bundle),'candidate bounds')
        core.require(core.digest(bundle[start:start+length])==candidate['source_sha256'],'candidate bytes mismatch')
        found=contexts(start,length,intervals)
        category=found[0]['kind'] if found else 'other-payload';counts[category]+=1
        rows.append(dict(id=candidate['id'],offset=start,bytes=length,sha256=candidate['source_sha256'],
            byte_context=found,category=category,semantic_review='pending',editable=False))
    summary=dict(bundle_sha256=BUNDLE_HASH,candidates=len(rows),counts=dict(counts),
        exact_mirror_occurrences=len(mirrors),stream_package_table_occurrences=len(tables),
        complete_game_text=False,celfid_semantics_complete=False,linked_groups_verified=False)
    return rows,mirrors,summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--corpus',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    core.require(core.file_digest(a.archive)==FILE_HASH,'FILE identity mismatch')
    core.require(core.file_digest(a.corpus)==CORPUS_HASH,'source corpus identity mismatch')
    archive=Afs.open(a.archive);names=filename_toc(archive)
    with a.archive.open('rb') as stream:bundle,_=unpack_chunks(archive.read_entry(names.index('celfid.lix'),stream))
    rows,mirrors,summary=inventory(bundle,json.loads(a.corpus.read_text('utf8')))
    out=core.output_directory(a.out)
    for name,value in [('contexts.json',rows),('mirrors.json',mirrors),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8');core.require(json.loads(p.read_text('utf8'))==value,'reopen mismatch')
    core.require(core.file_digest(a.archive)==FILE_HASH,'FILE changed')
    print(json.dumps(summary,sort_keys=True))
if __name__=='__main__':main()
