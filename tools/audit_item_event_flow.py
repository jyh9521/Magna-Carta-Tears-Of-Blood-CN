"""Read-only, fingerprint-bound audit of serialized event item handoffs."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'lib')]
from cri_afs import Afs
from afs import filename_toc
from research_native import ElfImage
from audit_text_slicing import scalar


def digest(data):
    return hashlib.sha256(data).hexdigest()


def parse_plans(blob, offset):
    def integer():
        nonlocal offset
        if not 0 <= offset <= len(blob)-4:
            raise ValueError('event table outside resource')
        value = struct.unpack_from('<i', blob, offset)[0]
        offset += 4
        return value
    count = integer()
    if not 1 <= count <= 1000:
        raise ValueError('unexpected plan count')
    plans = []
    for index in range(count):
        row = dict(index=index, offset=offset, repetitions=integer())
        if row['repetitions'] not in (0, 1):
            raise ValueError('unsupported repetition field')
        for field in ('pIf', 'pThen'):
            n = integer()
            if not 0 <= n <= 10000 or offset+n*60 > len(blob):
                raise ValueError('invalid command count')
            commands = []
            for j in range(n):
                at = offset
                cmd = integer()
                params = [integer() for _ in range(14)]
                if not 0 <= cmd < 10000:
                    raise ValueError('invalid event command')
                commands.append(dict(index=j, offset=at, cmd=cmd, params=params))
            row[field] = commands
        plans.append(row)
    return plans, offset


def native_spend_checks(image):
    results = []
    for quantity in (1, 2):
        memory = {}
        for at, value in [(0x100028,0x110000), (0x1107f0,0x120000),
                          (0x1107f4,1), (0x120000,497), (0x120004,quantity)]:
            for j,b in enumerate(struct.pack('<I',value)):
                memory[at+j] = b
        stop = 0x39fbc0 if quantity == 1 else 0x39fbf0
        state = scalar(image,0x39fb6c,stop,{4:0x100000,5:497,6:1,9:0},memory)
        remaining = int.from_bytes(bytes(memory[0x120004+j] for j in range(4)),'little')
        if remaining != quantity-1:
            raise ValueError('original native decrement mismatch')
        arguments = None
        if quantity == 1:
            regs = dict(enumerate(state['registers']))
            state = scalar(image,0x39fbc0,0x39fbd0,regs,memory)
            # Execute the JAL delay-slot instruction separately; stop before the callee.
            state = scalar(image,0x39fbd4,0x39fbd8,dict(enumerate(state['registers'])),memory)
            arguments = [state['registers'][j] for j in (4,5,6,7)]
            if arguments != [0x1107f0,0,1,8]:
                raise ValueError('Array.Remove argument mismatch')
        results.append(dict(before=quantity,after=remaining,array_remove_arguments=arguments))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('ship','elf','profile','out'):
        parser.add_argument('--'+key,type=Path,required=True)
    args = parser.parse_args()
    if args.out.resolve() in [p.resolve() for p in (args.ship,args.elf,args.profile)]:
        raise ValueError('report must not overwrite inputs')
    profile = json.loads(args.profile.read_text('utf8'))
    elf = args.elf.read_bytes()
    if profile.get('schema') != 1 or digest(elf) != profile['elf_sha256']:
        raise ValueError('unsupported ELF/profile')
    with args.ship.open('rb') as stream:
        ship_hash = hashlib.file_digest(stream,'sha256').hexdigest()
    if ship_hash != profile['ship_sha256']:
        raise ValueError('unsupported SHIP archive')
    archive = Afs.open(args.ship)
    names = filename_toc(archive)
    resources = {}
    raw_candidates = []
    with args.ship.open('rb') as stream:
        for name, binding in profile['resources'].items():
            blob = archive.read_entry(names.index(name),stream)
            if digest(blob) != binding['sha256'] or struct.unpack_from('<I',blob)[0] != binding['version']:
                raise ValueError('event resource identity/version mismatch')
            plans,end = parse_plans(blob,binding['event_offset'])
            resources[name] = dict(sha256=digest(blob),event_offset=binding['event_offset'],
                                  event_end=end,trailing_bytes=len(blob)-end,plans=plans)
        item_blob = archive.read_entry(names.index('00000953.itm'),stream)
        count,version = struct.unpack_from('<II',item_blob)
        if (count,version,len(item_blob)) != (479,25,8+479*594):
            raise ValueError('unsupported item table')
        items = []
        for index in range(count):
            at = 8+index*594
            key = struct.unpack_from('<I',item_blob,at)[0]
            name = item_blob[at+4:at+259].split(b'\0',1)[0].decode('cp949')
            items.append(dict(index=index,key=key,name=name))
        selected = [r for r in items if r['key']==profile['item_id']]
        if len(selected) != 1 or selected[0]['index'] != 305:
            raise ValueError('item key ambiguity')
        same_names = [r for r in items if r['name']==selected[0]['name']]
        for i,name in enumerate(names):
            if not name.endswith('.fld'):
                continue
            blob = archive.read_entry(i,stream)
            for cmd in (204,900,901):
                at = 0
                while (at:=blob.find(struct.pack('<i',cmd),at)) >= 0:
                    if at+60 <= len(blob):
                        params = list(struct.unpack_from('<14i',blob,at+4))
                        if params[1] == profile['item_id']:
                            raw_candidates.append(dict(resource=name,offset=at,cmd=cmd,params=params))
                    at += 1
    def command(name,plan,field,index,expected):
        value = resources[name]['plans'][plan][field][index]
        if [value['cmd'],*value['params'][:len(expected)-1]] != expected:
            raise ValueError('scene command anchor mismatch')
        return dict(resource=name,plan=plan,field=field,**value)
    hq='00005705.fld'
    chain = dict(first_receive=command(hq,47,'pThen',30,[900,1,497,0]),
                 forest_battle=command('00006790.fld',8,'pThen',4,[1203,183,197,-1]),
                 handover=command(hq,36,'pThen',25,[901,1,497,1]),
                 handover_flag=command(hq,36,'pThen',40,[102,2539,6]),
                 later_receive=command(hq,58,'pThen',6,[900,1,497,0]),
                 later_use=command('00005946.fld',5,'pThen',118,[901,1,497,1]))
    forest = resources['00006790.fld']['plans'][8]
    if any(c['cmd']==901 and c['params'][1]==497 for c in forest['pThen']):
        raise ValueError('unexpected immediate forest consumption')
    image=ElfImage(elf)
    anchors={0x38266c:0x8c440334,0x382670:0x0c0e7ed8,0x382674:0x8e26009c,
             0x381fb0:0x0c0e85d0,0x381f64:0x24060001,
             0x39fbb0:0xac620004,0x39fbd0:0x0c06861c}
    for at,word in anchors.items():
        if struct.unpack_from('<I',elf,image.to_offset(at))[0] != word:
            raise ValueError('native anchor mismatch')
    report=dict(profile_sha256=digest(args.profile.read_bytes()),ship_sha256=ship_hash,
                elf_sha256=digest(elf),item=selected[0],same_named_items=same_names,
                chain=chain,resources=resources,raw_item_command_candidates=raw_candidates,
                original_native_spend_checks=native_spend_checks(image),
                first_battle_consumes_item=False,removal_at_hq_handover=True,
                native_words={hex(k):hex(v) for k,v in anchors.items()},
                bounded_instruction_evidence=True,full_event_runtime_verified=False)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    if json.loads(args.out.read_text('utf8')) != report:
        raise ValueError('report readback mismatch')
    print('ITEM_FLOW_PASS first=497 forest_consumption=none HQ_handover=497:-1 later=497:+1 undine_use=497:-1 same_named_item_keys='+str(len(same_names)))
    print('NATIVE_SPEND_PASS quantity1=0/remove quantity2=1/retain full_runtime_verified=false')


if __name__ == '__main__':
    main()
