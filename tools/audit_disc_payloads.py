"""Read-only whole-disc hash inventory and embedded MUSIC AFS inspection."""
from __future__ import annotations
import argparse
from collections import Counter
from contextlib import nullcontext
import hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs,AfsEntry

class BorrowedPath:
    def __init__(self,stream):self.stream=stream
    def open(self,mode):
        core.require(mode=='rb','read-only borrowed archive')
        self.stream.seek(0)
        return nullcontext(self.stream)

def stream_archive(stream,size):
    stream.seek(0);core.require(stream.read(4)==b'AFS\0','AFS signature')
    count=struct.unpack('<I',stream.read(4))[0]
    core.require(8+8*count+8<=size,'AFS count bounds')
    entries=[]
    for i in range(count):
        off,length=struct.unpack('<II',stream.read(8))
        core.require(off+length<=size,'AFS entry bounds')
        entries.append(AfsEntry(i,off,length))
    toc,ts=struct.unpack('<II',stream.read(8))
    core.require(toc+ts<=size,'AFS filename bounds')
    archive=Afs(path=BorrowedPath(stream),entries=entries,toc_offset=toc,toc_size=ts)
    names=archive.read_filename_toc()
    core.require(names is not None and len(names)==len(set(names)),'AFS filename inventory')
    return archive,names

def hash_stream(stream,limit):
    h=hashlib.sha256();n=0;prefix=b''
    while n<limit:
        b=stream.read(min(1024*1024,limit-n))
        core.require(bool(b),'truncated input')
        if not prefix:prefix=b[:64]
        h.update(b);n+=len(b)
    return h.hexdigest(),prefix

def audit(iso,expected,out):
    import pycdlib
    before=core.file_digest(iso);core.require(before==expected,'ISO identity mismatch')
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    cd=pycdlib.PyCdlib();cd.open(str(iso));rows=[];music=[]
    try:
        for parent,dirs,files in cd.walk(iso_path='/'):
            for name in files:
                path=parent.rstrip('/')+'/'+name;size=cd.get_record(iso_path=path).data_length
                with cd.open_file_from_iso(iso_path=path) as stream:
                    digest,prefix=hash_stream(stream,size)
                    row=dict(path=path,size=size,sha256=digest,prefix_hex=prefix.hex(),text_review='pending')
                    if size<=4096:
                        stream.seek(0);row['raw_hex']=stream.read(size).hex()
                    if path=='/MUSIC.AFS;1':
                        archive,names=stream_archive(stream,size)
                        for i,name in enumerate(names):
                            entry=archive.entries[i];stream.seek(entry.offset)
                            sha,first=hash_stream(stream,entry.size)
                            r=dict(index=i,name=name,offset=entry.offset,size=entry.size,sha256=sha,prefix_hex=first.hex())
                            if first[:2]==b'\x80\0' and len(first)>=16:
                                header_size=struct.unpack_from('>H',first,2)[0]+4
                                rate,samples=struct.unpack_from('>II',first,8)
                                r.update(header_bytes=header_size,encoding=first[4],block_size=first[5],sample_bits=first[6],
                                    channels=first[7],sample_rate=rate,sample_count=samples,
                                    nominal_seconds=samples/rate if rate else None,status='ADX-header-observed')
                            else:
                                r['status']='non-ADX-header'
                                if entry.size<=65536:r['raw_hex']=archive.read_entry(i,stream).hex()
                            music.append(r)
                        row['afs_entries']=len(music)
                    rows.append(row);print(path,size,flush=True)
    finally:cd.close()
    core.require(core.file_digest(iso)==before,'ISO changed')
    result=dict(schema=1,source_iso_sha256=before,iso_files=len(rows),all_file_bytes_hashed=sum(r['size'] for r in rows),
        file_extensions=dict(sorted(Counter(Path(r['path'].split(';')[0]).suffix.upper() for r in rows).items())),
        music_entries=len(music),music_headers=dict(Counter(r['status'] for r in music)),
        complete_game_text=False,result='all ISO files hashed; audio headers indexed; semantic review pending')
    for name,data in [('iso-files.json',rows),('music-inventory.json',music),('summary.json',result)]:
        p=out/name;p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        core.require(json.loads(p.read_text('utf8'))==data,'reopen mismatch')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--iso',type=Path,required=True);p.add_argument('--expected-sha256',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    print(json.dumps(audit(a.iso,a.expected_sha256,a.out),sort_keys=True))
