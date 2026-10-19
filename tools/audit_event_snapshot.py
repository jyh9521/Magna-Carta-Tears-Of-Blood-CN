"""Read-only, source-bound UE2 event snapshot inspection for the supported ELF."""
from pathlib import Path
import argparse
import struct,zipfile,json,hashlib,sys,re,math
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
from research_native import ElfImage,ELF_SHA256
parser=argparse.ArgumentParser(description=__doc__)
for key in ('state','elf','out'):parser.add_argument('--'+key,type=Path,required=True)
args=parser.parse_args();state=args.state
if args.out.resolve() in (state.resolve(), args.elf.resolve()):
 raise ValueError("report must not overwrite an input")
raw=state.read_bytes();image=ElfImage(args.elf.read_bytes());assert hashlib.sha256(image.blob).hexdigest()==ELF_SHA256
with zipfile.ZipFile(state) as z: ram=z.read('eeMemory.bin')
assert len(ram)==32*1024*1024
U=lambda p:struct.unpack_from('<I',ram,p)[0]
I=lambda p:struct.unpack_from('<i',ram,p)[0]
V=lambda p:struct.unpack_from('<3f',ram,p)
def findword(v):
 at=0
 while (at:=ram.find(struct.pack('<I',v),at))>=0:
  if at%4==0:yield at
  at+=4
# Recover name table from complete exact names, index-bearing entries, and aligned pointer uses.
base_candidates=set();anchor=b'MrtsNpcMonsterPlug\0';at=0
while (at:=ram.find(anchor,at))>=0:
 if at>0x600000 and U(at-4)&0x4000000:
  entry=at-8;index=U(entry)&65535
  for reference in findword(entry):
   base=reference-index*4
   if 0x600000<base<len(ram)-65536*4:base_candidates.add(base)
 at+=len(anchor)
def readname(base,index):
 if not 0<=index<65536:return ''
 p=U(base+index*4)
 if not 0x600000<p<len(ram)-136 or p%4 or U(p)&65535!=index:return ''
 s=ram[p+8:p+136].split(b'\0',1)[0]
 try:return s.decode('ascii')
 except UnicodeError:return ''
valid=[]
for base in base_candidates:
 names={readname(base,i):i for i in range(65536) if readname(base,i)}
 if {'MrtsGameMagi','MrtsNpcMonsterPlug','MrtsFieldData','MrtsEventPlan','MrtsEventCmdStr','None','Class'}<=names.keys():valid.append((base,names))
assert len(valid)==1,('name table ambiguous',len(valid));NB,NAMES=valid[0]
def name(index):return readname(NB,index)
def objname(p):return name(U(p+32)) if 0x600000<p<len(ram)-40 else ''
def objclass(p):return objname(U(p+36)) if 0x600000<p<len(ram)-40 else ''
def header(p):return 0x600000<p<len(ram)-80 and 0x100000<U(p)<0x550000 and bool(objclass(p)) and bool(objname(p)) and -1<=I(p+4)<100000
def namedobjects(n):return [p-32 for p in findword(NAMES[n]) if p>=32 and header(p-32)]
def classptr(n):
 candidates=[p for p in namedobjects(n) if objclass(p) in ('Class','ScriptStruct','Struct')]
 assert len(candidates)==1,(n,candidates)
 return candidates[0]
def instances(n):return [p-36 for p in findword(classptr(n)) if p>=36 and header(p-36) and I(p-32)>=0]
def properties(owner):
 result={}
 for at in findword(classptr(owner)):
  p=at-24
  if not header(p) or not objclass(p).endswith('Property'):continue
  result[objname(p)]={'offset':U(p+60),'element_bytes':U(p+56),'array_dim':U(p+52),'mask':U(p+72),'type':objclass(p),'property_va':p}
 return result
PROPS={owner:properties(owner) for owner in ['MrtsFieldData','MrtsDataManager','MrtsGameMagi','MrtsGamePlug','MrtsNpcPlug','MrtsNpcMonsterPlug','MrtsEvent','MrtsEventPlan','MrtsEventCmdStr','MrtsCharPlacementData','MrtsMonsterPlacementData','Actor','MrtsPartyItem','MrtsPartyData','MrtsAreaVolumeData']}
def get(p,owner,field):return p+PROPS[owner][field]['offset']
def intfield(p,owner,field):return I(get(p,owner,field))
def ptrfield(p,owner,field):return U(get(p,owner,field))
def array(p,stride,max_count=10000):
 data,count,cap=struct.unpack_from('<III',ram,p);assert count<=cap<=max_count and (not count or 0<data<=len(ram)-count*stride),(hex(p),data,count,cap)
 return [data+j*stride for j in range(count)]
def state_name(p):
 f=U(p+12)
 return objname(U(f+24)) if f and 0<f<len(ram)-40 else ''
magis=instances('MrtsGameMagi');assert len(magis)==1;g=magis[0]
# Native Tick references at 003F6FF0/003F6FFC bind +268/+3B0; +220 appears at 003F72C4.
for addr,word in {0x3f6ff0:0x8e230268,0x3f6ffc:0x8c6503b0,0x3f72c4:0x8c830220}.items():assert U(addr)==struct.unpack_from('<I',image.blob,image.to_offset(addr))[0]==word
assert PROPS['MrtsGamePlug']['GameMagi']['offset']==0x268 and PROPS['MrtsGameMagi']['PlayerPlug']['offset']==0x3b0
DM=U(g+0x220);assert objclass(DM)=='MrtsDataManager';FD=ptrfield(DM,'MrtsDataManager','FieldData');assert objclass(FD)=='MrtsFieldData'
player=ptrfield(g,'MrtsGameMagi','PlayerPlug');pawn=U(player+0x1ec);pos=V(get(pawn,'Actor','Location'))
monsters=[]
for j,p in enumerate(array(get(FD,'MrtsFieldData','MonsterPlacementDataList'),U(classptr('MrtsMonsterPlacementData')+56))):
 cl='MrtsMonsterPlacementData';plug=ptrfield(p,cl,'Plug');loc=V(get(p,cl,'Location'));flags=U(get(plug,'MrtsNpcPlug','bPause')) if plug else 0
 monsters.append(dict(index=j,key=intfield(p,cl,'Key'),serial=intfield(p,cl,'Serial'),character_id=intfield(p,cl,'ChrID'),location=loc,distance=math.dist(pos,loc),plug=plug,state=state_name(plug),paused=bool(flags&PROPS['MrtsNpcPlug']['bPause']['mask'])))
