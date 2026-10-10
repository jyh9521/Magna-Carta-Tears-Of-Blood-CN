# 工作状态与新对话交接

更新日期：2026-10-10。本文为接续入口，不替代格式文档及各阶段验证记录。

## 1. 当前任务与完成边界

项目：《真名法典：真红的圣痕》，目标 locale 为 zh-CN。

当前任务是**集中提取覆盖核查**，不是继续分批翻译。工作顺序已明确为：

1. 全盘资源清点、集中提取及遗漏核查。
2. 冻结源文本集合、编码解释、内部标识符分类和统一术语。
3. 按统一术语翻译全部可翻译文本。
4. 校对译稿。
5. 按实际译文生成字库、导入及游戏验收。

既有译稿保留，新增全文翻译暂停。当前 `complete_game_text=false`、`translation_gate=coverage-audit-pending`。

2026-10-10接续更新：配置1008项已完成逐项角色分类；其余缺口继续核查，最新审核层见 `docs/COVERAGE_SEMANTIC_REVIEW.md`。当前工作树包含尚未提交的stage86–88工具、测试及文档；下述stage85提交／干净工作树记录属于接续前状态。不能把已支持格式导出完成、候选扫描完成或影片解码完成表述为全游戏文本无遗漏。

中文显示链路已在提供的 PCSX2 截图中得到局部运行验证：读档界面、角色名称、开头剧情、中文标点、长句换行及跨页末尾文字。思源黑体试用构建已经存在。上述结果不等于全游戏验收；存档写入／读回、跨场景及全部 UI 仍不能统一标记通过。

## 2. 环境与版本

- 工作目录：`C:/Users/noway/Downloads/Magna-Carta-Tears-Of-Blood-CN`。
- Shell：PowerShell。
- Python：`work/venv/Scripts/python.exe`，运行时使用 `-X utf8`。
- 分支：`main`。
- 本次交接前代码基线：`2940d0188a48cf07cd9a5a48ae07a9671950950d`，本地 HEAD 与 origin/main 一致，工作树干净。
- origin：<https://github.com/jyh9521/Magna-Carta-Tears-Of-Blood-CN>。
- upstream：<https://github.com/soyjxck/magna-carta-tears-of-blood-undub>。
- 最近阶段全套单元测试：803 项通过。此数量属于代码基线，不是游戏验收项目数。

继续前先读取 `AGENTS.md`、`docs/LOCALIZATION_STANDARD.md`，再读取 BUILDING、TRANSLATING、TECHNICAL、LICENSING、PITFALLS、FILE_FORMATS、KNOWN_ISSUES。文档较长，早期计数属于历史阶段，最新状态优先看本文及 `docs/EXTRACTION_COVERAGE.md` 顶部。

## 3. 必须保持的约束

- Markdown 使用准确、客观事实描述，不使用人称代词。
- 不重新开发成熟的上游 AFS、ISO、SFD pipeline；优先复用已有代码。
- 通用工具保持 locale-neutral；译文放在 `locales/zh-CN/`，不硬塞进 `en`。
- 原始 ISO 不移动、不改名、不修改；美版和日版 ISO 当前未提供，不以等待其他版本代替韩版核查。
- 磁盘容量紧张，不重复生成完整 ISO、AFS 或 SFD 副本。
- 不自动清理 `build/`、`work/` 或任何测试镜像；未完成测试的镜像曾被删除，后续必须避免再次发生。
- 研究输出限于已忽略目录；原始资源、ELF、BIOS、模拟器、ISO 不提交。
- `pcsx2/`、`AGENTS.md`、`docs/LOCALIZATION_STANDARD.md` 已由 `.gitignore` 忽略。
- Git 使用显式文件列表暂存，保留上游归属和历史；公开提交信息不出现工具身份名称。
- 未确认的控制符、占位符、identifier、路径、数值保持原样。
- 静态解析、原字节匹配、拟合模型、解码成功与运行显示证据分别记录。
- 未获得明确并行授权时不创建子任务代理。

## 4. 本地输入与保留产物

