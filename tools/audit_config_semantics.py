"""Classify config roles with source-byte and script-reference evidence.

A candidate role is not runtime visibility or an import authorization.
"""
from pathlib import Path
from collections import Counter, defaultdict
import argparse, copy, json, re, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'lib')]
import font_poc as core
from cri_afs import Afs
from afs import filename_toc
from audit_config_entries import parse_lines, exact_positions
from extract_script_buffers import FILE_HASH, text_buffer
from research_inventory import package_tables
from audit_container_payloads import unpack_chunks
from audit_bundle_contexts import BUNDLE_HASH
CORPUS_HASH='9f2a5445fe5b9e4c56f19df647a9e112d281bfe506549d4fe044fe498c77d1b7'
CATEGORIES={'visible-text-candidate','internal-configuration','diagnostic-text','unresolved'}


def members(value):
    """Bounded Public descriptor fields, preserving quoted commas and offsets."""
    core.require(value.startswith('(') and value.endswith(')'), 'descriptor parentheses')
    fields=[];pos=1
    while pos<len(value)-1:
        m=re.match(r'([A-Za-z]+)=',value[pos:]);core.require(m is not None,'descriptor key')
        key=m[1];pos+=len(m[0]);start=pos
        if value[pos:pos+1]=='"':
            pos+=1
            while pos<len(value)-1 and value[pos]!='"':
                if value[pos]=='\\':pos+=1
                pos+=1
            core.require(pos<len(value)-1,'descriptor quote');pos+=1
        else:
            while pos<len(value)-1 and value[pos]!=',':pos+=1
        core.require(pos>start,'empty descriptor member')
        fields.append(dict(key=key,start=start,end=pos,raw=value[start:pos],
            category='visible-text-candidate' if key=='Caption' else 'internal-configuration',
            reason='caption-label-candidate' if key=='Caption' else 'hierarchy-or-object-lookup-protected'))
        if pos<len(value)-1:core.require(value[pos]==',','descriptor separator');pos+=1
    core.require(pos==len(value)-1,'descriptor end')
    core.require(len({f['key'] for f in fields})==len(fields),'duplicate descriptor member')
    return fields


def role(resource,section,key,value):
    """Closed reviewed section/key rules. Unknown cases stay unresolved."""
    key=key.strip();base=re.sub(r'\[\d+\]$','',key)
    name=resource.split('/')[-1].lower()
    if not value:return 'internal-configuration','empty-value-no-text',[]
    if name.endswith('.ini'):
        if section in ('DefaultPlayer','URL') and key=='Name':return 'unresolved','default-player-identity-needs-consumer',[]
        if section=='URL' and key=='ProtocolDescription':return 'unresolved','protocol-description-needs-consumer',[]
        if section=='Engine.GameReplicationInfo' and key in ('ServerName','ShortName','AdminName','MOTDLine1','MOTDLine2','MOTDLine3','MOTDLine4'):
            return 'visible-text-candidate','server-metadata-not-game-ui-proof',[]
        if section=='Engine.Input':return 'internal-configuration','input-command-or-alias',[]
        if re.fullmatch(r'(?i:true|false|[-+]?\d+(?:\.\d+)?)',value.strip()):return 'internal-configuration','boolean-or-numeric-parameter',[]
        if section=='Core.System' or section=='Engine.StatLog' or key in ('Map','LocalMap','MapExt','SaveExt','Protocol','Host','Portal','Port','Class','Language','AdminEmail','ServerLogName','ServerPackages','DownloadManagers'):
            return 'internal-configuration','path-protocol-resource-or-lookup',[]
        if section=='Engine.Engine':return 'internal-configuration','class-or-subsystem-selection',[]
        if section=='PSX2Drv.PSX2Client' and key in ('SkinDetail','TextureDetail','LightmapDetail'):return 'internal-configuration','quality-enum',[]
        return 'unresolved','unreviewed-config-key',[]
    if section=='Public':
        if key in ('Object','Class'):return 'internal-configuration','public-class-registration',members(value)
        if key=='Preferences':return 'visible-text-candidate','mixed-preference-descriptor',members(value)
        return 'unresolved','unreviewed-public-key',[]
    if base in ('HelpCmd','HelpParm'):return 'internal-configuration','command-or-parameter-token-even-if-printed',[]
    if key.endswith('URL') or key in ('HelpWebLink','WebPage','Direct3DWebPage','DefaultFolder','ReadMe','Logo','License','OtherSideURL','ConnectingURL'):
        return 'internal-configuration','path-or-url-template',[]
    if section=='Language' and key in ('LangId','SubLangId'):return 'internal-configuration','numeric-language-id',[]
    if section=='Errors':return 'diagnostic-text','engine-or-installer-error-message',[]
    if base in ('HelpOneLiner','HelpUsage','HelpDesc'):return 'diagnostic-text','commandlet-help-with-protected-syntax',[]
    if name=='core.int' and section in ('Language','Query','Progress','General'):return 'visible-text-candidate','internationalization-label-or-prompt',[]
    if name=='engine.int' and section in ('Progress','Console','General','Menu','Inventory','GameInfo','LevelInfo','Weapon','Counter','Ammo','Pickup','SpecialEvent','DamageType','PlayerPawn','Pawn','Spectator'):
        return 'visible-text-candidate','engine-localized-default-candidate',[]
    if name in ('setup.int','startup.int','window.int','windrv.int','unrealed.int') or name.startswith('setupwarfare') or name=='manifest.int':
        if section=='Setup' and key not in ('LocalProduct','Developer','SetupWindowTitle','AutoplayWindowTitle'):return 'unresolved','unreviewed-setup-key',[]
        if section in ('Setup','General','FirstRun','Descriptions','WindowsClient') or section.startswith(('IDDIALOG_','IDMENU_')) or key in ('Caption','Description'):
            return 'visible-text-candidate','desktop-editor-installer-label-candidate',[]
    if key=='ClassCaption':return 'visible-text-candidate','subsystem-class-caption',[]
    return 'unresolved','unreviewed-int-key',[]


