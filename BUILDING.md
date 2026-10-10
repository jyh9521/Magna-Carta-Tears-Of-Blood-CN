# Building and Research

目前提供研究工具、单字/小字集/新增槽 PoC 及一键构建；全文初稿正在进行，新增校对译文尚未导入。完整游戏内验收待完成。

## Inputs
研究输入仅包含韩版SCKA-20043 ISO；保持原位，不复制进跟踪目录。
已研究hash `6242476a66a96110fb6ee1a1dd668eedd70d3df6c835f0de9192451b5f4fcd45`，3210412032 B。
其它版本只能重新研究，不允许以此hash的结论无条件patch。
上游USA-base undub CLI仍保留，但依赖USA ISO；KR-only实验profile已实施，完整locale生产流程仍待完善。

## Dependencies
Windows本次Python3.14.2，pinned requirements-research.txt：cri-afs0.1.1、sfd-muxer0.1.1、pycdlib1.21.0、Pillow12.3.0、fonttools4.66.1。
SFD实验使用FFmpeg9.0.2 full (libass) 与ffprobe，同一installation。
Python -X utf8避免日语Windows的CP932默认解码问题；不需要更改系统locale。
iso.py优先使用isoinfo；缺少该程序时用pycdlib读取ISO9660 metadata，写入/relocation仍复用上游算法。
不依赖gitignored上游lib/experiments。

```powershell
python -m venv work/venv
work/venv/Scripts/python.exe -m pip install -r requirements-research.txt
work/venv/Scripts/python.exe -X utf8 tools/research_inventory.py --iso "<original-KR-ISO-path>" --out work/research
work/venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p "test_*.py" -v
work/venv/Scripts/python.exe -X utf8 tools/research_media.py --iso "<original-KR-ISO-path>" 2> work/media-stderr.log
```

Inventory只读ISO；输出提取的SHIP/FILE/ELF、ISO身份/目录、text-family census、UE2 export表、font PNG于ignored work/research。
Media wrapper只抽单片180216，直接调用upstream build_cutscene，不新增SFD实现。使用relative ASS path避免Windowsfilter escaping问题。
所有游戏数据/实验副本仅work/build；生成catalog也不跟踪。研究工具不作为发布版验收；新增槽实验ISO的构建身份和运行时状态分别见docs/QA_EXPANDED_POC.md。

## 旧小字集阶段的历史结果与验收
46 tests passed（原14项、单字PoC10项、小字集22项，包含真实pycdlib metadata的relocation测试）；707 KR FPB无编辑byte-identical。
SFD一片静态demux/hardsub/mux成功且ADX相同；duration drift与warning见KNOWN_ISSUES。
Font bitmap可读是static evidence；截图另已确认读档UI单字显示，wrap/save/scene等门禁仍待完成，见docs/QA_GLYPH_POC.md。

## 当前KR-only最小PoC构建（限三个显示字段）
只读原版/verify hash → KR资源提取 → locales/<locale> target validation → stable glyph/code map →两font+bundle同步 → sparse text replacement →AFS manifest/TOC同步 →复用ISO patcher →outputs重新解析 →PCSX2验收。
source data UTF-8，runtime encoding由locale backend决定，不把中文写入en。
原版不覆盖，binary patch若后续需要必须expected bytes/hash gate。
先PoC再工具成熟与全文翻译；计划细节见docs/PHASE1_RESEARCH.md。

## 单字字体PoC（已实现；UI单字显示已观察）
`tools/font_poc.py`从已知hash原ISO直接提取，不依赖work/kr或研究中间文件。
配置在`locales/zh-CN/poc.json`，不改上游en catalog。Windows SimHei仅用于本地实验；profile锁定字体hash，不提交字体或bitmap。
fonttools检查cmap含“测”，Pillow生成两种高度的2bpp字形；不同字体版本需显式增加并验证profile。
发布级开放许可字体/获取机制仍待选择；当前不是最终发布构建方案。

