"""Restore only a disposable test ISO copy to the fingerprinted original."""
from pathlib import Path
import argparse,json,shutil,struct,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('tools','lib')]
from font_poc import require,file_digest
from iso import _portable_metadata,SECTOR


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);p.add_argument('--copy',type=Path,required=True);a=p.parse_args();report=json.loads(a.report.read_text('utf8'));source=Path(report['source_iso']);live=Path(report['modified_iso']);dest=a.copy.resolve()
    require(dest.is_relative_to(ROOT/'work') and dest not in (source.resolve(),live.resolve()) and not dest.exists(),'rollback requires a new disposable work copy')
    require(file_digest(source)==report['source_sha256'] and file_digest(live)==report['modified_sha256'],'rollback ISO fingerprint mismatch')
    files,dirs=_portable_metadata(source);intervals=[]
    for name in report['replacements']:
        lba,size=files[name];intervals.append((lba*SECTOR,lba*SECTOR+size));parent=name.rsplit('/',1)[0] or '/';dlba,dsize=dirs[parent.rstrip('/')+'/']
        with source.open('rb') as f:f.seek(dlba*SECTOR);blob=f.read(dsize)
        pos=0;found=False
        while pos<len(blob):
            count=blob[pos]
            if not count:pos=(pos//SECTOR+1)*SECTOR;continue
            if blob[pos+33:pos+33+blob[pos+32]]==(name.rsplit('/',1)[1]+';1').encode('ascii'):intervals.append((dlba*SECTOR+pos+2,dlba*SECTOR+pos+18));found=True
            pos+=count
        require(found,'rollback directory record missing')
    intervals.append((16*SECTOR+80,16*SECTOR+88))
    for q in report['udf_plan']['patches']:
        if q['original']:intervals.append((q['offset'],q['offset']+len(bytes.fromhex(q['original']))))
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(live,dest)
    with source.open('rb') as before,dest.open('r+b') as after:
        for start,end in intervals:
            before.seek(start);after.seek(start);left=end-start
            while left:
                data=before.read(min(left,8*1024*1024));require(data,'rollback source truncated');after.write(data);left-=len(data)
        after.truncate(source.stat().st_size)
    require(file_digest(dest)==report['source_sha256'] and file_digest(live)==report['modified_sha256'],'ISO rollback identity mismatch')
    print('TEST_ISO_ROLLBACK_PASS restored_sha256='+report['source_sha256']+' live_modified_retained=true')
if __name__=='__main__':main()
