# 第一阶段研究报告（2026-10-08）

研究与设计交付后已实施单字和33字小字集实验ISO；静态验证通过，旧单字版截图确认读档UI显示“测”。小字集运行时验收待完成，详见 [小字集QA](QA_TEXT_POC.md)，不进入全文翻译。
本文早期Verified为代码/字节/静态实验；新增局部截图观察见 [QA](QA_GLYPH_POC.md)，不外推完整PCSX2验收。

## 1. 输入、上游与审计范围

- 上游作者 soyjxck：<https://github.com/soyjxck/magna-carta-tears-of-blood-undub>。
- 审计版本 `0e8de85bffbbd392fb43ef7608df097a0fb829b6`。
- 项目远端原有 HEAD `a7af4fd75574ba65f9e2db038b1270157e5b235a`，是该上游版本的祖先。
- 初始本地只有模板，无 `.git`、`lib/`、`patch.py`；本次从 origin 恢复历史和工具，保留模板备份于忽略的 `work/audit/templates/`。历史恢复阶段没有生成新提交；后续研究与PoC提交已推送origin/main。
- 上游最新 SFD 实现/字幕修订已恢复到工作区；文本与容器模块未重写。
- 已实际阅读 README、TRANSLATING、TECHNICAL、patch.py、lib 全部生产模块与 lib/translate 全部模块；`lib/experiments/` 未随上游提交，不能依赖其中旧诊断脚本。
- 研究输入仅包含韩版ISO，USA/JP ISO未纳入研究输入。原始ISO没有下载、移动、改名或改写。
- 本地输入：SCKA-20043，SYSTEM.CNF `VER = 1.00`、NTSC；ISO 3,210,412,032 B。
- ISO SHA-256：`6242476a66a96110fb6ee1a1dd668eedd70d3df6c835f0de9192451b5f4fcd45`。
- ELF `SCKA_200.43`：4,439,344 B；SHIP 45,686,784 B；LINEAR 370,548,736 B；FILE 21,716,992 B。
- `.gitignore` 实测忽略 ISO、AGENTS.md、docs/LOCALIZATION_STANDARD.md、work/、build/；增加原始 PS2 资源防误提交规则。

## 2. 上游成果复用矩阵

| 实现 | 审计结论 | 处理 |
|---|---|---|
| cri-afs + lib/afs.py | AFS 读写、filename TOC、16 B 元数据保留、manifest finalize | 直接复用；合成 AFS 实测通过 |
| lib/iso.py | 原地写入、小文件也修正目录长度；超长 relocate，LE/BE extent/size 与 PVD 更新 | 复用算法；缺isoinfo时新增pycdlib metadata fallback，实际KR ISO两处in-place静态通过 |
| lib/ship.py | KR/JP 场景图保留、USA 文本覆盖、SHIP manifest 更新 | 保留；新增韩版同源 sparse override 模式，不强行调用 USA overlay |
| lib/linear.py | 首块路径分类、Texture/StaticMesh 与命名 allowlist、LINEAR manifest | 保留；中文方案不无条件套用 USA 图形 |
| fpb.py | byte offset/length、implicit seq0、按记录重建 | 直接复用结构层，扩展 encoder/locale 与严校验 |
| slot.py | USA 布局的分段、trailer 保留、容量检查 | 扩展；不能把几何常量当作所有韩版结构已验证 |
| region.py | USA ASCII printable-run 扫描与覆盖 | 英文提取器；不是各扩展名完整 parser，韩文发现需结构锚点 |
| celfid.py | chunked zlib、marker slot、linked group cascade | 复用压缩与受控替换思路；英文 regex/分组/ASCII 同长改名需扩展 |
| audit.py | readonly 字段、结构数量、Latin-1、caps、token 缺失、状态表 | 扩展 locale、字节编码、缺字、严格 token/placeholder、pixel width |
| cutscenes.py + sfd-muxer | FFmpeg demux→libass→MPEG-1 CBR→mux，缓存/part 原子更名 | 直接复用，不另写 SFD 系统；单韩版片段已静态验证 |
| ffmpeg.py | 找到带 libass 的系统版本；自动源码构建仅实现 macOS | Windows 使用已装 FFmpeg，不照抄 README 的通用自动构建承诺 |