def script_sources(afs,names,stream):
    sources=[]
    for index,name in enumerate(names):
        raw=afs.read_entry(index,stream)
        if not raw.startswith(bytes.fromhex('c1832a9e')):continue
        tables=package_tables(raw)
        for e in tables['exports']:
            if e['class']!='TextBuffer':continue
            serial=raw[e['offset']:e['offset']+e['size']];parsed=text_buffer(serial)
            owner=tables['exports'][e['outer']-1]['name'] if e['outer']>0 else None
            sources.append(dict(id=f'FILE/{name}/export/{e["index"]}/TextBuffer',owner=owner,package=name,
                package_sha256=core.digest(raw),serial_sha256=core.digest(serial),text=parsed['text']))
    return sources


def reference_index(sources):
    declarations=defaultdict(list);calls=[]
    for source in sources:
        for number,line in enumerate(source['text'].splitlines(),1):
            code=line.split('//',1)[0]
            # Only complete single-line declarations are indexed, not full source parsing.
            if re.match(r'\s*var(?:\(|\s)',code,re.I) and ';' in code:
                prefix=code.split(';',1)[0]
                for name in set(re.findall(r'\b[A-Za-z_]\w*\b',prefix)):
                    declarations[(source['owner'],name)].append(dict(source_id=source['id'],line=number,
                        serial_sha256=source['serial_sha256'],statement=line,kind='script-declaration-reference'))
            m=re.search(r'\bLocalize\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)',code,re.I)
            if m:calls.append(dict(section=m[1],key=m[2],package=m[3],source_id=source['id'],line=number,
                serial_sha256=source['serial_sha256'],statement=line,kind='literal-localize-source-call-not-runtime-trace'))
    return declarations,calls


def classify(row,resource,declarations,calls):
    value=row['references']['und'];category,reason,subfields=role(resource,row['section'],row['key'],value)
    owner=row['section'].split('.')[-1];key=re.sub(r'\[\d+\]$','',row['key'].strip())
    refs=declarations.get((owner,key),[])
    exact=[c for c in calls if c['section']==row['section'] and c['key']==row['key'] and c['package'].lower()==resource.split('/')[-1].rsplit('.',1)[0].lower()]
    result=dict(id=row['id'],resource=resource,section=row['section'],section_occurrence=row['section_occurrence'],key=row['key'],line=row['line'],
        offset=row['offset'],source_sha256=row['source_sha256'],source_bytes=row['source_bytes'],value=value,
        category=category,reason=reason,evidence_level='high-confidence-deduction' if category!='unresolved' else 'unverified-hypothesis',
        evidence=[dict(kind='verified-source-section-key',section=row['section'],key=row['key'],line=row['line']),*refs,*exact],subfields=subfields,
        semantic_review='classified-candidate-not-runtime-proof',editable=False,backend_eligible=False,runtime_visibility_verified=False)
    for f in subfields:
        f['resource_offset']=row['offset']+f['start'];f['sha256']=core.digest(f['raw'].encode('ascii'));f['editable']=False
    return result


