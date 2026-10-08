# Technical Notes — Magna Carta localization

## Research status: KR_SMALL_CHARSET_STATIC_VERIFIED

截至2026-10-08：仅韩版输入；33字小字集PoC完成静态验证，旧单字版截图确认UI显示“测”，不是完整中文补丁。研究见 [第一阶段报告](docs/PHASE1_RESEARCH.md)，新版本验收边界见 [小字集QA](docs/QA_TEXT_POC.md)。

### Evidence vocabulary
- Verified：直接代码/字节/静态实验或明确截图观察；必须说明具体证据，局部截图不意味着完整运行时验收。
- High-confidence deduction：有多项证据，仍需 runtime trace。
- Unverified hypothesis：没有直接实测支持。
- Upstream-reported：来自 soyjxck 的旧实验，不作为本次独立确认。

## Input identity (Verified)
SCKA-20043 / NTSC / SYSTEM.CNF VER 1.00。
ISO size 3210412032 B。
SHA-256 `6242476a66a96110fb6ee1a1dd668eedd70d3df6c835f0de9192451b5f4fcd45`。
SHIP 13862 entries / FILE 53 / LINEAR 4099。
原版 ISO 只读、原位；游戏字节输出均放 ignored work/build。

## Attribution and actual implementation
soyjxck upstream audit commit `0e8de85bffbbd392fb43ef7608df097a0fb829b6`。
AFS/ISO/FPB/SFD沿用上游生产实现；Git历史保留，研究和PoC提交已推送origin/main，技术里程碑标签为glyph-poc-01。
上游 manifest/voice-graph/SFD 研究属于上游贡献。
库版本与重现命令见 BUILDING.md。

## Encoding and rendering
实现层 USA latin-1，KR cp949，JP shift_jis。后两版差异仅代码/上游证据；无 USA/JP ISO。
707 可解析韩版 FPB 池中 695 严格 CP949 成功，12 失败（疑似残留日文）；不采用 errors=replace 隐藏问题。
主韩文字体含 KS X 1001 韩文范围，不能等同完整 UHC/GBK/Unicode 支持。
ELF 中 UFontObj/Canvas/UnicodeStringConst 名称为追踪线索；native 解码/宽度/换行尚未定位验证。

## Font system (Verified bytes)

字体容量/冲突离线审计确认2350个候选韩文槽，695个严格解码FPB池使用1064个槽；1286个未在该语料观察到，不能当全游戏空闲槽。当前33字map中16槽仍与目标窗口之外原文重合5140次、涉及615个FPB资源。两字体2350槽bitmap均非全零。范围、计数和证据边界见 [字体容量审计](docs/FONT_CAPACITY.md)。
FILE/MrtsEngine.u (UE2 v118) Font exports 735 NormalFont、736 KatakanaFont、739 NumberFont。
Normal: offset 129483, size 282852, 2667 glyphs, 19x21, row stride 5, bitmap 280035 B。
Katakana: offset 412335, size 242847, 2667 glyphs, 19x18, row stride 5, bitmap 240030 B。
bitmap 2bpp，LSB-first 四像素/byte；字形人工查看可读。
后跟 2667 B width 候选数组、27 u16 range keys、27 u16 base indices；尾部语义未知。
同样 serial 精确出现在 celfid bundle offset 1212059 / 1494911，必须考虑双副本加载。
NumberFont 是另一路 stock-style 数据；temple.utx 38 exports 无 Font，不能把它当主中文字库。
静态位图位置与数组长度 Verified；运行时映射公式/advance/atlas cache/kerning/baseline 均未验收。

## AFS / ISO
SHIP 和 LINEAR 的 slot 0 CRLF size manifest 必须与替换资源同步；filename TOC 和 16 B metadata 保序。
原始 SHIP UE2 stub 的 manifest size 是真实外部 package 大小，不是 4 B stub 长度，勿据此报损坏。
FILE 也有 AFSFileIndex.idx：上游 rebuild_afs 对 celfid 重压缩后保留旧 manifest；本次复现 TOC 1102180 vs manifest 1239770。
PoC复用上游rebuild_afs并定点同步FILE slot0；SHIP保留外部stub记录，不全表改成TOC size。runtime后果仍待确认。
ISO原地缩小/relocation合成测试通过；新增pycdlib只读metadata fallback，仍复用上游写入逻辑。
目前不存在ELF patch、生产中文encoding backend或完整中文翻译构建。

## Text and linked resources

TUI schema3只读审计确认两个256 B区段的全量字节布局，892非空区段CP949严格往返；段用途仍为待验证。通用fixed-slot函数的显式256 B合成测试已确认另一半/metadata保留和NUL溢出门禁，未对原版写回。旧PoC profile及ISO保留；详见 [TUI字段](docs/TUI_FIELDS.md)。