```powershell
work/venv/Scripts/python.exe -X utf8 tools/font_poc.py verify --iso "<original-KR-ISO-path>" --out build/poc --state baseline
work/venv/Scripts/python.exe -X utf8 tools/font_poc.py build --iso "<original-KR-ISO-path>" --out build/poc --font C:/Windows/Fonts/simhei.ttf
work/venv/Scripts/python.exe -X utf8 tools/font_poc.py verify --iso build/poc/MODIFIED_FILE.iso --out build/poc --state modified
```

输出build/poc/MODIFIED_FILE.iso、DIFF_FILE.json与glyph-preview.png；事务VERIFICATION.txt/ROLLBACK.sh仅本地。
回滚只作用于独立ROLLBACK_COPY.iso，恢复原版hash且保留MODIFIED_FILE；不得用hardlink代替独立副本。
复用上游rebuild_afs，定点同步slot0目标资源size，保留SHIP外部package stub sizes。
本次ISO为2 in-place、0 relocation；原版不变，无ELF修改。
PCSX2目录已忽略且未跟踪。原版先冷启动，再启动实验ISO并开始新游戏；开场喘息对白与后续含$n对白首字应出现“测”。
不要从旧savestate验收。截图、日志、BIOS、memory cards与savestates仅放ignored目录。

## 小字集PoC — text-poc-02

版本指纹在profiles/scka-20043.json；三个测试目标及33字显式mapping在locales/zh-CN。tools/build_locale.py复用上游AFS/FPB/压缩/ISO，src/localization/text.py负责编码与受控字段编辑。
从原ISO直接构建，不依赖旧提取目录；字体仍使用上述锁定hash的外部SimHei。旧build/poc不覆盖，输出目录不得与其他实验混用。

```powershell
work/venv/Scripts/python.exe -X utf8 tools/build_locale.py verify --iso "<original-KR-ISO-path>" --locale locales/zh-CN/poc-text.json --out build/text-poc-02 --state baseline
work/venv/Scripts/python.exe -X utf8 tools/build_locale.py build --iso "<original-KR-ISO-path>" --locale locales/zh-CN/poc-text.json --out build/text-poc-02 --font C:/Windows/Fonts/simhei.ttf
work/venv/Scripts/python.exe -X utf8 tools/build_locale.py verify --iso build/text-poc-02/MODIFIED_FILE.iso --locale locales/zh-CN/poc-text.json --out build/text-poc-02 --state modified
Copy-Item -LiteralPath build/text-poc-02/MODIFIED_FILE.iso -Destination build/text-poc-02/ROLLBACK_COPY.iso
work/venv/Scripts/python.exe -X utf8 tools/build_locale.py rollback --iso build/text-poc-02/ROLLBACK_COPY.iso --locale locales/zh-CN/poc-text.json --out build/text-poc-02
```

modified验证需要该build目录中的原AFS副本与DIFF_FILE.json；这些由同一次构建自动产生，不是未记录的外部依赖。
回滚仅覆盖指定独立ROLLBACK_COPY，保留修改ISO。精确日志、差分、preview及事务记录均在ignored build/text-poc-02。
46项自动测试通过；此构建未获PCSX2验收。短串、长句、槽位与测试顺序见 [QA_TEXT_POC](docs/QA_TEXT_POC.md)。

## 全量FPB只读审计

`tools/audit_text_resources.py --iso "<original-KR-ISO-path>" --out work/fpb-audit`校验版本完整hash并复用上游parser/builder，输出资源级前置条件与控制符统计，不写回游戏文件。
通过`work/venv/Scripts/python.exe -X utf8`运行；不依赖先前提取目录。完整资源和JSON只写入ignored输出。
当前工程测试总数57（此前46项加11项审计测试）；历史测试数量保持原里程碑记录。结果与例外见 [FPB审计](docs/FPB_AUDIT.md)。

## 字体槽位与冲突只读审计

`work/venv/Scripts/python.exe -X utf8 tools/audit_font_coverage.py --iso "<original-KR-ISO-path>" --locale locales/zh-CN/poc-text.json --out work/font-coverage`
从原ISO提取已知两Font和SHIP，无需先前审计输出；输出仅在ignored目录，不调整map或生成ISO。统计范围与容量限制见 [字体容量审计](docs/FONT_CAPACITY.md)。
当前总测试数65（此前57项加8项字体审计测试）；各历史里程碑的测试数量保持。

