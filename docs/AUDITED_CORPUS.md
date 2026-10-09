# 已核查布局的统一源集合

## 当前静态集合（2026-10-10）

998 个资源、19,137 个字段，其中 14,628 非空、4,509 空。167 个 CP949 严格解码失败和 101 个控制结构隔离保持保留，不能按正文可用计数。此表是已知格式集合，**不是全游戏无遗漏结论**。

| 扩展名 | 资源 | 全部字段 | CP949 失败 |
|---|---:|---:|---:|
| .abi | 1 | 716 | 0 |
| .att | 1 | 0 | 0 |
| .cdg | 1 | 144 | 0 |
| .cha | 1 | 301 | 0 |
| .cht | 45 | 1698 | 38 |
| .cls | 1 | 3 | 0 |
| .dod | 40 | 80 | 0 |
| .ecd | 25 | 97 | 0 |
| .fds | 2 | 52 | 0 |
| .fpb | 708 | 7998 | 127 |
| .gft | 2 | 1056 | 0 |
| .itm | 1 | 958 | 0 |
| .mdg | 1 | 90 | 0 |
| .nod | 1 | 108 | 0 |
| .odd | 2 | 60 | 0 |
| .pod | 148 | 3552 | 2 |
| .sgi | 1 | 498 | 0 |
| .tui | 16 | 1726 | 0 |
| .val | 1 | 0 | 0 |

194 个资源的旧 2,287 字段由 6,303 个完整布局字段替代，不追加重复计数。2,237 条精确 byte／offset／hash 别名保留旧 source ID 关联；33 个 region 子片段、10 个 POD 子片段及数值扫描候选只保留在 superseded／context 证据，不作为独立正文。

全部 6,334 个既有草稿逐 ID／原始 hash 经旧别名链与新集合精确关联；零 requires-source-remap。草稿内容未改写、未标记 reviewed、未导入游戏。新源字段不自动获得译文；空字段不自动生成翻译任务。

## 可重复生成

以下入口重新运行 CHA／MDG、固定 region 和 POD 的原始 SHIP 读取，不依赖前三轮临时核查结果。

```powershell
work/venv/Scripts/python.exe -X utf8 tools/consolidate_audited_fields.py --corpus work/extraction-coverage-48/final-audit/source-corpus.json --ship work/kr/SHIP.AFS --batch locales/zh-CN/opening-review-01.json --batch locales/zh-CN/menu-review-01.json --batch locales/zh-CN/interface-review-02.json --batch locales/zh-CN/character-commentary-review-01.json --batch locales/zh-CN/story-review-01.json --out work/audited-corpus
```

前置原始目录与 FDS／GFT／ODD 的集中生成沿用 assemble_source_corpus；输入源集合不可由“原文显示字符串重新编码”替代，始终核对原文件片段 hash。全部完整原文／旧视图仅保存在 ignored 输出。

## 尚未闭合

固定布局核查不证明 opaque 字段用途、运行时 codec、所有资源可达或所有标签语义。FPB pool 间隙、普通包参考 Str／脚本、ELF、celfid 其他载荷、流式 serial、Texture 图中文字和 SFD 原文仍是分别核查的证据层，没有混入主正文自动翻译。完整提取门禁继续关闭。
