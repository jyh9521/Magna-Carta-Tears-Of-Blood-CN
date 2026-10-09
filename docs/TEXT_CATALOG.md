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

当前校对集合为 6121 个互不重叠的初稿字段：

| 批次 | 字段数 | 范围 |
|---|---:|---|
| opening-review-01.json | 91 | 开场、教程、既有 UI 和姓名试译迁移 |
| menu-review-01.json | 101 | 菜单和属性提示 |
| interface-review-02.json | 235 | 人物姓名、目的地、占卜、商店、道场与战斗菜单 |
| character-commentary-review-01.json | 97 | 不同剧情进度的角色自述 / 评论 |
| story-review-01.json | 5597 | 584 个 FPB 的剧情、NPC 对话与书籍初稿 |

既有 92 条 seed 中，00001240.tui record242 的源文是 `리스_스테이터스설명`，试译值为“返回标题画面”，源文与译意不对应。该条不进入正文校对集合，历史试验配置和测试 ISO 保持不变。不能因源 hash 匹配就确认译义正确。

术语表累计 263 词条，人物音译、地名、势力和载具名称均标记暂定统一，非官方译名或已校对结果。最长词条匹配区分 `리스`、`크리스 아크웨이` 和 `리스트`；未收录的复合词仍可能触发术语误报，须结合原文处理。

当前初稿合计 2031 个非 ASCII 字符，思源 cmap 检查无缺字；保留旧 317 字符库存需追加 1717 个，总计 2034 槽。该数量不表示新字库已生成或容量 / 运行验证通过。

本地校对目录 `work/proofreading-stage-25/` 导出全部 15,635 条记录，含 6121 条初稿与 9,514 条未译记录。未译数包括空字段、候选标识符和异常字节，不作为可见正文翻译率分母。998 个逐资源 HTML 页面可浏览原文 / 初稿；`review.jsonl` 保留源元数据和校对字段；`resource-metadata.jsonl` 保留完整 FPB pool、结构审计和资源 hash；celfid 候选另存，不并入正文。

原文完整导出限定于现有 catalog；UE2 图片、硬编码、未解析资源和 SFD 文本仍是明确缺口，未声称全游戏穷尽。全文初稿正在进行，尚未完成。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/extract_strings.py --iso "<original-KR-ISO-path>" --out work/catalog
work/venv/Scripts/python.exe -X utf8 tools/validate_translation_batch.py --catalog work/catalog/source-catalog.json --batch locales/zh-CN/menu-review-01.json --font "<SourceHanSansSC-Regular.otf-path>"
```

输出目录须为空；已有 catalog 不覆盖。验证通过不等于 glyph 容量、固定 slot 写回、linked group 或游戏运行通过。

源语境待核对清单见 `locales/zh-CN/review-exclusions.json`，保存 191 条稳定 ID/hash 和原因，不包含原文。清单不删除校对包中的源记录，也不代表全部异常候选已完成审计。

## 混入日文的原字节回读（Verified static）

`00005420.fpb` 的 24 个、`00005421.fpb` 的 7 个，以及 `00007658.fpb` 和 `00011094.fpb` 各 6 个，以及 `00011739.fpb` 的 13 个严格 CP949 字段显示日文乱码。按完整 pool 的 offset/source_bytes 切片核对 SHA-256，再以 CP932 严格解码并逐字节往返，得到完整日文；56 条对应译文保留原 catalog ID/hash。编码证据清单见 `locales/zh-CN/source-interpretations.json`，不包含原文。该证据只确认这些字段的字节解释，不确认韩版引擎使用 CP932，不将全部资源改为日文，也不自动放行 CP949 解码失败字段。

原 catalog 与主校对包的 source 字段未改写；补充日中校对页位于 ignored `work/translation-stage-36/source-readings.html`，附带 hash 对照的 `source-readings.jsonl`。主校对页面仍显示原 CP949 reference，不能将其乱码误当成韩文。

新增 12 个 CP932 字段为商店名称及招呼语；静态字节解释已验证，实际游戏可见性仍待确认，不据此开放写回。此前 31 字段补充校对输出保留在 `work/translation-stage-30/`。

`00011739.fpb` 新增 13 条 CP932 回读对白；同样核对源切片 hash、原 CP949 reference 与逐字节往返。累计 56 条补充校对记录，之前的 31 条及 43 条补充页保持。

CP932 补充解释当前累计 101 条；00000357、00000432、00000453 新增 45 条，严格解码及原字节往返验证通过。新增日中校对补充见 ignored `work/translation-stage-42/source-readings.jsonl` 与 `source-readings.html`。旧 56 条补充文件保持；原 CP949 catalog 不替换，残缺语句保留，不补造内容，未批准导入。
