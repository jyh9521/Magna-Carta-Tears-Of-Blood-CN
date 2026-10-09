# 开发与测试进展

当前里程碑：`opening-trial-01`有界试译，91正文字段及1姓名，317新增字形；新ISO静态独立验证通过，运行时未验收。旧`name-slot-poc-01`三个菜单姓名与`expanded-text-poc-03-udf`小字集仅为各自候选的局部运行观察，不转移为新版本通过。未开始全文翻译。
README只保留当前摘要；后续阶段、构建身份、测试结果与失败记录统一登记在本文件，并链接专项文档。
历史测试数对应各自构建，静态通过、截图与完整游戏验收分别记录。

## 2026-10-09 — 开场与存档UI有界试译

生成唯一新ISO，91正文字段（首段开场9句、露营教程13句、TUI69字段）及1姓名。317新增字符分4个编码区段，原字形和原映射保持；多段校验、完整资源/AFS/manifest与ISO/UDF独立推导通过。369项自动测试和干净源码369项通过，干净源码独立复核同一ISO，隔离回归恢复353项基线；第一次package阶段的单段校验失败已修复并保留日志。存档点教程时序、图片菜单和后续剧情未覆盖/未确认，新候选游戏内待测；不启动全文翻译。见 [具体范围与测试](QA_OPENING_TRIAL.md)。

## 2026-10-09 — 姓名菜单截图与存储保护清单

名称候选收到三张新截图，编成页、道具页与角色详情页均显示“测试中文”；姓名显示的局部运行观察通过，其他菜单文字仍韩文。候选关联来自测试上下文，不从截图推断ISOhash、BIOS身份或完整回归；正常存读档、场景切换和战斗保持待验收。详见 [姓名QA](QA_NAME_POC.md)。

新增只读build_storage.py与显式保留清单；文件未登记一律unreviewed，不自动建议删除。实际目录仅剩两个ISO，分别重算hash与清单一致；本轮不复制或构建新ISO、不删除文件。原name-iso-21事务已清理，不能继续把其路径作为现存证据。353项测试通过；源码回滚验收另见本地本轮记录。存储规则见 [保留清单](BUILD_STORAGE.md)。

## 2026-10-09 — 单姓名字段候选ISO

新增显式locale name_slot_overlays，只写00000460.cha slot0及缓存副本，其余4条同名字段和其它记录保持；沿用相同33字符及三字段文本，不作全局改名。五阶段构建和独立推导通过，343项测试通过，干净源码复现ISO；源码回滚恢复322项，ISO副本恢复原hash。旧候选在新工具下同hash再次验证，未修改原输入/旧locale。新候选未获游戏验收，新增测试仅定位人物菜单姓名与剧情连续性，见 [名称候选QA](QA_NAME_POC.md)。

## 2026-10-09 — 新截图与名称资源准备

新增槽候选测试上下文收到四图，短UI、标点混排、长句折行及下一页尾句有直接可见证据；环境与镜像身份边界见 [新增槽QA](QA_EXPANDED_POC.md)。现有文本不重复测试，正常存读档/场景/战斗/名称门禁保留。
名称资源定位301条CHA中的5个完全相同首字段及celfid完整唯一副本；受控等长改写、trailer/未选记录及缓存镜像核验通过。322项测试通过，干净源码复现，隔离回滚恢复309项；未生成新ISO、未作全局姓名替换、未启动批量译文。见 [名称资源与下一步](NAME_SLOTS.md)。

## 2026-10-09 — 人工验收记录门禁

新增locale-neutral记录校验工具，绑定实际候选hash、环境字段、case inventory/expected和证据文件hash；pass/fail必须有证据，untested不自动升级。初始九项记录实测pending，旧候选hash被拒绝，合成fail退出2并保存失败记录；309项测试通过，隔离回滚恢复284项。工具不读取截图语义、不识别画面实际构建来源，不证明运行时通过。ISO/locale保持，没有新译文或游戏运行证据，见 [记录填写与门禁](POC_QA_RECORDS.md)。

## 2026-10-09 — 一键构建、独立推导与验收清单

新增五步编排，从原ISO/字体/locale构建并独立推导核验，不依赖旧work中间文件或构建报告；自动保存阶段命令/退出状态和输入/源码hash，生成待测试QA清单。输出ISO与上一新增槽候选同hash，没有新译文或另一组游戏资源。
隔离候选仅一个ELF byte被改动，验证器按未修改区间检测并退出1，无成功报告；原候选保持。284项测试通过，干净源码一键复现ISO，源码回滚恢复254项。UDF空间管理非零引用新增拒绝门禁，当前原韩版引用均zero。见 [构建、验证与早晨验收](POC_PIPELINE.md)。事务位于ignored build/pipeline-18；PCSX2新候选验收仍未完成，未启动批量翻译。

