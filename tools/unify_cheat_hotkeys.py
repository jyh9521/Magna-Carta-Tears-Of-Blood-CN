"""Audit and gate every known active effect without changing UI selection names.

Stateless patches restore original instructions on OFF. Battle speed retains a
selected maintenance hook so OFF can release its owned runtime coefficient.
"""
import argparse
import json
from pathlib import Path
import struct
import build_hotkey_cheats as hotkey
import build_field_speed_cheats as field
import build_qte_cheats as qte

ROOT=Path(__file__).resolve().parents[1]


def profiles():
    hp=hotkey.load_profiles()
    f=json.loads((ROOT/'profiles/cheats/SCKA-20043_AE86E04C-field-speed.json').read_text('utf8'))
    q=json.loads((ROOT/'profiles/cheats/SCKA-20043_AE86E04C-qte.json').read_text('utf8'))
    return hp,f,q


def parse(text):
    header=[];groups=[];current=None
    for line in text.splitlines():
        if line.startswith('[') and line.endswith(']'):
            current=dict(label=line[1:-1],lines=[],commands=[]);groups.append(current)
        elif current is None:
            if line.startswith('patch='):raise ValueError('unexpected unlabelled command')
            header.append(line)
        else:
            current['lines'].append(line)
            if line.startswith('patch='):
                parts=line.split('=',1)[1].split(',')
                if len(parts)!=5 or parts[1]!='EE' or parts[0] not in ('0','1'):
                    raise ValueError('unsupported command shape')
                a,v=int(parts[2],16),int(parts[4],16)
                if not 0 <= a <= 0xffffffff or not 0 <= v <= 0xffffffff:raise ValueError('word bounds')
                current['commands'].append((int(parts[0]),a,parts[3],v))
    if len(groups)!=len({g['label'] for g in groups}):raise ValueError('duplicate section')
    return header,groups


def raw(commands):
    startup={};continuous={}
    for place,address,kind,value in commands:
        if kind=='extended' and address>>28==2:address&=0x0fffffff
        elif kind!='word':raise ValueError('not plain writes')
        if address%4 or address+4>32*1024*1024:raise ValueError('write bounds')
        dest=startup if place==0 else continuous
        if address in dest:raise ValueError('duplicate plain write')
        dest[address]=value
    return startup,continuous


def conditional(commands,state):
    result={};at=0
    while at<len(commands):
        place,address,kind,value=commands[at];at+=1
        if place!=1 or kind!='extended' or address>>28!=14 or value!=state:
            raise ValueError('not exact shared-latch E block')
        match=address&65535;count=(address>>16)&255
        if match not in (0,1) or match in result or not count or at+count>len(commands):
            raise ValueError('invalid condition/count')
        body={}
        for command in commands[at:at+count]:
            place,address,kind,value=command
            if place!=1 or kind!='extended' or address>>28!=2:raise ValueError('invalid conditional write')
            va=address&0x0fffffff
            if va%4 or va+4>32*1024*1024 or va in body:raise ValueError('conditional write bounds/duplicate')
            body[va]=value
        at+=count;result[match]=body
    if set(result)!={0,1}:raise ValueError('both ON and OFF blocks required')
    return result


