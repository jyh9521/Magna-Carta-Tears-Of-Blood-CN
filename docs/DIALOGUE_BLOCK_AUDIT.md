# POD 完整文本块核查

## Verified static（2026-10-10）

148 个 POD 的完整 12,328 B 区块核对原始资源 hash。每个区块包含 24 个固定 512 B 文本槽，全部检查 NUL 与零 padding；剩余 40 B 分成 4 段 metadata，全文字节划分精确闭合。

| 文本槽 | 文件 offset | 槽数量／容量 |
|---|---|---|
| 0–9 | 20 + 512 × i | 10 × 512 B |
| 10 | 5144 | 1 × 512 B |
| 11–14 | 5656 + 512 × i | 4 × 512 B |
| 15–18 | 7708 + 512 × i | 4 × 512 B |
| 19 | 9756 | 1 × 512 B |
| 20–23 | 10268 + 512 × i | 4 × 512 B |

metadata 为 [0,20)、[5140,5144)、[7704,7708)、[12316,12328)。前 3 个 u32 在全部输入为 31、1、0；这些值不是本轮已经确认的 count／kind，具体语义保持未验证，不按其他资源头格式套用。

共 3,552 个完整字段：333 非空、3,219 空。旧集合 340 条启发式字段中 330 与完整字段精确相同，10 为文字子片段；没有数值区或跨界未解释片段。

补出 3 个没有旧完整视图的非空字段：00005214 的槽0／槽19是两处相同日文对白，均 CP949 失败、CP932 严格往返成功；00007253 的槽1为三个 ASCII 问号。日文两处独立 ID 保留，不凭相同字串自动合并 linked group；问号缺损／用途也不猜测。完整字段避免只搜 Hangul 造成的遗漏。

## High-confidence deduction

24 槽的分组与普通包脚本 MrtsCommunicatorData 中 OtherSpeech、MySpeech、Question、MyAnswer、OtherAnswer、DefaultSpeech、DefaultAnswer 的数组数量一致；具体落盘 metadata 到脚本成员映射与执行可达性尚未验证。第一槽和默认槽可相同也可不同，不将默认槽一律删除。

## 重现与边界

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_dialogue_blocks.py --corpus work/extraction-coverage-48/final-audit/source-corpus.json --ship work/kr/SHIP.AFS --out work/dialogue-blocks/audit
```

未知前缀、尺寸、脏 padding 均拒绝。完整原文仅在 ignored 输出；原始 corpus、SHIP、既有译文与测试 ISO 均未改动。不新增译文、不给予导入许可，全文覆盖仍未闭合。
