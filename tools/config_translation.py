"""Source-bound configuration value validation and delimiter-safe byte rewriting.

Preference labels are separate from immutable class/category/flag descriptors.
Opaque percent macros are preserved; this does not interpret their semantics.
"""
import hashlib,re
from audit_native_method_registration import require

PERCENT=re.compile(r'%%|%(?:\d+\$)?[-+0 #]*\d*(?:\.\d+)?[sdifuxXoc]|%[kw]')
LABEL=re.compile(r'(Caption|Parent)="([^"\r\n]*)"')

def template_tokens(text):
    percent=[];at=0
    while (at:=text.find('%',at))>=0:
        match=PERCENT.match(text,at);require(match is not None,'unknown configuration percent token')
        percent.append(match[0]);at=match.end()
    return dict(percent=percent,accelerators=re.findall(r'&&|&[A-Za-z0-9]',text),
                newline_escapes=re.findall(r'\\+n',text),paths=re.findall(r'[A-Za-z]:\\+[A-Za-z0-9_]+',text),
                angle_delimiters=[c for c in text if c in '<>'],
                other_placeholders=re.findall(r'\{\d+\}|\$[A-Za-z0-9_]+',text))

def group_labels(index,targets):
    """Bind group names to explicit source labels, never undefined references."""
    result={}
    for t in targets:
        _,e=index[t['id']];source=e['references']['und']
        require(e['source_sha256']==t['source_sha256'],'group label source binding mismatch')
        if t['value_kind']=='preference-descriptor':
            before=[m for m in LABEL.finditer(source) if m[1]=='Caption']
            after=[m for m in LABEL.finditer(t['target']) if m[1]=='Caption']
            require(len(before)==len(after)==1,'group caption selector mismatch')
            source,label=before[0][2],after[0][2]
        else:label=t['target']
        if source in result:require(result[source]['target']==label,'inconsistent group label translation')
        else:result[source]=dict(target=label,source_ids=[])
        result[source]['source_ids'].append(t['id'])
    return result

def validate_value(source,target,kind,*,parent_labels=None):
    require(isinstance(target,str) and bool(target) and not any(ord(c)<32 for c in target),'empty/control-byte configuration target')
    if kind=='preference-descriptor':
        before=list(LABEL.finditer(source));after=list(LABEL.finditer(target))
        require(before and [m[1] for m in before]==[m[1] for m in after],'preference label selector mismatch')
        require(LABEL.sub(lambda m:m[1]+'=""',source)==LABEL.sub(lambda m:m[1]+'=""',target),'preference machine descriptor changed')
        require(all(m[2] for m in after),'empty preference label')
        for old,new in zip(before,after):
            if old[1]=='Parent' and old[2]!=new[2]:
                require(parent_labels is not None and old[2] in parent_labels and parent_labels[old[2]]['target']==new[2],'unbound preference parent group changed')
    else:
        require(kind=='localized-template','unsupported configuration value kind')
        require(template_tokens(source)==template_tokens(target),'configuration template tokens changed')
        if source.startswith('"') and source.endswith('"'):
            require(target.startswith('"') and target.endswith('"'),'quoted configuration wrapper changed')
    return True

def config_lines(raw):
    require(b'\0' not in raw,'NUL in configuration')
    rows=[];section=None;occurrences={};offset=0
    for number,line in enumerate(raw.splitlines(keepends=True),1):
        content=line.rstrip(b'\r\n');stripped=content.strip()
        if stripped.startswith(b'[') and stripped.endswith(b']'):
            section=stripped[1:-1].decode('ascii');occurrences[section]=occurrences.get(section,0)+1
        elif stripped and not stripped.startswith((b';',b'#')):
            require(section is not None and b'=' in content,'unrecognized configuration line')
            key,value=content.split(b'=',1);key.decode('ascii');require(key.strip(),'empty configuration key')
            rows.append(dict(line=number,section=section,section_occurrence=occurrences[section],key=key.decode('ascii'),
                offset=offset+len(key)+1,value=value,newline=line[len(content):]))
        offset+=len(line)
    require(offset==len(raw),'configuration byte coverage mismatch')
    return rows

def rewrite_values(raw,entries,targets,encoder,*,parent_labels=None):
    require(len(entries)==len(targets) and bool(entries),'configuration target count mismatch')
    lines={r['line']:r for r in config_lines(raw)};changes=[];seen=set()
    for e,t in zip(entries,targets):
        require(e['id']==t['id'] and e['id'] not in seen,'configuration identity mismatch/duplicate');seen.add(e['id'])
        require(e['source_sha256']==t['source_sha256'],'configuration source hash mismatch')
        require(e['line'] in lines,'configuration source line missing')
        row=lines[e['line']];source=row['value']
        require(row['offset']==e['offset'] and len(source)==e['source_bytes'] and hashlib.sha256(source).hexdigest()==e['source_sha256'],'configuration source geometry mismatch')
        require(all(row[k]==e[k] for k in ('section','section_occurrence','key')),'configuration section/key mismatch')
        validate_value(source.decode('ascii'),t['target'],t['value_kind'],parent_labels=parent_labels)
        encoded=encoder.encode_characters(t['target']);require(not any(c in encoded for c in (0,10,13)),'encoded configuration contains a line delimiter')
        changes.append(dict(id=e['id'],offset=e['offset'],original=source,modified=encoded,line=e['line']))
    changes.sort(key=lambda x:x['offset']);result=bytearray();end=0;receipts=[]
    for c in changes:
        require(c['offset']>=end,'overlapping configuration targets');result.extend(raw[end:c['offset']]);at=len(result);result.extend(c['modified'])
        receipts.append(dict(id=c['id'],line=c['line'],old_offset=c['offset'],new_offset=at,old_bytes=len(c['original']),new_bytes=len(c['modified']),encoded_hex=c['modified'].hex()))
        end=c['offset']+len(c['original'])
    result.extend(raw[end:]);after={r['line']:r for r in config_lines(bytes(result))};selected={c['line']:c for c in changes}
    for number,row in lines.items():
        require(number in after and all(row[k]==after[number][k] for k in ('section','section_occurrence','key','newline')),'configuration identity/newline changed')
        require(after[number]['value']==(selected[number]['modified'] if number in selected else row['value']),'configuration selected/untargeted value changed')
    require(len(lines)==len(after),'configuration line count changed')
    return bytes(result),receipts
