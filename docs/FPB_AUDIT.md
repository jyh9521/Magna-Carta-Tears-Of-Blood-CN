# 韩版 FPB 离线适用性审计

日期：2026-10-08。输入：SCKA-20043，ISO SHA-256 `6242476a66a96110fb6ee1a1dd668eedd70d3df6c835f0de9192451b5f4fcd45`。
工具：`tools/audit_text_resources.py`。复用soyjxck上游FPB parser/builder及AFS读取实现，不新增游戏文本翻译。

## Verified — 字节与当前实现

| 检查 | 结果 | 含义 |
|---|---:|---|
| SHIP中的.fpb条目 | 708 | 707个解析资源、1个8 B stub；stub未按FPB解析 |
| 无编辑parse/build一致 | 707/707 | 字节回写不改变原资源，不等于修改后游戏可用 |
| 当前连续partition前置条件 | 701/707 | 6个资源的上游合成views未覆盖pool前缀 |
| 整池严格CP949解码 | 695/707 | 12个失败；未使用替换字符隐藏错误 |
| 严格控制结构、原始控制字节与窗口解码条件 | 673/707 | 20个资源含未识别百分号结构；另2个资源含NUL |
| partition与上述校验条件交集 | 667/707 | 仅结构前置条件，不包含目标文本、字库、长度、UI及运行时验证 |

695个可严格解码pool合计识别3382个`$n`；本次这些pool中未识别到`$DNN`。
该范围不覆盖解码失败资源、其他格式或其他版本；现有`$DNN`保护规则继续保留。
20个pool合计30处未识别`%`，当前规则保持拒绝，不将百分号无条件转为普通文本。

字符出现次数按CP949编码分层：可打印ASCII 74714、B0A1..C8FE韩文范围167168、其余CP949/控制字符4748。
次数不是去重字符数、译文条数或缺字数；最后一类并不意味着原引擎缺字，只说明不属于小字集后端开放的映射范围。

## Verified — 显式seq0与前缀

| 资源 | 合成views未覆盖的前缀长度/B | header +0x0C |
|---|---:|---:|
| 00004668.fpb | 177 | 177 |
| 00004669.fpb | 217 | 217 |
| 00004800.fpb | 86 | 86 |
| 00004994.fpb | 32 | 32 |
| 00005047.fpb | 167 | 167 |
| 00006436.fpb | 123 | 123 |

六个资源均已有显式seq0。上游`synthesize_implicit_seq0`遇显式seq0时不新增前缀view，因此当前逐view增长后端拒绝这些资源。
这里的gap描述合成view覆盖，不表示原文件损坏或前缀未被引擎使用；原版均可无编辑byte-identical回写。
后续若开放编辑，须同时处理header implicit length和显式窗口关系、保留前缀，不能直接丢弃gap或覆盖seq0。

`00000106.fpb`整池可解码，但合成窗口0..7逐窗严格CP949解码失败，并含12个NUL；`00000218.fpb`含6个NUL。
这些字节结构尚未确认为普通对话字段，不开放目标编辑。

## Unverified hypothesis — 编码与运行时

12个CP949解码失败资源是否残留日文、混合编码或非文本数据仍未确认；仅凭其他codec能解码不能判定字符编码。
30处百分号的运行时含义尚未确认；本次未修改validator规则。
显式seq0与header前缀的运行时读取优先级、所有窗口能否逐条增长、场景触发和字体容量尚待研究。
667个资源满足静态前置条件不构成批量翻译或批量写回授权。

## 重现与数据边界

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_text_resources.py --iso "<original-KR-ISO-path>" --out work/fpb-audit
```

工具先校验原ISO完整hash，再只读SHIP；审计后复核原ISOhash不变。
完整JSON仅写入ignored `work/fpb-audit/fpb-audit.json`，记录资源hash、窗口问题、控制符统计及错误位置，不导出原版对话正文。
提取SHIP仅放同一ignored目录。57项合成/工程测试通过，不需要游戏资源；PCSX2验收状态保持不变。

下一步：原版资源结构例外与控制符语义研究；新小字集版本的运行时步骤仍见 [QA_TEXT_POC](QA_TEXT_POC.md)。