### CLI 实际调用链

- `translate-extract` → require USA SHIP → extract_all（19 扩展）→ 可选 celfid catalog；KR/JP 参考输入可缺省。
- `translate-validate` / `translate-status` → audit_all，以 USA 原始资源派生结构/状态；不是 locale-neutral。
- `build-iso --translations [DIR]` → USA ISO + source SHIP/LINEAR/MUSIC；文本调用三类 translated_*；celfid 可触发 FILE rebuild。
- 全部目标文本读 `en`，linked group 读 `base`；encode_en 和 audit 固定 Latin-1。
- `.fpb` 模块旧 docstring 仍讲 pool diff-remap，但生产 translated_fpb_bytes 已改成逐记录 concatenate；不能按注释重写旧算法。

## 3. 文本资源与数量：三个口径分开

上游代码支持 **19 个 SHIP 扩展**，另有独立 `celfid.lix`。
上游 README 宣称 USA 提取/未编辑回写覆盖 **995 文件**，TRANSLATING 给 celfid 约 **615 slots / 67 groups / 242 grouped / 373 leaves**。
这些是上游报告，不是本次三版 ISO 重算结果。没有 USA/JP 输入，精确三语 catalog 文件/字符串总数仍未独立复核。

本地韩版：SHIP **13,862 entries**，19 类候选 **998 文件**；FILE **53 entries**；LINEAR **4,099 entries**（4,098 `.lin` + manifest）。

| 扩展 | 韩版文件数 | 本次可确认的文本计数/状态 |
|---|---:|---|
| .fpb | 708 | 707 可解析 + 1 个 8 B stub；7,998 个窗口视图（含 implicit seq0） |
| .cht | 45 | 上游分段 1,698；非独立确认的可见字符串总数 |
| .odd | 2 | 上游分段 48；含非文本/结构风险 |
| .gft | 2 | 上游分段 1,580；含非文本/结构风险 |
| .cha | 1 | 上游分段 301；角色资料，不等于所有显示姓名 |
| .cdg | 1 | 上游分段 144；不是已确认 144 条可见描述 |
| .mdg | 1 | 上游分段 90；不是已确认 90 个怪物 |
| .ecd | 25 | 22 可按上游分段、97 段；3 个 8 B stub |
| .fds | 2 | 上游分段 54；需结构核对 |
| .pod | 148 | 韩文文本条数待结构提取，不使用 ASCII 计数冒充 |
| .tui | 16 | 同上 |
| .itm / .abi / .sgi / .nod | 各 1 | 同上 |
| .dod | 40 | 同上；名称/内部关联风险 |
| .cls / .att / .val | 各 1 | 同上 |
| celfid.lix | FILE 内 1 | 韩版 4,195,112 B 解压启动包；英文 regex 不是韩文完整提取器 |

7,998 是窗口数量，不是去重文本数/最终翻译总量；同一池的 overlapping windows 可重复覆盖。
所有 slot 家族都有尾部部分分段，且 header/table 与“文本片段”的边界不同；正常部分槽并不自动意味着损坏。
韩版分段严格 CP949 解码失败：cht 38、odd 3、gft 68；不能直接拿这些分段作为中文写入边界。
完整扩展 census、失败名和 counts 在本地 `work/research/inventory.json`；该报告不跟踪原文 catalog。

## 4. 编码证据

- Verified（实现）：上游 English 用 `latin-1`，KR reference 用 `cp949`，JP reference 用 `shift_jis`，不是自动 UTF-8。
- Verified（韩版 bytes）：707 个 `.fpb` 池中 **695** 可严格 CP949 解码，12 个失败；EUC-KR 失败 13 个。
- High-confidence deduction：主韩文资源是 CP949-compatible / KS X 1001 范围的双字节机制；字体范围包含 B0A1..C8FE（2,350 个 KS 韩文）。不能由此宣称完整 CP949/UHC 11,172 Hangul 都能显示。
- High-confidence deduction：失败池含 `82xx/83xx` 日文式字节，可能是残留日文/开发文本；按资源追踪，不全局 errors=replace 或自动转码。
- 未独立验证：JP 是否需要 CP932 扩展而不仅 Shift-JIS，USA 实際 glyph coverage，三版 ELF 多字节解码函数。
- 韩版 ELF 存在 UnicodeStringConst、UFontObj SetText/SetFont、Canvas FontObjLen/DrawFontObj、MrtsRootWindow PostSetupFonts 字符串；这是函数定位线索，不是中文解析路径证明。

