"""Prepare bounded name-slot/mirrored-cache resource experiments, not a bootable ISO."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import font_poc as core
from build_locale import load_config
from verify_expanded_locale import fresh_output,expected_fonts
from translate.slot import parse_slot_file,split_slot,build_slot_file,SLOT_FORMATS
from translate.celfid import decompress_chunked
from bundle_resource import overlay_segments
from localization.text import validate_target


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


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--iso',type=Path,required=True);p.add_argument('--font',type=Path,required=True)
    p.add_argument('--locale',type=Path,required=True);p.add_argument('--resource',required=True)
    p.add_argument('--source-name',required=True);p.add_argument('--target-name',required=True)
    p.add_argument('--expected-matches',type=int,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();locale,game,old_encoder=load_config(a.locale)
    core.require(core.file_digest(a.iso)==game['expected_iso_sha256'],'source ISO fingerprint mismatch')
    out=fresh_output(a.out,[a.iso,a.font,a.locale]);contents=core.iso_files(a.iso,['FILE.AFS','SHIP.AFS'])
    for name,data in contents.items():(out/name).write_bytes(data)
    files=dict(core.archive_entries(out/'FILE.AFS')[1]);ship=dict(core.archive_entries(out/'SHIP.AFS')[1])
    _,_,encoder=expected_fonts(files['MrtsEngine.u'],game,locale,old_encoder.entries,a.font,0xD0A1)
    ext=Path(a.resource).suffix.lower();core.require(ext in SLOT_FORMATS and a.resource in ship,'unknown slot resource')
    validate_target(a.source_name,a.target_name)
    source=a.source_name.encode('cp949');target=encoder.encode(a.target_name)
    original=ship[a.resource];modified,changes=prepare_slots(original,ext,source,target,a.expected_matches)
    bundle=decompress_chunked(files['celfid.lix']);core.require(core.digest(bundle)==game['expected_bundle_sha256'],'bundle fingerprint mismatch')
    mirrored,offset=mirror_resource(bundle,original,modified)
    core.require(mirrored[offset:offset+len(original)]==modified,'mirror readback mismatch')
    (out/'original-resource.bin').write_bytes(original);(out/'modified-resource.bin').write_bytes(modified)
    # Do not emit an original-font bundle carrying appended-font codes as a runnable image.
    plan=dict(schema=1,locale=locale['locale'],source_iso_sha256=game['expected_iso_sha256'],resource=a.resource,
              source_name=a.source_name,target_name=a.target_name,encoding='appended mapped-double-byte D0A1',
              original_sha256=core.digest(original),modified_sha256=core.digest(modified),resource_bytes=len(original),
              slots=changes,cached_resource_offset=offset,cached_bundle_sha256=core.digest(bundle),
              bundle_occurrences=bundle.count(source),ship_occurrences=sum(data.count(source) for data in ship.values()),
              runtime='unverified; isolated resources only',semantic_group='equal leading strings; not a verified linked group',
              iso_generated=False,cached_bundle_written=False,
              next_gate='identify display/lookup semantics; merge explicit slots into expanded-font package/cache before ISO build')
    core.require(core.file_digest(a.iso)==game['expected_iso_sha256'],'source ISO changed')
    (out/'name-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(f'NAME RESOURCE STATIC PASS slots={len(changes)} cached_copies=1 bytes={len(original)} iso_generated=false runtime=unverified')


if __name__=='__main__':main()
