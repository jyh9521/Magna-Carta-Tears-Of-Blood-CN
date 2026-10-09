# 集中提取覆盖审计

## 当前门禁

全文翻译入口尚未开放。已有初稿保留，不因覆盖审计重建而删除；新增翻译暂停。当前顺序为：全盘资源清点 → 集中提取／候选分类 → 缺口核对 → 冻结源文本集合及术语 → 全量翻译 → 校对 → 导入。

19 类已支持格式的导出已完成，但只覆盖已知解析器和候选扫描范围，不能表述为全游戏文本已提取或无遗漏。既有分批翻译读取同一 catalog，并非每批重新提取；混合编码解释和遗漏检查与翻译交错进行，不符合先完成覆盖审计再统一翻译的顺序。

## 已复核的范围（Verified static）

- 原版 ISO SHA-256 与 catalog manifest 一致；ISO 内有 62 个文件，其中 46 个 SFD。该数量是容器库存，不是字幕条数。
- ISO 内 SHIP、FILE、LINEAR 三个 AFS 的流式 SHA-256 与本地研究副本逐一一致；不生成新的 AFS 或 ISO 副本。
- 三个 AFS 的文件名目录分别清点 13,862、53、4,099 项。完整逐文件目录仅输出到 ignored `work/extraction-coverage-45/final-audit/`。
- SHIP 中已支持的 998 个资源均存在于主 catalog，无缺少或额外资源；重新执行现有导出器后，资源 hash、原字段、pool、结构审计及候选结果与旧 catalog 完全一致。
- 主 catalog 保持 15,635 条结构记录，236 条解码失败、123 条控制结构隔离。该复核只证明现有导出可重现，不证明解析器发现了全部可见文本。

机器汇总见 [EXTRACTION_COVERAGE.json](EXTRACTION_COVERAGE.json)。原文、原始候选及包数据不进入该公开汇总。

## 待关闭缺口

| 范围 | 实际发现 | 后续审核要求 | 当前状态 |
|---|---|---|---|
| slot／trailer | 3,162 个候选中 2,302 个完全同区间、222 个已完全覆盖、527 个完全在主字段外、111 个部分重叠；638 个存在未覆盖字节 | 字节区间分类已完成；638 个未覆盖片段均落在现有 profile 划定的 trailer，仍须补充韩版结构解析并区分文本／内部数据；不能将片段数当作可见文本数 | 未关闭 |
| 混合编码 | 全目录回读产生 313 个可严格 CP932 往返且含假名的解释候选 | 与已有 101 条解释证据按 ID/hash 核对；语义、显示用途及误识别逐项确认；严格解码本身不是编码或可见性证明 | 未关闭 |
| FPB／slot 解析异常 | 10 个资源有 stub、分区间隙或解析问题 | 六个 FPB gap、一个 FPB stub、三个 8 B ECD stub 逐项判断；已有完整 pool 保留，不表示已成为独立正文条目 | 未关闭 |
| 启发式 region | 内部标识符与显示文字共存，`.att`／`.val` 当前无候选 | 结合结构、引用和运行路径分类；零候选不能视作无文本 | 未关闭 |
| UE2／图片 | 主文本 catalog 不覆盖完整包与图片文字 | 清点 SHIP／LINEAR／FILE 包的类和对象，提取文本属性；图片文字单列人工转写与资源定位 | 未关闭 |
| ELF | 主 catalog 不包含全部硬编码文本 | 版本锁定下导出字符串及引用位置，区分调试、资源名与显示文字 | 未关闭 |
| SFD | 原 ISO 清点 46 个 SFD；上游韩文／日文 ASS 各匹配 25 个影片，分别 238／272 个 cue，另 21 个影片未匹配 ASS | 既有 ASS 原 cue 已集中导出至本地 subtitle-cues.json；21 个未匹配影片逐项检查是否有对白／字幕，不把无 ASS 自动认作漏字幕；烧录文字单列转写 | 未关闭 |
| celfid | 已扫描 35,048 个只读候选及 21 个完整资源镜像 | 与主字段按源身份关联并去重，剩余结构分类；不把镜像计为额外对白，不自动判定全部 linked group | 未关闭 |

没有列出的容器扩展名仍属于待分类资源，不因名称类似动画、模型或声音而自动排除文本可能。美版／日版 ISO 缺席影响参考对照，韩版覆盖审计继续进行，不以等待其他版本代替审计。

## 统一翻译入口的验收条件

