# Pitfalls

## Detect-mode animation parameter is not a proven movement speed

The 0.5 constant at KR 00402CAC flows through 00388B80 to an animation virtual call, including a sequence name such as eclipse. Changing it is not evidence of faster movement. The field/speed research instead records ResetSpeed's real numeric speed stores and flags its selector semantics as pending runtime QA. Do not infer gameplay speed from nearby float constants or from 60 FPS changes.

stage168首次完整font构建在“empty glyph raster”停止，因为公告原文尾部全角空格保留到译文，U+3000本就没有墨迹。不要删字符或画假点：通用font builder仅允许Unicode Zs空bitmap，保持advance；字母/替换符/换行/tab/零宽与非Zs空字形仍拒绝。原失败命令/输入/stdout/stderr/exit保存在168/build-commands.json，修正后rebuild2全量验证。CDG263切片是旧leading-string边界，原生是526双字符串记录；record首u32不是Key，真实Key是+4。

新CHT16655/41的경험치 칸指经验值格，不能把其中칸机械替换为卡恩。登记最长源短语后继续使用既有最长匹配规则，旧卡恩系统术语不改变；全量validator会检测经验/经验值等不一致。

stage167初ASCII测试fixture的“20% off”实际会被TOKEN认成printf的“% o”，不是numeric-percent；因此正确被值/顺序测试拒绝。改用无printf碰撞的“20% reduction”作为字面fixture，默认严格语法不变；失败stdout/stderr/exit保存在167/initial-fixture-failure.json。相同源词不自动建立链接，POD两个槽与ITM/CDG重复仍保持独立身份；CHT旧516B零跑段继续不能当512B真实容量。

百分比、非ASCII尖括号名与箭头被通用markup/printf验证器隔离，不等于这些正文无需翻译。94条单独语言复核通过后仍保持原导入门禁；不得全局允许任意%/尖括号，不得把制表符/换行/NUL静默剥离。POD组合顺序与独立field0/19不能合并；翻译模板初稿重复“会得到…就会出现”已修正后逐条复核。

仅要求平假名会漏掉只有片假名的姓名/商店叫卖。词形筛选应接受全角片假名，同时保留严格原字节/往返/hash/native消费链门禁；半角噪声或私用字不因此升格为可翻译文本。

## Zero-run capacity can include numeric words (stage164)

CHTleading-slot scans previously yielded516 writablebytes because a post-textu32 happened to be zero. Actual native reader consumes512bytes. Do not replace the original whole-segment hash with a shorter unbound hash;keep its fingerprint andseparately protect the physical tail. New37alternatefields write512 andpreserve original20/4-byte tail as appropriate. Independently check all oldtargets against the native bound andall record numericmetadata after rebuilding.


## A default-codec rejection fixture must actually fail (stage163)

The initial fixture名前は？ also decodes strictly as CP949. That is not evidence for silent fallback: both codecs accept those bytes, with different meaning. Use a real failed primary-codec windowヤソンじゃないだろうな？ to verify the default remains strict CP949. The first verification script guessed the six added glyphs from all154readings; actual115FPB inventory is裙旱祷蜂寺豁, while沐浴 belong to still-unimportedCHT. The prefix assertion correctly rejected that guessed oracle; independently compare baseline/current inventories and fix the verifier, not the built glyph data. Production inputs require explicit source/reading hashes andsource locale, not whichever decoder happens to return Unicode.


## Alternate-codec success is not import approval (stage162)

167primary-decode failures yield164CP932 round trips, but only154 have usable lexical readings with Hiragana and no private-use characters. The remaining13 are not guessed prose or automatically retained as harmless data. Reading audit rejects changed resource/span/hash, unknown controls, invented runtime/import claims and corrupt native record bindings. The first draft Japanese カン alias was wrongly set to 坎; full-old-draft validation rejected it because the existing Korean canonical term 칸 is 卡恩. Fix the new alias and new targets, not old correct translations. The same check found 巫者/大巫者 should use existing 巫师/大巫师 rather than copying Japanese kanji. Protected$n boundaries cannot be dropped to improve typography; three initial draft count mismatches were corrected before saving the reviewed profile.


## Full-size hash fixture memory overlaps (stage161)

A small synthetic item hash fixture passed, but479 twelve-byte nodes at0xa000 overwrote the initially chosen0xb000 bucket region. This produced false missing-key/failing lookups; actual game data was unchanged. Use nonoverlapping0x9000 buckets/0xa000 nodes andverify every original key,hash collisions,duplicate replacement andmissing fallback. Do not convert a fixture memory bug into a game-format conclusion. Read exact instruction words: a guessed bne register field1690000b was rejected; source word1682000b is the verified anchor.


## FPB sequence is not a guessed native ordinal (stage157)

Using seq+1 against00000358 bound record11 while the requested source span was record10; source hash rejected the mistake. Match raw pool offset, length and SHA256 uniquely, then verify first numeric-key lookup. A zero named compiled-call count did not make GetPlayBookDataText unused: Then_2DObjectControl_Chat calls its helper directly in native code. Trace native consumers as well as VM symbols.


## Saved script source is not live bytecode (stage156)

PilotTextList and RoadSignTextList exist as ArrayProperty exports but the full original script-token inventory has no selected property reference or GetPilotTextDataIndex calls. An explicit --field request correctly fails, rather than calling zero matches verified. MrtsPilot archived ScriptText contains PilotTextList in a commented-out confirmation state. Do not promote translations from comment matches. SetDestList callback is564bytes, exceeding512 default; use a caller-selected bounded scan rather than silently searching until some unrelated return.


## SGI pending count is not a name count (stage155)

The246 historical pending entries were206 names plus40 descriptions. A Name-only assertion failed on field1. Bind source field_index and description HelpText independently; no blanket name-only proof. The first field selector CurStyleData was absent from annotated tokens and correctly failed; actual StyleData references are used. A StyleData.Name string comparison must not be ignored: trace AddList a_Name to Caption, and preserve all original/translated equality classes before promotion.


## Static amount promotion and stale quarantine count (stage154)

The historical test asserted that all seven TUI templates remained pending. After four amount chains were statically bound, that fixed count failed (3 versus7). Preserve the old negative fixture; update the regression to require the exact remaining tilde/travel IDs and verify all four promoted source hashes/targets/static bindings. Do not remove the quarantine guard or permit arbitrary fields. Retry the whole transaction in fresh isolated directories.


## Reusing an older registry silently drops intervening batches (stage153)

Copying a stage152 rebuild script still referencing151 omitted the suffix batch when adding Common fragments. Font count alone did not detect it because no new glyphs were needed. Scope showed8 missing instead of0. Use immediate previous complete command registry, require exact reviewed/selected counts, and rebuild in a fresh directory; initial output is not authoritative.


## Getter-only searches miss direct array text (stage151)

No literal getter call is not evidence that a TUI fragment is unused. Direct FieldMenuTextList/CommonTextList array accesses recovered nine missing consumers after getter-only analysis. Conversely, a direct array literal is a physical ordinal, whereas a getter integer is a stored key. Use actual expression parent/child boundaries, never the nearest integer. Do not translate Korean particles alone: Name+stat+number+trailingverb becomes unnatural Chinese unless coordinated predicate placement is reviewed.


## Getter integer is not a physical line number (stage149)

A preceding caller scan listed integers against physical TUI ordinals; GetNationName(238) then appeared to fetch the damage-record label. Original native lookup disproves this association: integer238 matches record key238, whereas damage record key300 is physical ordinal238. Never select a field using a nearby number or array ordinal without source-key binding.144 reparsed literal FieldTextData calls differ from physical ordinals. New audit preserves original catalog IDs and exposes the actual key/source pair; dynamic integers require further expression analysis.


## Configuration templates are not dialogue grammar (stage147)

The first attempted configuration import stopped at %k/%w: the generic dialogue placeholder checker intentionally rejects those Engine template macros; interface angle delimiters also have different meanings. Do not globally loosen dialogue grammar to make config pass. Add consumer-specific exact-token validation and use the checked character-encoding primitive afterward. The partial config-copies directory is not authoritative; config-copies2 is the verified receipt. Unknown macro changes, hotkey changes and raw line delimiters fail tests.


