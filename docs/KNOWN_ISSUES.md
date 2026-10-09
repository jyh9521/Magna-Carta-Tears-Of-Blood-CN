# Known Issues

研究状态：已有局部zh-CN PoC运行截图，尚无完整验收或正式发布的中文补丁。以下是验收缺口，不声称是已复现的中文游戏崩溃。

| 项目 | 状态 | 证据/下一步 |
|---|---|---|
| 中文显示/无乱码/不崩溃 | Partial observation | 读档短UI和开场中文样本可读；完整字集、冷启动与长期稳定性待测 |
| 共享字形槽副作用 | Screenshot + static inventory | 旧text-poc-02的33字map有16槽与原文重合5140次/615个FPB；当前新增槽候选静态保留原字形，不继承旧覆盖方案，完整范围/长期稳定性待测 |
| 字宽/自动换行/标点/两font切换 | Partial observation | 本轮新增槽四图显示标点混排、长句折行及末页尾句；完整排版与两Font切换待测，见QA_EXPANDED_POC.md |
| mapping稳定/容量扩展 | Static PoC | 当前D0新增33字形已接入候选并有局部显示反馈；原字形保持为静态证据，运行时全范围/缓存/跨场景稳定仍未知 |
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

2026-10-09：Font双字节候选metric读取与原两Font各2667项离线相容，模式分支及有限加载参数已定位；实际bitmap加载、cache容量、浮点宽度/换行仍待验证。189项测试不替代PCSX2验收。见 [metric研究](FONT_METRICS.md)。

2026-10-09：FontObj bitmap消费者与动态page候选已定位，1024组标量转换及两Font全宽投影通过；format selector、page创建、总容量和真实渲染仍待验证。189项测试不改变当前PoC游戏内验收状态。见 [bitmap研究](FONT_BITMAP.md)。

2026-10-09：两套独立Font已追加33个中文glyph并保留原glyph；201项测试通过。增长资源尚未集成UE2/celfid/ISO，runtime显示及容量未验证，不能作为新可玩版本或正式试译启动证据。见 [扩容实验](FONT_EXPANSION.md)。

2026-10-09：独立UE2包已静态接入两增长Font，218项测试通过，7666个无关export保持；celfid副本、ISO和运行时加载仍未接入/验收，不替代新增槽游戏显示测试。见 [包级构建](FONT_PACKAGE.md)。

2026-10-09：增长Font的celfid六段候选同步及压缩往返通过，242项测试通过；真实增长FILE触发ISO/UDF不一致，回读失败，失败镜像不作测试版。新增预检在写ISO前阻止UDF size变化；UDF metadata同步是当前新镜像阻碍，缓存加载语义仍需运行时验收。见 [缓存与镜像门禁](FONT_BUNDLE.md)。

2026-10-09更新：有限布局UDF同步已通过真实韩版双视图回读，新候选ISO可进入运行测试；254项自动测试通过。已复现的anchor/extent静态不一致不再是本候选的构建阻碍，但PCSX2启动、D0显示、字体缓存、存读档/场景仍未验收。旧截图只属于旧槽版本。见 [新增槽PoC](QA_EXPANDED_POC.md)。

2026-10-09：一键构建及不依赖构建报告的完整二次推导通过，隔离ELF tamper检测通过，284项测试通过；ISOhash保持，不新增运行时证据。共同parser/writer缺陷、字体cache、布局、存读档/场景/linked名称仍需游戏验收。见 [构建链与最短验收](POC_PIPELINE.md)。

2026-10-09新增人工验收记录门禁，309项测试通过；实际候选九项仍untested。旧记录hash可拒绝，错误截图内容仍需人工核对；没有新增PCSX2运行证据。见 [验收记录](POC_QA_RECORDS.md)。

2026-10-09新增槽反馈补齐短UI/标点/长句及末页直接截图；完整运行时项目仍未验收。角色名称5字段及缓存仅独立资源准备，尚未生成可运行名称候选，见 [名称实验](NAME_SLOTS.md)与 [新截图](QA_EXPANDED_POC.md)。

2026-10-09：name-slot-poc-01已生成，只修改CHA slot0与缓存，343项测试通过。它尚未运行验收；旧候选截图不自动升级名称测试，姓名原文或启动异常均须保留定位结果。见 [名称候选QA](QA_NAME_POC.md)。