## 5. 韩版字体：真实字节发现

Verified：UE2 v118，FILE/MrtsEngine.u 内 Font exports：

| 字体 | export | serial offset | size | glyph 数 | bitmap |
|---|---:|---:|---:|---:|---|
| NormalFont | 735 | 129483 (0x1F9CB) | 282852 | 2667 | 19×21，5 B/row，2bpp，280035 B |
| KatakanaFont | 736 | 412335 | 242847 | 2667 | 19×18，5 B/row，2bpp，240030 B |
| NumberFont | 739 | 656240 | 2603 | 待专项解析 | stock-style 数据；Texture0 export 7239 |

自定义字体不是“只替换 temple.utx atlas”：temple 的 38 个 export 未发现 Font；主字体自带 packed glyph bitmap。
通过低位优先每像素 2 bit、每行 5 B 解码，ASCII 与韩文字形已人工查看可读；预览保留在忽略目录。
Normal/Katakana 后跟 **2,667 B 逐字宽度候选表**、两组 **27 个 u16 范围/基址表**，尾部 `b503000001000000` 语义未定。
逐字宽表与实际 advance 的精确关系、baseline/kerning/自动 wrap 需渲染路径追踪，不能以静态数组直接认定全部 metrics。

两套字体位图+表在 celfid 解压包各精确出现一次：Normal 1,212,059，Katakana 1,494,911（均为 bundle-relative serial 起点）。
构建需同步处理独立 MrtsEngine.u 与 bundled copy，或先用运行时断点验证加载优先级；不能只改一个副本。

范围数组观察：A1A6、B0A1..C8A1、C8FF sentinel；base 256、317、411..2573、2667。
High-confidence deduction：256 单字节槽 + 61 特殊符号 + 2350 韩文槽 = 2667；公式 `base[row] + code - range[row]` 在图形和范围上吻合，但运行时公式尚未证实。
扩展字体容量、动态 atlas/cache/PS2 显存上限仍是 Unverified hypothesis。

## 6. 中文最大阻碍与三路线

最大阻碍不是 JSON 或 AFS，而是 **运行时 byte-pair→glyph 选择 + 字宽/布局 + identifier 分离 + 有限 glyph 容量**。
CP949 编码器不会自动赋予中文字形，GBK 与原韩版范围表不兼容，UTF-8 也没有已验证支持。

| 路线 | 证据/优势 | 代价/未验证 | 判定 |
|---|---|---|---|
| A USA base + 扩展 | 上游完整 USA undub overlay 管线 | 无 USA 输入；需要解码、字体和布局移植；上游 D19/20 字体单换布局失效 | 不是当前首选 |
| B KR base + 中文字库 | 原版已有两字节字体、bitmap/表已定位；仅韩版输入，场景/音频/存档标识保持原图 | 2350 韩文槽可置换容量有限；实际 decoder、文本身份混用和 wrap 待测 | **优先 PoC 路线** |
| C KR runtime + resource/catalog hybrid | 可复用上游 AFS/ISO/SFD、结构 parser 与未来三语 reference | USA/JP 数据未提供；不能直接复用 ASCII detector/USA offset assumptions | 推荐作为工程复用方式，不混换 engine/font/assets |

推荐 **B 为运行时基底，C 的工具复用方式**，先保持全部韩版 graph，只对明确文本和 glyph 做 sparse override。
不立即移植 USA FILE/ELF，不全盘改编码，不把 B 视作容量扩展已成功。

## 7. celfid linked groups 与保护机制