## 上游历史（upstream-reported，非本次运行时复现）
来源 soyjxck TECHNICAL D9-D40，审计版本见 PHASE1_RESEARCH.md。
- D19/20：只移植字体到USA MrtsEngine，部分字形改善而布局损坏；font/metrics/decoder要配套。
- D26/27：USA engine/script与source voice graph混用，cutscene trigger失败；保留fld/lpt/btv/MUSIC关联。
- D30-36：FPB大于source时读取/解析失败；trailer替换未解决。D37重建slot0 size manifest解决，勿丢对白强行截短。
- D38-40：tui改成English而menu仍原文；像素文字在LINEAR Texture/StaticMesh/title Map，不是普通string。
- linked T.Roxy/name不一致上游报告boot crash；English substring群不能当全部运行时依赖。

## FPB旧说明错误（Verified）
TECHNICAL说seq,length,offset与+0x0C padding；production code和707韩版字节确认seq,offset,length与implicit seq0 length。
fpb.py旧docstring的diff-remap不是当前production rebuild；读实现而非复刻旧说明。
Regression：707个parse/build字节一致；growth synthetic验证implicit length与byte offsets。

## 韩版不是USA ASCII catalog（Verified）
region detector只扫描ASCII>=4；KR text计数不采用该结果。
slot分段不等于完整physical records；部分末槽正常，但CP949分段失败和metadata风险需定位。
研究脚本最初遇到8 B FPB/ECD stub并停止；已记录这些输入，inventory明示失败名而不吞异常冒充正文。

## 不全局转换CP949（Verified / High-confidence）
707 FPB池中12严格CP949失败，含日文式bytes（残留日文仅推断）。按resource查证，不以replacement chars掩盖。
glyph表仅有2350 KS韩文字母+符号/单字节槽，不代表全部CP949/UHC或中文。

## FILE manifest stale（Verified bytes; runtime consequence unknown）
上游rebuild_afs docstring称FILE无slot0 manifest，但韩版FILE有AFSFileIndex.idx。
原celfid1239770 B → 同解压数据重压缩1102180 B，TOC更新，manifest仍1239770。
在实验副本复现；未改原版。后续复用manifest/finalize helper同步，PCSX2验证其读取后果。
不能把SHIP stubs的外部package size和4 B TOC差异一律当stale。

## Validator并非严格token/terminator门禁（Verified synthetic）
Counter只检查$n/$DNN减少（warning）；增加/乱序/%/markup/glyph未完整检查。
region cap允许写满无NUL。中文profile要保留终止符且按bytes拒绝越界，语法风险升级error。

## Windows stdout/ASS/FFmpeg（Verified）

干净源码测试fixture首次缺少work目录，四个测试的TemporaryDirectory(dir=ROOT/work)报FileNotFoundError。按构建流程建立work后，基线46项与新增版57项均通过；该失败属于fixture目录准备，不是游戏资源或审计算法失败。
宿主默认CP932：打印韩文会UnicodeEncodeError，上游ASS.read_text遇UTF-8 BOM会UnicodeDecodeError。
复现命令使用python -X utf8（stdout按需要设置PYTHONIOENCODING=utf-8），不改变系统locale。
上游ass filter直接插入Path，Windows绝对drive colon/反斜线需要escaping；本次仅wrapper切到ignored output cwd并传relative sample.ass。
FFmpeg自动源码构建仅macOS；Windows采用已有带libass版本。
单片重建有DTS/PTS warning、ASS缺PlayRes、约104ms duration差；exit0并非A/V sync或游戏播放验收。

## 字体定位与双副本（Verified）

ELF有.symtab section不等于保留函数符号，该版长度为0。合并RWX load段含数据；pointer词、指令形状及No font诊断引用不等于已确认函数边界。初始合成测试将0xFFFFFFFF误当未知操作，但其opcode0x3F匹配已支持的SD类；未知操作测试改用0xE8000000。详见 [native研究](NATIVE_RESEARCH.md)。

未在695个严格CP949 FPB中出现的1286个韩文槽不等于全游戏空闲；两Font这些槽仍有bitmap，其他资源及12个失败池未纳入。当前33字稳定map仍有16槽与原文发生大量字节重合；稳定映射不能消除共享槽副作用。不得依据单一语料统计自动换槽或扩容。见 [字体容量审计](FONT_CAPACITY.md)。
主Custom Fonts位于MrtsEngine.u且复制进celfid，不是temple.utx Font export。
错误bitmap方向/packing初次预览倾斜/旋转；row stride5、2bpp LSB-first解码已得到正向ASCII/韩文。
仍未验证baseline、advance计算、runtime cache；不要从可读PNG推断可玩中文。

## 本地Git历史缺失（Verified）
最初工作区没有.git和上游code，不是完整checkout。恢复origin历史并保留templates，不创建无来源的新initial commit。
只忽略文件不保证已跟踪文件退出索引；check-ignore与git ls-files均检查。AGENTS和LOCALIZATION_STANDARD不提交。

## 同名UE2 export不等于同一类别（实际失败后修复）
除Font类NormalFont外还有同名14 B export。初次PoC仅按name匹配，baseline触发font replicas differ/exit1，未构建ISO。
修复为class==Font且name匹配，再验证serial hash；保留初次失败日志于build/poc。
单槽“가”→“测”影响所有B0A1，不能作为正式中文编码；需游戏验收后建立稳定locale mapping。
保持原width byte仅证明字段一致，不证明中文advance/wrap。SimHei hash锁定，发布级开放字体仍待选择。

## UI资源副本与小字集实验

29个TUI非零尾部全部始于载荷+256且独立CP949/NUL通过，后续双区段审计已消除“任意残留”假设；两段用途仍未知。按首NUL后第一个非零位置计算整记录可写容量，会把第二段空位或间隙当容量；未来显式采用256 B段范围并保留另一半。旧PoC的512 B span仅限定id176空次段，不作为生产定义。见 [TUI字段](TUI_FIELDS.md)。

全部16个TUI几何一致仍不等于所有512 B字段都是单一纯文本槽：29个字段在首NUL后有非零数据，当前只读审计排除这些字段，不能清零尾部。10个资源存在完整celfid副本，副本不应重复累计使用次数。见 [TUI审计](TUI_AUDIT.md)。

全量FPB审计发现显式seq0和header implicit前缀同时存在的六个资源。不能把synthesize_implicit_seq0返回的views当作所有文件的完整pool partition，不能丢弃未覆盖前缀。另有20个pool含当前未识别百分号，2个pool含NUL；普通对话规则不能无条件套用。详见 [FPB审计](FPB_AUDIT.md)。
00001240.tui完整资源同时位于SHIP和celfid，显示字段只改SHIP可能仍显示旧文本；加载优先级未证明，实验同步两份。
原.tui 512 B字段布局不等于上游ASCII heuristic容量，必须按header/count/record id/source slot hash定位并保留NUL。
逐字按自身bbox垂直居中会改变标点位置；小字集按共同参考baseline渲染，仍需游戏验收。
小字集虽有稳定map，仍占用原韩文字形槽；保留的韩文会受影响，不能当完整生产编码。
控制符测试最初将%unknown误判为未知结构，但其前缀%u是合法printf token；未知符测试改用%q，保留合法token规则。初始测试日志在ignored build/text-poc-02。
初始UI全标点候选串估算297/306宽，超过实验静态预算192，未进行游戏验收；UI改用短串估算164/173，完整标点留在FPB。这个差值来自候选metrics，不是实测UI像素宽度，也不作为已复现裁切证据。

## 有限调用数据流与delay slot

JALR参数可能在紧随的delay slot才赋值；只扫描直接JAL会遗漏00001240两处a2=256的间接调用。不能将前一次调用的delay定义跨调用保留，也不能把未解析的vtable表达式当已定位reader。schema2从此前transfer之后、排除其delay的位置重新建立未知状态；未知指令停止回看，未知delay不输出参数。共享形状不证明跨窗口对象身份相同。

## GP槽初值不等于运行时对象

韩版TUI相关gp-32200槽的原文件word指向memory-only区域，初始化邻域又存在SW覆盖；盲目从文件初值追踪vtable会选错对象或读到非文件区域。GP-29528写入还位于调用delay slot，源值在调用返回前已构造，不能按返回值解释。Linear候选路径带条件分支且有对象+4后端转发，不能把一张表的+0x14当成所有TUI的唯一reader。

