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
