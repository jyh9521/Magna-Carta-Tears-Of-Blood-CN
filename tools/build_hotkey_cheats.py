"""Wrap validated Korean cheats with a sampled-controller ON/OFF latch.

Unlabelled PNACH controller code is automatic; UI-selected groups alone are gated.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import build_battle_cheats as battle
import build_gameplay_cheats as gameplay
import port_frame_limit_patch as frame

ROOT=Path(__file__).resolve().parents[1]


def load_profiles():
    base=ROOT/'profiles/cheats'
    return tuple(json.loads((base/name).read_text('utf8')) for name in [
        'SCKA-20043_AE86E04C-hotkeys.json','SCKA-20043_AE86E04C.json',
        'SCKA-20043_AE86E04C-battle.json'])


def controller_program(profile):
    if (profile['controller_port'],profile['controller_slot'])!=(0,0):
        raise ValueError('only verified primary controller port/slot is supported')
    a=battle.Assembler(int(profile['controller_cave'],16))
    a.word(battle.instruction(9,29,29,-160))
    for i,r in enumerate([4,5,6]):a.word(battle.instruction(31,29,r,16*i))
    a.word(battle.instruction(63,29,31,0x30))
    a.word(0x0c000000 | (int(profile['pad_read'],16)>>2));a.word(0)
    # Save scratch registers AFTER the original read, retaining its returned state.
    for i,r in enumerate([8,9,10,11]):a.word(battle.instruction(31,29,r,0x40+16*i))
    a.word(battle.instruction(35,29,8,0))  # original port
    a.branch(5,8,0,'restore')
    a.word(battle.instruction(35,29,8,0x10))  # original slot
    a.branch(5,8,0,'restore')
    state=int(profile['state_address'],16)
    a.word(battle.instruction(15,0,11,state>>16))
    a.word(battle.instruction(13,11,11,state&65535))
    a.branch(6,2,0,'off')  # failed primary-controller read disables the latch
    a.word(battle.instruction(35,29,10,0x20))
    a.word(battle.instruction(36,10,8,0))
    a.branch(5,8,0,'off')
    a.word(battle.instruction(36,10,8,1))
    for mode in profile['valid_modes']:
        a.word(battle.instruction(9,0,9,mode))
        a.branch(4,8,9,'packet_ok')
    a.branch(4,0,0,'off')
    a.label('packet_ok')
    a.word(battle.instruction(36,10,8,2))
    a.word(battle.instruction(36,10,9,3))
    # libpad's raw packet stores low button bits in byte 2. The game's
    # downstream consumer swaps these into its own mask; SDK masks do not.
    a.word((9<<16)|(9<<11)|(8<<6))  # SLL t1,t1,8
    a.word((8<<21)|(9<<16)|(8<<11)|0x25)  # OR t0,t0,t1
    a.word(battle.instruction(14,8,8,65535))  # invert active-low button bits
    # OFF wins if both direction combinations are held.
    a.word(battle.instruction(12,8,9,profile['off_mask']))
    a.word(battle.instruction(9,0,10,profile['off_mask']))
    a.branch(4,9,10,'off')
    a.word(battle.instruction(12,8,9,profile['on_mask']))
    a.word(battle.instruction(9,0,10,profile['on_mask']))
    a.branch(5,9,10,'restore')
    a.word(battle.instruction(9,0,8,1))
    a.word(battle.instruction(43,11,8,0))
    a.branch(4,0,0,'restore')
    a.label('off');a.word(battle.instruction(43,11,0,0))
    a.label('restore')
    for i,r in enumerate([8,9,10,11]):a.word(battle.instruction(30,29,r,0x40+16*i))
    a.word(battle.instruction(55,29,31,0x30))  # LD original caller return
    a.word(0x03e00008);a.word(battle.instruction(9,29,29,160))
    result=a.finish()
    result[int(profile['input_hook'],16)]=0x0c000000|(a.base>>2)
    return result


def cases(profiles):
    hp,gp,bp=profiles
    rows={'60 FPS':{0x1c69e4:0x28410001}}
    rows.update({r['label']:{int(r['va'],16):int(r['replacement'],16)} for r in gp['codes']})
    rows.update({label:battle.writes(bp,mode) for mode,label in battle.MODES.items()})
    return rows


def original_memory(elf,profiles):
    hp,gp,bp=profiles
    original=battle.baseline(elf,bp)
    gameplay.validate(elf,gp)
    if len(elf)!=hp['elf_size'] or battle.sha(elf)!=hp['elf_sha256']:
        raise ValueError('unsupported input-hook ELF')
    for va,data in hp['anchors'].items():
        off=frame.offset(elf,int(va,16));raw=bytes.fromhex(data)
        if elf[off:off+len(raw)]!=raw:raise ValueError('input anchor mismatch')
    core=controller_program(hp)
    for va in core:
        if va<0x100000 and original[va:va+4]!=bytes(4):
            raise ValueError('controller cave not zero in original fixture')
    return original


def restore_words(original,writes):
    # Only original executable instructions are restored on OFF. Caves remain
    # unreachable instead of clearing code while a previously entered hook returns.
    return {va:struct.unpack_from('<I',original,va)[0] for va in writes if va>=0x100000}


def blocks(profile,on,off):
    state=int(profile['state_address'],16);lines=[]
    for value,body in [(1,on),(0,off)]:
        if not 0<len(body)<=255:raise ValueError('invalid conditional block length')
        lines.append(f'patch=1,EE,{0xe0000000|(len(body)<<16)|value:08X},extended,{state:08X}')
        for va,word in sorted(body.items()):
            lines.append(f'patch=1,EE,{0x20000000|va:08X},extended,{word:08X}')
    return lines


def render(elf,profiles,source):
    original=original_memory(elf,profiles);profile=profiles[0];known=cases(profiles)
    lines=source.splitlines();groups=[];header=[];current=None
    for line in lines:
        if line.startswith('[') and line.endswith(']'):
            current={'label':line[1:-1],'lines':[],'writes':{}};groups.append(current)
        elif current is None:header.append(line)
        elif line.startswith('patch='):
            parts=line.split('=',1)[1].split(',')
            if len(parts)!=5 or parts[:2]!=['1','EE']:raise ValueError('unsupported source patch')
            va,typ,word=int(parts[2],16),parts[3],int(parts[4],16)
            if typ=='extended' and va>>28==2:va&=0x0fffffff
            elif typ!='word':raise ValueError('unsupported source patch type')
            if va in current['writes']:raise ValueError('duplicate source write')
            current['writes'][va]=word
        else:current['lines'].append(line)
    if len(groups)!=len({g['label'] for g in groups}):raise ValueError('duplicate sections')
    for g in groups:
        if g['label'] not in known or g['writes']!=known[g['label']]:
            raise ValueError('unrecognized source cheat; no guessed restoration')
    text='\n'.join(header).rstrip()+'\n'
    text+='// 按键切换测试版：未分组控制代码自动加载，初始效果关闭。\n'
    text+='// 选择键＋方向键上开启已勾选项目；选择键＋方向键下关闭。\n'
    text+='// 保持模拟器作弊总开关开启；互斥模式仍只选一项。\n'
    text+=f"patch=0,EE,{profile['state_address']},word,00000000\n"
    for va,word in sorted(controller_program(profile).items()):
        text+=f'patch=1,EE,{va:08X},word,{word:08X}\n'
    for g in groups:
        text+='\n['+g['label']+']\n'
        for line in g['lines']:
            if line.startswith('description='):
                line+='选择键加上开启，加下关闭；默认关闭。'
            text+=line+'\n'
        text+='\n'.join(blocks(profile,g['writes'],restore_words(original,g['writes'])))+'\n'
    return text


def apply_pnach(memory,text,enabled,startup=False):
    """Small model of the emitted PNACH subset, matching primary PCSX2 E-code rules."""
    result=bytearray(memory);group='';skip=0
    for line in text.splitlines():
        if line.startswith('['):group=line[1:-1];skip=0;continue
        if not line.startswith('patch=') or (group and group not in enabled):continue
        place,cpu,addr,kind,data=line.split('=',1)[1].split(',')
        if (place=='0')!=startup:continue
        if skip:skip-=1;continue
        address,value=int(addr,16),int(data,16)
        if kind=='extended' and address>>28==14:
            if struct.unpack_from('<H',result,value)[0]!=(address&65535):skip=(address>>16)&255
        elif kind=='word' or (kind=='extended' and address>>28==2):
            va=address if kind=='word' else address&0x0fffffff
            struct.pack_into('<I',result,va,value)
        else:raise ValueError('unknown emitted PNACH command')
    return bytes(result)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--elf',type=Path,required=True);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.resolve() in [a.elf.resolve(),a.source.resolve()]:raise ValueError('separate output required')
    result=render(a.elf.read_bytes(),load_profiles(),a.source.read_text('utf8'))
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(result,encoding='utf8')
    if a.output.read_text('utf8')!=result:raise ValueError('readback mismatch')
    print('HOTKEY_BUILD PASS default=off groups='+str(result.count('\n['))+' sha256='+battle.sha(a.output.read_bytes()))


if __name__=='__main__':main()
