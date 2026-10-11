"""Version-locked CDG/TUI text storage and actual key selection; not visual QA."""
from pathlib import Path
import struct
from font_poc import digest,require
from audit_text_slicing import scalar
from audit_native_method_registration import bind_inline
from audit_native_text_index import validate_lookup,run_lookup
from import_audited_fields import fixed_extent,fingerprint_extent

CDG_SHA = 'f8e9a5a4ddfb9a2dc823f9e8cf21e8f9a3d2cf0b404bed48c10c3456872e8877'
CDG_ANCHORS = {
    0x313f94:0x3c05004b,0x313f9c:0x24a57c30,0x314010:0xae000118,
    0x31401c:0x8e03011c,0x3140b4:0x0320f809,0x3140b8:0x00438821,
    0x3140cc:0x0320f809,0x3140d0:0x24060004,0x3140e4:0x0320f809,
    0x3140e8:0x240600ff,0x31410c:0x0c069530,0x314160:0x0c045b1c,
    0x314170:0x26250008,0x31417c:0x24060004,0x314188:0x2625000c,
    0x314194:0x24060004,0x3141a8:0x0320f809,0x3141ac:0x240600ff,
    0x3141d0:0x0c069530,0x314220:0x8e24001c,0x314224:0x0c045b1c,
    0x3111d4:0x8e230118,0x3111e8:0x8ee30000,0x3111ec:0x14c30011,
    0x3111f4:0x0c0c3e68,0x311204:0x26e50010,0x311224:0x0c06cd10,
    0x311228:0x26e5001c,0x1a54c0:0x03e00008,0x1a54c4:0x0080102d}
TUI_SPECS = {
    '00001239.tui':dict(sha256='5bd2bdd2d410ad6d4985eb5b3ee9949024703e3800d9b82e3ee79dacc7b705b5',count=34,loader=0x308250,path=0x4b7810,array=0x148,lookup=0x312f60,method='GetStoreTextDataIndex'),
    '00001249.tui':dict(sha256='0677124a3457f7bbcfdc32957b919b5fee6f48f1755567445d33ed6bcb84efb9',count=27,loader=0x308950,path=0x4b7850,array=0x16c,lookup=0x3132f0,method='GetGymTextDataIndex')}


def exact(image,words):
    require(image is not None,'literal native image missing')
    for va,word in words.items():
        require(struct.unpack_from('<I',image.blob,image.to_offset(va))[0] == word,'literal storage native anchor mismatch '+hex(va))


def validate_native_anchors(image):
    exact(image,CDG_ANCHORS)
    at=image.to_offset(0x4b7c30)
    require(image.blob[at:].split(b'\0',1)[0] == b'..\\CharmDogam\\00006460.cdg','CDG native path mismatch')
    cb=bind_inline(image,'intUMrtsDataManagerexecGetCharmDogamData',callback_limit=1024)
    require(cb['callback']=='0x311100' and cb['callback_end']=='0x311270','CDG native callback mismatch')
    for name,spec in TUI_SPECS.items():
        start=spec['loader'];delta=start-0x308250
        words={start+4:0x3c05004b,start+12:0x24a50000|(spec['path']&0xffff),
            start+0x88:0x26650000|spec['array'],start+0xbc:0x8e620000|spec['array'],
            start+0xd4:0x0320f809,start+0xec:0x0320f809,start+0xf0:0x24060100,
            start+0xf8:0x26040004,start+0x114:0x0c069530,start+0x168:0x0c045b1c,
            start+0x180:0x0320f809,start+0x184:0x24060100,start+0x1a8:0x0c069530,
            start+0x1fc:0x0c045b1c}
        exact(image,words);at=image.to_offset(spec['path'])
        require(image.blob[at:].split(b'\0',1)[0] == ('..\\UIText\\'+name).encode('ascii'),'TUI native path mismatch')
        cb=bind_inline(image,'intUMrtsDataManagerexec'+spec['method'])
        require(any(int(q['target'],16)==spec['lookup'] for q in cb['bounded_callback_jals']),'TUI native key helper missing')
        validate_lookup(image,spec['lookup'],spec['array'])