以下路径均相对于工作目录，仅用于定位；原始资源不进入 Git。

| 对象 | 路径／身份 |
|---|---|
| 原韩版 ISO | `마그나카르타 - 진홍의 성흔.iso`，3210412032 B |
| ISO SHA-256 | `6242476a66a96110fb6ee1a1dd668eedd70d3df6c835f0de9192451b5f4fcd45` |
| 研究输入 | `work/kr/SHIP.AFS`、`work/kr/FILE.AFS`、`work/kr/LINEAR.AFS`、`work/kr/SCKA_200.43` |
| 版本 profile | `profiles/scka-20043.json` |
| 保留测试镜像 | `build/opening-trial-02-source-han/image/MODIFIED_FILE.iso` |
| 测试镜像此前记录 SHA-256 | `0c2d8ebf005fb3a9bfbe12f19525594834c9e3b7c094cb9b6d749d20c910dcb2` |

交接时确认测试镜像仍存在；本次没有重新计算其大文件哈希，也没有改写镜像。

## 5. 最新集中源快照

文件：`work/extraction-coverage-86/review-audit/source-corpus.json`。

此前stage82快照完整保留，仍作为固定哈希工具输入，不批量替换旧工具路径。

SHA-256：`39884cc3e9175811800c92ee8ae7f3d1a50b96a67bb9d0d41cf0fb8f84895dc6`；stage86输出重新打开并核对。

| 指标 | 数量及解释 |
|---|---|
| 资源 | 1027 |
| 结构化字段 | 20151，不能称为最终可翻译条数 |
| 非空／空字段 | 15552／4599 |
| 解码失败 | 167，不能静默丢弃 |
| 控制结构隔离 | 101，尚非全部已知语义 |
| celfid 启发式候选 | 35048，与字段集合分开，不直接相加 |
| 候选字节上下文未闭合 | 6，最新stage88上下文；不是6条遗漏正文，均位于地图native |
| 既有译稿 | 6334，源链接未改变 |

此前 stage 69 快照为 998 资源／19143 字段。stage 82 新增 29 个配置资源／1008 个配置值；原字段及候选保持不变。部分旧审计工具有意锁定 stage 69 哈希，不能盲目批量替换为新快照路径。

配置值全部保持 `editable=false`、`backend_eligible=false`；现有373可见候选、460内部配置（含90空值）、172诊断、3待确认。ASCII不代表英文正文，分类记录不代表运行可见性或可编辑批准。

## 6. 已有翻译、术语和字库

既有五份译稿位于 `locales/zh-CN/`：

| 文件 | 已有条目数 |
|---|---:|
| opening-review-01.json | 191 |
| menu-review-01.json | 101 |
| interface-review-02.json | 235 |
| character-commentary-review-01.json | 197 |
| story-review-01.json | 5810 |

合计 6334，保持 draft，不自动升级为 reviewed。术语基线见 `GLOSSARY.md`；此前记录为 268 项，新增术语前须重新读取核对。编码解释见 `locales/zh-CN/source-interpretations.json`，排除项见 `review-exclusions.json`。

字体接续入口：`docs/SOURCE_HAN_FONT.md`、BUILDING 及已有字体工具。韩版双字节路径、字符映射、bitmap 和 metrics 已有研究，不从零逆向。全文翻译完成后依据实际字符集合生成字库；翻译过程中也可以增量统计缺字和容量，不必等全文结束才发现容量问题。

## 7. 最近四阶段实际完成的工作

| 阶段／提交 | 已验证结果 | 入口 |
|---|---|---|
| 82／d78e075 | 29 配置资源的 1008 值并入只读快照；6334 译稿全部 exact-source-link | `docs/CONFIG_CORPUS_CONSOLIDATION.md`、`tools/consolidate_config_fields.py` |
| 83／1d95e69 | celfid 3218646–4185028 连续 37 个单 wrapper 资源正文与 SHIP 精确匹配；未闭合候选 972→192 | `docs/STREAM_RESOURCE_CHAIN.md`、`tools/audit_stream_resource_chain.py` |
| 84／59e9d11 | 3214774–3217619 的纹理与后续 1027 B Palette 有界解析；4 mip 呈深色渐变，未见完整文字 | `docs/STREAM_TEXTURE_TAIL.md`、`tools/audit_stream_texture.py` |
| 85／2940d01 | 全部 46 SFD 完整解码 72696 帧，各退出码 0、error 日志为空 | `docs/MOVIE_FULL_DECODE.md`、`tools/audit_movie_decode.py` |

