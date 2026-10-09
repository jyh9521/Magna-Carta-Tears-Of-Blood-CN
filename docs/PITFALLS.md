# Pitfalls

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
