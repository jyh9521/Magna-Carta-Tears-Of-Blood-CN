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

韩版ELF只读审计确认没有有效符号条目；native相关23个标识、13个有限地址构造候选和9个数据pointer词已定位。00001240路径候选邻域有两个256立即数，仅作双区段读取线索，尚未确认parser/字体查表函数。地址、输入hash和证据类型见 [native研究](docs/NATIVE_RESEARCH.md)。
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

## ELF局部调用参数（Verified static / semantics pending）

00001240候选的JALR `0x30AD88`与`0x30AE1C`，delay slot分别将a2设为256；a0为局部r20、a1为sp+0x60，间接目标形状为`load32(load32(r20)+0x14)`。相邻`0x30AD70`的a2为4，与id/双256 B资源几何一致。参数状态已由有限指令推演验证；读取语义、vtable目标和实际执行未验证。schema2报告276条窗口内调用候选，116项合成/工程测试通过。见 [native研究](docs/NATIVE_RESEARCH.md)。

## GP初始化与reader包装层候选（2026-10-09）

Verified static：`.reginfo`声明GP=0x5437F0；TUI相关gp-32200槽VA0x53BA28，文件初值指向memory-only区域且存在SW覆盖候选，不能据初值解析运行时vtable。候选0x4FE270的+0x0C值为0x1E4A10；其条件性分配路径使用Linear标识并写入表0x4FE390，该表+0x14值为0x1E59E0，邻域具有底层转发和对象+0x44累计形状。包装层解释为High-confidence deduction；实际分支、底层reader和运行时状态未验证。schema3与131项测试见 [native研究](docs/NATIVE_RESEARCH.md)。

## 字符→glyph片段（2026-10-09，Verified offline model）

VA0x20EE80的212 B版本锁定片段含双字节组合与动态范围查表。合成对象字段+0x4C/+0x74/+0x80/+0x84分别控制分支、range pointer、base pointer与条目数。原两Font各2411个双字节成员、128个ASCII、29个fallback边界以及33个PoC映射均通过；94个合成扩展编码能返回2667–2760，但真实Font数量、bitmap和metric未扩展。字节表模型为Verified offline；实际Font实例、缓存容量、宽度与换行仍待验证。见 [查表模型](docs/GLYPH_LOOKUP.md)。

## Font metric消费者（2026-10-09）

Verified static：0x272734按Font候选+0x4C选择传统page与双字节路径；非零路径使用16位glyph index从+0x68单字节数组读取。Verified offline model：原两Font各2667项metric逐项读取通过，范围0–19；模型拒绝越界不等于引擎具有检查。+0x68/+0x74/+0x80加载调用参数相容但真实对象布局仍待验证。High-confidence deduction：metric参与宽度累加。详见 [metric研究](docs/FONT_METRICS.md)。

## FontObj bitmap/cache候选（2026-10-09）

Verified static：0x333A4C查表后保留16位glyph，0x333C30邻域从Font候选+0x60取源bitmap；page邻域有65比较和动态pointer/count/capacity分配。Verified offline projection：五条标量操作对1024组输入产生0/60/120/180，原两Font完整19列投影一致。High-confidence deduction：+0x54/+0x5C为height/stride，page采用64边界；实际format selector、texture/cache容量与运行路径仍未验证。见 [bitmap研究](docs/FONT_BITMAP.md)。

## 真实Font资源追加（2026-10-09，Verified static）

两Font2667→2700 glyph，真实新增bitmap/metrics与D0A1–D0C1表；原glyph、metric、geometry及未知tail保持。原指令查表模型核对每Font2411个原双字节成员、128个ASCII和33个新增编码。未知runtime容量不作已验证上限；下一步UE2 export重定位与celfid增长副本同步，随后新增槽ISO验收。见 [扩容实验](docs/FONT_EXPANSION.md)。

## 小字集PoC运行时观察（2026-10-09）

Verified screenshot observation：短UI中的中文、句号和ASCII可读；实时开场场景的标点混排样本与长句折行可见。Reported observation：长句末尾在下一页显示，未附该页截图；不作为丢字/裁切故障记录。High-confidence deduction：截图内容与text-poc-02三个目标相容，但没有载入ISO的独立hash证据。存读档、切场景及新增槽字库运行时容量仍未验证；分页不替代场景切换，实时场景字幕不替代SFD验证。详见 [证据记录](docs/QA_TEXT_POC.md)。