全部16个KR TUI记录几何已核对，共863项；834字段满足严格CP949和clean NUL padding，29项存在非零尾部。10个资源有一个完整celfid副本。限定FPB+TUI语料使用1084槽，当前map冲突17槽/5406次/629资源；不作为全游戏空闲或运行时证明。见 [TUI审计](docs/TUI_AUDIT.md)。

全量KR FPB离线审计：707个解析资源无编辑回写一致；701个符合当前连续partition条件，667个同时符合严格解码与控制结构前置条件。六个显式seq0资源存在合成views未覆盖的前缀，不能通过简单串接丢弃。详见 [FPB审计](docs/FPB_AUDIT.md)；仅静态证据，不改变运行时验收状态。
FPB 真正字段 `(seq, offset, length)`，header+0x0C 是 implicit seq0 length。
707 韩版 FPB 无编辑 parse/build byte-identical；8 B stub 单独跳过。
Slot constants 是 USA 分段模型；韩版仍需定位实际 record/metadata/text 边界。
Region extractor 仅 ASCII heuristic，不能直接扫描韩文作为全部可见文本。
Celfid 英文 slot detector/linked substring grouping 不是完整 UE2 identity parser；显示名和内部 key 不自动同译。
联动涉及 celfid/SHIP/LINEAR 纹理可能重叠，优先级和实际依赖须逐屏 trace。

## Recommended route (High-confidence deduction)
B：韩版 ELF/FILE/场景/音频保持完整，自定义 Unicode->韩版 byte-pair->glyph 稳定映射；先小量置换，不扩容。
C：复用上游结构 parser、压缩、AFS/ISO/SFD 和未来 references，不把目标放进 en。
A（USA runtime 扩中文）当前没有 binary comparison 输入，且修改面大，非首选。
2350 Hangul 槽的最终容量是否够用需完整字集统计；扩容是后续独立课题。

## Tests and stopping point
46 tests passed；707 FPB byte-identical roundtrips；SFD单片重建/ADX一致，但时长差0.103944 s与DTS warnings未消除。
截图确认UI单字显示；完整mapping、width/wrap、存档/切场景仍pending。详见docs/KNOWN_ISSUES.md。
只进行小字集实验，不进入全文翻译。

## Single-glyph PoC (Verified static; limited UI screenshot observation)
tools/font_poc.py使用locales/zh-CN/poc.json。B0A1/原“가”/候选glyph317置换为“测”，并非CP949直接编码中文。
两Font只改glyph317 bitmap；serial长度、其余glyph、全部metrics/range/base/tail保持原字节。
MrtsEngine.u及celfid内两font精确副本同步；压缩复用上游24576 B chunks/zlib9。
00001944.fpb seq0/seq2首个双字节字符写B0A1，530 B长度、windows、$n及其它tokens保持。
共享槽使其它原“가”也显示“测”：这是实验副作用，非正式译文；不修改resource IDs。
FILE.AFS 21716992→21579776 B；SHIP仍45686784 B；ISO仍3210412032 B。
重解析验证AFS顺序/metadata、无关entry、两font副本、manifest与FPB；全ISO对照只允许两AFS extent及FILE目录length字段变化。
ELF/LINEAR/MUSIC/SFD原字节保持。静态字形可读不等于runtime解码/advance/wrap/save通过。
实验环境PCSX2 exe版本metadata2.8.2.0；读档UI截图，四处空槽提示显示“测”。截图Vulkan/640×447（1x）；BIOS、实际载入ISO hash、冷启动流程与版本没有出现在图内。
该观察支持B0A1/index317候选映射路径（High-confidence deduction），没有证明两font加载优先级或所有双字节范围。

## Small charset PoC (Verified static; runtime unverified)
游戏profile与locale数据分离；33字符明确分配B0A1..B0C1/glyph317..349，每项对照两font的range/base。该范围全体运行时lookup尚未实测。
两font selected bitmap与advance候选byte统一19，其余字节不变；按共同参考baseline定位标点，不逐字垂直居中。
00001944.fpb seq0由20→30 B、seq2由80→118 B；seq2仍保留一个$n。隐式长度、显式offset/length与总池重建，530→578 B。
韩版00001240.tui实测125396 B=8+243*516；header第二u32为2，语义未知。243个record IDs唯一；每项u32 id+512 B字段。
record index127/id176位于65540，文本65544，原串18 B且余槽零填充；对应读档空提示的语义为高置信推断。
该完整tui在celfid解压buffer中唯一出现于3929716，不能仅替换SHIP文本；本次同步整个同长资源副本。
FILE/SHIP slot0只更新目标size、保留外部stub size；AFS条目顺序和metadata不变。ISO仅FILE/SHIP extent及FILE目录size字段改变。
当前文本层保护控制token数量/顺序/值并拒绝未知结构；已有46项自动测试。完整UI长度/自动wrap、linked names、字库扩容与存档仍待验收。