## 返回glyph index不等于成功扩容

原查表片段在合成29条表下能返回2667–2760，真实Font仍只有2667个glyph。只有返回值正确而没有同步bitmap/metrics/page/cache会产生未验证的越界风险；不能把metadata-only模型称为可玩扩容。双字节拼合也不等于完整CP949/GBK/UTF-8解码，+0x4C为零时高字节还返回LB低32位结果。详见 [查表模型](GLYPH_LOOKUP.md)。

## Git archive与Windows工作区换行

查表模型的首次事务验证中，测试和JSON复现通过，但既有native工具的原始字节比较失败：工作区CRLF与Git archive的LF不同。未修改该工具；改用带路径过滤的Git blob身份核对，同时保留工作区原始hash与失败日志。不将换行归一化差异误判为代码回归，也不放宽ISO/ELF/font二进制hash门禁。

## 局部掩码与无边界metric读取

0x271584路径存在0xFF掩码，但0x2727BC双字节分支使用0xFFFF；不能按单处掩码判定所有中文glyph截断或直接patch。合成扩range/base后返回新index而metrics未扩会访问原数组之外；模型的拒绝是审计工具边界，不是游戏fallback。加载helper带版本/状态分支，不能把文件字段顺序直接当native对象布局。见 [metric研究](FONT_METRICS.md)。

## Bitmap投影不等于缓存纹理

原2bpp源的完整19列投影不包含实际metric/spacing裁剪、page定位、allocator、SB写入和GS上传；不能将投影hash视为PCSX2纹理验收。局部65比较不代表字库只支持64字符，也不证明总page数量无上限。format selector仍有替代分支，源几何不能替代运行时分派证据。见 [bitmap研究](FONT_BITMAP.md)。

## 新增字库不能复用等长Font替换

Font扩容同时增长bitmap、metrics与range/base，既有engine/bundle等长slice路径不支持该长度变化；直接赋值会移动后续bytes却不修复export metadata。首次D0实验被旧MappedEncoder按预期拒绝；新增显式Font表校验而非删除旧几何门禁。见 [扩容实验](FONT_EXPANSION.md)。

## celfid不能按完整MrtsEngine包替换

原celfid解压buffer中没有完整MrtsEngine.u副本；仅匹配到Font serial不证明周边资源记录可增长。新增包export offset/size修复不会自动同步bundle索引。必须验证bundle边界与长度metadata后再接入，禁止直接增长serial slice或盲目替换整包。追加新export表避免原compact字段长度变化移动原包，但保留旧资源会增加包大小；实际loader兼容性另行验收。见 [包级接入](FONT_PACKAGE.md)。

## ISO9660 relocation不能直接用于当前混合UDF镜像

增长FILE.AFS触发1 in-place/1 relocation，ISO9660目录/PVD已更新，但pycdlib回读报`Expected at least 2 UDF Anchors`。旧末尾anchor位置随镜像增长失效，UDF File.afs也仍引用原slot；仅补一个anchor或绕过UDF parser不会修复双视图不一致。失败ISO标记REJECTED并保持ignored，新增预检阻止重复生成同类输出。合成ISO9660 relocation成功不代表韩版混合镜像成功。见 [实际失败及下一步](FONT_BUNDLE.md)。

## 混合UDF修复不只移动anchor

已复现的增长镜像错误通过同步标准File Entry/short AD、主备partition length、integrity size table、新尾anchor和PVD解决静态回读；未知descriptor bytes必须保留并重新计算原范围CRC/checksum。新anchor需要额外sector，不能写入新增AFS最后一sector。仅放宽旧预检或忽略UDF parser会留下错误文件视图。254项测试与真实双视图回读不替代PCSX2缓存/字库验收。见 [新候选验证](QA_EXPANDED_POC.md)。

## 构建报告和同源验证的证据边界

仅按DIFF_FILE中的hash核对输出可能漏掉错误报告或中间资源传递；新增验证从原ISO/字体/locale重新推导，不读取构建报告，隔离ELF byte tamper已检测。二次推导仍复用同一parser/writer，不能代替独立格式审计或PCSX2运行测试。输出目录重复使用会混合历史产物，新编排/验证要求空子目录，不删除旧候选。见 [构建链](POC_PIPELINE.md)。
UDF partition含非零空间bitmap/table/integrity-table时，单改长度不足；当前overlay检查主备五组引用全部为空，未知布局拒绝。

## 有效记录不等同游戏验收

记录校验退出0包括pending；recorded-complete只表示全部人工pass。证据hash证明文件绑定，不证明截图来自候选ISO或画面符合预期。不能从文件存在、hash匹配或单幅截图推导存读档/场景/战斗通过，详见 [验收记录边界](POC_QA_RECORDS.md)。

## 姓名重复不等于全局改名授权

原celfid17处、SHIP437处姓名字节命中包括其它语义；只允许显式字段试验，不用substring/global rename推导关联。新D0文本若配原字库会产生不匹配，因此名称实验不输出原Font缓存包或ISO，须与新增字库候选协调接入。见 [名称资源](NAME_SLOTS.md)。

## 扩容后不能搬用原缓存绝对位置

单姓名资源在原bundle起点3220278，新Font扩容后为3226797。名称overlay在版本/hash门禁后匹配完整唯一资源，不把旧offset盲写进新bundle；每次报告实际offset。只改slot0也可能触及lookup语义，运行时试验前不扩展其它字段，见 [单姓名候选](QA_NAME_POC.md)。

## 构建目录不等于可删除副本（2026-10-09）

name-iso-21在名称测试尚未完成时被列为可删除事务；其镜像与保留候选同hash，但未完成测试状态应在清理建议前明确核对。目录名称、可重建性和实验用途不构成删除依据。当前保留清单与只读盘点见 [存储规则](BUILD_STORAGE.md)。

## 有界试译字库超过单段（2026-10-09）

317字符不能从D0A1连续递增而越过trail-byte=00。新builder按非零区段追加并保留sentinel。第一次试译pipeline在package阶段仍调用单段verify_append，报expanded mapping changed，未生成ISO；改为多段verify_slots后五阶段独立验证通过，失败receipt/log保留。不能为了继续构建删去原映射校验。

原文TUI中的菜单标题可能不是实际像素标签来源；编辑同文TUI不保证LINEAR纹理标题变为中文。开场9句不等于后续所有剧情；00004060教程出现时机未确认。新试译只作为可玩回归辅助，不声称全UI或存档流程已验证。

## 思源字体共同baseline与目录误计（2026-10-09）

思源SC Regular用旧Katakana 16px栅格时，“意”越界并被构建拒绝；不能直接换路径后取消裁切检查。显式15px通过现有317逐字检查，原字号路径缺省不改；字宽与运行外观另验。

全量扫描的15635字段包含空字段、异常window和候选，celfid35048候选含重复缓存和二进制噪声；不能以这些数字声称全部游戏文字已确认或计算翻译百分比。USA slot几何不能直接认定为韩版全部字段格式。


## 术语短名子串与试译 seed（Verified，2026-10-09）

直接 substring 检查把人物名 `리스` 同时匹配进 `크리스 아크웨이`、`리스트`，造成错误的莉丝术语要求。校验改为已登记词条的最长非重叠匹配，并增加长名 / 列表 / 单独短名回归。该方法不是韩语形态分析，未登记的复合词仍可能误报。

既有 seed 的 source hash 正确不代表译义正确。00001240.tui record242 源字段为 `리스_스테이터스설명`，试译值为“返回标题画面”。正式校对集合排除此条，历史 PoC 不重写。未知 `_설명` 类字段不直接作为可见简介译入。

初稿的 $n 数量检查曾阻止角色评论 record8 / 33 / 43 的行分隔遗漏或新增；修订译文保持原数量，不关闭控制符验证。原文中的排版标记仍需要后续上下文排版校对。

## 严格解码并不确认源语言

