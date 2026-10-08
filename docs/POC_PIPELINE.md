# 一键PoC构建与独立镜像验证

日期：2026-10-09。状态：Verified static。工程284项测试通过；不新增译文，不改变测试内容，不代表PCSX2验收。

## 本轮范围

`tools/build_poc_pipeline.py`串联现有Font扩容、package、bundle、ISO与独立verify五步，不重写上游AFS/ISO/SFD，也不扩大当前三个显示字段。locale为显式参数，语言数据继续位于locales/<locale>。
每步使用同一Python runtime、参数数组和明确profile/输出目录；失败立即停止，保存步骤日志/退出状态和failed_step。输出目录必须是work/build下的新空子目录，不清理、不覆盖既有候选，不允许输入位于输出树中。
pipeline.json保存原ISO、外部字体、locale及工具源码hash、每步命令/退出状态、最终ISOhash。完成时重新确认输入hash；状态static-pass与runtime unverified分别记录。
QA_CHECKLIST.md提供最短验收步骤；QA_CHECKLIST.json预留PCSX2版本/BIOS标识/renderer和每项状态/证据，全部初始为untested。

## 干净源码加外部输入

按BUILDING.md安装requirements-research.txt中的固定依赖。当前profile仅支持已确认韩版；SimHei必须匹配locale中的锁定hash，仅作本地实验，不分发字体/bitmap。

```powershell
work/venv/Scripts/python.exe -X utf8 tools/build_poc_pipeline.py --iso "<original-KR-ISO-path>" --font "<matching-font-path>" --locale locales/zh-CN/poc-text.json --out build/poc-pipeline
```

输出为fonts/、package/、bundle/、image/MODIFIED_FILE.iso、verification/、各阶段log、pipeline.json和QA_CHECKLIST.md/json，均ignored。构建只需源码、固定依赖、原ISO及匹配字体；不读取旧work/font-expansion等私有中间文件。单阶段命令继续保留。
本轮实际一键输出位于ignored `build/pipeline-poc-04-final/`。ISO为3232653312 B，SHA-256 `e1cb3fb807fd9cf158bd3147b4ef3e6c2fabafcbc4224319f4a8a8c31445355f`，与 [新增槽候选](QA_EXPANDED_POC.md)完全相同，不是另一组测试文字或新汉化版本。

## 不信任构建报告的验证

```powershell
work/venv/Scripts/python.exe -X utf8 tools/verify_expanded_locale.py --source "<original-KR-ISO-path>" --candidate "<candidate-ISO-path>" --font "<matching-font-path>" --locale locales/zh-CN/poc-text.json --out work/independent-verification
```

输入仅为原ISO、候选ISO、字体和显式locale；不读取候选的DIFF_FILE.json、pipeline.json或中间Font/AFS副本。候选只读，推导产物写入新空ignored目录。

独立推导与验证范围：

- 原ISO/profile与字体hash、cmap和33字符覆盖；重新rasterize两Font，核对原glyph/metric/map保持。
- 重新生成完整UE2包，保留7666个无关export；缓存六段和UI副本按原输入重新推导。
- FPB增长、固定槽、控制符/placeholder、UI静态宽度预算；重新构建两个AFS及slot0 manifest。
- 从候选ISO读回AFS并比较全部archive bytes；重新规划UDF更新，验证ISO9660/UDF视图、padding、PVD和全部原镜像未修改区间。
- 检查前后源ISO和候选hash保持；通过后才生成verification.json。

实际负向测试仅修改隔离候选的一个ELF byte，验证器报`untargeted ISO bytes changed at 0`，退出1，没有成功报告；原ISO与可验收候选保持。该负向样本不启动、不作为游戏测试版本。
独立验证复用成熟parser/writer/rasterizer，是不依赖构建报告的二次推导，不是第二套独立实现；共同实现缺陷仍需合成测试和运行时验收揭示。

## 新增测试与边界

17项编排/输出卫生/失败记录/QA初态测试、10项合成独立Font推导和版本门禁测试、3项UDF空间管理门禁测试新增后共284项通过。UDF overlay仅支持空space bitmap/table/integrity-table引用；非零描述符明确拒绝，防止扩展partition却漏更新bitmap。原韩版主备五组引用均为零，实际候选bytes不变。
干净源码一键构建复现相同ISOhash；源码回滚恢复254项基线，既有新增槽和旧小字集ISOhash保持。事务位于ignored `build/pipeline-18/VERIFICATION.txt`。
**Verified static**：上述构建、二次推导、tamper检测和可复现性。
**High-confidence deduction**：减少对未记录中间文件和构建报告的依赖，有助于隔离构建/传递错误。
**Unverified hypothesis**：PCSX2启动、D0字形显示、缓存容量、版式、存读档、场景、战斗和linked名称；本轮没有模拟器运行证据。

## 早晨最短验收

仍可使用上轮build/expanded-text-poc-03-udf/MODIFIED_FILE.iso；它与一键产物bytes相同，不要求重复验收同hash副本。先冷启动、进入读档列表，确认“测试中文。123ABC”。短UI通过后再推进剧情；空槽列表不替代正常存读档，分页不替代切场景。
保存截图或日志时记录ISOhash和PCSX2版本/backend，按QA_CHECKLIST逐项登记；系统字体、原资产、模拟器、BIOS和配置不进入Git。
