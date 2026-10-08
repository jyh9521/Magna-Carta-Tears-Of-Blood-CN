"""One-command staged PoC build and report-independent candidate verification."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import font_poc as core
from build_locale import load_config
from verify_expanded_locale import fresh_output


def command_plan(iso: Path,font: Path,locale: Path,profile: Path,out: Path,start: int) -> list[tuple[str,list[str]]]:
    base=[sys.executable,'-X','utf8'];tools=ROOT/'tools'
    fonts=out/'fonts';package=out/'package';bundle=out/'bundle';image=out/'image'
    common=['--iso',str(iso)]
    return [
        ('fonts',base+[str(tools/'build_font_expansion.py'),*common,'--font',str(font),'--locale',str(locale),'--range-start',hex(start),'--out',str(fonts)]),
        ('package',base+[str(tools/'build_font_package.py'),*common,'--expansion-dir',str(fonts),'--profile',str(profile),'--out',str(package)]),
        ('bundle',base+[str(tools/'build_font_bundle.py'),*common,'--package-dir',str(package),'--profile',str(profile),'--out',str(bundle)]),
        ('image',base+[str(tools/'build_expanded_locale.py'),*common,'--expansion-dir',str(fonts),'--package-dir',str(package),'--bundle-dir',str(bundle),'--locale',str(locale),'--out',str(image)]),
        ('verify',base+[str(tools/'verify_expanded_locale.py'),'--source',str(iso),'--candidate',str(image/'MODIFIED_FILE.iso'),
                       '--font',str(font),'--locale',str(locale),'--range-start',hex(start),'--out',str(out/'verification')])]


def run_steps(plan: list[tuple[str,list[str]]],out: Path,receipt: dict,*,runner=subprocess.run) -> None:
    def save(): (out/'pipeline.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    receipt['status']='running';receipt['steps']=[];save()
    for name,command in plan:
        try:
            result=runner(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,encoding='utf8')
            (out/(name+'.log')).write_text(result.stdout,encoding='utf8')
            receipt['steps'].append(dict(name=name,command=command,exit=result.returncode,log=name+'.log'));save()
            print(result.stdout.rstrip(),flush=True)
            if result.returncode:
                receipt['status']='failed';receipt['failed_step']=name;save()
                raise ValueError('pipeline step failed: '+name)
        except Exception:
            receipt['status']='failed';receipt['failed_step']=name;save();raise
    receipt['status']='static-pass';save()


def write_qa(out: Path, config: dict, result: dict) -> None:
    cases=[dict(id=entry['id'],kind=entry['kind'],expected=entry['target'],status='untested',evidence=[])
           for entry in config['entries']]
    for name in ['cold-boot','two-font-paths','normal-save-load','scene-transition','battle','linked-character-name']:
        cases.append(dict(id=name,status='untested',evidence=[]))
    (out/'QA_CHECKLIST.json').write_text(json.dumps(dict(candidate_sha256=result['candidate_sha256'],
        pcsx2_version=None,bios_identifier=None,renderer=None,cases=cases),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    ui=next(entry['target'] for entry in config['entries'] if entry['kind']=='fixed-display-slot')
    text=f'''# 新增槽PoC验收清单

构建状态：独立静态验证通过；运行时项目全部未测试，不是正式补丁。
实验ISO：`{out / 'image/MODIFIED_FILE.iso'}`。
SHA-256：`{result['candidate_sha256']}`。

## 最短测试

1. 冷启动本目录image/MODIFIED_FILE.iso，不载入旧即时存档。
2. 进入读档列表，空槽提示预期为“{ui}”；记录启动、缺字/乱码、重叠及裁切结果。这一步不需等待完整开场。
3. 短UI通过后再检查开场标点、$n、长句折行和下一页末尾。分页不计作切场景。

## 证据记录

QA_CHECKLIST.json预留PCSX2版本、BIOS标识、renderer、每项状态和证据路径。
空槽列表不验证正常存读档；正常存读档、场景、战斗、两字体路径和linked名称单独记录。旧构建截图不转移为本构建的验收。
pipeline.json保存每步命令/退出状态和源文件hash，verification/verification.json保存独立验证结论。
系统字体、ISO、原资源、模拟器、配置和BIOS均不进入Git。没有新增正式译文。
'''
    (out/'QA_CHECKLIST.md').write_text(text,encoding='utf8')


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--iso',type=Path,required=True);p.add_argument('--font',type=Path,required=True)
    p.add_argument('--locale',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--range-start',type=lambda x:int(x,0),default=0xD0A1)
    a=p.parse_args();iso,font,locale=[path.resolve() for path in (a.iso,a.font,a.locale)]
    config,game,encoder=load_config(locale)
    core.require(core.file_digest(iso)==game['expected_iso_sha256'],'source ISO fingerprint mismatch')
    core.require(core.file_digest(font)==config['font_input']['sha256'],'font input fingerprint mismatch')
    out=fresh_output(a.out,[iso,font,locale])
    receipt=dict(schema=1,locale=config['locale'],source_sha256=game['expected_iso_sha256'],font_sha256=config['font_input']['sha256'],
                 locale_sha256=core.file_digest(locale),range_start=f'{a.range_start:04X}',runtime='unverified',
                 tool_sha256={str(path.relative_to(ROOT)).replace('\\','/'):core.file_digest(path)
                              for directory in ['tools','src/localization','lib','lib/translate'] for path in sorted((ROOT/directory).glob('*.py'))})
    plan=command_plan(iso,font,locale,(ROOT/config['game_profile']).resolve(),out,a.range_start)
    run_steps(plan,out,receipt)
    try:
        result=json.loads((out/'verification/verification.json').read_text('utf8'))
        core.require(core.file_digest(iso)==receipt['source_sha256'] and core.file_digest(font)==receipt['font_sha256']
                     and core.file_digest(locale)==receipt['locale_sha256'],'pipeline input changed')
        core.require(result['source_sha256']==receipt['source_sha256'] and result['font_sha256']==receipt['font_sha256']
                     and result['locale']==receipt['locale'],'independent verification inputs disagree')
        write_qa(out,config,result)
    except Exception:
        receipt['status']='failed';receipt['failed_step']='final-input-validation'
        (out/'pipeline.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8');raise
    receipt['candidate_sha256']=result['candidate_sha256'];receipt['candidate']='image/MODIFIED_FILE.iso'
    (out/'pipeline.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(f"POC PIPELINE PASS stages=5 independent_verify=true sha256={result['candidate_sha256']} runtime=unverified")


if __name__=='__main__':main()