影片时轴合计 2425.6232 秒。只输出约 8 MB framehash 文本，不保存全部帧图片。完整解码不是完整文字转写，也不替代逐条字幕核查。

其他已完成核查：全盘容器库存、普通 UE2 包对象／文本属性、全部 8032 编译脚本定义解析、普通 FILE 包 37 Texture／35 Palette／212 mip。具体范围及保留项见对应专题文档，不将反汇编字符串引用直接当作显示可达性。

## 8. 剩余工作及建议顺序

### 配置值角色分类已完成；消费者证据继续核查

读取 `docs/CONFIG_ENTRY_AUDIT.md`、`docs/CONFIG_CORPUS_CONSOLIDATION.md` 及完整配置输出。对 1008 个值逐项形成可复核分类：

- 可见提示／菜单文本候选。
- 文件路径、类名、资源 ID、枚举和数值等内部配置。
- 调试或引擎错误信息。
- 暂无充分证据的待确认项。

结合 section、key、脚本／加载引用提供证据，不仅凭“看起来像英文”判定。保留原 ID/hash/offset/重复键；先生成分类记录，再决定可编辑范围。`%s` 等格式符不因分类而改写。

### 下一步优先：celfid 剩余原生／地图区段

最近上下文输出：`work/extraction-coverage-88/map-audit/contexts.json`；stage83、stage86、stage87输入完整保留。

最新6个未闭合候选全部位于地图native；stage88有界核查四个compact-string记录，补齐两个候选，字段角色保留高置信推断，见 `docs/NATIVE_STRING_FIELD_REVIEW.md`。stage87按13个DMA_RET包及320条VIF命令核查145个网格候选的完整字节归属，见 `docs/STREAM_VIF_REVIEW.md`。此前8／153／192为历史上下文视图。前部存在配置／wrapper 跨界候选；尾部包含地图路径及 Untitled 等数据，不能按解码成功自动升级为正文。

重点研究 3201448–3218646 的 StaticMesh 等结构，以及 4185028 之后地图区段。纹理／Palette 局部已有有界证据，但网格完整边界仍未闭合。普通包中声明的 StaticMesh size 不可直接用于跳过流式 PS2 数据。`00014365.usx`／`00014366.utx` 普通资源为 4 B stub，不能当完整 native oracle。

纹理 mip 顺序存在两种布局；只接受逐记录唯一几何匹配。不要把早期“宽高都不超过 8”的观察写成全局引擎规则。

### 第三步：其他明确保留项

- 167 解码失败：127 FPB、38 CHT、2 POD；保留原字节与解释证据。
- 101 控制结构隔离项：逐项确认，不改未知 `$`、`%`、`<...>` 等结构。
- CLS／ATT／VAL完整839记录／8401 word及三个ELF路径构造已核查，3个CLS候选落在u32=16791中；具体native字段消费仍未全部闭合。
- 1207编译常量stage88最新分类：103可见候选、358诊断、238内部lookup/command、265空串、243待确认；77项补齐同函数字段消费者证据，不代表reaching-definition或运行可达性闭合，见 `docs/NATIVE_STRING_FIELD_REVIEW.md`。
- SFD 画面文字逐条转写、时间轴及与 FPB／ASS 去重；尤其序章、尾声、名单。

已有 8 秒抽样接触表在 `work/extraction-coverage-52/movie-sheets/`；属于抽样视觉证据。上游韩文／日文 ASS 各对应 25 个影片，分别 238／272 cues，不代表全部原版字幕数量。无 ASS 不自动认定无对白。

### 核查完成后