characters=[]
for j,p in enumerate(array(get(FD,'MrtsFieldData','CharPlacementDataList'),U(classptr('MrtsCharPlacementData')+56))):
 cl='MrtsCharPlacementData';plug=ptrfield(p,cl,'Plug');loc=V(get(p,cl,'Location'))
 characters.append(dict(index=j,key=intfield(p,cl,'Key'),character_id=intfield(p,cl,'ChrID'),location=loc,distance=math.dist(pos,loc),plug=plug,plug_name=objname(plug),plug_class=objclass(plug),state=state_name(plug) if plug else None))
# GameEvent inherits MrtsEvent; DM.GlobalEvent is the independent global switch owner.
event_objects={'current':ptrfield(g,'MrtsGameMagi','GameEvent'),'global':ptrfield(DM,'MrtsDataManager','GlobalEvent'),'loaded':ptrfield(DM,'MrtsDataManager','LoadedEvent')}
events={}
for label,p in event_objects.items():
 if not p:continue
 assert objclass(p) in ['MrtsEvent','MrtsGameEvent'],(label,hex(p),objclass(p))
 switches=[I(at) for at in array(get(p,'MrtsEvent','Switches'),4,200000)]
 plans=[]
 for at in array(get(p,'MrtsEvent','Plans'),U(classptr('MrtsEventPlan')+56)):
  row={k:intfield(at,'MrtsEventPlan',k) for k in ['ID','nRepnum','when','nTimes','nCurThen','nWait','nEvObj']};row['busy']=bool(U(get(at,'MrtsEventPlan','bBusy'))&1)
  for field in ['pIf','pThen']:
   row[field]=[{'count':I(cmd),'cmd':I(cmd+4),'params':list(struct.unpack_from('<14i',ram,cmd+8)),'temporary':I(cmd+64)} for cmd in array(get(at,'MrtsEventPlan',field),68)]
  plans.append(row)
 events[label]=dict(pointer=p,name=objname(p),class_name=objclass(p),flags=U(get(p,'MrtsEvent','bEnable')),active=intfield(p,'MrtsEvent','nActiveEvent'),switches=switches,plans=plans)
checks=[]
# Explicit supported native patch sites; no dependency on local installed cheats.
for ad in [0x17c738,0x1c69e4,0x399190,0x399194,0x39fbb0,0x3a06f0,
           0x3a06f8,0x3a0700,0x3fd758,0x3fe208,0x3fe20c,0x2f8b8c,
           0x3f72c0,0x3f72c4,0x3f746c,0x3f7470]:
 off=image.to_offset(ad)
 checks.append(dict(address=ad,actual=U(ad),original=struct.unpack_from('<I',image.blob,off)[0]))
checks=list({x['address']:x for x in checks}.values())

itemclass=classptr('MrtsPartyItem');itemprops=properties('MrtsPartyItem');items=[]
for at in array(get(DM,'MrtsDataManager','PartyItemList'),U(itemclass+56)):
 items.append({key:I(at+q['offset']) for key,q in itemprops.items() if q['type'] in ('IntProperty','ByteProperty')})


areas=[]
area_props=properties('MrtsAreaVolumeData');stride=U(classptr('MrtsAreaVolumeData')+56)
for at in array(get(FD,'MrtsFieldData','AreaVolumeList'),stride):
 areas.append(dict(key=I(at),min=V(at+area_props['Min']['offset']),max=V(at+area_props['Max']['offset']),use_z=bool(U(at+area_props['bUseZ']['offset'])&area_props['bUseZ']['mask'])))
party=ptrfield(DM,'MrtsDataManager','PartyData');party_type=ram[party+PROPS['MrtsPartyData']['PartyType']['offset']]

report=dict(areas=areas,party_type=party_type,party_items=items,state=str(state.resolve()),state_sha256=hashlib.sha256(raw).hexdigest(),elf_sha256=ELF_SHA256,name_table_base=NB,game_magi=g,game_state=state_name(g),data_manager=DM,field_data=FD,field={key:intfield(FD,'MrtsFieldData',key) for key in ['MapID','nParentField','PlayBookID','nPlayBookFileID1','nPlayBookFileID2','nMonsterGSW']},player_location=pos,characters=characters,monsters=monsters,event_objects=events,known_patch_instruction_checks=checks,known_patch_mismatches=[x for x in checks if x['actual']!=x['original']],reflection=PROPS,source_unchanged=state.read_bytes()==raw)
out=args.out;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2),'utf8');assert json.loads(out.read_text('utf8'))['state_sha256']==report['state_sha256']
print('EVENT_STATE_READ_PASS state='+state.name+' patches='+str(len(report['known_patch_mismatches']))+' map='+str(report['field']['MapID'])+' parent='+str(report['field']['nParentField'])+' characters='+str(len(characters))+' monsters='+str(len(monsters)))
for key,e in events.items():print('EVENT',key,hex(e['pointer']),e['class_name'],'flags',e['flags'],'plans',len(e['plans']),'switches',len(e['switches']))
