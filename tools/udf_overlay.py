"""Narrow UDF metadata overlay around the upstream ISO9660 patcher.

Supports one physical partition, short file allocation descriptors and
standard File Entries. Other layouts fail before the output is written.
"""
from __future__ import annotations
import binascii
import struct
from pathlib import Path
from font_resource import require
from iso import _portable_metadata, SECTOR, _patch_pvd_volume_size


def validate_tag(block: bytes) -> None:
    require(len(block)==SECTOR,'invalid descriptor sector size')
    length=struct.unpack_from('<H',block,10)[0]
    require(length<=SECTOR-16,'descriptor CRC outside sector')
    require(block[4]==(sum(block[:4])+sum(block[5:16]))&255,'descriptor tag checksum mismatch')
    require(struct.unpack_from('<H',block,8)[0]==binascii.crc_hqx(block[16:16+length],0),'descriptor CRC mismatch')


def retag(block: bytes) -> bytes:
    result=bytearray(block);length=struct.unpack_from('<H',result,10)[0]
    require(length<=SECTOR-16,'descriptor CRC outside sector')
    struct.pack_into('<H',result,8,binascii.crc_hqx(result[16:16+length],0))
    result[4]=(sum(result[:4])+sum(result[5:16]))&255
    validate_tag(bytes(result));return bytes(result)


def require_empty_space_descriptors(partition) -> None:
    for name in ('freed_space_bitmap','freed_space_table','partition_integrity_table','unalloc_space_bitmap','unalloc_space_table'):
        descriptor=getattr(partition.part_contents_use,name)
        require(descriptor.extent_length==0 and descriptor.log_block_num==0,
                'UDF space-management descriptor requires additional synchronization')


