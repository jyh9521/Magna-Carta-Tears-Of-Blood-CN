# 固定 region 资源完整字段补提取

## Verified static（2026-10-10）

44 个 ITM／ABI／SGI／NOD／DOD 资源按 8 B 头（count、kind）及实际记录 stride 精确闭合。1,180 个记录的全部 2,360 个文本字段均检查 NUL、零 padding、原始资源和字段 SHA-256；2,014 非空、346 空、零 CP949 严格解码失败。不采用 ASCII／Hangul 扫描作为正文边界。

| 格式 | kind | stride | 文本区（记录内 offset／容量 B） | 文件／记录 |
|---|---:|---:|---|---|
| ITM | 25 | 594 | 4／255、331／255 | 1／479 |
| ABI | 7 | 192 | 4／40、64／128 | 1／358 |
| SGI | 22 | 251 | 4／100、184／67 | 1／249 |
| NOD | 11 | 132 | 4／25、45／87 | 1／54 |
| DOD | 14 | 564 | 4／256、308／256 | 40／40 |

非文本区按精确边界和 hash 保留为 opaque；名称／描述／技能说明等用途可由内容及脚本结构对照，但不将全部字段自动授权为可见或可导入。

## 已证实的提取缺口

旧集合这五类包含 1,556 条启发式字段：1,516 与完整文本字段精确相同，33 是文本子片段，7 完全位于数值／opaque 区。全部旧片段都已核对原始 hash；没有边界跨越或未归类旧片段。

完整字段中，**498 个非空字段没有旧精确视图**：ITM 412、ABI 21、SGI 52、NOD 13。其中 **488 个与旧正文片段无字节重叠**，10 个仅部分字节重叠；此外补保留 346 个空字段。空字段和候选数不等于实际翻译量。

ITM 包含大量先前漏提取的物品描述，包括武器、装备、材料、消耗品和流派书说明。非零数值区（例如 0xffffffff）与后续描述相邻时，NUL 启发式把数值区一起当成字串，严格 CP949 解码拒绝，从而漏掉后面的合法正文；完整记录字段能单独取到文本。严格解码通过仍不证明所有文字语言为韩文，日文／标记与语义继续核查。

新增完整原文仅保存在 ignored 输出，不新增翻译、不覆盖旧 corpus，不自动迁移既有草稿。统一源集合合并时需替代旧启发式字段，保留精确 ID／hash 关联，子片段与数值候选分别隔离；禁止新旧重复计数。

## 重现与证据边界

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_region_records.py --corpus work/extraction-coverage-48/final-audit/source-corpus.json --ship work/kr/SHIP.AFS --out work/region-records/audit
```

复用上游 AFS reader；未知 kind、count／尺寸不符、无 NUL、脏 padding 均拒绝。源集合与 SHIP hash 在执行前后一致。完整 records、text-fields、previous-contexts、missing-full-fields、summary 输出均重新打开验证。数据布局已静态核查；opaque 用途、运行时引用、导入支持、图片及 SFD 完整覆盖仍未闭合。