## 2026-10-09 — UDF同步与新增槽候选ISO

复用上游ISO relocation，新增有限布局UDF overlay，同步file entry/short AD、主备partition、integrity size table和新尾部anchor，重算CRC/checksum并更新PVD。真实韩版候选3232653312 B，两视图完整AFS回读一致，全镜像未修改区间验证通过，新增槽字库镜像首次完成结构验收。
254项测试通过；干净源码复现ISOhash，独立源码回滚恢复242项基线，独立ISO副本回滚恢复原hash；原输入、旧PoC、locale和tag保持。新候选尚无PCSX2验收，没有批量译文。见 [构建身份与最短测试](QA_EXPANDED_POC.md)。事务位于ignored `build/udf-overlay-17/VERIFICATION.txt`。

## 2026-10-09 — celfid增长候选与UDF预检

缓存中engine header/table/两Font和两处文件大小共六段同步，压缩往返与其他bytes保持通过；242项测试通过，干净源码复现相同celfid，源码回滚恢复218项，独立资源回滚恢复原压缩bytes。复用上游AFS和manifest集成后FILE增长到22239232 B；ISO relocation实测导致UDF anchor回读错误，失败样本标记REJECTED，未作为可验收ISO。
新增混合镜像预检在写ISO前拦截size变化，负向实测退出1且ISO不存在。下一步补齐UDF文件视图/分配/anchor及校验同步，不绕过回读错误；旧PoC、原ISO/ELF、locale和tag不改，无新增运行时验收或译文。见 [缓存、失败证据与门禁](FONT_BUNDLE.md)。事务位于ignored `build/bundle-font-16/VERIFICATION.txt`。

## 2026-10-09 — 增长Font接入独立UE2包

新增有hash/version门禁的append-only export builder，实际MrtsEngine.u的7668项回读通过；两增长Font追加并更新size/offset，7666个无关export及原包数据保持。包2058129→2713665 B；干净源码复现同一包hash，218项测试通过，独立源码回滚恢复201项基线，独立包副本恢复原包hash。见 [包级构建与证据](FONT_PACKAGE.md)。
未修改原ISO/ELF/旧PoC/locale，未新增译文。celfid不是完整engine副本，增长副本及新ISO尚未接入，运行时扩容仍未验证。事务位于ignored `build/package-font-15/VERIFICATION.txt`；后续优先bundle记录重建和上游AFS/ISO接入。

## 2026-10-09 — 小字集PoC运行截图与分页反馈

三张截图分别显示短UI、中文标点/ASCII混排和开场长句折行；长句末尾下一页显示有反馈确认，未附该页截图，不记录为丢字或裁切。截图目标与text-poc-02相容，但没有镜像路径/hash、PCSX2版本或BIOS身份。正常存读档、切场景、战斗及长期稳定性未测试；分页不计作切场景。见 [逐项证据与截图hash](QA_TEXT_POC.md)。
本轮仅维护验收文档，未修改ISO、字库、locale或工具；201项自动测试保持通过，独立副本回滚恢复原文档。截图副本与事务仅保存在ignored `build/qa-text-14/`。后续继续新增Font的UE2/celfid增长接入，不将旧槽截图转移为新增槽运行时验收。

## 2026-10-09 — 保留原韩文字形的资源扩容

新增append-only Font builder和显式Font表编码校验，两Font各追加33个真实字形，2667→2700；原bitmap、metrics和映射保持。原指令模型核对新增编码与原成员，201项测试通过。增长资源仅为独立Font，UE2/celfid/ISO接入待完成，不宣称运行时扩容成功。见 [扩容实验与试译门禁](FONT_EXPANSION.md)。
干净源码构建复现相同资源hash，独立源码回滚恢复179项基线，两Font资源另在独立副本回滚；原ISO、ELF、小字集PoC和locale不改。事务保存在ignored `build/font-expansion-13/VERIFICATION.txt`。
后续优先增长资源的包与镜像接入，不继续无关只读审计；正式试译在最小PoC门禁通过后分批启动，不等待穷尽全部逆向。

## 2026-10-09 — FontObj bitmap消费者与page候选