def check_span(resource,entry,binding,original,expected_sha,span):
    require(binding['id']==entry['id'] and binding['resource']==resource['resource'],'literal storage identity mismatch')
    require(digest(original)==resource['sha256']==binding['resource_sha256']==expected_sha,'literal storage resource fingerprint mismatch')
    require(all(binding[k]==entry[k] for k in ('offset','source_bytes','source_sha256')),'literal storage source binding mismatch')
    at,n=entry['offset'],entry['source_bytes']
    require(type(at) is int and type(n) is int and 0<=at and 0<n<span and at+span<=len(original),'literal storage span bounds')
    slot=original[at:at+span]
    require(digest(slot[:n])==entry['source_sha256'] and slot[n]==0 and not any(slot[n:]),'literal storage source padding/hash mismatch')
    write,hashed_sha=fixed_extent(entry);hashed=fingerprint_extent(entry,write)
    require(write==span and at+hashed<=len(original) and digest(original[at:at+hashed])==hashed_sha,'literal storage full field fingerprint mismatch')
    return dict(writable_bytes=span,fingerprint_bytes=hashed,preserved_tail_bytes=hashed-span,
                preserved_tail_sha256=digest(original[at+span:at+hashed]),runtime_verified=False)


def cdg_records(original):
    require(len(original)==8+72*526 and struct.unpack_from('<II',original)==(72,5),'CDG source record geometry mismatch')
    return [dict(physical_index=i,source_key=struct.unpack_from('<I',original,12+526*i)[0],
        name_offset=16+526*i,description_offset=279+526*i) for i in range(72)]


def validate_cdg(resource,entry,binding,original,image):
    require(resource['resource']=='SHIP/00006460.cdg','unsupported literal CDG')
    geometry=check_span(resource,entry,binding,original,CDG_SHA,255);rows=cdg_records(original)
    i=binding['physical_index'];require(type(i) is int and 0<=i<72,'CDG physical record out of range')
    row=rows[i]
    require(entry['slot']==2*i+1 and entry['offset']==row['description_offset'] and binding['native_string_offset']==28,'CDG description field mismatch')
    key=binding['record_key'];require(key==row['source_key'],'CDG source key mismatch')
    require(next((q['physical_index'] for q in rows if q['source_key']==key),None)==i,'CDG first-key lookup selects another record')
    mem={0x8118+j:b for j,b in enumerate(struct.pack('<I',0x9000))}
    result=scalar(image,0x3111d4,0x3111e8,{17:0x8000,7:i},mem)
    require(result['registers'][23]==0x9000+40*i,'CDG native record stride mismatch')
    return dict(geometry,native_string_offset=28,numeric_key_verified=True)


def validate_tui(resource,entry,binding,original,image):
    name=Path(resource['resource']).name;require(name in TUI_SPECS,'unsupported literal TUI')
    spec=TUI_SPECS[name];geometry=check_span(resource,entry,binding,original,spec['sha256'],256)
    require(len(original)==8+516*spec['count'] and struct.unpack_from('<II',original)==(spec['count'],2),'TUI source record geometry mismatch')
    i=binding['physical_index'];require(type(i) is int and 0<=i<spec['count'],'TUI physical record out of range')
    require(entry['record_index']==i and entry['half']==0 and entry['offset']==12+516*i and binding['native_string_offset']==4,'TUI main field geometry mismatch')
    keys=[struct.unpack_from('<I',original,8+516*j)[0] for j in range(spec['count'])]
    require(binding['record_key']==entry['record_id']==keys[i],'TUI source key mismatch')
    result=run_lookup(image,spec['lookup'],spec['array'],keys,binding['record_key'])
    require(result['found'] and result['index']==i,'TUI native key lookup selects another field')
    return dict(geometry,native_string_offset=4,native_stride=28,numeric_key_verified=True)