schema2同一命令可指定`--out work/font-tui-coverage`，增加TUI字段分类、完整celfid副本计数和FPB+TUI合并使用统计。输出不开放新字段写回。当前工程75项测试通过（65+10）；范围与例外见 [TUI审计](docs/TUI_AUDIT.md)。

schema3可指定`--out work/tui-pair-audit`，同时保留旧统计并增加两个256 B区段分类及完整TUI使用计数。当前86项测试通过（75+11）；重现和旧PoC profile兼容性见 [TUI字段](docs/TUI_FIELDS.md)。

## Native只读研究

`work/venv/Scripts/python.exe -X utf8 tools/research_native.py --iso "<original-KR-ISO-path>" --out work/native-research`
直接从已知ISO验证ELF并分析，原ELF只在内存读取，JSON只写ignored目录；无需capstone或反汇编器依赖。不是ELF patcher。当前98项测试通过（86+12），见 [native研究](docs/NATIVE_RESEARCH.md)。

### ELF局部调用参数审计（schema2）

同一`tools/research_native.py --iso "<original-KR-ISO-path>" --out work/native-research`命令新增有限JAL/JALR参数报告，包含delay slot、屏障与未知值；仍只读原ISO并校验完整输入hash。当前116项自动测试通过。参数表达式不是运行时trace，复现规则见 [native研究](docs/NATIVE_RESEARCH.md)。

### 候选表与GP槽审计（schema3）

`tools/research_native.py`新增可重复`--table-va`和`--gp-displacement`选项，每张表仅16个u32；选择地址仍受版本/映射边界校验。131项测试通过，完整命令与结果见 [native研究](docs/NATIVE_RESEARCH.md)。报告区分文件初值和可变运行时指针，不生成新ISO。

## 字符→glyph离线模型

`work/venv/Scripts/python.exe -X utf8 tools/research_glyph_lookup.py --iso "<original-KR-ISO-path>" --out work/glyph-lookup`
版本锁定212 B指令片段；从原ISO读取两Font并在合成对象中核对范围、ASCII、gap及现有locale映射，额外执行metadata-only扩展实验。148项测试通过；不是实际字库扩容或新ISO构建。见 [查表模型](docs/GLYPH_LOOKUP.md)。

## Font metric与加载候选只读审计

`work/venv/Scripts/python.exe -X utf8 tools/research_font_metrics.py --iso "<original-KR-ISO-path>" --out work/font-metrics`
版本锁定原ELF片段和两Font，从原ISO独立复现metric逐项读取及有限加载调用参数。163项测试通过；不生成ISO或扩容字库。见 [metric研究](docs/FONT_METRICS.md)。

## FontObj bitmap离线投影

`work/venv/Scripts/python.exe -X utf8 tools/research_font_bitmap.py --iso "<original-KR-ISO-path>" --out work/font-bitmap`
版本锁定bitmap/cache候选邻域，执行1024组标量转换并对照原两Font完整19列投影；JSON不含原bitmap或纹理。179项测试通过，不生成实际cache或ISO。见 [bitmap研究](docs/FONT_BITMAP.md)。

## 独立Font资源扩容实验

`work/venv/Scripts/python.exe -X utf8 tools/build_font_expansion.py --iso "<original-KR-ISO-path>" --font C:/Windows/Fonts/simhei.ttf --out work/font-expansion`
两Font追加33 glyph，原bitmap/metrics保持；输出仅为ignored独立资源和实验map，不生成包或ISO。独立Font阶段201项测试通过；UE2 export增长已完成独立包接入，celfid同步尚未接入，不能直接沿用等长slice替换。见 [扩容实验](docs/FONT_EXPANSION.md)。

## 增长Font包级构建