- 上游 `_find_slots` 使用英文大写词+null padding+FF marker regex，过滤非唯一 marker；标记跨区参考使用 find 而非完整 package 身份。
- `_detect_linked_groups` 用共享子串和纯重复聚类；Roxy/T.Roxy、Reith 重复及 item 模板被同 base 驱动。
- Verified（代码）：cascade 使用 template.format，容量 max_bytes-1；同长度 ASCII base 还触发全 bundle word-boundary 替换。
- 上游报告：只改 T.Roxy 关联会导致 boot crash；本次未在 PCSX2 复现。子串同文不等于全部硬依赖已确认。
- 中文必须将 display label 与 package/name-table/internal key 分开；不得沿用全局 ASCII rename。必要时逐条验证真正需同步的 lookup。
- celfid 与 SHIP .cha/.itm/.mdg/.sgi/.tui 等重叠，UI 纹理也可能含姓名；加载优先级未知，须分资源测试。上游技术文“姓名是纹理”与新 translating“姓名来自 celfid”不完全一致，不能直接选一个当全部 UI 事实。
- `$n` 保留换行；`$DNN` 原样保留，speaker/portrait 的具体含义仍是猜测；`<...>` 仅允许已确认 label 内文改写，其他标签保护。
- 上游 token Counter 仅报缺失为 warning，不报增加/重排；未完整检查 `%`、`{0}`、所有标签、字体覆盖和容量。region cap 边界允许写满而失去 NUL（合成测试已复现）。中文 validator 应 fail closed。

## 8. AFS / ISO / SFD 实验

- Verified：707 个可解析韩版 `.fpb` parse→build 无编辑 **全部 byte-identical**；8 B stub 不当正文。
- Verified：14 个合成测试通过，包括 AFS manifest、ISO 原地缩短+relocation、FPB 字节增长、slot trailer、cap 边界与 validator gaps。
- ISO 元数据测试注入 pycdlib 读出的 LBA；没有宣称 Windows isoinfo 依赖或完整韩版 ISO rebuild 已验收。
- SHIP/LINEAR slot 0 明确存在；上游 D37 的运行时 size-cache 结论归上游。原始 manifest 的 UE2 stub size 可大于 TOC 中 4 B stub，不把所有不一致当损坏。
- **FILE 同样有 manifest**：韩版 AFSFileIndex.idx 的 celfid.lix 值 1,239,770。上游 rebuild_afs 原样保留它。
- 重现：同一 celfid 解压数据重压缩 → 1,102,180 B；上游 FILE rebuild 的 TOC 更新为 1,102,180，而 manifest 仍 1,239,770。解压内容完全相同。
- Verified 为 metadata stale；其在 FILE 路径的实际运行时崩溃/读取后果尚未验证。后续复用 finalize/manifest helper 同步 FILE，不另写 AFS builder。
- SFD `180216` 单片复用 build_cutscene 成功，5500 kbps MPEG-1 / libass / 29.97 fps；ADX 复解包与原 demux **SHA-256 完全相同**。
- FFprobe 输入 6.384667 s、输出 6.488611 s；有 DTS/PTS 警告、ASS 缺 PlayRes；差异 **0.103944 s**。游戏 A/V sync、字幕清晰度和完整 cutscene 集合仍未验收。
- 这是韩片+上游英文 ASS 的管线测试，不是中文字幕烧录或中文 PoC。

## 9. 真正 locale 模型（设计，尚未连接生产 build）

```text
work/catalog/<input-hash>/references/     # ISO-derived originals; ignored
locales/<locale>/locale.json              # profile, base region, encoding backend
locales/<locale>/strings.json             # id + target + review status; UTF-8
locales/<locale>/glyph-map.json           # Unicode -> stable runtime code -> glyph
locales/<locale>/subtitles/               # ASS + timing/style
build/<locale>/                           # regenerated assets, verification, ISO
```