定位FontObj候选的16位glyph、源bitmap、尺寸和动态page分配邻域；只读标量模型新增SRAV并核对1024组转换，原两Font完整19列投影一致。format分支、64边界用途与实际cache容量保持分级，未生成runtime page或修改ISO。详见 [bitmap研究](FONT_BITMAP.md)。
新增16项合成测试，工程179项通过；干净源码复现同一报告，独立源码回滚恢复163项基线。原ISO、ELF、PoC与locale保持，无新增运行时验收或批量译文。事务保存于ignored `build/font-bitmap-12/VERIFICATION.txt`。

## 2026-10-09 — Font metric消费者与加载候选

新增只读Font metric审计，确认候选+0x4C非零分支使用16位index和+0x68字节数组；原两Font各2667项逐项模型读取通过。加载邻域的+0x68/+0x74/+0x80参数相容，真实对象/版本分支与bitmap/cache仍待验证。详见 [metric研究](FONT_METRICS.md)。
新增15项合成测试，工程163项通过；独立源码回滚恢复148项基线，干净源码报告复现。原ISO、ELF、PoC及locale保持，无新增运行时验收或批量译文。事务保存在ignored `build/font-metrics-11/VERIFICATION.txt`。

## 2026-10-09 — 字符→glyph离线执行与合成扩展

从DrawText候选定位到双字节拼合/范围查表片段，新增只读低32位模型并锁定212 B指令hash；复用上游AFS/UE2读取与既有Font解析。两Font各2411个双字节成员、128个ASCII、29个fallback样本和33个PoC编码全部通过。合成追加两个表条目后94个编码返回glyph2667–2760；真实Font资源及glyph数量不改。详见 [查表模型](GLYPH_LOOKUP.md)。
新增17项合成测试，工程148项通过；干净源码复现同一报告，独立源码回滚恢复131项基线测试。原ISO、ELF、PoC ISO、profile及locale数据保持，无新增运行时验收或批量翻译。
事务命令、literal输出与hash保存于ignored `build/glyph-lookup-10/VERIFICATION.txt`。下一步核对Font加载、metrics/page与缓存容量，不将离线返回值等同于扩容完成。

## 2026-10-09 — GP可变槽与reader包装层候选

只读工具schema3新增GP metadata、可选双64 B表扫描、常量store候选和GP槽load/store候选。确认TUI相关GP槽有覆盖写入，文件初值不能解析为运行时对象。候选表0x4FE270的+0x0C路径含Linear分配和替代后端；Linear表0x4FE390的+0x14指向具有转发/累计字段形状的邻域。结论分级与重现见 [native研究](NATIVE_RESEARCH.md)。
新增15项合成测试，工程131项通过；schema2全部既有数据区段保持。原ISO、ELF、PoC ISO、locale数据不改，没有新运行时验收。
干净源码复现131项测试与同一JSON，独立副本回滚恢复116项基线测试；事务证据保存于ignored `build/native-tables-09/VERIFICATION.txt`。

## 2026-10-08 — TUI间接调用参数与延迟槽审计

只读ELF工具schema2新增有限局部JAL/JALR参数推演。00001240两处a2=256位于间接调用的delay slot，a1均为sp+0x60，目标形状为对象+0x14槽；相邻a2=4与id/双256 B布局一致。参数状态属于Verified static，读取语义属于High-confidence deduction，vtable目标、字段用途和可达路径仍未验证。详见 [native研究](NATIVE_RESEARCH.md)。
新增18项合成测试，当前116项通过。原ISO、ELF、PoC ISO、profile、映射及译文保持；没有新增运行时验收，不扩大翻译或写回范围。
干净源码副本复现116项测试及同一schema2 JSON，独立源码回滚恢复98项基线测试；事务命令、literal输出、hash及Git记录保留于ignored `build/native-calls-08/VERIFICATION.txt`。

## 2026-10-08 — ELF映射与native文本候选定位

新增版本锁定的只读ELF工具，从原ISO直接分析；确认没有有效符号条目，定位23个文本相关标识、13个地址构造候选、9个数据pointer词。
00001240路径候选邻域出现两处256立即数，与双区段布局一致但parser/函数用途未确认；No font诊断及native签名表作为后续线索。证据类型和地址见 [native研究](NATIVE_RESEARCH.md)。
新增12项合成测试，当前98项通过；没有ELF patch或字库扩容，原ISO、PoC配置和译文不改，PCSX2无新增验收。
干净源码副本复现98项测试及同一JSON，独立源码回滚恢复86项基线测试；19份项目Markdown客观措辞及65个本地链接检查通过。原ELF与PoC ISOhash保持；事务记录位于ignored `build/native-audit-07/VERIFICATION.txt`。

## 2026-10-08 — TUI双区段定位与单段写入测试

