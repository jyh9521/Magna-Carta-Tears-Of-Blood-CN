# 版本管理与记录

进展组织参考 [The Wheel of Time项目的STATUS.md](https://github.com/jyh9521/The-Wheel-of-Time-CN/blob/main/docs/STATUS.md)：README保持摘要，阶段与QA证据进入docs。

- README：当前状态和入口；STATUS：按日期记录阶段、输入/输出hash、测试数、实际验收与待办。
- TECHNICAL/FILE_FORMATS：可复用研究；PITFALLS：失败；KNOWN_ISSUES：当前限制；专项QA保存证据边界。
- 每个可核验阶段采用正常描述的独立commit；上游同步与本项目改动分开。保留原历史及作者来源，禁用强推改写历史。
- 提交前运行自动测试及`git diff --cached --check`，逐项审查暂存路径和文件体积；不以`git add -A`代替检查。
- 本阶段代码和文档已提交并推送origin/main；推送后用`git ls-remote`核对远端与本地commit/tag一致，并确认工作区状态。
- 技术里程碑可用annotated tag；`glyph-poc-01`只表示单字实验及有限UI截图验证，不代表发布版或完整第一阶段验收。
- 不移动旧tag，不创建未经验收的正式Release；版本号与通关/稳定性状态分别表达。
- ISO/ELF/AFS/SFD/字体/BIOS、pcsx2及work/build不提交；AGENTS.md和LOCALIZATION_STANDARD.md只作为本地规范。
- 实验保留原输入hash，输出独立副本；回滚在另一独立副本测试，不覆盖原ISO或保留的修改ISO。
- 新技术/测试结果产生时，同步更新相关文档。后续提交内容与当次任务范围保持一致。
- 文档正文采用客观事实表述，避免人称代词和对话参与者称谓；结论明确标注证据类型与验收范围。
