# 韩版文本目录与翻译批次

## 2026-10-09 提取结果（Verified static）

输入 SCKA-20043 ISO SHA-256：`6242476a66a96110fb6ee1a1dd668eedd70d3df6c835f0de9192451b5f4fcd45`。
`tools/extract_strings.py` 复用上游 AFS、FPB、slot、ASCII region 和 celfid 解压实现，严格 CP949 解码，不替换异常字节、不写回原输入。

| 扩展名 | 文件 | 导出字段或候选片段 | 非空 | 解码失败 |
|---|---:|---:|---:|---:|
| .fpb | 708 | 7998 | 7996 | 127 |
| .cht | 45 | 1698 | 1696 | 38 |
| .odd | 2 | 48 | 24 | 3 |
| .gft | 2 | 1580 | 233 | 68 |
| .cha | 1 | 301 | 300 | 0 |
| .cdg | 1 | 144 | 144 | 0 |
| .mdg | 1 | 90 | 88 | 0 |
| .ecd | 25 | 97 | 97 | 0 |
| .fds | 2 | 54 | 10 | 0 |
| .tui | 16 | 1726 | 892 | 0 |
| .pod | 148 | 340 | 340 | 0 |
| .itm | 1 | 558 | 558 | 0 |
| .abi | 1 | 533 | 533 | 0 |
| .sgi | 1 | 269 | 269 | 0 |
| .nod | 1 | 95 | 95 | 0 |
| .dod | 40 | 101 | 101 | 0 |
| .cls | 1 | 3 | 3 | 0 |
| .att | 1 | 0 | 0 | 0 |
| .val | 1 | 0 | 0 | 0 |

19 类合计 998 个资源、15,635 个字段或候选片段。统计不是可见文本总数，也不是翻译完成度分母。完整机器统计见 [TEXT_CATALOG_COUNTS.json](TEXT_CATALOG_COUNTS.json)。

- FPB 包含 707 个可解析资源及一个 8 B stub；导出显式/隐式窗口，另存完整 pool，保留未覆盖前缀、间隙、重叠和坏字节。7,764 个窗口满足当前窗口后端的静态前置条件；空窗口、上下文和运行时仍另行审核。
- TUI 为 863 条记录的两个 256 B 字段；空字段也计数。第二字段、内部键、带制表符字段和非零 padding 不自动开放写回。
- slot 复用 USA 几何作为只读观察，不把 KR trailer 当作正文，也不将局部有效结果推广到全部 slot。
- 其余 region 为 NUL/CP949 韩文候选加上游 ASCII 扫描；同文、同 offset、可解码均不证明实际显示语义。
- celfid 独立扫描产生 35,048 个只读候选，含资源镜像、标识符及可能的二进制噪声，不能计为独立对白。识别出 21 个完整资源镜像，记录实际解压 offset；不是全部 linked group 的确认。
- `.att`、`.val` 无候选不代表不存在文本。UE2 图片文字、未解析包、ELF 硬编码及 SFD 字幕仍属于覆盖缺口。美版/日版 reference 保持缺席，不伪造三语对照。

## 数据层

提取输出仅位于 ignored `work/`：

- `source-catalog.json`：原文、源 hash、稳定 ID、结构和隔离原因。
- `target-template.json`：13,143 个严格解码的非空记录，target 初始空；未知语义需审核，不因模板存在而获得写回权限。
- `target-seed.json`：按源身份迁移的 92 个既有试译，不重新生成译文。
- `manifest.json`：版本、数量、原 AFS hash、覆盖缺口和镜像库存。

实际本地目录为 `work/catalog-stage-24/catalog-final/`。全量原文和模板不进入 Git；原创译文批次保存在 `locales/zh-CN/`。模板与 catalog 的 offset 是定位证据，后端仍须重新验证原资源身份，不能盲写。

## 翻译状态

既有 92 个草稿加 `menu-review-01.json` 的 101 个新菜单草稿，共 193 个互不重叠的已译字段。新批次已检查源 hash、控制符、术语和思源字体 cmap；未写入测试镜像，未完成上下文与布局验收。
合并译文有 398 个非 ASCII 字符，其中 89 个不在现有 317 字符库存。保持旧库存后追加时需要 406 个槽，而不是重排为 398 个槽。

`GLOSSARY.md` 是唯一术语基准，21 个词条目前标记“暂定统一”。后续按资源/上下文小批次翻译；未知格式与 lookup key 不进行自动翻译或全局替换。全文翻译尚未完成。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/extract_strings.py --iso "<original-KR-ISO-path>" --out work/catalog
work/venv/Scripts/python.exe -X utf8 tools/validate_translation_batch.py --catalog work/catalog/source-catalog.json --batch locales/zh-CN/menu-review-01.json --font "<SourceHanSansSC-Regular.otf-path>"
```

输出目录须为空；已有 catalog 不覆盖。验证通过不等于 glyph 容量、固定 slot 写回、linked group 或游戏运行通过。