## 增长Font的UE2 export接入（2026-10-09，Verified static）

原MrtsEngine.u为version118/licensee15、flags1，共7668个export。新增append-only包builder，仅改变header @24表偏移，追加两Font和新表；size/offset采用compact index，目标entry身份前缀保持。原包数据区、name/import及7666个无关export保持。2058129→2713665 B，真实包回读及干净源码复现通过；runtime/celfid/ISO尚未验证。celfid解压buffer不存在完整原engine副本，整包替换路线不适用。详见 [包级接入](docs/FONT_PACKAGE.md)。

## celfid增长片段与混合镜像失败（2026-10-09）

Verified static：celfid包含唯一engine header、export table、两Font serial与两条132 B文件路径/大小记录；六段同步及其他区间保持通过，4195112→4201631 B。完整缓存语义仍未验证。AFS集成FILE增长到22239232 B，触发上游ISO relocation；真实混合ISO/UDF回读报缺少anchor。原尾部anchor不再位于新末尾，UDF File.afs引用还指向旧区域，单补anchor不足。新增预检在ISO写入前阻止UDF size变化；242项测试不代表UDF修复或runtime扩容完成。见 [缓存证据与失败记录](docs/FONT_BUNDLE.md)。

## 韩版混合ISO/UDF同步（2026-10-09，Verified static）

保留上游ISO9660 patcher，新增单物理partition/Type1 map/标准File Entry/单short AD的防御性overlay。FILE.AFS增长重定位后同步UDF info length、recorded blocks和AD；主备partition与integrity size table增长，新anchor追加到镜像末尾而非覆盖文件，tag location/CRC16/checksum和ISO PVD同步。未知descriptor fields、时间与扩展属性保持，原源bytes/两视图extent先验证；不套用固定韩版offset到未知布局。
真实候选3232653312 B，ISO与UDF读回两AFS一致，全原区域未修改bytes通过；源ISO/ELF不改。运行时cache/显示未验收。字段、hash与测试见 [新增槽PoC](docs/QA_EXPANDED_POC.md)。

## 不依赖构建报告的PoC二次推导（2026-10-09）

Verified static：原ISO+匹配字体+显式locale独立推导Font/UE2/celfid/FPB/UI/AFS，比较候选全部archive bytes及ISO9660/UDF metadata和原区域未修改bytes；不读取DIFF_FILE或中间资源报告。一键编排复用既有阶段，干净源码复现相同ISOhash，隔离ELF单byte tamper被拒绝。UDF主备空空间管理引用已实际确认并加入门禁，非零引用不放行。
验证复用同一基础parser/writer，不能排除共同实现缺陷；284项测试不替代运行时验收。见 [构建与验证链](docs/POC_PIPELINE.md)。

## 2026-10-09 名称首字段与缓存

原00000460.cha为301×299 B记录加12 B header，在celfid完整唯一副本起点3220278。5条相同姓名首字段的容量/trailer和受控同步实验已核验；相同字节命中不等于运行时linked group，见 [名称资源实验](docs/NAME_SLOTS.md)。新增槽四图支持局部显示，完整运行时门禁仍保留。

## 2026-10-09 单slot名称接入

显式name_slot_overlays采用原资源hash及完整匹配库存门禁，仅按targets子集修改，复用slot_resource中的上游slot包装。slot0和新增Font缓存同步已接入AFS/ISO/UDF；旧三字段镜像在新工具下同hash验证通过。名称语义/运行时仍未验证，见 [候选身份](docs/QA_NAME_POC.md)。

## 姓名字段的局部运行观察（2026-10-09）

单独修改CHA slot0及缓存副本的候选在编成、道具和角色详情页均显示“测试中文”。截图中的显示为Verified observation；资源到菜单的关联为High-confidence deduction，不能区分SHIP与缓存加载优先级，不证明其他四个同名slot用途或lookup安全性。详见 [姓名QA](docs/QA_NAME_POC.md)。

## 多编码段与有界显示资源（2026-10-09）

font_resource新增append_slots/verify_slots，将字形追加拆成非零trail-byte区段，各段含独立sentinel/base。317字库存使用D0/D1/D2三组94字符和D3组35字符；两Font2984 glyph，原2667 glyph与原映射保持。多段字库的完整原映射及317个新增码离线模型通过；最大游戏缓存容量仍未验证。