部分日文字节以 CP949 严格解码也能通过，却产生形似韩文的乱码。00005420/00005421.fpb 的 31 个窗口已用 pool 原字节/hash 和 CP932 完全往返确认日文读法。不能按 ko-KR 标签翻译乱码，也不能把所有 CP949 候选强行改用 CP932。日文字段词内的字面问号是另一种源缺损，不能借此回读结论擅自补字。

## 导出范围与全游戏覆盖混淆

998 个已知资源和 15,635 条结构记录是解析器输出，不是可见文字的穷尽证明。候选分类与混合编码回读和翻译交错进行，会使统一源集合与术语基准迟迟无法冻结。集中提取覆盖审计及缺口清单先于扩大翻译批次；同区间／可解码不证明显示语义。

## 候选区间与 trailer 误排除

非同 offset／length 不等于新增文本：860 个非同区间候选中 222 个已经完全被主字段覆盖。反过来，split_slot 的 observed-trailer 不等于内部数据：韩版 FDS／GFT／ODD 中抽查发现完整句子。仅检查首字段会漏掉候选正文，按整个槽容量计算覆盖会掩盖缺口；按主字段有效字节并集分类并保留完整候选。片段切界可拆开双字节字符，不能凭片段解码失败丢弃原文。

## USA slot geometry 不能直接作为韩版正文视图

韩版 FDS 记录每组四个512 B字段前插入u32 ID，GFT两文件字段容量不同，ODD正文包含三个区段与数字元数据。旧stride扫描能找到部分句子却把ID混入或从句中截断；这些“trailer文字”并不全是附加字段，也可能源自边界错位。新只读记录解析通过全长、分区和padding核对，保留原catalog及译文身份；新字段与旧字段按区间关联，不直接追加为未去重的对白总数。

## 流式包误当普通包

将LINEAR中UE2 magic起点之后的字节直接交给普通包offset parser，会产生2,894项异常；其中2,882项源于表布局差异，另外12项在压缩分帧阶段失败。读取顺序重定位表后包表异常归零，但serial定位尚未实现。不能靠减264或忽略越界使普通parser看似通过，也不能把未识别签名的载荷判作无文字。

## 显式seq0不保证pool开头已索引

上游隐式seq0合成遇任何显式seq0即返回；韩版6个文件的seq0处于后部，前缀仍含书籍／信件／对白文本。应按有效字段区间并集求pool补集，不能凭存在seq0宣称所有字节已逐字段导出，也不能把缺口盲写为另一个seq0。

## ASS 文件存在不等于原版画面文字全覆盖

46 个原版影片完整解码为 47 张接触表并逐表审查，8 秒抽样中 25 个影片观察到文字。新增确认韩文序章／尾声、韩文及日文制作名单；现有两地区 ASS 共 510 条是上游参照行，不等于韩文原文提取。抽样间隙、完整转写及语音内容仍待核查，全文覆盖门禁保持关闭。详情见 `docs/MOVIE_TEXT_AUDIT.md`。


### ELF 完整字节候选扫描

详见 `docs/ELF_TEXT_AUDIT.md`。192,781 条跨编码候选及地址数值命中不等于游戏文本；机器代码也能严格解码。ELF 文本语义覆盖尚未闭合，完整提取门禁保持关闭。


### 普通 UE2 包脚本全文参考

详见 `docs/SCRIPT_TEXT_AUDIT.md`。568 个普通包 TextBuffer 完整正文与 2,993 条双引号候选已定位；源码与运行时显示仍需区分。宽字符中的 CP949 打包阅读视图不替换原文，流式 serial 与编译字节码覆盖尚未闭合。


### 脚本源字面量与编译 serial 关联

详见 `docs/SCRIPT_LITERAL_LINKS.md`。5 条宽 code unit 派生标签在同 owner Function serial 命中 CP949 字节；字节存在已确认，指令边界、执行可达性与菜单可见性尚未确认。短字符串精确匹配也可能命中其他数据或后缀，不能据命中次数计算翻译量。


### LINEAR 未解释尾部与有效前缀

详见 `docs/STREAM_TAIL_AUDIT.md`。全部 4,098 项 manifest/TOC 尺寸一致；12 个尾部疑问仍未解决，有效前缀追加 57 次包表及 87 次 Texture export。部分载荷仍保持未闭合状态，不截尾或扩大可重建保证。


### 执行栈与空属性误判

采用 u16 LatentAction 会错位读取韩版 Entry.unr；应按已核对 u32 布局。Class 和 native 尾部不能因首个 None 自动判定无文本。详见 `docs/OBJECT_PROPERTY_AUDIT.md`。


### 虚拟脚本长度不能直接跳过

Class 的额外 u32 漏读会令 metadata 错位；非零 ScriptSize 不保证磁盘字节数相等。13 个疑问类保持未解析，不能以猜测跳过编译脚本。详见 `docs/CLASS_DEFAULT_AUDIT.md`。


### native 阈值错读

把 0x72／0x77 作为双字节 native 会吞掉首参数并破坏边界；本轮直接参数读取与虚拟长度／后续 Class 默认属性闭合同时校验。详见 `docs/REPLICATION_DEFAULT_AUDIT.md`。


### 活跃源异常字节核查

旧前导字段视图被完整记录替代后不能重复计入活跃失败；局部 CP932 可解码不能证明整池 CP932。完整 pool 解码通过也不能掩盖窗口切断双字节。详见 [异常字节核查](DECODE_QUARANTINE_AUDIT.md)。


### CHA／MDG 怪字候选闭合

实际 8 B 头与完整记录布局核对 346 记录／391 文本字段；381 候选中 375 正文、6 数值区，零未覆盖候选。6 个怪字不属于新增正文；具体 u32 用途未完成。详见 [记录核查](NAME_RECORD_AUDIT.md)。


### 固定 region 正文遗漏补核查

44 个 ITM／ABI／SGI／NOD／DOD 文件的完整记录补导出 2360 字段，其中 498 非空字段缺少旧完整视图（488 无旧正文 byte overlap）。NUL 启发式会吞入前邻非零数值并漏提后续正文；新旧字段尚待统一集合合并，不重复计数或开始新增翻译。详见 [完整 region 字段](REGION_RECORD_AUDIT.md)。


### POD 全区块字段核查

148 POD 的 24 槽布局共 3552 字段（333 非空），补出 2 个 CP932 日文槽和 1 个问号槽。40 B metadata 的具体用途仍未验证；首 u32=31 不套用其他格式 count。详见 [POD 核查](DIALOGUE_BLOCK_AUDIT.md)。


### 未知控制结构完整观察

当前 101 个隔离字段全部遍历，共 225 个标记／控制字符观察；149 次尖括号内部文字与 ITM 名称精确关联。运行语义未确认，validator 保持不变，不移除标记或批量放行。详见 [控制观察](CONTROL_OBSERVATION_AUDIT.md)。


### Texture 图名与属性不足以排除图片文字

Editor Bad 的首级包含烧录 `BAD SIZE`；Texture0 是 NumberFont 字形表。普通 mip 的 lazy end 是原包绝对位置，流式包不能盲目沿用该坐标。首级视觉检查与全部 mip 结构闭合是不同证据。详见 TEXTURE_MIP_AUDIT.md。


### Function native 字段不能照搬 UE1

实测 Function 为 u8 precedence＋u32 flags，NativeFunction 再附加 u16 native index。统一先读 u16 native 会错读标志。121 个 operator FriendlyName 与 export name 不同；virtual script size 也不等于磁盘长度。详见 COMPILED_SCRIPT_AUDIT.md。


### 直接父 token 不能代替最终调用上下文

434 个字符串直接位于 Concat_StrStr 内，更外层可能为日志或显示接口。韩版包中的英文 UI 常量也应保留；SetText 等名称只能支持候选判定，不能证明运行可见性。详见 LITERAL_CONTEXT_AUDIT.md。


### celfid 流式字段前缀对照

Core.u 表后连续 2229 B 与普通包的 144 个源片段逐字节对应，观察到 Children／Next 参数链及 Struct 依赖内嵌。RandRange 脚本首次差异处严格停止，根 Object 和完整流未闭合；不能按 declared_size 连续切片或删重复 opcode。详见 [流式前缀](STREAM_FIELD_PREFIX.md)。


### Core Object 依赖树对照