先生成上述Font扩容产物，再运行：
`work/venv/Scripts/python.exe -X utf8 tools/build_font_package.py --iso "<original-KR-ISO-path>" --expansion-dir work/font-expansion --out work/font-package`
真实包7668 export回读通过，替换两Font并保持7666个无关export；218项测试通过。输出为独立UE2包，不生成celfid/AFS/ISO。原包hash、大小及后续门禁见 [包级接入](docs/FONT_PACKAGE.md)。

## 启动缓存候选与增长镜像预检

`work/venv/Scripts/python.exe -X utf8 tools/build_font_bundle.py --iso "<original-KR-ISO-path>" --package-dir work/font-package --out work/font-bundle`
复用上游压缩并核对六个缓存片段，输出仅在ignored目录。集成命令及当前UDF负向预检结果见 [启动缓存与ISO门禁](docs/FONT_BUNDLE.md)。242项测试通过；当前新增槽ISO构建因混合UDF元数据同步缺口在写入前停止，旧小字集ISO不变。

## 新增槽ISO与UDF同步

完成Font扩容、package和bundle后运行：
`work/venv/Scripts/python.exe -X utf8 tools/build_expanded_locale.py --iso "<original-KR-ISO-path>" --expansion-dir work/font-expansion --package-dir work/font-package --bundle-dir work/font-bundle --out build/expanded-text-poc-03-udf`
集成命令现在先规划有限布局UDF overlay，再复用上游ISO writer并同步UDF。真实韩版1 in-place/1 relocation与两视图回读通过，254项测试通过；未知布局仍在写入前拒绝。候选hash及运行时门禁见 [新增槽验收](docs/QA_EXPANDED_POC.md)。

## 一键构建与独立验证

`work/venv/Scripts/python.exe -X utf8 tools/build_poc_pipeline.py --iso "<original-KR-ISO-path>" --font "<matching-font-path>" --locale locales/zh-CN/poc-text.json --out build/poc-pipeline`
五步从原输入完成Font/package/bundle/ISO/独立verify，不依赖旧work中间文件。输出必须是新空ignored子目录；pipeline.json记录每步命令、退出状态和源码/输入hash，自动生成待测试QA清单。
单独验证命令不信任构建报告，见 [完整构建、验证及证据边界](docs/POC_PIPELINE.md)。284项测试通过，输出ISO与上一候选相同；PCSX2验收仍待完成。

## PoC验收记录校验

一键生成的QA_CHECKLIST.json可复制到ignored测试目录，填写人工状态/环境/证据后使用tools/validate_poc_qa.py。命令、退出状态及人工证据边界见 [验收记录](docs/POC_QA_RECORDS.md)。有效pending记录退出0不代表游戏验收通过。

## 名称资源隔离实验

tools/prepare_name_slots.py复用上游slot/AFS/zlib及现有D0 Font表，从原ISO和明确字体/locale生成名称资源与plan，不生成ISO；命令及未确认语义见 [名称资源](docs/NAME_SLOTS.md)。不能把输出单独替入原字库镜像。

## 单姓名候选的一键构建

现有build_poc_pipeline.py使用--locale locales/zh-CN/poc-name-01.json，输出新目录，即可增加一个显式CHA字段。独立验证器从原输入重新推导同一字段/缓存和完整AFS；旧poc-text.json不含此配置，保持原ISO内容。构建身份和测试步骤见 [名称候选](docs/QA_NAME_POC.md)。

## 构建存储

只保留明确登记的当前候选与基线；未登记产物不自动判为可删除。只读盘点、hash核对及清单规则见 [构建存储](docs/BUILD_STORAGE.md)。日常合成测试和源码回滚不复制完整ISO。

## 有界开场与存档UI试译

使用--locale locales/zh-CN/opening-trial-01.json运行现有五阶段pipeline；覆盖91正文字段及1个姓名。text_resources显式列出资源hash、FPB seq/source窗口hash或TUI单256 B profile，不再要求恰好三条测试文本。font_characters为字符库存，不拿旧韩文字节槽作为新字库映射。实际范围、候选hash和步骤见 [开场试译QA](docs/QA_OPENING_TRIAL.md)。仅新增一份测试ISO；完整存读档回归仍待完成。