def audit(elf,text):
    hp,f,q=profiles();original=hotkey.original_memory(elf,hp)
    field.baseline(elf,f);qte.validate(elf,q)
    header,groups=parse(text);latch=int(hp[0]['state_address'],16)
    known=list(hotkey.cases(hp).values())
    known.append(field.writes(f,'undetected'))
    known.append({int(r['va'],16):int(r['replacement'],16) for r in q['codes']})
    expected_core=hotkey.controller_program(hp[0]);records=[];cores=0
    speed_start={int(f['speed_state'],16)+i:0 for i in (0,4,8)}
    off_sets=[hotkey.restore_words(original,w) for w in known]
    combined={}
    for w in known:
        if set(w)&{0x3a06f0,0x3a06f8,0x3a0700}:combined.update(hotkey.restore_words(original,w))
    off_sets.append(combined)
    for g in groups:
        cmds=g['commands'];row=dict(label=g['label'])
        if not cmds:row['kind']='hint';records.append(row);continue
        if cmds[0][2]=='extended' and cmds[0][1]>>28==14:
            blocks=conditional(cmds,latch)
            if blocks[1] not in known or blocks[0]!=hotkey.restore_words(original,blocks[1]):
                raise ValueError('unknown effect or incorrect original restoration')
            row.update(kind='conditional',on=blocks[1],off=blocks[0]);records.append(row);continue
        startup,writes=raw(cmds)
        if startup=={latch:0} and writes==expected_core:
            row.update(kind='controller');cores+=1;records.append(row);continue
        if not startup and writes in known:
            row.update(kind='ungated',on=writes,off=hotkey.restore_words(original,writes));records.append(row);continue
        if not startup and writes in off_sets:
            row.update(kind='restore_only');records.append(row);continue
        if startup==speed_start:
            for factor in (2,4):
                if writes==field.speed_program(f,factor):
                    row.update(kind='speed_ungated',factor=factor);break
                if writes==field.speed_program(f,factor,gate=latch):
                    row.update(kind='speed_runtime_gate',factor=factor);break
            else:raise ValueError('unknown speed payload')
            records.append(row);continue
        raise ValueError('unknown effect; no inferred original bytes: '+g['label'])
    if cores!=1:raise ValueError('exactly one verified controller core required')
    return original,header,groups,records


def render(elf,text):
    original,header,groups,records=audit(elf,text);hp,f,q=profiles()
    result='\n'.join(header).rstrip()+'\n'
    note='SELECT＋上开启，SELECT＋下关闭；初始关闭。'
    for g,row in zip(groups,records):
        result+='\n['+g['label']+']\n'
        if row['kind'] in ('ungated','speed_ungated','speed_runtime_gate'):
            meta=[line for line in g['lines'] if not line.startswith('patch=')]
            meta=[line.replace('independent of SELECT latch','shared SELECT latch') for line in meta]
            meta=[line+note if line.startswith('description=') and note not in line else line for line in meta]
            result+='\n'.join(meta).rstrip()+'\n'
            if row['kind']=='ungated':
                result+='\n'.join(hotkey.blocks(hp[0],row['on'],row['off']))+'\n'
            else:
                for delta in (0,4,8):result+=f"patch=0,EE,{int(f['speed_state'],16)+delta:08X},word,00000000\n"
                for va,value in sorted(field.speed_program(f,row['factor'],gate=int(hp[0]['state_address'],16)).items()):
                    result+=f'patch=1,EE,{va:08X},word,{value:08X}\n'
        else:
            lines=[line.replace('independent of SELECT latch','shared SELECT latch') if line.startswith('//') else line for line in g['lines']]
            result+='\n'.join(lines).rstrip()+'\n'
    _,_,_,rows=audit(elf,result)
    if any(r['kind'] in ('ungated','speed_ungated') for r in rows):raise ValueError('ungated effect remains')
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--elf',type=Path,required=True);ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--audit-output',type=Path)
    a=ap.parse_args()
    if a.output.resolve() in (a.source.resolve(),a.elf.resolve()):raise ValueError('separate output required')
    elf=a.elf.read_bytes();text=render(elf,a.source.read_text('utf8'))
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(text,'utf8',newline='\n')
    assert a.output.read_text('utf8')==text
    records=audit(elf,text)[3]
    if a.audit_output:
        a.audit_output.parent.mkdir(parents=True,exist_ok=True)
        a.audit_output.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n','utf8')
        assert json.loads(a.audit_output.read_text('utf8'))==json.loads(json.dumps(records))
    count=sum(r['kind'] in ('conditional','speed_runtime_gate') for r in records)
    print(f'ALL_HOTKEY_BUILD PASS effects={count} ungated=0 shared_latch=000C3FE0 default=off')


if __name__=='__main__':main()