display_resources按显式资源hash/窗口hash应用既有rewrite_fpb和rewrite_fixed_slot，固定字段限TUI首256 B。cached_copies必须显式为0/1并与原buffer匹配；若有完整副本则同步，不修改substring或推定linked group。AFS/ISO/SFD工具未重写。见 [有界试译QA](docs/QA_OPENING_TRIAL.md)。

## 全量目录和外部字体参数（2026-10-09）

Verified static：19类SHIP资源998文件导出15635字段/候选，FPB窗口7998、TUI两字段1726；解码失败及未知token隔离，candidate不等于display text。celfid完整镜像21资源，独立候选35048，不推断linked group。数量及覆盖缺口见 [文本目录](docs/TEXT_CATALOG.md)。

Source Han Sans SC Regular 2.005R替换新增glyph输入，NormalFont 19px/KatakanaFont 15px，原字形及字宽保持，317追加映射不变；共同baseline裁切门禁保持。五阶段/独立回读通过，运行外观待验收，见 [字体对照](docs/SOURCE_HAN_FONT.md)。

## 混入日文的局部源解码（Verified static，2026-10-09）

00005420/00005421.fpb 共 31 个 CP949 严格解码字段实际呈现日文乱码。完整 pool 切片 SHA-256 与字段 source_sha256 相同；CP932 严格解码与重新编码逐字节往返成功。此结果属于源字段解释，不是游戏解码器改造结论。原 catalog 不改写，译文通过相同 ID/hash 关联，局部编码清单见 `locales/zh-CN/source-interpretations.json`；补充校对文件见 [文本目录](docs/TEXT_CATALOG.md)。其他资源的 CP932 解释、CP949 失败字段、引擎运行编码仍逐项待核对。

## 集中提取覆盖证据

只读审计工具 audit_extraction_coverage.py 复用上游 AFS reader 与现有 extract_resource；ISO 三个 AFS 流式 hash 对照后，998 个已支持资源重提取与原 catalog 完全一致。库目录一致性不等于语义覆盖，候选、包、ELF、SFD 和图片文字仍分层审计。具体数量与门禁见 docs/EXTRACTION_COVERAGE.md。

## slot 候选字段外字节（Verified static）

3,162 个候选按主字段有效字节并集分类：2,302 完全同区间、222 完全覆盖、527 字段外、111 部分重叠。638 个未覆盖片段均位于当前上游 slot profile 的 observed-trailer；抽查 FDS／GFT／ODD 存在完整韩文句子，leading-only 导出不能代表该区间全部内容。韩版字段结构、显示用途仍待确认；不改变 writer 或启用盲写。详见 docs/EXTRACTION_COVERAGE.md。

## 韩版多字段记录（Verified static）

FDS 两文件为 8 B 头及 2052 B 记录，四个 512 B 字段；GFT 两文件分别为 822／10307 B 记录、11 个字段；ODD 正文为 560 B 记录、80／240／200 B 三字段，小变体保留 20 B 元数据。六文件集中补充导出 1168 字段，旧 689 个扫描候选全部被新字段覆盖。只读补充层不替换上游 USA parser/writer，不扩大翻译或导入；详细边界与证据见 docs/RECORD_FIELDS.md。

## 只读 source-corpus 修订层

六资源的新结构字段按完整资源hash替代活动视图，旧资源metadata/entries保留superseded层。alias要求资源、offset、length、字段SHA256完全相同；相同文字、不同位置或部分重叠不自动关联。6334既有初稿ID/hash保持；CP949解码可含日文，不能凭语义改成CP932。机器聚合见 docs/SOURCE_CORPUS.json，流程见 docs/SOURCE_CORPUS.md。

## 全容器载荷核查

Verified static：三个本地归档逐项读取18,014项；4,058项包表接受、12项分帧差异保留。LINEAR嵌入包的声明offset不是解压流实际offset；顺序表读取与serial解码分开，详见 [容器核查](docs/CONTAINER_PAYLOADS.md)。全文覆盖尚未完成。

## 全盘与音视频流库存

Verified static：62个ISO文件全部hash；MUSIC 3646项逐项读取，3645项ADX头、1项manifest。46个SFD完整输入ffprobe packet核查均exit0，46视频流／45音频流；不等于字幕／图片字覆盖完成。详见 [全盘核查](docs/DISC_PAYLOADS.md)。

## FPB pool 补集

