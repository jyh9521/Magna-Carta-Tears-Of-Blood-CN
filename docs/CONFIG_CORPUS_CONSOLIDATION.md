# 配置值并入统一只读源快照

## Verified

全部 29 个 FILE 配置／国际化资源的 1008 个值并入统一源快照。快照共 1027 个资源、20151 个字段，其中 15552 个非空、4599 个空字段；167 个解码失败和 101 个控制符隔离条目保持不变。此前 998 个资源／19143 个字段及 35048 个 celfid 启发式候选逐项保持不变。6334 条既有译稿全部保持 exact-source-link，无 ID 重映射或译文修改。

新增字段保留 section、重复 section 序号、key、行号、值的资源绝对 offset、原字节长度与 SHA-256。ASCII 原值使用 source_locale=und 和 references.und；ASCII 编码不等于英文可见正文。新增字段均 editable=false、backend_eligible=false、semantic_review=pending。3 个整资源镜像只标记 exact-byte-mirror，不宣称运行 linked group。

源快照 SHA-256：`9f2a5445fe5b9e4c56f19df647a9e112d281bfe506549d4fe044fe498c77d1b7`。

## 未闭合部分

20151 是已结构化字段数量，不是全文最终可翻译数量。配置值的运行语义、编译脚本与类属性、celfid 原生尾部、CG 画面文字仍属于独立核查范围。complete_game_text=false、translation_gate=coverage-audit-pending；此次未翻译、未导入、未生成 ISO。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/consolidate_config_fields.py --corpus work/extraction-coverage-69/consolidated-audit/source-corpus.json --archive work/kr/FILE.AFS --batch locales/zh-CN/opening-review-01.json --batch locales/zh-CN/menu-review-01.json --batch locales/zh-CN/interface-review-02.json --batch locales/zh-CN/character-commentary-review-01.json --batch locales/zh-CN/story-review-01.json --out work/config-consolidated-audit
```

输入源快照及 FILE 身份必须符合固定哈希，输出目录必须为空。工具重新读取原档，按 ID 检查冲突，拒绝意外可编辑补充字段。输出保存 source-corpus.json、draft-links.json、summary.json，逐一重新打开验证，原档与五份译稿哈希保持不变。原文输出仅保存在忽略目录。
