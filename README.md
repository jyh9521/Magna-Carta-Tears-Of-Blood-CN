# 真名法典：真红的圣痕 — 本地化工程

Magna Carta: Tears of Blood / 마그나카르타 진홍의 성흔，PS2，目标简体中文 zh-CN。

当前：已生成首段开场/露营教程/存档相关UI的有界试译测试ISO，91正文字段及1姓名；静态独立验证通过，新版本运行时待测。此前名称和小字集已有局部截图，存读档/切场景回归仍待验收；未开始全文翻译。

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