Verified static：708项FPB逐项身份核对，707普通pool共433271 B；原字段并集之外6个前缀共802 B全部导出，未伪造seq0。8 B零FPB与三个[0,9]空ECD单独记录，详见 [补集核查](docs/FPB_POOL_GAPS.md)。

## SFD 原版画面抽样

46 个原版影片完整解码为 47 张接触表并逐表审查，8 秒抽样中 25 个影片观察到文字。新增确认韩文序章／尾声、韩文及日文制作名单；现有两地区 ASS 共 510 条是上游参照行，不等于韩文原文提取。抽样间隙、完整转写及语音内容仍待核查，全文覆盖门禁保持关闭。详情见 `docs/MOVIE_TEXT_AUDIT.md`。


### ELF 完整字节候选扫描

详见 `docs/ELF_TEXT_AUDIT.md`。192,781 条跨编码候选及地址数值命中不等于游戏文本；机器代码也能严格解码。ELF 文本语义覆盖尚未闭合，完整提取门禁保持关闭。


### 普通 UE2 包脚本全文参考

详见 `docs/SCRIPT_TEXT_AUDIT.md`。568 个普通包 TextBuffer 完整正文与 2,993 条双引号候选已定位；源码与运行时显示仍需区分。宽字符中的 CP949 打包阅读视图不替换原文，流式 serial 与编译字节码覆盖尚未闭合。


### 脚本源字面量与编译 serial 关联

详见 `docs/SCRIPT_LITERAL_LINKS.md`。5 条宽 code unit 派生标签在同 owner Function serial 命中 CP949 字节；字节存在已确认，指令边界、执行可达性与菜单可见性尚未确认。短字符串精确匹配也可能命中其他数据或后缀，不能据命中次数计算翻译量。


### LINEAR 未解释尾部与有效前缀

详见 `docs/STREAM_TAIL_AUDIT.md`。全部 4,098 项 manifest/TOC 尺寸一致；12 个尾部疑问仍未解决，有效前缀追加 57 次包表及 87 次 Texture export。部分载荷仍保持未闭合状态，不截尾或扩大可重建保证。


### celfid 候选字节上下文

详见 `docs/BUNDLE_CONTEXT_AUDIT.md`。35,048 条候选全部校验片段身份；2,595 条位于完整 SHIP 镜像，16,767 条位于流式包表，15,686 条仍处于其他载荷。分类不推断可见文本或 linked group。


### 普通 UE2 实例属性

10 个普通包 30,813 个实例属性块、634 个 tag、22 个执行栈静态核查，零属性解析疑问；568 个 Class 与 30,788 个 native 尾部尚未解析。详见 `docs/OBJECT_PROPERTY_AUDIT.md`。


### Class 默认属性

568 个 Class 中 555 个零脚本类默认属性精确闭合，1473 tag／119 Str；13 个非零脚本类默认属性仍待核查。详见 `docs/CLASS_DEFAULT_AUDIT.md`。


### 普通 Class 默认属性闭合

13 个复制脚本边界已核查，全部 568 个 Class 默认属性读取至精确 serial 末尾；1634 tag／132 Str。通用 Function 字节码与流式正文仍未闭合。详见 `docs/REPLICATION_DEFAULT_AUDIT.md`。


### 活跃源异常字节核查

活跃 CP949 失败为 165，而非旧视图 236；12 个完整 FPB pool 和 38 个 CHT 字段存在严格 CP932 往返阅读，另 8 个 FPB 窗口切断 CP949 字符。替代阅读不改 canonical 编码或导入许可。详见 [异常字节核查](docs/DECODE_QUARANTINE_AUDIT.md)。


### CHA／MDG 怪字候选闭合

实际 8 B 头与完整记录布局核对 346 记录／391 文本字段；381 候选中 375 正文、6 数值区，零未覆盖候选。6 个怪字不属于新增正文；具体 u32 用途未完成。详见 [记录核查](docs/NAME_RECORD_AUDIT.md)。


### 固定 region 正文遗漏补核查

44 个 ITM／ABI／SGI／NOD／DOD 文件的完整记录补导出 2360 字段，其中 498 非空字段缺少旧完整视图（488 无旧正文 byte overlap）。NUL 启发式会吞入前邻非零数值并漏提后续正文；新旧字段尚待统一集合合并，不重复计数或开始新增翻译。详见 [完整 region 字段](docs/REGION_RECORD_AUDIT.md)。


### POD 全区块字段核查

