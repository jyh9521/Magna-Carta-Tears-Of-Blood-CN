"""Explicit experimental name-slot selections; equal text never implies a group."""
from pathlib import Path
import font_poc as core
from localization.text import validate_target
from slot_resource import prepare_slots,mirror_resource
from translate.slot import SLOT_FORMATS


def name_cases(config: dict) -> list[dict]:
    cases=[]
    for plan in config.get('name_slot_overlays',[]):
        for row in plan['targets']:
            cases.append(dict(id=f"SHIP/{plan['resource']}/slot/{row['slot']}",kind='name-slot-experiment',
                              expected=row['target'],status='untested',evidence=[]))
    return cases


def apply_name_slots(ship: dict[str,bytes],bundle: bytes,encoder,plans: list[dict]) -> tuple[dict[str,bytes],bytes,list[dict]]:
    core.require(isinstance(plans,list),'name overlays must be a list')
    overrides={};reports=[]
    for plan in plans:
        name=plan['resource'];core.require(name in ship and name.lower() not in overrides,'unknown or duplicate name resource')
        ext=Path(name).suffix.lower();core.require(ext in SLOT_FORMATS,'unsupported name resource format')
        old=ship[name];core.require(core.digest(old)==plan['expected_sha256'],'name resource fingerprint mismatch')
        expected=plan['expected_slots'];rows=plan['targets']
        core.require(isinstance(expected,list) and expected and all(type(i) is int and i>=0 for i in expected)
                     and len(set(expected))==len(expected),'invalid expected name slots')
        core.require(isinstance(rows,list) and rows and all(type(r.get('slot')) is int for r in rows),'invalid name targets')
        indices=[r['slot'] for r in rows]
        core.require(len(set(indices))==len(indices) and set(indices)<=set(expected),'duplicate or unexpected target name slot')
        source=plan['source_text'].encode(plan['source_encoding']);result=bytearray(old);selected=[]
        for row in rows:
            validate_target(plan['source_text'],row['target']);target=encoder.encode(row['target'])
            proposed,all_matches=prepare_slots(old,ext,source,target,len(expected))
            core.require([r['slot'] for r in all_matches]==sorted(expected),'name slot inventory mismatch')
            entry=next(r for r in all_matches if r['slot']==row['slot']);offset=entry['offset'];stride=SLOT_FORMATS[ext][1]
            result[offset:offset+stride]=proposed[offset:offset+stride]
            selected.append(dict(**entry,target=row['target'],encoded_hex=target.hex()))
        modified=bytes(result);bundle,offset=mirror_resource(bundle,old,modified);overrides[name.lower()]=modified
        reports.append(dict(resource=name,original_sha256=core.digest(old),modified_sha256=core.digest(modified),
                            selected=selected,expected_slots=expected,cached_offset=offset,
                            semantic_group='unverified; explicit experimental selection only'))
    return overrides,bundle,reports