2026-10-09更新：名称候选新增三张菜单截图，编成、道具和角色详情页均显示中文姓名；此前“名称候选尚未运行”的条目为历史状态。正常存读档、场景、战斗及完整姓名联动仍待验收，不从菜单截图推断通过。见 [姓名QA](QA_NAME_POC.md)。

2026-10-09：opening-trial-01为有界试译测试版，91正文字段及1姓名，317新增glyph，两Font2984；五阶段和独立验证通过。本版尚无PCSX2反馈，新字集容量/多段渲染/实际UI宽度和存读档/场景/战斗均待测。未覆盖后续全部开头剧情、物品名、图片菜单及CG字幕；详见 [试译范围](QA_OPENING_TRIAL.md)。

2026-10-09更新：开场试译收到10张截图，已观察存档短提示、首段对白、分页末句及角色菜单姓名；正常存读档/切场景仍未验收。思源黑体对照镜像静态通过，不能继承SimHei版截图。101个新菜单草稿尚未应用，图片菜单仍为韩文；全文提取的未知格式、硬编码、图片/SFD文本及linked group覆盖缺口见 [目录](TEXT_CATALOG.md)。


## 全文初稿阶段

当前校对集合 6334 字段，全文初稿尚未完成；9,301 个未译结构记录包含候选键、空字段与异常字节。图片字、未解析包、ELF 硬编码及 SFD 文本覆盖仍未穷尽。268 项暂定术语不等于官方或最终定稿。新初稿未写入游戏，新增字符槽容量和新界面排版没有运行验收。

## 全文翻译前的覆盖门禁

已知格式集中导出不等于全游戏无遗漏。新增翻译暂停；额外 slot 候选、混合编码、解析间隙、celfid、UE2 图片与属性、ELF 和 46 个 SFD 的字幕语料仍待集中审计。详见 EXTRACTION_COVERAGE.md；6334 条既有初稿保留，未自动获得导入或校对验收。

全容器载荷遍历已完成，全文语义核查未完成。12项LINEAR压缩尾部／末帧差异未解决；流式export的原始声明offset不直接定位载荷正文。详见 CONTAINER_PAYLOADS.md。

62个ISO载荷和MUSIC库存、46个SFD流元数据核查已完成；音频转写和视觉字覆盖未完成。无ASS不能自动认定无台词，存在ASS也不能认定覆盖所有画面字。

## SFD 原文覆盖仍未闭合

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


### 普通包 native 与默认属性

实例 tag 读取已完成；Class 默认属性、30,788 个 native 尾部、编译字节码与流式 serial 尚待核查。全文门禁保持关闭。详见 `docs/OBJECT_PROPERTY_AUDIT.md`。


### Class 默认属性余项

555 个零脚本类已读，13 个非零脚本类边界未闭合；119 Str 仅参考属性，不自动确认游戏可见或升级为翻译正文。详见 `docs/CLASS_DEFAULT_AUDIT.md`。


### 普通 Class 默认属性更新

此前 13 个非零脚本 Class 默认属性未解析为历史状态；本轮有界读取全部闭合。132 个 Str 仍属参考，Function 字节码与流式 serial 尚未穷尽。详见 `docs/REPLICATION_DEFAULT_AUDIT.md`。


### 活跃源异常字节核查

165 个活跃 CP949 失败已按替代阅读或字符边界分类，运行时 codec、引用关系与导入尚未确认。全文门禁保持关闭。详见 [异常字节核查](DECODE_QUARANTINE_AUDIT.md)。


### CHA／MDG 怪字候选闭合

实际 8 B 头与完整记录布局核对 346 记录／391 文本字段；381 候选中 375 正文、6 数值区，零未覆盖候选。6 个怪字不属于新增正文；具体 u32 用途未完成。详见 [记录核查](NAME_RECORD_AUDIT.md)。


### 固定 region 正文遗漏补核查

44 个 ITM／ABI／SGI／NOD／DOD 文件的完整记录补导出 2360 字段，其中 498 非空字段缺少旧完整视图（488 无旧正文 byte overlap）。NUL 启发式会吞入前邻非零数值并漏提后续正文；新旧字段尚待统一集合合并，不重复计数或开始新增翻译。详见 [完整 region 字段](REGION_RECORD_AUDIT.md)。


### POD 全区块字段核查

