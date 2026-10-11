# 真名法典：真红的圣痕 — 本地化工程

Magna Carta: Tears of Blood / 마그나카르타 진홍의 성흔，PS2，目标简体中文 zh-CN。

当前：已生成简体中文集成测试镜像，正在进行实际游戏验收，尚非正式发布版。

- 14683 条已校对译文完成回填，名词表 2021 项；两套字库各 5133 字形。
- 25 部已验收中文字幕影片已整合，21 部无需中文字幕的影片保持原版。
- 标题菜单与小标题完成中文图片替换；3631 个 UI 字段全量核查，修正 636 处句末标点。
- 1943 项自动测试、ISO9660/UDF 双视图回读与非目标字节验证通过。完整流程、动态排版、战斗与正常存读档仍需实际游戏测试；静态通过不代表全游戏零漏译或通关验收。

本地测试镜像位于 `build/test-iso/Magna-Carta-zh-CN-test.iso`。更新镜像后完全关闭游戏并冷启动，不加载旧即时存档。[测试内容与镜像身份](docs/TEST_ISO.md) · [标题与 UI 修正](docs/UI_TITLE_REVISION.md)

仓库提供译文数据、字库配置、工具和技术文档，不提供完整游戏镜像。构建需自行提供受支持的韩版原始文件；参见 [构建说明](BUILDING.md)。现阶段构建链中仍有已记录的阶段输入与本地审计产物，尚未整理为单命令发布构建。

- [文本目录与数量](docs/TEXT_CATALOG.md) · [统一术语表](GLOSSARY.md) · [思源黑体与测试镜像](docs/SOURCE_HAN_FONT.md)
- [开场与存档UI试译](docs/QA_OPENING_TRIAL.md)
- [第一阶段研究与证据](docs/PHASE1_RESEARCH.md)
- [开发与测试进展](docs/STATUS.md) · [单字PoC验收](docs/QA_GLYPH_POC.md) · [版本管理](docs/VERSIONING.md)
- [单姓名候选验收](docs/QA_NAME_POC.md) · [新增槽PoC验收](docs/QA_EXPANDED_POC.md) · [一键构建与独立验证](docs/POC_PIPELINE.md)
- [小字集PoC测试步骤](docs/QA_TEXT_POC.md) · [新增字库实验与试译门禁](docs/FONT_EXPANSION.md)
- [复现研究](BUILDING.md) · [技术](TECHNICAL.md) · [格式](docs/FILE_FORMATS.md)
- [数据设计](TRANSLATING.md) · [陷阱](docs/PITFALLS.md) · [未验收项目](docs/KNOWN_ISSUES.md)
- [许可与来源](LICENSING.md)

基于 [soyjxck 的上游 undub 项目](https://github.com/soyjxck/magna-carta-tears-of-blood-undub)，保留Git历史及AFS/ISO/文本/SFD实现。
英文CG字幕由GXZ95贡献，SofDec组件沿用sfd-muxer（源自nebulas-star/SFD_Muxer）。
当前研究输入仅包含韩版ISO；优先研究韩版runtime+中文字库，复用上游工具，不要求先取得美日ISO。
本地ISO/ELF/AFS/SFD/fonts及输出不进入Git。构建需要外部提供原版输入；所有实验输出写入work/build。
