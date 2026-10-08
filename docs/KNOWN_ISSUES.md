# Known Issues

研究状态：已有局部zh-CN PoC运行截图，尚无完整验收或正式发布的中文补丁。以下是验收缺口，不声称是已复现的中文游戏崩溃。

| 项目 | 状态 | 证据/下一步 |
|---|---|---|
| 中文显示/无乱码/不崩溃 | Partial observation | 读档短UI和开场中文样本可读；完整字集、冷启动与长期稳定性待测 |
| 共享字形槽副作用 | Screenshot + static inventory | 当前33字map的16槽与目标窗口外原文重合5140次/615个FPB；稳定map不能消除冲突，完整原文范围和容量方案待研究 |
| 字宽/自动换行/标点/两font切换 | Partial observation | 所示长句折行和标点混排可见；末尾下一页显示有反馈确认，无该页截图；完整排版与两Font切换待测 |
| mapping稳定/容量扩展 | Static PoC | 33字显式map重排不重分配；运行时全范围、跨场景稳定与扩容未知 |
| native函数定位 | Static candidates only | ELF无有效符号；23个标识/13个有限地址构造候选已定位，字体查表和字宽算法未确认；见NATIVE_RESEARCH.md |
| 小字集实验text-poc-02 | Partial runtime observation | 三张截图与三个测试目标相容；镜像hash未在截图中绑定，存读档/切场景未测试；见QA_TEXT_POC.md |
| 全量FPB编辑例外 | Verified static / semantics pending | 六个显式seq0前缀不满足partition；12个池严格CP949失败；百分号和NUL结构待研究；见FPB_AUDIT.md |
| TUI双区段与共享槽范围 | Verified static / semantics pending | 863首段+29非空次段，256 B边界已核对，用途和旧profile迁移待验收；完整区段语料冲突17槽/5420次/629资源，非全游戏总量；见TUI_FIELDS.md |
|存档/切场景/战斗回归|Open|未做中文PCSX2测试，不宣称兼容|
|完整韩文资源/linked dependency mapping|Investigating|FPB/slots/region/celfid数据性质分别见研究报告|
|USA/JP binary比较|Deferred|相应版本ISO未纳入研究输入，不作为KR PoC硬依赖；仅引用上游encoding choices|
|生产ISO命令Windows路径|Verified static|pycdlib metadata fallback与实际KR ISO两处in-place已通过；runtime仍待测|
|FILE manifest stale|Fixed in PoC static|PoC同步celfid压缩长度，保留其他manifest记录；runtime影响待测|
|SFD时长/时间戳/中文字幕|Investigating|180216静态音频一致，0.103944s drift与warning；中文ASS/游戏同步未验收|
|大规模翻译/Release|Not started|PoC门禁与阶段验收完成后才能进入批量翻译|

测试须记录PCSX2版本/backend/BIOS、原版与测试版hash、冷启动、截图和每个验收项；不能只用savestate或静态测试代替。

局部ELF数据流新增两处JALR的a2=256、a1=sp+0x60静态证据；对象+0x14槽未解析，读取、字段含义与实际运行路径仍未确认。116项自动测试不替代PCSX2字宽、换行、存档和场景验收。

2026-10-09：GP可变槽与Linear包装层候选已静态定位；包装层条件分支、底层+0x38对象及替代后端未解析，TUI实际reader仍未完全确认。131项测试通过，仍无新PCSX2验收或新增翻译。

2026-10-09：字符→glyph片段与两Font原表的离线模型通过，合成范围扩展能返回超出原glyph数量的index；实际字体加载、bitmap/metrics扩容、atlas/cache和PCSX2仍未验证。148项测试不改变当前PoC验收状态。见 [查表模型](GLYPH_LOOKUP.md)。

2026-10-09：Font双字节候选metric读取与原两Font各2667项离线相容，模式分支及有限加载参数已定位；实际bitmap加载、cache容量、浮点宽度/换行仍待验证。163项测试不替代PCSX2验收。见 [metric研究](FONT_METRICS.md)。

2026-10-09：FontObj bitmap消费者与动态page候选已定位，1024组标量转换及两Font全宽投影通过；format selector、page创建、总容量和真实渲染仍待验证。179项测试不改变当前PoC游戏内验收状态。见 [bitmap研究](FONT_BITMAP.md)。

2026-10-09：两套独立Font已追加33个中文glyph并保留原glyph；201项测试通过。增长资源尚未集成UE2/celfid/ISO，runtime显示及容量未验证，不能作为新可玩版本或正式试译启动证据。见 [扩容实验](FONT_EXPANSION.md)。

2026-10-09：独立UE2包已静态接入两增长Font，218项测试通过，7666个无关export保持；celfid副本、ISO和运行时加载仍未接入/验收，不替代新增槽游戏显示测试。见 [包级构建](FONT_PACKAGE.md)。

2026-10-09：增长Font的celfid六段候选同步及压缩往返通过，242项测试通过；真实增长FILE触发ISO/UDF不一致，回读失败，失败镜像不作测试版。新增预检在写ISO前阻止UDF size变化；UDF metadata同步是当前新镜像阻碍，缓存加载语义仍需运行时验收。见 [缓存与镜像门禁](FONT_BUNDLE.md)。

2026-10-09更新：有限布局UDF同步已通过真实韩版双视图回读，新候选ISO可进入运行测试；254项自动测试通过。已复现的anchor/extent静态不一致不再是本候选的构建阻碍，但PCSX2启动、D0显示、字体缓存、存读档/场景仍未验收。旧截图只属于旧槽版本。见 [新增槽PoC](QA_EXPANDED_POC.md)。

2026-10-09：一键构建及不依赖构建报告的完整二次推导通过，隔离ELF tamper检测通过，284项测试通过；ISOhash保持，不新增运行时证据。共同parser/writer缺陷、字体cache、布局、存读档/场景/linked名称仍需游戏验收。见 [构建链与最短验收](POC_PIPELINE.md)。

2026-10-09新增人工验收记录门禁，309项测试通过；实际候选九项仍untested。旧记录hash可拒绝，错误截图内容仍需人工核对；没有新增PCSX2运行证据。见 [验收记录](POC_QA_RECORDS.md)。