148 POD 的 24 槽布局共 3552 字段（333 非空），补出 2 个 CP932 日文槽和 1 个问号槽。40 B metadata 的具体用途仍未验证；首 u32=31 不套用其他格式 count。详见 [POD 核查](DIALOGUE_BLOCK_AUDIT.md)。


### 统一源集合更新

已核查布局重组为 998 资源／19137 字段（14628 非空），6334 草稿全部保留精确关联；167 CP949 失败／101 控制结构隔离。旧 15121 字段为前一版集合，非全游戏无遗漏结论。详见 [统一集合](AUDITED_CORPUS.md)。


### 未知控制结构完整观察

当前 101 个隔离字段全部遍历，共 225 个标记／控制字符观察；149 次尖括号内部文字与 ITM 名称精确关联。运行语义未确认，validator 保持不变，不移除标记或批量放行。详见 [控制观察](CONTROL_OBSERVATION_AUDIT.md)。


### 普通 Texture 载荷核查

28 Texture／27 Palette／191 mip 全部结构闭合；28 首级图已检查，Editor Bad 含 `BAD SIZE`，NumberFont 为 glyph atlas。163 小 mip 已完成原尺寸逐图检查（见 SMALLER_MIP_AUDIT.md），流式 Texture 未覆盖；全文门禁不变。详见 [普通纹理核查](TEXTURE_MIP_AUDIT.md)。


### 普通编译脚本完整结构核查

8032 个 Function／NativeFunction／State／Struct 全部 serial 闭合，1207 个字符串常量、5 个含韩文、0 解码失败；运行可见性与流式脚本未完成。详见 [编译脚本核查](COMPILED_SCRIPT_AUDIT.md)。


### FPB 池余段纳入统一源引用

当前统一集合为 998 资源／19143 字段（14634 非空），6 段／802 B 非索引池余段已保留，6334 初稿关联不变。167 活跃解码失败重新核验；非索引片段不伪造 sequence ID 或导入。详见 [池余段统一集合](POOL_REFERENCE_CORPUS.md)。


### 普通包全部 mip 视觉核查

163 个非首级 mip 经 7 张原尺寸 contact sheet 全部检查；普通包 191 mip 视觉覆盖闭合，未观察到新增独立短语候选。流式 Texture／SFD 仍未覆盖，全文门禁不变。详见 [小 mip 核查](SMALLER_MIP_AUDIT.md)。


### 普通编译字符串上下文核查

1207 字符串的祖先表达式及调用符号已完整核对；1025 有调用祖先，474 有赋值祖先，133 显示符号候选保留只读。英文 UI 候选不能因韩版来源排除；运行可见性与动态文本流未证明。详见 [字符串上下文](LITERAL_CONTEXT_AUDIT.md)。


### celfid 流式字段前缀对照

Core.u 表后连续 2229 B 与普通包的 144 个源片段逐字节对应，观察到 Children／Next 参数链及 Struct 依赖内嵌。RandRange 脚本首次差异处严格停止，根 Object 和完整流未闭合；不能按 declared_size 连续切片或删重复 opcode。详见 [流式前缀](STREAM_FIELD_PREFIX.md)。


### Core Object 依赖树对照

源包 oracle 对应连续 27922 B／1715 个字段对象自身片段；27898 B 原字节相同，24 B RandRange 差异脚本保留 opaque。局部根树闭合不代表跨包或全流覆盖，默认严格模式仍在差异处停止。详见 [依赖树对照](STREAM_DEPENDENCY_ORACLE.md)。

### celfid 跨包 Class header 全量对照

568 个普通 Class header 全部核查，534 个唯一精确锚点、34 个无相同 header；6 包完整表元数据一致。Core 根树后首先对应 Engine Material，而非 Actor/Pawn。锚点不等于 serial 边界或全文覆盖，门禁保持 false。详见 [Class header 对照](STREAM_CLASS_HEADER_AUDIT.md)。

### celfid 编译脚本前缀全量有界对照

8032 个普通脚本定义全部重读；7983 个有 header 对应的定义、7987 个候选均符合限定重复模型，49 个 header 无匹配。4 个多位置定义与 1501 个内部路径歧义保留；1193 个既有常量位于符合模型的源定义中。后验拟合不是独立解码或 VM 等价证明，门禁仍为 false。详见 [脚本有界对照](STREAM_SCRIPT_CORRESPONDENCE.md)。
