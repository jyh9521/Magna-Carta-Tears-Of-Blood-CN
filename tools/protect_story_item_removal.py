"""Replace only a known blanket item patch with a caller-selective hook.

Final postprocessing step for a user-supplied unified PNACH. Other sections are
preserved byte-for-byte; no emulator settings, game image or save is written.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
from research_native import ElfImage


def program(p):
    base=p['cave'];words=[];labels={};fixups=[]
    def ins(op,rs,rt,imm):return (op<<26)|(rs<<21)|(rt<<16)|(imm&65535)
    def branch(op,rs,rt,label):
        fixups.append((len(words),label));words.extend([ins(op,rs,rt,0),0])
    words.extend([ins(9,29,29,-16),ins(31,29,1,0)]) # preserve full 128-bit AT
    ra=p['ordinary_return'];upper=(ra+0x8000)>>16
    words.extend([ins(15,0,1,upper),ins(9,1,1,ra&65535)])
    branch(5,31,1,'stock') # everything except known ordinary wrapper writes normally
    branch(4,0,0,'resume')
    labels['stock']=len(words);words.append(0xac620004)
    labels['resume']=len(words)
    words.extend([ins(30,29,1,0),ins(9,29,29,16),0x08000000|(p['resume']>>2),0x8c620004])
    for at,label in fixups:words[at]|=(labels[label]-at-1)&65535
    if base%4 or base+len(words)*4>p['latch'] or base<0xc3200:
        raise ValueError('unsupported cave geometry')
    result={base+4*i:w for i,w in enumerate(words)}
    result[p['hook']]=0x08000000|(base>>2);result[p['hook']+4]=0
    return result


def validate(elf,p):
    if p.get('schema')!=1 or hashlib.sha256(elf).hexdigest()!=p['elf_sha256']:
        raise ValueError('unsupported ELF/profile')
    image=ElfImage(elf)
    for address,expected in p['anchors'].items():
        at=int(address,16)
        if struct.unpack_from('<I',elf,image.to_offset(at))[0]!=int(expected,16):
            raise ValueError('original instruction mismatch')
    calls=[];jal=0x0c000000|(0x39fb60>>2)
    for at in range(0,len(elf)-4,4):
        if struct.unpack_from('<I',elf,at)[0]==jal:calls.append(image.to_va(at)+8)
    if sorted(calls)!=sorted([p['ordinary_return'],*p['script_returns']]):
        raise ValueError('native callsite set changed')
    return image


def section_span(text,name):
    matches=list(re.finditer(r'^\[([^\r\n]+)\]\r?$',text,re.M))
    selected=[i for i,m in enumerate(matches) if m.group(1)==name]
    if len(selected)!=1:raise ValueError('item section missing/ambiguous')
    i=selected[0];return matches[i].start(),matches[i+1].start() if i+1<len(matches) else len(text)


def commands(text):
    result=[]
    for line in text.splitlines():
        if line.startswith('patch='):
            args=line.split('=',1)[1].split(',')
            if len(args)!=5 or args[1]!='EE':raise ValueError('unsupported item command')
            result.append((int(args[0]),int(args[2],16),args[3],int(args[4],16)))
    return result


def render(elf,p,text):
    validate(elf,p)
    lo,hi=section_span(text,p['section']);body=text[lo:hi]
    expected=[(1,0xe0010001,'extended',p['latch']),
              (1,0x20000000|p['hook'],'extended',0),
              (1,0xe0010000,'extended',p['latch']),
              (1,0x20000000|p['hook'],'extended',0xac620004)]
    if commands(body)!=expected:raise ValueError('source is not exact legacy item effect')
    writes=program(p);outside=text[:lo]+text[hi:]
    for _,address,kind,_ in commands(outside):
        if kind=='word':target=address
        elif kind=='extended' and address>>28==2:target=address&0xfffffff
        elif kind=='extended' and address>>28==14:continue
        elif kind=='extended' and address>>28 in (0,1):
            target=address&0xfffffff
        else:raise ValueError('unrecognized external patch encoding; collision not checked')
        if target in writes:raise ValueError('another section touches item hook/cave')
    lines=['['+p['section']+']','description='+p['description'],
           '// caller-selective v1; only known ordinary RemoveItem wrapper retains count',
           '// original story TakeItem callers and unknown callers keep stock decrement']
    off={p['hook']:0xac620004,p['hook']+4:0x8c620004}
    for state,mapping in [(1,writes),(0,off)]:
        lines.append(f"patch=1,EE,{0xe0000000|(len(mapping)<<16)|state:08X},extended,{p['latch']:08X}")
        lines.extend(f'patch=1,EE,{0x20000000|at:08X},extended,{word:08X}' for at,word in sorted(mapping.items()))
    result=text[:lo]+'\n'.join(lines)+'\n\n'+text[hi:]
    a,b=section_span(result,p['section'])
    if result[:a]!=text[:lo] or result[b:]!=text[hi:]:raise ValueError('unrelated sections changed')
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ('elf','profile','source','out'):ap.add_argument('--'+key,type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists() or a.out.resolve() in [v.resolve() for v in (a.elf,a.profile,a.source)]:
        raise ValueError('output must be a new separate copy')
    source=a.source.read_bytes();elf=a.elf.read_bytes();p=json.loads(a.profile.read_text('utf8'))
    result=render(elf,p,source.decode('utf8'))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('w',encoding='utf8',newline='') as f:f.write(result)
    if a.out.read_bytes()!=result.encode('utf8') or a.source.read_bytes()!=source:
        raise ValueError('readback mismatch or original changed')
    print('ITEM_STORY_BUILD_PASS ordinary=retain script_callers=4:stock unknown_callers=stock other_sections=exact default=OFF')


if __name__=='__main__':main()