形成冻结源集合、已排除内部数据、保留未知项、编码和控制符报告，明确有证据的覆盖边界。随后统一术语、全量翻译、校对、字库生成及导入。避免回到提取核查与新增翻译交错的流程。

## 9. 验证与接续操作

```powershell
Set-Location 'C:/Users/noway/Downloads/Magna-Carta-Tears-Of-Blood-CN'
git status --short
git log -5 --oneline
work/venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -q
```

stage 85 已记录：基线 791、修改版 803、隔离修改版 803、隔离回滚 791，均退出 0。测试标准输出可能含 `BAD`、`PASS`、`PASS`，来自负例 fixture；结合 unittest 的 `OK` 和退出码判断。

最近各阶段验证记录：`work/extraction-coverage-82/VERIFICATION.txt` 至 `work/extraction-coverage-88/VERIFICATION.txt`。stage87基线856、修改版896、隔离回滚856项通过，原输入与译稿保持不变。stage88基线896、修改版933、隔离回滚896项通过，两个真实输入核查链分别完整复现。同目录保存 `MODIFIED_FILE.py`、`DIFF_FILE.patch`、`ROLLBACK.sh`；回滚只针对隔离代码副本，实工作树修改保留。不得把隔离回滚命令直接改造成实工作目录删除。

完整原文、候选和资源研究数据在 ignored work，公开 docs 主要为汇总。新对话若仍使用此工作目录，可直接复用这些输出；其他机器需要按专题重现命令重新生成，不能仅凭 Git 文档假定本地产物存在。

本次交接仅新增工作状态文档，不改变译文、工具、字体、原始资源或测试 ISO。

交接文档生成后重新执行上述单元测试：803 项通过，退出码 0；关键接续文件存在，源快照哈希匹配。

## stage89 接续状态

见 MOVIE_OCR_REVIEW.md。167 个 CP949 原字节失败已逐项实证并暂缓，不继续无依据解码。180111 完整 1635 帧 OCR 已完成且全部匹配 stage85 哈希；三个视觉校准帧确认 OCR 有误识，候选不是核定原文。46 部全帧任务已启动，输出 work/extraction-coverage-89/full-ocr；当前进程与逐片 progress.json、终止结果为准，不在中断后重复启动。exec session 27325，进程首记录 PID 72332。其余未闭合项继续核查，不新增译文。

## stage90 解析器操作数

见 [解析器核查](PARSER_OPERAND_REVIEW.md)。全部8032对象/1207常量重解析；15项补充有界解析器操作数候选，最新待确认228项。101个隔离字段与validator保持不变；coverage_review_complete=false。

## stage91 停止全帧 OCR 并切换音频优先

全帧 OCR 已主动停止；完成状态不由旧 progress.json 推断。清理2102张批量候选帧图，释放485360132字节，保留3张视觉校准图及JSON/JSONL、错误日志、哈希和删除清单。旧 evidence 图路径对应已清理图片，后续按源ISO定点重生成；不删除原ISO/AFS、译稿、framehash或测试镜像。

189993的3777帧全部匹配既有framehash、退出0；日志仅为rawvideo muxer重复DTS，原失败事件和日志完整保留。reconcile_movie_ocr.py验证原source hash、帧记录和代表图（清理前执行）后生成独立纠正记录；这不是实际解码失败，不修改PTS。新decoder_outcome只接受精确已知rawvideo日志且全帧/退出0，其他日志继续隔离。

后续采用本地多语言Whisper原语言转写、既有资源/ASS时轴比对、疑点定点OCR/听音复核。片尾名单、标题与无配音文字仍单列视觉核查。语音/视觉候选不自动升级原文或译稿；覆盖核查门禁继续关闭。

## stage92 音频优先接续

见 [音频优先核查](MOVIE_ASR_REVIEW.md)。全46影片库存：45音轨完成本地原语言候选转写，1片无音轨；283片段、174低置信度片段定点OCR队列，26个空白折叠源匹配不作exact去重。停止全帧OCR，批量清理有哈希清单；原资源/6334译稿不改。音频候选流程完成不等于全游戏覆盖完成，继续保留静默视觉文字与未知native语义。
