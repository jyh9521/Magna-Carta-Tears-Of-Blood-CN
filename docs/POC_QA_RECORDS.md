# PoC验收记录校验

日期：2026-10-09。范围：人工验收记录的结构、构建身份与证据文件绑定。不是游戏运行结果判定器。

## 记录入口

一键构建产生QA_CHECKLIST.json；保留初始文件，将副本放入ignored work/build作为本次测试记录。字段说明：

- candidate_sha256必须匹配实际指定ISO；不能把旧构建记录直接套到新候选。
- pcsx2_version、bios_identifier、renderer记录实际环境的非空字符串；BIOS只记录身份，不附BIOS文件。
- 三个文本case的id/kind/expected保持原值，另有cold-boot、two-font-paths、normal-save-load、scene-transition、battle、linked-character-name六项。
- status只接受untested/pass/fail。pass和fail都是人工声明，不由工具推断；两者都须有环境信息及至少一项证据。
- evidence为文件路径数组，相对路径基于记录文件目录，也可使用绝对路径。截图、文本日志或录像保持在ignored目录。支持png/jpg/jpeg/webp/txt/log/mp4/mkv；不接受ISO或原资源作为证据。
- untested须保持空evidence。短UI列表不替代正常存读档，字幕分页不替代场景切换。证据无法覆盖某项时，该项保持untested。

局部记录例子如下；环境值及路径为占位符，不是实际测试证据：

```json
{
  "id": "cold-boot",
  "status": "pass",
  "evidence": ["screens/cold-boot.png"]
}
```

## 校验命令

```powershell
work/venv/Scripts/python.exe -X utf8 tools/validate_poc_qa.py --candidate "<candidate-ISO-path>" --receipt work/qa-session/QA_CHECKLIST.json --locale locales/zh-CN/poc-text.json --out work/qa-record-validation
```

输出目录使用新空work/build子目录，不覆盖已有记录/证据/ISO；输入不得位于输出树中。输出qa-validation.json记录候选、locale、receipt及每个证据文件hash/大小，并保存人工状态和未测试项。
候选、locale、receipt前后hash保持；证据hash在写结果前再次核对。相同case内重复文件、缺失/空证据、未知状态、重复/缺少case、预期文本变化、错误候选hash和缺失环境均拒绝。

| 记录状态 | 条件 | CLI退出状态 |
|---|---|---:|
| pending | 至少一项untested且没有fail | 0 |
| recorded-complete | 全部为人工pass | 0 |
| recorded-failure | 至少一项人工fail | 2 |
| 无结果 | 记录无效、输入改变或输出目录不符合条件 | 1 |

退出0只说明有效记录，不能等同完整验收。recorded-failure仍保存有效失败记录；结构错误不保存qa-validation.json。
工具不启动PCSX2、不理解截图内容、不判断截图是否来自指定ISO、不验证视频真实性；candidate hash仅绑定记录声明。错误截图即使被填入当前记录也可能通过文件检查，需人工核对画面/日志与构建身份。单个截图/日志不自动证明存读档、长期稳定性或两字体路径。

## 本轮验证

25项新增合成测试后工程309项通过；人工pass完整样本仍输出manual claims/not independently verified。真实候选与一键生成的初始记录实测输出pending，九项均untested；旧PoC hash的记录副本退出1且没有成功报告。人工fail的隔离合成CLI样本退出2并保存recorded-failure；它不作为游戏失败证据。
干净源码复现同一记录校验结果，隔离源码回滚恢复284项基线。没有改动候选ISO、locale文字或构建工具，没有新增游戏运行证据。事务保存在ignored build/qa-receipt-19/VERIFICATION.txt。

**Verified**：记录结构、输入/证据文件hash、拒绝门禁、合成状态与CLI行为。
**High-confidence deduction**：独立记录副本及证据hash有助于追踪人工验收资料的版本和后续变化。
**Unverified hypothesis**：新增槽候选的游戏内表现；完整人工pass也不自动升级为独立运行时验证。

## 可选名称case

locale含显式name_slot_overlays时，生成器与validator增加SHIP/resource/slot/N名称case；单字段候选共10项而非9项，expected与target严格比较。人物菜单的名称证据独立于相同测试文字的剧情/UI证据，见 [单姓名候选](QA_NAME_POC.md)。