def audit(corpus_path,archive,out):
    core.require(core.file_digest(corpus_path)==CORPUS_HASH,'corpus identity mismatch')
    core.require(core.file_digest(archive)==FILE_HASH,'FILE identity mismatch')
    corpus=json.loads(corpus_path.read_text('utf8'));configs=[r for r in corpus['resources'] if r['resource'].startswith('FILE/')]
    afs=Afs.open(archive);names=filename_toc(afs);rows=[];mirrors=[]
    with archive.open('rb') as f:
        sources=script_sources(afs,names,f);declarations,calls=reference_index(sources)
        bundle,_=unpack_chunks(afs.read_entry(names.index('celfid.lix'),f));core.require(core.digest(bundle)==BUNDLE_HASH,'bundle mismatch')
        for r in configs:
            raw=afs.read_entry(names.index(r['resource'].split('/')[1]),f)
            core.require(core.digest(raw)==r['sha256'] and len(raw)==r['size'],'config identity mismatch')
            _,entries=parse_lines(raw);core.require(len(entries)==len(r['entries']),'config count mismatch')
            for e,v in zip(r['entries'],entries):
                core.require(e['id']==r['resource']+'/line/'+str(v['line']) and e['section']==v['section'] and e['key']==v['key'] and e['section_occurrence']==v['section_occurrence'],'config metadata mismatch')
                core.require(e['offset']==v['value_offset'] and e['source_bytes']==v['value_bytes'] and e['source_sha256']==v['value_sha256'] and e['references']['und']==v['value'],'config source mismatch')
                rows.append(classify(e,r['resource'],declarations,calls))
            mirrors.append(dict(resource=r['resource'],body_offsets=exact_positions(bundle,raw)))
    core.require(len(rows)==1008 and len({r['id'] for r in rows})==len(rows),'config coverage mismatch')
    review=copy.deepcopy(corpus)
    by_id={r['id']:r for r in rows}
    for resource in review['resources']:
        for e in resource['entries']:
            if e['id'] in by_id:
                c=by_id[e['id']];e.update(semantic_review=c['semantic_review'],semantic=c['category'],semantic_reason=c['reason'],semantic_evidence_level=c['evidence_level'])
    review.update(revision='config-role-classified-readonly',previous_corpus_sha256=CORPUS_HASH)
    summary=dict(schema=1,resources=len(configs),entries=len(rows),counts=dict(sorted(Counter(r['category'] for r in rows).items())),
        reasons=dict(sorted(Counter(r['reason'] for r in rows).items())),empty_values=sum(not r['value'] for r in rows),
        mixed_descriptors=sum(bool(r['subfields']) for r in rows),descriptor_caption_candidates=sum(f['key']=='Caption' for r in rows for f in r['subfields']),
        entries_with_script_declaration=sum(any(e['kind']=='script-declaration-reference' for e in r['evidence']) for r in rows),
        entries_with_literal_localize_call=sum(any(e['kind']=='literal-localize-source-call-not-runtime-trace' for e in r['evidence']) for r in rows),
        scripts_reparsed=len(sources),config_role_review_complete=True,runtime_visibility_verified=False,editable_values=0,
        backend_eligible_values=0,complete_game_text=False,translation_gate='coverage-audit-pending',source_modified=False,
        corpus_sha256=CORPUS_HASH,file_sha256=FILE_HASH)
    out=core.output_directory(out);core.require(not any(out.iterdir()),'output must be empty')
    for name,value in [('classifications.json',rows),('source-corpus.json',review),('localize-calls.json',calls),('mirrors.json',mirrors),('summary.json',summary)]:
        p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8');core.require(json.loads(p.read_text('utf8'))==value,'JSON reopen')
    core.require(core.file_digest(corpus_path)==CORPUS_HASH and core.file_digest(archive)==FILE_HASH,'input changed')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['corpus','archive','out']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.corpus,a.archive,a.out),sort_keys=True))