29个非零尾部全部位于载荷+256；全量863记录均支持两个256 B NUL填充区段，首段863非空、次段29非空/834空，892非空段严格CP949往返一致。段用途仍待验证。
新增8项区段审计及3项通用fixed-slot显式字段测试，共86项通过；单段写入保留另一半和metadata，256 B目标按NUL容量拒绝。只用合成数据，不对原TUI写回。
schema3保留旧范围统计，新范围当前map冲突17槽/5420次/629资源。旧PoC的ISO、profile、映射与译文保持，PCSX2无新增验收证据。范围及兼容性见 [TUI字段](TUI_FIELDS.md)。
干净源码副本复现86项测试及同一审计JSON，六个schema2历史数据区段保持一致；独立源码回滚恢复75项基线测试。18份项目Markdown客观措辞及59个本地链接检查通过；精确事务记录见ignored `build/tui-pair-06/VERIFICATION.txt`。

## 2026-10-08 — TUI记录与合并字形使用审计

全部16个韩版TUI满足相同记录几何，共863项；834个字段严格CP949/clean NUL通过，29项存在非零尾部并保留为例外，不扩大写回范围。
10个资源有一个完整celfid副本。FPB+已纳入TUI字段合计使用1084槽，当前33字map与目标字段之外原文重合17槽/5406次/629个资源。
新增10项合成测试，工程共75项通过；只读报告schema2保留原FPB基线和独立TUI统计。原ISO、PoC ISO和映射均保持，PCSX2未新增验收证据。详情见 [TUI审计](TUI_AUDIT.md)。
干净源码副本复现75项测试及同一审计JSON，独立源码回滚恢复65项基线测试；17份项目Markdown客观措辞和50个本地链接检查通过。原工具hash与事务命令/输出保存在ignored `build/tui-audit-05/VERIFICATION.txt`。

## 2026-10-08 — 字体槽位容量与原文冲突审计

新增只读字体审计工具，核对版本、两Font完整范围表和FPB pool字节身份；原ISO、现有实验ISO及locale映射不改。
2350个候选韩文槽中，695个严格解码FPB使用1064个；另外1286个仅为该语料未观察槽，不是全游戏空闲。
当前33字map中16个槽与目标窗口之外原文重合5140次，涉及615个FPB资源；稳定map不能消除共享槽副作用。两Font的2350槽bitmap均非全零。
新增8项合成测试，工程共65项通过；容量和证据边界见 [字体审计](FONT_CAPACITY.md)。PCSX2、扩容和完整原文范围仍待验证，不进入批量翻译。
干净源码副本复现65项测试与相同审计JSON；独立源码回滚恢复57项基线测试。16份项目Markdown客观措辞及42个本地文档链接检查通过；原ISO与小字集ISOhash保持，事务记录位于ignored `build/font-audit-04/VERIFICATION.txt`。

## 2026-10-08 — 全量韩版FPB只读适用性审计


新增版本锁定的离线审计工具，复用上游FPB/AFS代码；原ISO和text-poc-02实验ISO均不修改，不增加测试译文。
708个SHIP FPB条目中707个解析资源无编辑回写一致、1个8 B stub；701个满足当前partition条件，695个池严格CP949成功，667个同时满足严格解码与控制结构前置条件。
六个显式seq0资源的前缀未包含在合成views中；20个池共30处未识别百分号，2个池含NUL。原因和证据边界见 [FPB审计](FPB_AUDIT.md)。
新增11项合成审计测试，当前57项工程测试通过；历史46项测试及小字集PCSX2待验收状态保持。仅离线结构判断，不开始批量翻译。
干净源码fixture复现57项测试与相同审计JSON；独立源码副本回滚恢复新增前46项测试。原ISO与小字集ISOhash保持，15份项目Markdown客观措辞及35个本地链接检查通过。事务记录位于ignored `build/fpb-audit-03/VERIFICATION.txt`。

## 2026-10-08 — 小字集映射、FPB增长和固定UI槽