## 思源黑体与全量目录

当前开放字体配置为opening-trial-02.json，固定Adobe Source Han Sans SC Regular 2.005R与完整SHA-256，下载与五阶段命令见 [思源字体](docs/SOURCE_HAN_FONT.md)。旧SimHei配置仅保留历史复现。全量catalog和新菜单批次校验命令见 [文本目录](docs/TEXT_CATALOG.md)；提取不修改原ISO，输出目录须为空，完整原文仅在ignored work。


## 全量本地校对导出（不生成 ISO）

已有 source-catalog.json 可以直接复用，无需再次提取 AFS 或复制 ISO。输出路径须位于 ignored work/build，且须为空。

```powershell
work/venv/Scripts/python.exe -X utf8 tools/export_review.py --catalog work/catalog-stage-24/catalog-final/source-catalog.json --batch locales/zh-CN/opening-review-01.json --batch locales/zh-CN/menu-review-01.json --batch locales/zh-CN/interface-review-02.json --batch locales/zh-CN/character-commentary-review-01.json --batch locales/zh-CN/story-review-01.json --out work/proofreading-stage-25
```

浏览输出 index.html，逐资源对照；review.jsonl 保存全部字段，未译目标为空。完整原文、celfid 候选和所有页面均只保留本地。重复 target ID、源 hash 不匹配、混合目标 locale、控制符或术语检查失败均拒绝导出。输出已存在时拒绝覆盖。


### 统一源集合更新

已核查布局重组为 998 资源／19137 字段（14628 非空），6334 草稿全部保留精确关联；167 CP949 失败／101 控制结构隔离。旧 15121 字段为前一版集合，非全游戏无遗漏结论。详见 [统一集合](docs/AUDITED_CORPUS.md)。


### FPB 池余段纳入统一源引用

当前统一集合为 998 资源／19143 字段（14634 非空），6 段／802 B 非索引池余段已保留，6334 初稿关联不变。167 活跃解码失败重新核验；非索引片段不伪造 sequence ID 或导入。详见 [池余段统一集合](docs/POOL_REFERENCE_CORPUS.md)。


### 集中提取审核层重现

`tools/audit_coverage_review.py`可一次重现配置、celfid尾部、数值资源、编译上下文、解码与控制结构补核，并输出只读审核快照及6334条精确译稿链接。完整参数、输入前序产物和核查边界见 [语义补核](docs/COVERAGE_SEMANTIC_REVIEW.md)。不生成或清理游戏镜像。

## VIF 只读上下文核查

见 `docs/STREAM_VIF_REVIEW.md`。13个包、320条命令及65个UNPACK输入段有界闭合，145个候选上下文补齐；剩余地图native候选8个。完整网格schema与运行时执行尚未验证，全量覆盖门禁保持待核查。

## stage88 地图字符串／字段消费者

见 `docs/NATIVE_STRING_FIELD_REVIEW.md`。地图compact-string记录补齐两个候选，上下文未闭合8→6；8032编译对象重新解析，77项取得同函数字段消费者证据，未确认320→243。新角色仍为只读候选，完整native序列化、reaching-definition及运行显示尚未证明，覆盖门禁保持待核查。


## stage89 全帧文字候选与暂缓解码

见 [全帧 OCR 候选核查](docs/MOVIE_OCR_REVIEW.md)。167 个真实 strict CP949 失败字段保持原字节及其他编码证据并暂缓；首片 1635 帧匹配通过。全片 OCR 不等于人工原文转写，覆盖门禁保持未完成。

## stage92 音频优先接续

见 [音频优先核查](docs/MOVIE_ASR_REVIEW.md)。全46影片库存：45音轨完成本地原语言候选转写，1片无音轨；283片段、174低置信度片段定点OCR队列，26个空白折叠源匹配不作exact去重。停止全帧OCR，批量清理有哈希清单；原资源/6334译稿不改。音频候选流程完成不等于全游戏覆盖完成，继续保留静默视觉文字与未知native语义。
