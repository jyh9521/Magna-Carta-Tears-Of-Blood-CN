# Licensing boundaries and upstream attribution

## Project-owned material
LICENSE的MIT声明适用于jyh9521及贡献者自己的新增code/docs，不能自动覆盖其它作者的代码或游戏资源。
LICENSE-translations.md约定本项目原创译文许可；原版source text和game assets的权利不随翻译许可转移。
原创全文初稿保存在 locales/zh-CN，适用 LICENSE-translations.md；完整原文、glyph preview 和生成的游戏资源仅存于 ignored work/build。思源黑体来源及 OFL 许可记录见 assets/fonts/ 与 docs/SOURCE_HAN_FONT.md。

## Upstream
soyjxck：magna-carta-tears-of-blood-undub，审计commit0e8de85bffbbd392fb43ef7608df097a0fb829b6。
保留原Git历史、作者贡献、patch/lib/subs来源；上游AFS/manifest/ISO/SFD/格式研究不描述为本项目原创。
审计snapshot未发现上游仓库LICENSE文件；新增MIT不代表获得上游relicense授权。发布前需向上游明确code/subtitle许可边界。
上游英文ASS为GXZ95贡献，SFD_Muxer来源nebulas-star；保持attribution，不能擅称新译文属于本项目。
cri-afs/sfd-muxer独立package licenses以实际发行版本metadata与许可证为准；不由根LICENSE覆盖。
FFmpeg/libass/pycdlib/Pillow与未来外部字体遵守各自许可证；工具不打包外部软件。

## Fonts and game resources
不得跟踪/提交ISO、原始ELF、完整AFS/SFD/ADX/UE2包、原版font bitmap或系统字体。
发布级glyph generator需开放许可字体并记录来源/版本/hash/license。SimHei仅用于本地实验，profile锁定hash且不打包系统字体或生成bitmap。
生成edited texture/font/video/archive仍含原版资产，继续放ignored output；优先发行差分/脚本而非完整游戏文件。
AGENTS.md和docs/LOCALIZATION_STANDARD.md仅local instructions，保持ignored不提交。

## Source Han Sans SC Regular 2.005R

新增开放字体配置取代当前试译的系统字体输入，原SimHei配置保留历史身份。Adobe固定2.005R，OTF hash与官方来源在assets/fonts/source-han-sans.json，完整版权/OFL 1.1在assets/fonts/SourceHanSans-LICENSE.txt。开放字体文件不跟踪，派生字形仍受OFL；发行差分须附相应声明与许可，派生字体主要名称不采用保留名Source。此许可不覆盖原游戏glyph、完整包、ISO或上游代码。细节见 [字体来源](docs/SOURCE_HAN_FONT.md)。


## stage89 全帧文字候选与暂缓解码

见 [全帧 OCR 候选核查](docs/MOVIE_OCR_REVIEW.md)。167 个真实 strict CP949 失败字段保持原字节及其他编码证据并暂缓；首片 1635 帧匹配通过。全片 OCR 不等于人工原文转写，覆盖门禁保持未完成。

## stage92 音频优先接续

见 [音频优先核查](docs/MOVIE_ASR_REVIEW.md)。全46影片库存：45音轨完成本地原语言候选转写，1片无音轨；283片段、174低置信度片段定点OCR队列，26个空白折叠源匹配不作exact去重。停止全帧OCR，批量清理有哈希清单；原资源/6334译稿不改。音频候选流程完成不等于全游戏覆盖完成，继续保留静默视觉文字与未知native语义。


## stage180 标题与 UI 反馈修正

stage180仅新增项目生成的透明中文艺术PNG与指纹配方，不提交完整原版标题纹理、调色板、AFS或ISO。构建从用户提供的原版资产生成本地输出。


## stage182 菜单与宋体修正

宋体试用输入来自 Adobe Source Han Serif 2.003R，SIL OFL 1.1；许可全文见 assets/fonts/SourceHanSerif-LICENSE.txt。输入 OTF 与完整游戏图集不提交，仓库保留字体配置、文字矩形和可复现工具。


## 当前默认 Medium 字体

A-medium-mixed 使用 Adobe Source Han Sans SC Medium 2.005R，输入SHA-256 1df61d31687d04fd2f928a3bb6ca6cd61f0e988cc267cf317f32406edbb49f70，字体内嵌 SIL OFL 1.1。沿用 assets/fonts/SourceHanSans-LICENSE.txt；不提交OTF或完整游戏字库。Regular/Serif历史记录仍保留，各自许可继续适用。
## 本地高清贴图输入

用户提供的 SLUS-21221 高清 DDS 包仅作本地 SCKA-20043 替换使用。随包未提供作者、版本或再分发许可，
不将其收入仓库或发布包。`tools/port_texture_pack.py` 只生成目录、等价名称和身份清单，
不赋予素材再分发许可。文件命名语义依据 PCSX2 2.8.2 开源代码，来源链接及验证边界见
[高清贴图复用](docs/HD_TEXTURE_PACK.md)。

## Gameplay cheat references

US original gameplay codes come from root670/CheatDevicePS2 CheatDatabase.txt, GPL-3.0; retain source attribution and upstream license boundaries in derived PNACH/profile data. JP Xterminator Extreme reference has no stated redistribution license; only brief references and independent KR instruction findings are recorded, not the full page. Neither reference licenses original game assets. See docs/GAMEPLAY_CHEAT_PORT.md.