148 POD 的 24 槽布局共 3552 字段（333 非空），补出 2 个 CP932 日文槽和 1 个问号槽。40 B metadata 的具体用途仍未验证；首 u32=31 不套用其他格式 count。详见 [POD 核查](docs/DIALOGUE_BLOCK_AUDIT.md)。


### 统一源集合更新

已核查布局重组为 998 资源／19137 字段（14628 非空），6334 草稿全部保留精确关联；167 CP949 失败／101 控制结构隔离。旧 15121 字段为前一版集合，非全游戏无遗漏结论。详见 [统一集合](docs/AUDITED_CORPUS.md)。


### 未知控制结构完整观察

当前 101 个隔离字段全部遍历，共 225 个标记／控制字符观察；149 次尖括号内部文字与 ITM 名称精确关联。运行语义未确认，validator 保持不变，不移除标记或批量放行。详见 [控制观察](docs/CONTROL_OBSERVATION_AUDIT.md)。


### 普通 Texture 载荷核查

28 Texture／27 Palette／191 mip 全部结构闭合；28 首级图已检查，Editor Bad 含 `BAD SIZE`，NumberFont 为 glyph atlas。163 小 mip 已完成原尺寸逐图检查（见 SMALLER_MIP_AUDIT.md），流式 Texture 未覆盖；全文门禁不变。详见 [普通纹理核查](docs/TEXTURE_MIP_AUDIT.md)。


### 普通编译脚本完整结构核查

8032 个 Function／NativeFunction／State／Struct 全部 serial 闭合，1207 个字符串常量、5 个含韩文、0 解码失败；运行可见性与流式脚本未完成。详见 [编译脚本核查](docs/COMPILED_SCRIPT_AUDIT.md)。


### FPB 池余段纳入统一源引用

当前统一集合为 998 资源／19143 字段（14634 非空），6 段／802 B 非索引池余段已保留，6334 初稿关联不变。167 活跃解码失败重新核验；非索引片段不伪造 sequence ID 或导入。详见 [池余段统一集合](docs/POOL_REFERENCE_CORPUS.md)。


### 普通包全部 mip 视觉核查

163 个非首级 mip 经 7 张原尺寸 contact sheet 全部检查；普通包 191 mip 视觉覆盖闭合，未观察到新增独立短语候选。流式 Texture／SFD 仍未覆盖，全文门禁不变。详见 [小 mip 核查](docs/SMALLER_MIP_AUDIT.md)。


### 普通编译字符串上下文核查

1207 字符串的祖先表达式及调用符号已完整核对；1025 有调用祖先，474 有赋值祖先，133 显示符号候选保留只读。英文 UI 候选不能因韩版来源排除；运行可见性与动态文本流未证明。详见 [字符串上下文](docs/LITERAL_CONTEXT_AUDIT.md)。


### celfid 流式字段前缀对照

Core.u 表后连续 2229 B 与普通包的 144 个源片段逐字节对应，观察到 Children／Next 参数链及 Struct 依赖内嵌。RandRange 脚本首次差异处严格停止，根 Object 和完整流未闭合；不能按 declared_size 连续切片或删重复 opcode。详见 [流式前缀](docs/STREAM_FIELD_PREFIX.md)。


### Core Object 依赖树对照

源包 oracle 对应连续 27922 B／1715 个字段对象自身片段；27898 B 原字节相同，24 B RandRange 差异脚本保留 opaque。局部根树闭合不代表跨包或全流覆盖，默认严格模式仍在差异处停止。详见 [依赖树对照](docs/STREAM_DEPENDENCY_ORACLE.md)。

### celfid 跨包 Class header 全量对照

568 个普通 Class header 全部核查，534 个唯一精确锚点、34 个无相同 header；6 包完整表元数据一致。Core 根树后首先对应 Engine Material，而非 Actor/Pawn。锚点不等于 serial 边界或全文覆盖，门禁保持 false。详见 [Class header 对照](docs/STREAM_CLASS_HEADER_AUDIT.md)。

### celfid 编译脚本前缀全量有界对照

8032 个普通脚本定义全部重读；7983 个有 header 对应的定义、7987 个候选均符合限定重复模型，49 个 header 无匹配。4 个多位置定义与 1501 个内部路径歧义保留；1193 个既有常量位于符合模型的源定义中。后验拟合不是独立解码或 VM 等价证明，门禁仍为 false。详见 [脚本有界对照](docs/STREAM_SCRIPT_CORRESPONDENCE.md)。
