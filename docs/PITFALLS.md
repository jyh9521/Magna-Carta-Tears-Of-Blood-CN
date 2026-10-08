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
