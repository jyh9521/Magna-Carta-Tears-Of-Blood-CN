"""Inspect valid compressed prefixes without accepting unresolved archive tails."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import struct
import sys
import zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from audit_container_payloads import probe_all_packages
LINEAR_HASH='1c86cd48019b10e2c9566ec92fbb9db79cebd2a58f3984036b7841b7f782a33a'


def prefix_frames(blob):
    pos=0;parts=[];frames=[];reason=None
    while pos<len(blob):
        if len(blob)-pos<8:reason='truncated header';break
        unc,cmp=struct.unpack_from('<II',blob,pos)
        if not(0<unc<=24576 and 0<cmp and pos+8+cmp<=len(blob)):
            reason='invalid frame bounds';break
        try:
            decoder=zlib.decompressobj();data=decoder.decompress(blob[pos+8:pos+8+cmp])
            if not(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail and len(data)==unc):
                reason='frame stream/length mismatch';break
        except zlib.error:reason='invalid zlib stream';break
        frames.append(dict(offset=pos,compressed_bytes=cmp,uncompressed_bytes=unc))
        parts.append(data);pos+=8+cmp
    tail=blob[pos:]
    return b''.join(parts),dict(valid_frames=frames,prefix_end=pos,remaining_bytes=len(tail),
        tail_sha256=core.digest(tail),stop_reason=reason,complete_framing=pos==len(blob))


def manifest_rows(blob):
    lines=blob.decode('ascii',errors='strict').split('\r\n')
    core.require(lines[-1]=='' and len(lines[:-1])%2==0,'manifest geometry')
    core.require(lines[:2]==['AFSLINEARFileIndex','0'],'manifest header')
    rows={}
    for pos in range(2,len(lines)-1,2):
        name,size=lines[pos:pos+2]
        core.require(name and name not in rows and size.isdecimal(),'manifest row')
        rows[name]=int(size)
    return rows


def audit(path,questions,out):
    core.require(core.file_digest(path)==LINEAR_HASH,'LINEAR identity mismatch')
    archive=Afs.open(path);names=filename_toc(archive);rows=[];packages=[];classes=Counter()
    with path.open('rb') as stream:
        manifest=manifest_rows(archive.read_entry(0,stream))
        core.require(set(manifest)=={n[:-4] for n in names[1:]},'manifest/TOC inventory mismatch')
        mismatches=[]
        for index,name in enumerate(names[1:],1):
            size=len(archive.read_entry(index,stream))
            if manifest[name[:-4]]!=size:mismatches.append(dict(name=name,manifest=manifest[name[:-4]],toc=size))
        for question in questions:
            core.require(question['archive']=='LINEAR.AFS','unexpected archive question')
            index=question['index'];name=question['name'];core.require(names[index]==name,'question resource mismatch')
            blob=archive.read_entry(index,stream);payload,framing=prefix_frames(blob)
            core.require(not framing['complete_framing'],'expected unresolved tail absent')
            row=dict(name=name,index=index,bytes=len(blob),sha256=core.digest(blob),
                manifest_size=manifest[name[:-4]],prefix_payload_bytes=len(payload),
                prefix_payload_sha256=core.digest(payload),**framing,
                semantic_coverage_complete=False,tail_disposition='unresolved; not discarded')
            try:
                tables=probe_all_packages(payload)
                for table in tables:
                    packages.append(dict(name=name,index=index,partial_payload=True,**table))
                    classes.update(e['class'] for e in table['exports'])
                row['prefix_package_tables']=len(tables)
            except (ValueError,IndexError,struct.error,UnicodeError) as error:row['table_question']=str(error)
            rows.append(row)
    core.require(core.file_digest(path)==LINEAR_HASH,'LINEAR changed')
    summary=dict(source_sha256=LINEAR_HASH,manifest_rows=len(manifest),manifest_mismatches=mismatches,
        unresolved_resources=len(rows),prefix_package_occurrences=len(packages),export_classes=dict(classes),
        complete_game_text=False,tail_semantics_verified=False,serial_mapping='unresolved')
    out=core.output_directory(out)
    for name,value in [('framing.json',rows),('prefix-tables.json',packages),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        core.require(json.loads(p.read_text('utf8'))==value,'reopen mismatch')
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--questions',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.archive,json.loads(a.questions.read_text('utf8')),a.out),sort_keys=True))
if __name__=='__main__':main()
