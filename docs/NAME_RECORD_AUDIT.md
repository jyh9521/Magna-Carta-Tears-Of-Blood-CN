# CHA／MDG 完整记录与怪字候选核查

## Verified static（2026-10-10）

两个资源均为 8 B header（count、kind），按实际 count 精确闭合至文件末尾。CHA 为 kind11、301 个 299 B 记录；MDG 为 kind5、45 个 526 B 记录。346 个完整记录中的 391 个文本字段全部严格 CP949 解码、NUL 终止且剩余 padding 为零。

| 格式 | 记录内相对 offset | 字节长度 | 观测布局 |
|---|---:|---:|---|
| CHA | 0 | 4 | u32，具体语义未完成 |
| CHA | 4 | 255 | 名称文本区 |
| CHA | 259 | 40 | 10 个 u32，具体语义未完成 |
| MDG | 0 | 8 | 2 个 u32，具体语义未完成 |
| MDG | 8 | 255 | 名称文本区 |
| MDG | 263 | 8 | 2 个 u32，具体语义未完成 |
| MDG | 271 | 255 | 描述文本区 |

旧 CHA header12／stride299 与旧 MDG header16／stride263 视图的全部 391 个字段和新布局的文本 offset、长度、hash 一一相同；新布局解释数值区，不新增正文。旧字段 ID 保留，局部核查输出提供 hash-bound 别名，不改既有译文。

381 个扫描候选中 375 个已落在文本正文，剩余 6 个全部落在完整 u32 数值内，没有未覆盖候选。此前 CHA／MDG 的 6 个怪字候选字节缺口因此关闭，但数值字段的完整用途与运行时显示关系不从扫描自动推断。

| 资源 | 候选文件 offset | 包含的 u32 值 |
|---|---:|---:|
| 00000460.cha | 61287 | 16819 |
| 00000460.cha | 66960 | 16816 |
| 00000460.cha | 66964 | 16824 |
| 00000460.cha | 67259 | 16830 |
| 00000460.cha | 67263 | 16836 |
| 00006461.mdg | 9213 | 16792 |

这 6 个数值的低位字节恰能解码为单个韩文音节；后续高位零字节令 NUL 启发式误识别成文字。不能将它们作为翻译字段或修改数值。资源引用等具体语义尚需代码／关联表证据。

## 重现与边界

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_name_records.py --corpus work/extraction-coverage-48/final-audit/source-corpus.json --ship work/kr/SHIP.AFS --out work/name-records/audit
```

复用上游 AFS reader，实际记录区划分单独核对；未知 kind、尺寸不符、无 NUL、非零文本 padding、旧字段不匹配均拒绝。完整原文仅进入 ignored 输出；不导入游戏、不扩大翻译、不生成 ISO。全文覆盖门禁仍未闭合。
