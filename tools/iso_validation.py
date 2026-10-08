"""Verify upstream in-place/relocated ISO output without rebuilding an ISO."""
from pathlib import Path
import struct
from font_resource import require
from iso import _portable_metadata, SECTOR


def require_iso_overlay_layout(source: Path, replacements: dict[str, Path]) -> None:
    """Reject mixed UDF metadata changes before an output ISO is written."""
    import pycdlib
    cd=pycdlib.PyCdlib();cd.open(str(source))
    try: has_udf=cd.has_udf()
    finally: cd.close()
    old,_=_portable_metadata(source)
    require(set(replacements)<=old.keys(),'unknown ISO replacement')
    if has_udf:
        require(all(path.stat().st_size==old[name][1] for name,path in replacements.items()),
                'UDF size/relocation metadata synchronization required before ISO build')


def verify_iso_overlay(source: Path, modified: Path, replacements: dict[str, Path], *, udf_plan: dict | None = None) -> dict:
    old, directories = _portable_metadata(source); new, new_directories = _portable_metadata(modified)
    require(old.keys() == new.keys() and directories == new_directories, 'ISO file/directory inventory changed')
    require(replacements and set(replacements) <= old.keys(), 'unknown ISO replacement')
    require(source.stat().st_size % SECTOR == 0, 'source ISO not sector aligned')
    allowed=[]; relocated=0; append=source.stat().st_size
    with source.open('rb') as before, modified.open('rb') as after:
        for name,(lba,size) in old.items():
            if name not in replacements:
                require(new[name] == (lba,size), 'untargeted ISO extent changed'); continue
            replacement=replacements[name]; length=replacement.stat().st_size
            require(new[name][1] == length, 'replacement directory size mismatch')
            allowed.append((lba*SECTOR,lba*SECTOR+size))
        for name,replacement in replacements.items():
            lba,size=old[name];length=replacement.stat().st_size;actual_lba=new[name][0]
            if length <= size:
                require(actual_lba == lba, 'unexpected in-place relocation')
                after.seek(lba*SECTOR+length);require(after.read(size-length)==b'\xff'*(size-length),'in-place padding mismatch')
            else:
                require(actual_lba*SECTOR == append,'unexpected appended extent');relocated+=1
                after.seek(lba*SECTOR);require(after.read(size)==b'\xff'*size,'old relocated slot not cleared')
                padding=(-length)%SECTOR;after.seek(append+length);require(after.read(padding)==bytes(padding),'append padding mismatch')
                append+=length+padding
            after.seek(actual_lba*SECTOR)
            with replacement.open('rb') as expected:
                while chunk:=expected.read(8*1024*1024):require(after.read(len(chunk))==chunk,'replacement payload mismatch')
            parent=name.rsplit('/',1)[0] or '/';directory=directories[parent.rstrip('/')+'/']
            before.seek(directory[0]*SECTOR);blob=before.read(directory[1]);pos=0;found=False
            while pos<len(blob):
                count=blob[pos]
                if not count:pos=(pos//SECTOR+1)*SECTOR;continue
                if blob[pos+33:pos+33+blob[pos+32]]==(name.rsplit('/',1)[1]+';1').encode('ascii'):
                    allowed.append((directory[0]*SECTOR+pos+2,directory[0]*SECTOR+pos+18));found=True
                pos+=count
            require(found,'replacement directory record missing')
        if udf_plan:
            for patch in udf_plan['patches']:
                after.seek(patch['offset']);require(after.read(len(patch['modified']))==patch['modified'],'UDF overlay bytes mismatch')
                if patch['original']:allowed.append((patch['offset'],patch['offset']+len(patch['modified'])))
            append+=udf_plan['extra_sectors']*SECTOR
        require(modified.stat().st_size==append,'unexpected ISO output length')
        if relocated:
            position=16*SECTOR+80;allowed.append((position,position+8));after.seek(position)
            require(after.read(8)==struct.pack('<I',append//SECTOR)+struct.pack('>I',append//SECTOR),'PVD volume size mismatch')
        before.seek(0);after.seek(0);offset=0
        while chunk:=before.read(8*1024*1024):
            current=bytearray(after.read(len(chunk)))
            for start,end in allowed:
                lo=max(start,offset)-offset;hi=min(end,offset+len(chunk))-offset
                if lo<hi:current[lo:hi]=chunk[lo:hi]
            require(current==chunk,'untargeted ISO bytes changed at '+str(offset));offset+=len(chunk)
    if udf_plan:
        from udf_overlay import verify_udf_files
        verify_udf_files(modified,replacements,udf_plan)
    return dict(in_place=len(replacements)-relocated,relocated=relocated,original_bytes=source.stat().st_size,
                modified_bytes=append,untargeted_bytes_preserved=True,udf_synced=bool(udf_plan and udf_plan['has_udf']))
