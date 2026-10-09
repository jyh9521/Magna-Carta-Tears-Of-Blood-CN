# 统一源文本集合：记录补充修订

## 当前范围（Verified static）

只读组装器 `tools/assemble_source_corpus.py` 从旧主 catalog 与版本锁定的 SHIP.AFS 重现韩版多字段提取，不依赖上一轮本地补提取 JSON。998 个已知格式资源集中形成 source-corpus.json；全文覆盖仍未完成，`complete_game_text=false`，翻译门禁保持 `coverage-audit-not-complete`。

旧集合 15,635 个结构记录，六个修订资源的 1,682 个旧 leading-slot 记录由 1,168 个实际记录字段替代，当前活动集合 15,121 字段。数量下降 514 并不表示删除原文：六个旧资源完整存入 superseded-resources.json；其混入元数据、切段和空槽的旧视图仍可复核。原 source-catalog.json 保持原 hash，不覆写校对包。

61 个旧／新字段关联满足同一资源、offset、有效原文长度及 SHA-256 完全相同；只建立 source-aliases.json，不凭同文、子串或部分重叠转移译文。空字段也可有技术关联，该计数不是新增／保留对白数量。

五批次 6334 条既有初稿全部保持活动源 ID，源 SHA-256 逐条相符；本轮没有初稿落入需重新定位的旧视图。draft-links.json 只记录关联与 disposition，不复制译文、升级 reviewed 或授予导入权限。工具同时支持后续发现的 requires-source-remap 状态，禁止静默猜测映射。

## 补充字段编码观察（Verified bytes）

从实际 SHIP 字节切片核对字段 hash，不从显示文本重新编码以代替原输入。1168 个补充字段中有 5 个严格 CP949 解码结果含日文假名：FDS record-index/9 的四个字段，以及短 GFT record-index/50/field/6。CP949 字符集包含日文字符，日文语义不能直接证明 CP932 编码。

以现有“严格 CP932 往返且包含全角假名”候选规则检查，补充字段产生 0 个候选。这个零值只是该规则结果，不证明运行编码或彻底排除其他编码。此前 RECORD_FIELDS.md 的日文样本说明按此区分更正。

55 个非空 ASCII 字段集中列入语义审核；其中长 GFT 有 44 个内容为 0 的字段，另外包括英文句子、缩写／标识样式及标点。它们仍保留，不自动判定全部为内部键、调试残留或可见对白。显示用途与资源实际加载路径仍为 Unverified hypothesis。

## 输出与重现

本地 ignored 输出包括 source-corpus.json、superseded-resources.json、source-aliases.json、draft-links.json、supplement-encoding-audit.json、records/record-fields.json，以及 source-free summary.json。公开 [SOURCE_CORPUS.json](SOURCE_CORPUS.json) 不含原游戏正文。

```powershell
work/venv/Scripts/python.exe -X utf8 tools/assemble_source_corpus.py --catalog work/catalog-stage-24/catalog-final/source-catalog.json --ship work/kr/SHIP.AFS --batch locales/zh-CN/opening-review-01.json --batch locales/zh-CN/menu-review-01.json --batch locales/zh-CN/interface-review-02.json --batch locales/zh-CN/character-commentary-review-01.json --batch locales/zh-CN/story-review-01.json --out work/source-corpus/audit
```

输出必须为空且在 ignored work/build。输入 hash、资源身份、重复 ID、歧义 alias、旧译文源 hash、输出 JSON 回读及最终输入未改写均检查。新增九项测试；基线433项、修改版442项、隔离回滚433项通过。

## 未关闭项

这不是已冻结的全文语料，不自动启动统一翻译。其余编码候选、FPB 间隙、CHA／MDG 候选、region 内部标识符、celfid、UE2 属性与图片、ELF 和未匹配字幕仍待审计。后续在同一源集合上补充记录处理状态，源层与译文层继续分离。
