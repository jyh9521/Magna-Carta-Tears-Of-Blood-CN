"""Bounded fixed-slot experiments using upstream slot serialization."""
import font_poc as core
from translate.slot import parse_slot_file,split_slot,build_slot_file,SLOT_FORMATS
from bundle_resource import overlay_segments

def prepare_slots(blob: bytes,ext: str,source: bytes,target: bytes,expected_matches: int) -> tuple[bytes,list[dict]]:
    core.require(source and target and b'\x00' not in source+target,'invalid name bytes')
    core.require(type(expected_matches) is int and expected_matches>0,'invalid expected count')
    header,slots=parse_slot_file(blob,ext);entries=[];changes=[]
    for index,(slot,cap) in enumerate(slots):
        raw,tail,trailer=split_slot(slot,cap)
        core.require(b'\x00' in slot[:cap],'unterminated slot')
        value=target if raw==source else raw
        entries.append((value,cap,tail,trailer))
        if raw==source:
            changes.append(dict(slot=index,offset=len(header)+index*SLOT_FORMATS[ext][1],capacity=tail-1,
                                original_bytes=len(raw),target_bytes=len(value),trailer_bytes=len(trailer)))
    core.require(len(changes)==expected_matches,'name slot count mismatch')
    originals=[(split_slot(slot,cap)[0],cap,split_slot(slot,cap)[1],split_slot(slot,cap)[2]) for slot,cap in slots]
    core.require(build_slot_file(header,originals,ext)==blob,'original slot roundtrip mismatch')
    result=build_slot_file(header,entries,ext)
    core.require(len(result)==len(blob) and result[:len(header)]==header,'resource size/header changed')
    modified_slots=parse_slot_file(result,ext)[1]
    selected={c['slot'] for c in changes}
    for index,((old,cap),(new,_)) in enumerate(zip(slots,modified_slots,strict=True)):
        if index not in selected:core.require(old==new,'untargeted slot changed')
        else:
            raw,tail,trailer=split_slot(old,cap)
            core.require(new[:len(target)]==target and new[len(target):tail]==bytes(tail-len(target))
                         and new[tail:]==trailer,'target padding/trailer mismatch')
    return result,changes


def mirror_resource(bundle: bytes,original: bytes,modified: bytes) -> tuple[bytes,int]:
    core.require(bundle.count(original)==1,'cached resource not unique')
    offset=bundle.index(original)
    output,_=overlay_segments(bundle,[dict(label='name-slot-resource',offset=offset,original=original,modified=modified)],
                              expected_sha256=core.digest(bundle))
    return output,offset