源包 oracle 对应连续 27922 B／1715 个字段对象自身片段；27898 B 原字节相同，24 B RandRange 差异脚本保留 opaque。局部根树闭合不代表跨包或全流覆盖，默认严格模式仍在差异处停止。详见 [依赖树对照](STREAM_DEPENDENCY_ORACLE.md)。

### celfid 跨包 Class header 全量对照

568 个普通 Class header 全部核查，534 个唯一精确锚点、34 个无相同 header；6 包完整表元数据一致。Core 根树后首先对应 Engine Material，而非 Actor/Pawn。锚点不等于 serial 边界或全文覆盖，门禁保持 false。详见 [Class header 对照](STREAM_CLASS_HEADER_AUDIT.md)。

### celfid 编译脚本前缀全量有界对照

8032 个普通脚本定义全部重读；7983 个有 header 对应的定义、7987 个候选均符合限定重复模型，49 个 header 无匹配。4 个多位置定义与 1501 个内部路径歧义保留；1193 个既有常量位于符合模型的源定义中。后验拟合不是独立解码或 VM 等价证明，门禁仍为 false。详见 [脚本有界对照](STREAM_SCRIPT_CORRESPONDENCE.md)。


### celfid 跨包依赖连续对照

源包 oracle 在 Core 根树后连续对应 224167 B／5248 个新增对象片段集合；INI 与 SmallFont 精确匹配，两个 Texture 完成限定 mip 顺序投影。负引用按完整外层身份解析，487115 的多义 Palette 候选未放行。后验对照不等于独立流解析或全文覆盖，门禁保持 false。详见 [跨包连续对照](STREAM_CROSS_PACKAGE_ORACLE.md)。


### celfid 原生字节等价候选扩展

显式模式保留全部同字节身份，连续诊断 2938500 B／532 次 Class 根请求；7 个身份歧义和 2 个 parsed-table-only 区段未伪装为完整资源映射。下一处原生数据在 3201448 停止，全文门禁仍为 false。详见 [原生字节等价对照](STREAM_NATIVE_EQUIVALENCE.md)。


### 普通包本地 Class 纹理覆盖修正

旧纹理计数只覆盖 import-class 子集。本地正 Class 引用补核后，总计 37 Texture／35 Palette／212 mip；新增 9 个 Engine 纹理的 21 个 mip 全部检查，其中 3 个 Latin／符号图集、无新增整句候选。全文门禁保持 false。详见 [本地 Class 纹理审计](LOCAL_CLASS_TEXTURE_AUDIT.md)。


### celfid 全候选字节上下文复核

35048 个启发式候选全部复核字节身份，38499 个区段索引提供只读上下文；1233 个仍为未闭合字节上下文。候选命中不等于可见正文，所有语义判定继续 pending，全文门禁保持 false。详见 [全候选上下文核查](STREAM_CANDIDATE_CONTEXTS.md)。


### FILE 配置及国际化值补充核查

全部 29 个 .ini／.int 导出 1008 个值（918 非空、90 空），ASCII 严格读取且全部行字节闭合；Core.int 原正文位于 celfid 末尾。配置标识与可见提示尚待区分，补充清单不等于 1008 个可翻译正文，主 corpus 暂保持不变。详见 [配置条目审计](CONFIG_ENTRY_AUDIT.md)。


### celfid wrapper 与配置镜像上下文补核

9 包及 3 配置正文的双 132 B wrapper 全部逐字节核查，首部 2 文件记录与源文件大小对应。35048 候选中的未知字节上下文降至 972，仍不是可见语义闭合；原包声明 size 不可直接作为流式 serial 长度。详见 [wrapper 补核](STREAM_WRAPPER_CONTEXTS.md)。


### 配置值统一源快照补全

29 个配置资源／1008 个值并入只读快照后，结构化统计为 1027 个资源／20151 个字段（15552 非空、4599 空）；原资源、候选及 6334 条译稿链接不变。新增字段保持 und／pending／不可导入；该数量不是全文最终可翻译数量，全文门禁仍为 false。详见 [配置值快照](CONFIG_CORPUS_CONSOLIDATION.md)。


### celfid 尾部资源链补核

37 个单 132 B wrapper 与 SHIP 正文连续闭合 966382 B；780 个候选补充明确字节上下文，未闭合数降至 192。单记录资源 wrapper 与双记录包 wrapper 必须区分；字节镜像不代表可见正文或可编辑许可。详见 [资源链核查](STREAM_RESOURCE_CHAIN.md)。


### celfid 原生尾部纹理补核

新增一个有界 P8 纹理／Palette 与 4 mip 全部检查；8×64 等细长 mip 先读 dimensions，再读 pixel count，不能沿用此前宽高同时不超过 8 的观察作为全局规则。图像未发现完整正文，StaticMesh 与全文门禁仍未闭合。详见 [尾部纹理核查](STREAM_TEXTURE_TAIL.md)。


### SFD 全帧解码补核

46 个影片全量解码 72696 帧，全部输入 hash／退出码通过，error 日志为空；实际视频时轴合计 2425.6232 秒。逐帧 hash 不等于逐帧文字转写，抽样视觉结论未升级，全文门禁仍为 false。详见 [全帧解码核查](MOVIE_FULL_DECODE.md)。


### 显示调用外层与内部参数不能混同

Message(Localize(...))的字符串参数属于section/key/package查找标识，不直接是显示正文；同样，Preferences.Caption与Parent/Class不能整行翻译。DisplayDebug中的DrawText不当成普通流程UI。CLS三个怪字扫描命中同一个u32值16791，不由严格CP949解码成功升级为文本。详见COVERAGE_SEMANTIC_REVIEW.md。

## DMA块长度与完整对象边界

13200 B 长度须同时通过包数、13个QWC与逐条VIF输入长度验证；长度相等本身不构成schema证据。WL=0与NUM=0表示256，CL=0保持0。候选可能跨命令／payload边界，必须保存原完整候选与片段哈希。DMA_RET包排列不等于已验证运行执行链，块外前缀与对象依赖边界仍需独立核查。见 `STREAM_VIF_REVIEW.md`。

## 字段引用与源码注释不等于动态传值

stage88初次工具假设字段引用全部为本地正export，真实import引用使其失败。修订为校验import／export上下界，并保留import／null未知身份，不作本地StrProperty推断。赋值左值中的数组索引不是目标字符串；同字段跨函数读取不是reaching-definition证明。源码中被注释掉的SetText不能认定显示消费者，版本字符串TempB仍保留未确认；最近调用取自重新解析的编译token，不凭全文正则调用命中推广角色。见 `NATIVE_STRING_FIELD_REVIEW.md`。


## stage89 全帧文字候选与暂缓解码

见 [全帧 OCR 候选核查](MOVIE_OCR_REVIEW.md)。167 个真实 strict CP949 失败字段保持原字节及其他编码证据并暂缓；首片 1635 帧匹配通过。全片 OCR 不等于人工原文转写，覆盖门禁保持未完成。

## stage91 停止全帧 OCR 并切换音频优先

全帧 OCR 已主动停止；完成状态不由旧 progress.json 推断。清理2102张批量候选帧图，释放485360132字节，保留3张视觉校准图及JSON/JSONL、错误日志、哈希和删除清单。旧 evidence 图路径对应已清理图片，后续按源ISO定点重生成；不删除原ISO/AFS、译稿、framehash或测试镜像。

189993的3777帧全部匹配既有framehash、退出0；日志仅为rawvideo muxer重复DTS，原失败事件和日志完整保留。reconcile_movie_ocr.py验证原source hash、帧记录和代表图（清理前执行）后生成独立纠正记录；这不是实际解码失败，不修改PTS。新decoder_outcome只接受精确已知rawvideo日志且全帧/退出0，其他日志继续隔离。

后续采用本地多语言Whisper原语言转写、既有资源/ASS时轴比对、疑点定点OCR/听音复核。片尾名单、标题与无配音文字仍单列视觉核查。语音/视觉候选不自动升级原文或译稿；覆盖核查门禁继续关闭。

## stage92 音频优先接续

