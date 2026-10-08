# Licensing boundaries and upstream attribution

## Project-owned material
LICENSE的MIT声明适用于jyh9521及贡献者自己的新增code/docs，不能自动覆盖其它作者的代码或游戏资源。
LICENSE-translations.md约定本项目原创译文许可；原版source text和game assets的权利不随翻译许可转移。
本阶段没有大量译文或字体包；glyph preview/压缩资源仅本地ignored work/build。

## Upstream
soyjxck：magna-carta-tears-of-blood-undub，审计commit0e8de85bffbbd392fb43ef7608df097a0fb829b6。
保留原Git历史、作者贡献、patch/lib/subs来源；上游AFS/manifest/ISO/SFD/格式研究不描述为本项目原创。
审计snapshot未发现上游仓库LICENSE文件；新增MIT不代表获得上游relicense授权。发布前需向上游明确code/subtitle许可边界。
上游英文ASS为GXZ95贡献，SFD_Muxer来源nebulas-star；保持attribution，不能擅称新译文属于本项目。
cri-afs/sfd-muxer独立package licenses以实际发行版本metadata与许可证为准；不由根LICENSE覆盖。
FFmpeg/libass/pycdlib/Pillow与未来外部字体遵守各自许可证；工具不打包外部软件。

## Fonts and game resources
不得跟踪/提交ISO、原始ELF、完整AFS/SFD/ADX/UE2包、原版font bitmap或系统字体。
发布级glyph generator需开放许可字体并记录来源/版本/hash/license。本次SimHei仅本机实验，profile锁定hash且不打包系统字体或生成bitmap。
生成edited texture/font/video/archive仍含原版资产，继续放ignored output；优先发行差分/脚本而非完整游戏文件。
AGENTS.md和docs/LOCALIZATION_STANDARD.md仅local instructions，保持ignored不提交。