1. ISO 全文件与 AFS 全项库存拥有明确的文本处理状态：已解析、镜像、无文本证据、图片转写、媒体字幕或未解决缺口。
2. 未解决候选保留 ID、源 hash、定位、原因；可见文本集合与内部标识符集合分开。
3. 混合编码解释和原始字节对应冻结；解码失败与控制符隔离不被静默丢弃或替换。
4. 全量源集合、术语、去重／联动关系及数量形成可复核汇总；未知项明确标注，不声称绝对无遗漏。
5. 覆盖审计结论形成后再扩大翻译批次；校对前保持 draft，不自动升级 reviewed。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_extraction_coverage.py --iso "<original-KR-ISO-path>" --catalog-dir work/catalog-stage-24/catalog-final --archive-dir work/kr --out work/extraction-coverage/audit
```

输入为现有导出目录与研究副本；输出须为空且位于 ignored work/build。脚本复用上游 AFS 读库与现有提取器，原 ISO 与 catalog 只读；失败不自动重提取或改写输入。首轮新增九项工具测试通过，整体 415 项测试通过；不代表缺口已关闭或游戏运行验收通过。

## 固定槽位候选区间复核（Verified static）

复用上游 slot parser 和现有导出器，逐资源重新提取并比较完整元数据；原字段及候选的 SHA-256 与 SHIP 原字节分别核对。区间按半开边界计算，主字段只计原文有效字节，不计整槽容量或零填充；重叠先求并集，避免重复计数。

| 分类 | 候选数 | 含义 |
|---|---:|---|
| 完全相同主字段区间 | 2302 | 扫描重复，不新增语料 |
| 非同区间但完全落在主字段并集内 | 222 | 子串或重复扫描，不新增字节 |
| 完全位于主字段之外 | 527 | 保留审核，未判定可见性 |
| 部分重叠主字段 | 111 | 原完整候选保留，另列未覆盖字节片段 |

638 个唯一未覆盖片段均位于现有 profile 的 observed-trailer；600 个片段严格 CP949 解码成功，38 个失败。片段切界可能穿过双字节字符，因此片段失败不等于完整候选损坏；原完整候选始终保留。该 trailer 定义只是首 NUL 后首个非零字节至槽尾的观察区间，不是内部结构语义证明。

抽查 `SHIP/00003591.fds` @2064、`SHIP/00003531.gft` @838、`SHIP/00002106.odd` @336 的字段外字节可读为完整韩文句子；ODD 样本含 `$n`。CHA／MDG 同类候选也包含短小怪字，不能将全部 638 个直接升级正文。已确认 leading-only 主记录漏掉部分具有句子内容的原字节；运行显示用途与完整韩版多字段布局仍待确认。下一步优先研究 FDS／GFT／ODD 的 header、记录边界及多字段结构，再补充集中语料，暂不改写游戏。

源集合与既有 6334 条译文保持；不删除候选，不生成或删除 ISO。机器聚合见 [CANDIDATE_SPANS.json](CANDIDATE_SPANS.json)；完整候选、区间与源片段只保存在 ignored `work/extraction-coverage-46/final-audit/`。

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_candidate_spans.py --catalog work/catalog-stage-24/catalog-final/source-catalog.json --ship work/kr/SHIP.AFS --out work/candidate-spans/audit
```

新增八项区间测试，基线 415 项、修改版 423 项、隔离回滚 415 项通过。静态区间覆盖不构成全文提取完成或游戏显示验收。

## 韩版多字段补充层

FDS／GFT／ODD六文件已按实际8 B头和记录分区补导出1168字段，1065非空；旧689个扫描候选全部覆盖，关闭该候选集合的字节缺口，语义与混合编码审核仍待完成。此前“638片段”统计属于旧leading-only视图，不作为新字段条数；CHA／MDG短候选尚未关闭。补充数据独立保存，不覆写旧主catalog或新增译文。见 [RECORD_FIELDS.md](RECORD_FIELDS.md)。

## 统一集合修订

新只读集合保留998资源，活动字段15121；六资源旧1682条槽视图完整保存在superseded层，以1168个实际字段替代。61个精确字节alias形成，6334初稿源ID全部保持。补充字段有5个CP949假名读法和55个非空ASCII，语义尚未全部确认，全文覆盖门禁不变。见 SOURCE_CORPUS.md。


### 固定 region 正文遗漏补核查

44 个 ITM／ABI／SGI／NOD／DOD 文件的完整记录补导出 2360 字段，其中 498 非空字段缺少旧完整视图（488 无旧正文 byte overlap）。NUL 启发式会吞入前邻非零数值并漏提后续正文；新旧字段尚待统一集合合并，不重复计数或开始新增翻译。详见 [完整 region 字段](REGION_RECORD_AUDIT.md)。


### POD 全区块字段核查

148 POD 的 24 槽布局共 3552 字段（333 非空），补出 2 个 CP932 日文槽和 1 个问号槽。40 B metadata 的具体用途仍未验证；首 u32=31 不套用其他格式 count。详见 [POD 核查](DIALOGUE_BLOCK_AUDIT.md)。


### 统一源集合更新

已核查布局重组为 998 资源／19137 字段（14628 非空），6334 草稿全部保留精确关联；167 CP949 失败／101 控制结构隔离。旧 15121 字段为前一版集合，非全游戏无遗漏结论。详见 [统一集合](AUDITED_CORPUS.md)。


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