见 [音频优先核查](MOVIE_ASR_REVIEW.md)。全46影片库存：45音轨完成本地原语言候选转写，1片无音轨；283片段、174低置信度片段定点OCR队列，26个空白折叠源匹配不作exact去重。停止全帧OCR，批量清理有哈希清单；原资源/6334译稿不改。音频候选流程完成不等于全游戏覆盖完成，继续保留静默视觉文字与未知native语义。

## 全字符集合的字号与词义检查

当前2176字库存中NormalFont19px的分号越过共同baseline；改用18px并逐字复核后通过，KatakanaFont15px通过，不裁切或忽略该字符。扩容map必须配合实际扩容Font tables验证，不能沿用仅原韩文range的MappedEncoder缺省构造。

韩语`사과`也表示道歉，`옥`可出现在监牢等复合词中，`하곤`可为语法结构。名词校验使用显式exact-source元数据，仅绑定完整字段名称，不能为了消除误报而把对话中的道歉翻译成苹果。原专名最长匹配及未知控制隔离继续保留。

### leading field指纹范围与可写容量不同

CHT/ECD等旧slot视图的slot_sha256锁定整个上游segment，observed_byte_capacity只描述leading正文的首NUL/零区。不能直接用后者长度检验完整slot hash，也不能为了让hash通过而把trailer变成可写容量。实际143字段触发该问题；现采用完整segment hash、独立trailer hash、leading-only写入及全资源非选择字节比较。四个专门回归测试保留。

### 自动翻译先导不构成全文校对