def plan_udf_overlay(source: Path, replacements: dict[str, Path]) -> dict:
    import pycdlib
    from pycdlib.udf import UDFFileEntry,UDFShortAD
    files,_=_portable_metadata(source)
    require(set(replacements)<=files.keys(),'unknown ISO replacement')
    cd=pycdlib.PyCdlib();cd.open(str(source))
    try:
        if not cd.has_udf():return dict(patches=[],files=[],extra_sectors=0,has_udf=False)
        main=cd.udf_main_descs.partitions;reserve=cd.udf_reserve_descs.partitions
        require(len(main)==len(reserve)==1,'UDF requires one physical partition')
        partition=main[0];start=partition.part_start_location
        require(partition.part_num==0 and partition.access_type==1 and reserve[0].part_start_location==start
                and reserve[0].part_length==partition.part_length,'UDF partition geometry mismatch')
        for item in (main[0],reserve[0]):require_empty_space_descriptors(item)
        for sequence in (cd.udf_main_descs,cd.udf_reserve_descs):
            require(len(sequence.logical_volumes)==1 and len(sequence.logical_volumes[0].partition_maps)==1
                    and type(sequence.logical_volumes[0].partition_maps[0]).__name__=='UDFType1PartitionMap',
                    'UDF requires a physical Type1 partition map')
        integrity=cd.udf_logical_volume_integrity
        require(integrity.num_partitions==1 and integrity.size_tables==[partition.part_length]
                and integrity.free_space_tables==[0] and integrity.integrity_type==1,'unsupported UDF integrity state')
        paths={}
        for parent,_,names in cd.walk(udf_path='/'):
            for name in names:
                path=parent.rstrip('/')+'/'+name;key=path.upper()
                require(key not in paths,'ambiguous UDF filename');paths[key]=path
        patches=[];targets=[];append=source.stat().st_size;grew=False
        with source.open('rb') as stream:
            def sector(lba):
                stream.seek(lba*SECTOR);raw=stream.read(SECTOR);validate_tag(raw);return raw
            def change(label,lba,edits):
                old=sector(lba);new=bytearray(old)
                for offset,fmt,expected,value in edits:
                    require(struct.unpack_from(fmt,old,offset)[0]==expected,'UDF field mismatch: '+label)
                    struct.pack_into(fmt,new,offset,value)
                patches.append(dict(label=label,offset=lba*SECTOR,original=old,modified=retag(bytes(new))))
            for name,path in replacements.items():
                require(name.upper() in paths,'UDF file missing')
                udf_path=paths[name.upper()];entry=cd.get_record(udf_path=udf_path)
                require(type(entry) is UDFFileEntry and len(entry.alloc_descs)==1 and type(entry.alloc_descs[0]) is UDFShortAD
                        and entry.icb_tag.flags&7==0 and entry.icb_tag.file_type==5,'unsupported UDF file allocation')
                allocation=entry.alloc_descs[0];lba,size=files[name];length=path.stat().st_size
                require(allocation.extent_type==0 and allocation.log_block_num+start==lba and allocation.extent_length==size
                        and entry.info_len==size,'ISO/UDF source file views disagree')
                require(0<length<0x40000000,'UDF short extent length overflow')
                new_lba=lba
                if length>size:new_lba=append//SECTOR;append+=(length+SECTOR-1)//SECTOR*SECTOR;grew=True
                ad=176+entry.len_extended_attrs
                require(ad+8<=SECTOR,'UDF allocation outside sector')
                change('file:'+udf_path,entry.extent_location(),[(56,'<Q',size,length),
                    (64,'<Q',entry.log_block_recorded,(length+SECTOR-1)//SECTOR),
                    (ad,'<I',size,length),(ad+4,'<I',allocation.log_block_num,new_lba-start)])
                targets.append(dict(iso_path=name,udf_path=udf_path,lba=new_lba,size=length))
            if grew:
                # Preserve the original trailing anchor; append a new anchor
                # outside the expanded partition, never over replacement data.
                require(source.stat().st_size%SECTOR==0,'unaligned source ISO')
                trailing=[a for a in cd.udf_anchors if a.extent_location()==source.stat().st_size//SECTOR-1]
                require(len(trailing)==1,'source trailing UDF anchor missing')
                raw=sector(trailing[0].extent_location());new=bytearray(raw)
                struct.pack_into('<I',new,12,append//SECTOR)
                patches.append(dict(label='new-tail-anchor',offset=append,original=b'',modified=retag(bytes(new))))
                length=append//SECTOR-start
                for p in (main[0],reserve[0]):change('partition',p.extent_location(),[(192,'<I',p.part_length,length)])
                change('integrity',integrity.extent_location(),[(84,'<I',partition.part_length,length)])
        return dict(patches=patches,files=targets,extra_sectors=int(grew),has_udf=True)
    finally:cd.close()


def apply_udf_overlay(modified: Path, plan: dict) -> None:
    with modified.open('r+b') as stream:
        for patch in plan['patches']:
            stream.seek(patch['offset'])
            require(stream.read(len(patch['original']))==patch['original'],'UDF descriptor changed before overlay')
            if not patch['original']:require(modified.stat().st_size==patch['offset'],'UDF anchor append mismatch')
            stream.seek(patch['offset']);stream.write(patch['modified'])
    if plan['extra_sectors']:_patch_pvd_volume_size(modified,modified.stat().st_size//SECTOR)


def verify_udf_files(modified: Path, replacements: dict[str,Path], plan: dict) -> None:
    import io
    import pycdlib
    if not plan['has_udf']:return
    cd=pycdlib.PyCdlib();cd.open(str(modified))
    try:
        partition=cd.udf_main_descs.partitions[0]
        for item in plan['files']:
            entry=cd.get_record(udf_path=item['udf_path']);allocation=entry.alloc_descs[0]
            require(entry.info_len==allocation.extent_length==item['size'] and
                    allocation.log_block_num+partition.part_start_location==item['lba'],'UDF target geometry mismatch')
            result=io.BytesIO();cd.get_file_from_iso_fp(result,udf_path=item['udf_path'])
            require(result.getvalue()==replacements[item['iso_path']].read_bytes(),'UDF payload mismatch')
    finally:cd.close()