新增显式33字映射与三个测试目标，语言数据和游戏版本指纹分离；通用文本层保护token数量、值和顺序，并拒绝未知结构、缺字、重复映射及固定槽溢出。
00001944.fpb 530→578 B，seq0/seq2目标更新，其他记录透传；00001240.tui id176的512 B文本槽和celfid完整副本同步。
两Font共四份副本同步，33个候选advance统一19；celfid压缩长度与两AFS slot0同步，ISO为2 in-place、0 relocation。
实验ISO SHA-256 `73ea382c5c457e8da1f93ecda5ecc670af3cadef4ad88f3d8ce9242c3f419690`。46项自动测试通过；游戏内显示、换行与存档尚未验收。
两次最终构建hash一致，独立副本回滚恢复原版完整hash，修改ISO保留；干净源码副本同样通过46项测试。14份项目Markdown客观表述检查及29个本地文档链接检查通过。精确命令、输出与退出码见ignored `build/text-poc-02/VERIFICATION.txt`。
原单字实验保持，不扩大翻译量；实施范围与验收步骤见 [小字集PoC QA](QA_TEXT_POC.md)。
UI最终采用16 B短串，候选字宽164/173均在实验预算192内；该预算不是实测UI边界。离线实现不代表旧单字版或新版本的完整运行时门禁通过。

## 2026-10-08 — 文档客观表述整理

项目说明、技术记录、QA及版本管理正文统一采用事实表述，保留静态验证、截图观察和未验收项的区别；TECHNICAL中的旧提交状态修正为已推送。
13份项目Markdown的人称措辞检查和22个本地文档链接检查通过；24项自动测试通过。上游原文快照、构建配置和游戏实验输出保持不变。

## 2026-10-08 — 截图确认单字显示

PCSX2读档界面截图中，空存档提示中可见“测”，四个槽位显示一致；截图状态栏显示Vulkan、640×447（1x）、速度100%。
这确认该截图中的中文单字已进入游戏UI渲染，不再只有离线bitmap预览。运行至此界面可见，但不等于冷启动流程、长期稳定性、正常存档/读档或剧情换行通过。
共享B0A1槽导致其他原“가”也显示“测”，属于本次实验的预期副作用，不是正常中文译文。

本地实验ISO SHA-256：`a6d2e03fac515243bc9cc9abd35b8bb5ef7f5729e74dd4b27203ee9c78d0ffd5`。
截图本身没有ISO hash、BIOS身份、版本号或启动过程；上述ISO身份来自本地构建记录，截图尚未独立确认实际载入文件的身份。
24项自动测试再次通过，Git archive导出的干净源码副本也通过同样24项测试（共用已安装依赖，没有游戏输入或私有work中间资源）；22个项目本地文档链接检查通过。
本地基线/修改版验证及独立副本回滚的精确命令、输出与hash保留于ignored `build/poc/VERIFICATION.txt`。
专项证据、验收矩阵与下一步见 [单字PoC QA](QA_GLYPH_POC.md)。

版本管理：上游更新单独提交，工程/PoC单独提交，本次截图验收和当前状态单独提交；里程碑标签为`glyph-poc-01`，不创建正式Release。
提交与tag可通过Git历史查找，不把可变的main或历史tag改写成新结果。规范见 [版本管理](VERSIONING.md)。

## 2026-10-08 — 技术研究与单字实验构建

研究韩版ISO并审计soyjxck上游`0e8de85bffbbd392fb43ef7608df097a0fb829b6`。复用AFS/FPB/压缩/ISO/SFD实现；未重写容器工具。
两套字体glyph317及celfid精确副本同步，00001944.fpb seq0/seq2定点替换，FILE manifest更新；原ISO和ELF保持。
两次构建得到同一输出hash；2个ISO in-place、0 relocation；全ISO非目标字节一致。24项自动测试通过。
原版完整hash回滚通过，修改ISO保留；当时尚无运行时截图，该历史状态已由上方的有限截图证据更新。
707个KR FPB无编辑回写一致；单片SFD重建/ADX一致，时长约104ms差与警告仍待游戏验收。
字体/编码/资源计数/路线比较见 [第一阶段报告](PHASE1_RESEARCH.md)，上游原文见 [保留快照](upstream/README_SOURCE.md)。

## 2026-10-09 — 思源字体、全量目录与统一术语

开场试译新增10张局部显示截图，显示与分页已观察，完整运行回归未完成。新版采用固定Source Han Sans SC Regular 2.005R，解决共同baseline的单字裁切后五阶段独立验证通过；只有一份新字体对照ISO，旧镜像保留。

全量SHIP目录覆盖19类998资源、15635字段/候选，13,143个严格解码非空模板记录；坏字节和未确认语义保留。celfid21个完整镜像与35048候选另计，不声称全游戏文字穷尽。统一术语21词条；新增101菜单草稿，加既有92共193字段，非全文完成。详见 [目录](TEXT_CATALOG.md)和 [思源字体](SOURCE_HAN_FONT.md)。

394项测试通过（原369+25）。静态/干净源码/隔离回滚记录保存在ignored work/catalog-stage-24/VERIFICATION.txt；原ISO不改，模拟器/BIOS/完整原文/字体输入不提交。