本地NLLB转换模型的韩中先导可译普通问候，但在大魔法阵/血泪等专名上产生错误、未知字符和句子遗漏。把名词预换成中文也没有通过该样本。候选没有并入正式批次；来源为Meta NLLB及Yasmin Moslem的[CTranslate2转换说明](https://forum.opennmt.net/t/nllb-200-with-ctranslate2/5090)，下载hash和实际命令/输出保留ignored work。该结果只约束此次模型/配置与输入，不能泛化为全部自动翻译系统的表现。

### ASS文件hash必须绑定落盘字节

Windows默认write_text会把LF换成CRLF，内存ASS字符串的hash不等于落盘文件hash。27个现有成片的ASS语义与SFD未改变；receipt保留旧LF内容hash，并补正确的实际文件hash，旧receipt另存。后续工具显式写LF并从实际文件计算hash。音轨/帧数通过不替代字幕文件身份核对。

### 无音轨SFD的本地预览提取

991802没有音轨。上游`sfd_muxer.SFD.from_file`在构造对象时要求ADX参数，空音轨会触发`not an ADX/SFA file: head=`，不是原视频损坏。FFmpeg视频stream-copy在该片原时间戳下会报告重复DTS；失败中间流保留。只读预览提取改用同一上游`container._demux_streams`取得视频/音频payload，显式要求音频为空，再独立转码为MP4；733帧及完整无音轨解码检查通过。不更改上游库、原SFD或游戏播放时轴。

### 大面积字幕遮罩导致原画遮挡

stage93下方黑色字幕带和全屏故事面板覆盖原动画，用户完整成片验收判定不可接受；保留音轨/帧数不代表原画保留。stage94移除所有背景drawing和Mask style，长段落分成最多两行短句，使用无背景白字描边硬字幕。对白位置70%避免与原底部韩文重叠，歌曲/滚动文字位置84%。原画内烧录文字仍然存在，不宣称已消除。初次无背景样本显示84%对白位置与原韩文重叠，因此对白上移；初次候选保留，当前构建以`*-94-final`目录为准。

### 空白区不能从单张画面推广到全部影片

991803截图右下区域较空，但180111/181307原韩文可横跨画面中线。stage95以21部所有参考字幕窗口起中末的345张原帧核查每片边界，取红框内更靠右的矩形，不把单帧或OCR无输出当作每帧无字证明。原帧hash、OCR低置信度及全帧未穷尽标记保留。固定两行排版解除后，仍须受矩形像素高度约束；标点连续串必须与前一个原子绑定，否则挪走单个前字仍会在下一行留下标点。

## 右侧硬字幕的字体度量不一致（stage97）

已验证：Pillow的EM像素大小与libass的ASS字号不是同一个尺度。思源黑体24px的ascent/descent为28/7，ASS样式采用35号字才能匹配24px测宽。旧版按18px测宽却渲染18号ASS字，造成可用区域内明显小字和空白。`pixel_font_size=true`启用字体度量校准；逐行独立定位避免字体高升降部导致行间距膨胀。其他布局默认不启用，避免改动已验收范围之外的影片。对181307的55秒原帧已生成并检查24px新版样张；原生韩文仍保留。

## 按字符凑宽度会拆散中文词组（stage98）

已验证：stage97虽保护名词表，却仍把其他文本逐字符排版，181307的“作出什么判决”在行尾/翻页处被拆散。仅追加少量禁拆词或自动分词不能等同于逐句语义复核。stage98为21部115个源cue添加显式词组和语义页，复核页不允许自动按高度切割；保持大字号，不通过缩字掩盖问题。180115寻找亚逊的一句改为先说明寻找对象再描述宾迪，避免长定语在狭窄区域造成悬空翻页，含义保持不变。

## 严格编码往返不等于语言解释正确

六个CHT源字段在主CP949解释下呈现无语义文字，但完全相同的原字节也能严格CP932往返，得到连贯日文问题/说明。两种编码的字节往返都成立；不能把主解码strict误称为语言语义已证实，也不能据六例全盘替换编码。保留原源hash和主参考，按字段记录替代读法与原保护控制序列，译文独立回填。具体字段与往返记录为stage105 camp-context-review.json。

## 中文润色不能越过动态字符串的固定截取边界

占卜金额14与商店金额7的调用先放数量再接字段，单字段译成需要花费希德币会形成100需要花费希德币。消灾编号9同时出现LeftA／MidA的5字符截取与Left／Mid的11字节截取；原ELF标量代码确认A版按高位双字节扫描，非A版按字节。使用5个双字节前缀字符加一个ASCII空格同时满足两者，不能仅凭整句自然或font cmap通过而改长度。列表最终绑定与完整运行未确认，显式pending policy保持；没有盲改原ELF或调用常量。见DYNAMIC_TEXT_CONSUMERS.md。

2026-10-11 stage141：partition-only FPB错误统一报overlap；六个原文件实为领先pool前缀和显式seq0导致未合成implicit视图。诊断必须看实际区间，不能删除前缀来满足partition，也不能把未编号误判为无显示。新backend保留gap／tail并仅重定位明确窗口。

2026-10-11 stage142：celfid mirror清单24项不是全属SHIP，3个配置／INT原属FILE。错误以SHIP定位会KeyError psx2user.ini；首失败记录initial-mirror-owner-failure.json保留。按resource owner绑定后全24offset/hash核对。font增长后原物理offset已移动，只有原流验证offset、改流重新唯一定位资源才可同步缓存；不得直接套原offset。

## Whole-resource style name collisions (stage155)

The initial 206-name subset passed but all249 source/encoded name comparisons found eight collisions with older translated names. The failure report is retained. Test all249 including previously reviewed and unchanged fields; do not fix the test by reducing its domain. Orthographic qualifiers preserve five base names and original equality partitions, without assuming unused or distinct gameplay.

Stage157 initial suite also retained an old six-field quarantine assertion after105 source-bound promotions. It failed as expected; replace it with exact six-ID/profile hash/target assertions and explicit static-not-runtime checks, then test fresh baseline/rollback copies. The original failure output remains saved.

## Batch consumers have distinct schemas (stage158)

Appending an ordinary FPB batch to every command with --batch broke configuration validation because the configuration path requires references.und. Append only to FONT_INVENTORY, SCOPE and PREFLIGHT; do not pass it to CONFIG_VALIDATE, CONFIG_IMPORT or the native header-only batch parser. Preserve the failed command and rebuild into a fresh output directory.

The second build reached SHIP_IMPORT but duplicated the new batch: its --batch already points to the preflight-generated selected-copy-batch that includes the new entries. Keep source registry inputs separate from derived aggregate inputs. Rebuild fresh after removing that duplicate argument; do not weaken duplicate-ID validation.

stage169初次构建计划误把CHT新batch也附加给配置专用validator，触发references[und] KeyError；原资料未损坏。修正配置专用输入，只给ordinary scope/font/preflight/import加入新batch。build-initial-failure.json保存实际失败；不得以失败计划作为发布证据。

stage169同类输入计划错误还触发CONFIG_IMPORT、SHIP_IMPORT重复identity、HEADERS错误policy；分别保存在build-second/third/fourth-input-failure.json。只给FONT_INVENTORY/SCOPE/PREFLIGHT追加ordinary batch，SHIP_IMPORT读取已合并preflight batch，配置与header输入保持专用。失败header输出目录保留为header-copies-failed-input；原文件没有改动。

stage170：两条TUI制表符源字段00000682 key17/physical16与00001240 key192/physical9补译，native256/MainFString4及真实Key查询绑定。single-tab-byte-v1只允许一个TAB，保留09字节并保持数字、protected tokens在TAB两侧顺序，默认API仍拒绝控制字节。风之符咒依名词表部件统一，不写护符；全角空格保留。14616reviewed、2013terms、2464chars/两5131glyph；5control→3control，8decode/其他scope/动画ISO继续，最终验证见170/VERIFICATION.txt。原文中的TAB实际排版语义不因静态存储确认而冒称已验收。

stage170首次语言目标用“风之护符”被全量glossary checker以部件부적拒绝；按已有2013词表修正为风之符咒。并未绕过校验或改源字段。

stage171：00000218.fpb实际header key0/offset0/length43绑定，37B可见韩文场景测试对白后6个NUL。terminal-null-padding-v1以source/reading/target/native hashes启用，仅源末尾零字节；目标正文无NUL，rewrite_fpb在译文bytes后追加原6zero并更新native header长度，不删除源padding、不改原档、不推断事件未使用。普通14239/含FILE14617reviewed、2013terms；剩2control与8decode集中00000106源异常窗口，其他scope及ISO继续。完整验证171/VERIFICATION.txt；默认FPB API原行为不变，无自动padding判断。

stage171初次scope对任何NUL强制隔离，即便源已hash/native-bound核实。仅允许有效terminal-null-padding-v1 proof；未绑定或伪造拒绝。CLI新proof helper缺少src模块路径时报ModuleNotFoundError，按通用tools/src/lib路径修正，实际失败记录保留。新scope2与2scope测试验证，不改原source。

stage172：00000106.fpb十个原生记录明确列为retain-source-fault（8个CP949 bytewindow截断字符、1个非语法测试残片えうれおいつえれｄ+3NUL、1个9NUL全零记录）。prepare_source_fault_retention按原SHIP/ELF/nativeKey/physical/span/fullpool/hash核查，派生catalog只添加retention proof，原decode/controls/editable/backend/offset/raw均不改变。scope单列源异常保留10，不计已翻译、不授予import、不声明事件未使用；普通scopereview仍不能跳过quarantine。171字库/AFS实际bytes不改，14617reviewed/2013terms/1011资源14614fields。新scope不再有deferred-decode/control，原8failed/2quarantine如实保留；10Latin/3configsemantics/3pending/compiled/native/image/layout与已验收动画/最终ISO继续。证据172/VERIFICATION.txt。

stage173：余10Latin范围收拢：9条可读英文补译（CommonSid1/GFTOrhaText2/FDS原型6），vbvb b source-bound literal保留（累计139）。GFT原92*822+8、native180/arrayf4，GetGiftData按首Key0比较；0/1键唯一，OrhaText源70/nativea8，Core结构最后StrProperty，compiled10958 BeginState的SetChatText参数，不是内部tag。CommonGetCommonTextIndex312920→3127f0/array130，key19实际physical18。FDS03633为2*2052+8四512文本原型，与active03591同定槽schema；不宣称其游戏加载已执行。Sid→希德币、Orha1/2→奥尔哈1/2、pparkjju/2→朴柱/2项目统一，不推断人物身份性别，数字与机器metadata保留。14626reviewed/2018terms；最终字库/AFS验证173/VERIFICATION.txt。10源异常仍保留，3configsemantics/3pending/compiled/native/image/layout及动画ISO继续。

stage173初次5alias插在名词表尾注之后，被连续表格回归拒绝。修正插入真实最后术语行后，保留5alias内容、尾注与已有2013词条。test-initial-failure.json和初manifest保留，重新在baseline-tests2/rollback-copy2跑完整事务。


## 默认Player不等于主角

DefaultPlayer/URL中的Player是引擎默认身份，不能凭可读英文替换为卡琳兹。协议描述有native配置加载，不意味着已证实剧情可见或运行不可见。应把显式保留决断与原semantic分类分开，不用新分类掩盖旧未确认状态。


typed存储回填与动态模板替换证明不应混为一谈：保留原标记、key与槽，用户测试可验收翻译后的模板，即使没有覆盖所有历史运行分支。不能删除~或把模板重写为假定主角名；无compiled调用也不是无用证明。


## builtin注册采用栈溢出模板

对intUObjectexecJump等套用旧inline PMF工具会报exact inline method descriptor copy missing or ambiguous。不是回调不存在，也不能把name table+4的初始0当地址。原initializer将source/destination指针SQ到栈后LQ恢复，FPR复制PMF。新bounded tracer闭合此实际模板；unknown/call/branch直接停止并报错，不越过未知执行流猜寄存器。


## Display call不等于每个参数都是标题

SetSentinel收取MrtsGame.Mrts*Window类路径，即使旧semantic表将该call归入display候选，也必须保护这些machine-readable参数。compiled front-end保留它们；不能因全文翻译要求破坏类lookup。47个真实显示label分开写入语言batch，等待bytecode/cache backend。


stage177首次alias插入选中了文末示例表，连续词表回归失败。已用最后actual approved term row重定位，原2018词条与文末说明逐行恢复一致，失败日志保存test-initial-failure.json；最终事务使用隔离copy2重新验证。

## stage178 real import repair and cache boundaries

The first ordinary-copy run failed properties/Function tail changed because property_block includes native_tail_sha256/native_tail_bytes for the entire post-property object. Those derived research metrics naturally change when scripts change; compare property stack/rows/end and the actual Function tail instead. Initial command/output/exit1 is retained in178/ordinary-command-initial-failure.json; actual properties and tail are still exact.

Do not substitute next-token offset for the exact child-expression end, normalize historical Context skip words, treat Assert diagnostic words as branches, or equate streamed script prefixes with complete serial bodies. Several selected stream prefixes do not have the ordinary Function tail immediately following. The overlay intentionally retains all metadata beyond the unique prefix, and demands consensus across every original alignment. Runtime acceptance remains a separate test.

## stage179 ISO/UDF directory-group ordering regression

The first complete movie+archive ISO failed independent verification with unexpected appended extent. Source acceptance list placesMOVIE99/1825381 beforeMOVIE18/189992; upstreampatch_iso batches byparent directory and therefore appends allMOVIE18 beforeMOVIE99. UDF planner/validator usedglobalinput order and selecteddifferent extents. The literal exit1 log remains in179/iso-build-initial-failure.json; the unverified4.25GB image was subsequently removed with its hash recorded in180/obsolete-generated-images.json. grouped_replacements now normalizes the exact directory-batch order before planning/writing/checking; a cross-directory regression test guards it. Successful candidate was rebuilt from the original, not accepted by weakening validation.


## stage180 标题与 UI 反馈修正

stage180：菜单位图不会随普通文本回填自动翻译。旧预览按BGRA呈现蓝色羽毛，标题实证应为RGB；palette原字节不改。LINEAR清单键不是.lin文件名，首轮重建在manifest门禁失败，修正stem键后重建。另一同名标题变体源像素不同，门禁拒绝，不强写。首次在派生selected-copy-batch中改UI已恢复，随后按canonical registry同步；只有新integrated-afs2可作为本版输入。隔离基线测试需创建work临时目录，缺目录造成的四项失败日志保留，补目录后1913项通过。


## stage182 菜单与宋体修正

宋体墨迹可能超出名义 advance；按实际 ink bbox 居中并检查格内覆盖，必要时收缩宽度。U+3000 为空白合法，不应误报缺字；其他字符须通过 cmap 与量化后非空检查。图集普通 caption 已译不代表 bitmap 消费者已译。


## stage183 离线字形实验

超采样在15px/四级量化下可能比hinted native更细；增粗也可能合并组件、关闭孔或挤出advance。应比较真正2-bit解码图，拒绝危险增粗并逐字记录，不能把高分辨率字体预览当游戏效果。见 FONT_RENDER_EXPERIMENT.md。


## PCSX2诊断 datapath

本地v2.8.2的 -datapath 对输入目录再追加 PCSX2 子目录。首次184探针误将INI放在父目录，日志停在输入源初始化且无ELF执行，记录保留。纠正为 <datapath>/PCSX2/inis/PCSX2.ini 后观察原ELF冷启动执行。软件SaveFrame开关未产生图像，不将空诊断输出当作视觉验收；隔离设置不影响用户日常配置。
# PCSX2 贴图根目录与区域哈希

`Textures` 应指向贴图根目录，模拟器会追加 serial/replacements；指向 replacements 内部会导致多拼一层目录。
旧 r-region 和旧 TCC 位在 PCSX2 2.8.2 名称解析中已兼容，不应因此重新猜纹理哈希。
跨版本复用必须保持 CLUT 与格式键，不用无调色板哈希的别名强配。具体证据及恢复见 [高清贴图复用](HD_TEXTURE_PACK.md)。

## 名称修订与字幕容器检查

不能将保留旧输入比较值的历史UI标点recipe当作当前游戏文字，也不能只改名词表而漏掉已生成的SFD与celfid副本。stage187保留旧recipe、另做源hash绑定增量后处理并全ISO回读。影片严格-xerror framehash在旧/新SFD上均因rawvideo muxer非单调DTS停止；复核使用既有decoder_outcome的窄日志规则，要求完整相等帧数/退出0，保留日志且container_timing_verified=false，不移除SFD时间戳、不将此说成新的游戏内播放验收。


## 字格内逐字clamp不保留字体共同基线

参考字顶边不是全字符集合的最小顶边；逐字clamp会改变少数字形的坐标基准。应量化后测全集、统一平移并检查上下透明边界；不得通过裁掉顶笔画、强迫包围盒等高或缩字绕过。透明边界针对采样风险，不等于已证明具体游戏GS过滤根因，见FONT_ALIGNMENT_REVISION.md。


## UI字图的RGB振铃不能直接变为不透明描边

黑底RGB Lanczos后的任意非零颜色若都映射到非透明索引，会产生暗色杂点。目标五标签采用L覆盖率门限后生成局部轮廓，并限制原中性灰阶；其他资产不全局改写。见TAB_SHADOW_REVISION.md。


## stage190 陷阱

新增字形横向有效步进内1px留白，宽墨迹量化前拟合；全量14683译文扫描及2992字段换行修订。离线预览必须按metrics裁剪数字字格，避免把原字格尾部画到邻字上。指定tabs-fixed.iso更新，其他测试ISO保留；冷启动视觉复测尚待验收。详见 FONT_SIDE_AND_LAYOUT_REVISION.md。


## stage191 顶栏底边

顶部六标签两个副本的211/233/255行是旧图残留，上一轮仅覆盖21px字格未清理端点行。新增显式clear_rect向下清1px，设置统一coverage-mask；包表、调色板及非目标像素保持。详见 TAB_FRINGE_REVISION.md。测试ISO沿用目前实际文件名Magna-Carta-Tears-of-Blood-zh-CN-test.iso，字库/换行/影片不回退，冷启动视觉复测待验。


## stage192 菜单渲染

原字库存储填充全量清理，保持有效笔画/编码/步进；四信息按钮按27px按钮与1..18墨迹中心将Y5改4，属性主体与描边60处Y上移2px。魅力两个图集副本改为有透明边界的彩色coverage-mask。普通资源及启动缓存同步；译文/动画/ELF保持。详细重建、原字形填充字节变化及尚待游戏同场景验证的边界见docs/UI_RENDER_REVISION.md（docs内路径为UI_RENDER_REVISION.md）。

## Cross-region battle cheat hooks

Do not reuse an upstream raw object/vtable-address bit as a Korean affiliation test: such address bits can change between builds. Korean team bytes and native class-cast paths provide independent anchors. Preserve R5900 128-bit GPRs with SQ/LQ rather than a 32-bit scratch save. ELF-unmapped code caves still need dynamic ownership checks; synthetic RAM proof is not emulator memory evidence. See [BATTLE_CHEAT_PORT.md](BATTLE_CHEAT_PORT.md).

## Hotkey OFF is distinct from removing a patch group

Never implement OFF by merely stopping ON writes: modified instruction memory remains. Conditional restores must use verified original words. Clearing a GUI group also removes its OFF handler, so preselect modes and use the runtime latch. PCSX2 extended condition bodies must not mix ordinary word commands with RAW commands; exact skip lengths and group boundaries are tested. The actual input consumer is preferable to a foreign-region fixed pad address. See [HOTKEY_CHEATS.md](HOTKEY_CHEATS.md).

## libpad raw buttons versus engine-internal masks

The Korean consumer byte-swaps packet buttons into its internal mask. Using
that combination with SDK SELECT/Up/Down masks broke the hotkey wrapper.
Live captured packet `00 73 EE FF` and independent raw replay expose the
mistake; a generated packet fixture had duplicated it and falsely passed.
Keep raw captures separate from mask-to-packet test generators. Corrected
wrapper uses `byte2 | byte3 << 8`; physical repaired ON/OFF remains pending.
See [HOTKEY_CHEATS.md](HOTKEY_CHEATS.md).

## Renamed cheat sections retain stale selection names

A player-edited `[60帧]` section no longer matched saved `Enable = 60 FPS`.
The startup log loaded the internal controller and other selected effects,
but omitted the frame-rate group. Captured controller commands still matched
the working byte-order repair exactly. Only the enabled FPS name was migrated;
player-edited descriptions/PNACH bytes were preserved. This explains the FPS
selection failure, not a proven failure of the detector for other effects.
Evidence: `build/hotkey-selection-repair/VERIFICATION.txt`. Reload the settings
window after an external INI change; verify actual selected groups on cold boot.

## SFD全帧解码不等于播放器结束验收（2026-10-12）

全46影片均可FFmpeg完整解码，但25部重编码ES缺精确EOF的B7；容器B9不能替代视频B7，EOF flush会掩盖该差异。本地sfd-muxer0.1.1的10位temporal_reference错误右移还导致时轴问题，隔离只修位移仍未消除所有DTS倒退。解析器不得用pos+4>=len忽略精确EOF的4字节start code。原输入、全量报告、失败与修正实验证据保持，见[MOVIE_PLAYBACK_AUDIT.md](MOVIE_PLAYBACK_AUDIT.md)。

## 不重编码的SFD修复与旧缓存失效

仅改旧parser一行仍有DTS倒退，正式修复改用完整ES全局I/P时轴并保留现有字幕视频，仅加B7。追加B7应增加最后视频PES length并缩减padding，不能只放到SFD容器B9后。生成入口显式bf0并后处理，cache stamp改version2/playback_repair1，避免修复工具正确但仍复用旧坏输出。旧已验收画面通过全帧像素hash继承，不把它扩展为播放结束验收。详见[MOVIE_PLAYBACK_REPAIR.md](MOVIE_PLAYBACK_REPAIR.md)。


## 发现指令残留与选择项分类（2026-10-19）

真实p2s中隐身latch=0但四处发现跳转仍生效；关闭作弊总开关不会执行OFF恢复，重新进图不等于重载ELF，旧即时存档还会带回修改。FPB中同时含剧情与选择项，不再以扩展名整批视为剧情。详见 OPTION_PUNCTUATION_AND_TRIGGER.md。


## 隐身残留与事件条件应分别验证（2026-10-19）

开关OFF不证明EE指令已恢复；恢复指令也不证明事件条件满足。温蒂妮本次干净现场的实际阻塞条件是提前持有物品497，而非普通怪物发现/碰撞。检查加载中的事件、源键、原生比较方向及实际背包数量；不要把脚本人物当普通MonsterPlug，也不要盲改剧情开关。零数量物品应遵循原生FArray移除语义。仅在副本操作，原指令静态执行与用户游戏内验收分开记录。见 [UNDINE_EVENT_TRIGGER.md](UNDINE_EVENT_TRIGGER.md)。
