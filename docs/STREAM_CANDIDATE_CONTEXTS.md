# celfid 全启发式候选的字节区段核查

## Verified

当前源 corpus 的 35048 个启发式候选全部按 offset／length／SHA256 复核，既有 Core 与跨包连续对照映射按固定 hash 读取并重新核查每个片段字节。38499 个互不重叠的观察区段组成只读索引；候选跨区段边界时不拼接为已知文本。

| 字节上下文 | 候选数量 |
|---|---:|
| 有界脚本前缀 | 10219 |
| 原字节相同的字段片段 | 2232 |
| 原字节相同的 INI | 209 |
| 原字节相同的原生 serial | 1410 |
| 限定 Texture mip 投影 | 369 |
| 当前连续区段内包表及 wrapper | 11005 |
| 其他已读取包表 | 5776 |
| 原资源精确镜像 | 2595 |
| 未闭合字节上下文 | 1233 |

上述数量是启发式扫描命中数，不是正文数量。纹理像素、字体 bitmap、二进制字段和 opcode 均可能产生可解码候选；映射到资源也不证明运行可见。不依据这些分类删除候选、加入译文、改变 linked group 或放行门禁。全部候选保留 editable=false、semantic_review=pending。

## High-confidence deduction

连续对照使大量此前 other-payload 命中获得具体字段／脚本／原生资源上下文。剩余 1233 个仍需要逐类结构核查，不能以数量较少为由忽略。完整文本覆盖需要结构与可见语义共同证明。

## 未闭合部分

字体／像素／脚本中命中的实际含义、动态组合文本、原生尾区段和 CG 全时间轴仍未全部核实，semantic_review_complete=false、complete_game_text=false。

## 重现

先运行 Core --extended-oracle 与跨包 --equivalent-native 诊断生成 hash 一致的映射，再执行：

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_stream_candidate_contexts.py --archive work/kr/FILE.AFS --corpus work/extraction-coverage-69/consolidated-audit/source-corpus.json --core-map work/extraction-coverage-73/tree-audit-v2/prefix-map.json --dependency-map work/extraction-coverage-77/equivalent-audit/dependency-map.json --out work/stream-candidate-contexts
```

参数路径可替换，但输入内容身份必须一致。源 corpus 由已有 consolidated extraction 流程生成，不能以任意旧版扫描结果替代。原文和详细命中只保存 ignored work/build，公共报告只含数量与 hash。