目标字段统一 `target`，locale 为 `zh-CN`，reference 单独映射 en-US/ko-KR/ja-JP（可缺省）。
ID 以 archive/member/seq 或结构字段/marker+package identity 为准，不按原文合并；存 source hash/cap/protection/link metadata。
资源结构层接受已编码 bytes；encoder 从 locale profile 选择。未编辑资源逐字节透传；不是把中文投进临时 en catalog。
先设计 `mapped-double-byte` backend：固定 Unicode→原韩文字节槽，不依赖 OS codepage；ASCII/token 保留。该模型只是方案，不是已实现编码器。
locale validator 要覆盖 token Counter 等值与必要顺序、placeholder、markup、linked members、NUL/cap、encoding、missing glyph、glyph capacity、pixel width、未知 identifier 锁定、版本/hash 与输出 bounds。

## 10. 最小中文 PoC 实施与验收计划

1. 单字符实验：在两个主字体的同一韩文槽替换“测”bitmap/width，保留编码值、glyph 数与 serial size；同步 bundle 和独立副本。原韩文对应文本原样保留用于定位显示路径。先确认 runtime lookup，不先改 ELF。
2. 从测试文本收集唯一字符，固定少量 B0A1 起始槽位映射，保留 ASCII/$n/$DNN。两套字体分别生成，不使用系统 locale。
3. `.fpb` 用已定位 `00001944.fpb` 的 seq0/seq1 等少量记录测试；长句重算 byte offsets、implicit length、sentinel，并检查 SHIP manifest。
4. UI 在 `00001240.tui` 中以结构锚点找到可见确认弹窗，不以像素 menu tab 当动态文本。固定 slot 优先 `.cht` 清晰记录，先定位 count/metadata/string/trailer，不照抄 ASCII run。
5. 角色名在 celfid 对应 FontObj/显示数据路径定位，先保留内部 key，仅改 display。必要关联以实验确认而非英文 substring 猜测；与 SHIP/纹理对照。
6. 文本至少八类：角色名、UI 短文本、普通对话、含 `$n`、中文标点、长句、固定 slot、可增长 FPB；覆盖 `测试中文，。！？“”《》123ABC`。少量中文测试不是正式译文。
7. 复用现成 AFS、chunked zlib、ISO patcher；原版只读，output 独立；修改前 hash/expected bytes、修改后重新解析。FILE manifest 同步是门禁。
8. PCSX2 原版/测试版同设置对照：记录 emulator 版本、renderer、BIOS、输入/输出 hash；冷启动，不靠旧 savestate 替代。
9. 逐项验收：正确字形无乱码；ASCII 混排/标点宽度；两套字体切换；显式 `$n` 与无空格长中文自动 wrap；边界槽无溢出；反复切场景/战斗/菜单；正常存档新建、载入与原版对照。保存截图/录像/日志、每一项 pass/fail。
10. 若 2350 槽不足，先统计完整 zh-CN 唯一字集，再决定扩容数组/映射/显存，必要时 ELF renderer patch。不得通过删正文、重用不明 key 或改系统地区来隐藏问题。

后续截图已确认读档UI单字显示；无崩溃、字宽、自动换行、跨场景映射稳定与正常存档/载入仍属后续验收，见 [QA](QA_GLYPH_POC.md)。

## 11. 证据分级与停止点

**Verified**：上游实现路径与编码常量、韩版 ISO 身份/资源 census、FPB header/window bounds 与 707 无编辑回写、字体 exports/bitmap 可读/数组长度/双副本、FILE manifest stale、14 合成 tests、单片 SFD 重建与音频同一性。

**High-confidence deduction**：KS 韩文范围映射公式、宽度数组参与 advance、B+C 比 A 更小的 PoC 修改面、12 个 CP949 失败池可能残留日文。

**Unverified hypothesis**：实际 MIPS decoder/自动 wrap/kerning/baseline、字库扩容、所有姓名及 linked 依赖、韩版 celfid 完整可见文本量、JP CP932/USA 全字体范围、FILE stale 的运行时影响、SFD 播放同步、中文运行时与存档。

当前扩展至小字集实验构建及旧单字版有限UI截图观察；不启动批量翻译，不发布正式中文补丁，不声称第一阶段全部验收完成。当前进展统一见 [STATUS](STATUS.md)。
