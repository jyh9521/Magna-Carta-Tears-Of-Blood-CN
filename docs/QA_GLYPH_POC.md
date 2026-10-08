# 单字字体PoC验收 — glyph-poc-01

日期：2026-10-08；目标：在韩版原生双字节路径中显示“测”，不验证完整中文编码器。

## 构建身份与改动

- 原版：SCKA-20043，3,210,412,032 B，SHA-256 `6242476a66a96110fb6ee1a1dd668eedd70d3df6c835f0de9192451b5f4fcd45`。
- 实验ISO：同样大小，SHA-256 `a6d2e03fac515243bc9cc9abd35b8bb5ef7f5729e74dd4b27203ee9c78d0ffd5`。
- B0A1原“가”候选glyph317：NormalFont/KatakanaFont bitmap置换，所有原metrics/range/base保留，celfid副本同步。
- 00001944.fpb seq0/seq2首个双字节写B0A1；530 B长度与$n保持，FILE slot0同步压缩长度。
- NormalFont原advance候选byte16、Katakana19保持；不把字段一致当作中文实际字宽验收。
- 实验环境exe FileVersion/ProductVersion为2.8.2.0，截图未显示版本；不将该metadata作为截图中版本的独立证据。

## 读档界面截图（Verified observation）

本次PoC的截图证据为读档界面。四个空存档提示中清晰可见“测”，其余文字为韩文；替换槽在这张截图内重复显示一致。
状态栏可读：Vulkan、640×447（1x）、FPS30、VPS60、速度100%；这些是截图瞬时状态，不是长期性能测试。
截图原始尺寸3992×2312，SHA-256 `44277e01f806d9961b313f5d638720a601957fc1e7f8b78fa0f52d2d87d6f4eb`。
原截图本地保存在ignored `work/audit/user-qa-20261008/load-menu.png`，不随源码发布；公开文档保留观察、hash与结果，不依赖该图才能构建。
截图不是启动录像；ISO路径/hash、BIOS身份、完整按键流程均未显示。证据类型为截图观察，静态检查和运行时观察分别记录。

## 证据分级

**Verified**：截图中的读档UI渲染出“测”；构建中双副本同步、固定字节替换、索引同步、非目标字节不变与24项自动测试。
**High-confidence deduction**：B0A1→glyph317→“测”的候选路径在此UI生效，支持以韩版runtime做后续小字集实验；仍需绑定实际载入ISO身份并扩大测例。
**Unverified hypothesis**：两字体各自都被运行时使用、独立包/启动bundle加载优先级、完整中文解码、字宽/自动换行、字体容量扩展、剧情及存档兼容。

## 验收矩阵

| 项目 | 结果 | 边界 |
|---|---|---|
| UI单字显示 | 截图通过 | 只确认当前读档UI的“测” |
| 重复显示 | 截图内通过 | 四个槽位；跨启动/场景仍待测 |
| 启动/运行 | 部分观察 | 已见游戏界面；冷启动完整流程与稳定性待测 |
| 字宽/基线/裁切 | 待测 | 有可见字形，不代表长文本排版正常 |
| 剧情seq0/seq2、$n | 待测 | 静态控制符保持，尚无对白截图 |
| 存档/读档 | 待测 | 空存档列表不是实际写入/载入成功 |
| 两font切换/切场景/战斗 | 待测 | 当前截图未覆盖 |
| 最小完整中文测试集 | 未实施 | 角色名、标点、长句、固定slot、FPB增长仍属后续 |

## 下一次测试

1. 记录实际载入ISO路径与hash、PCSX2版本、BIOS标识及renderer；原版与实验版使用同设置冷启动，不依赖旧savestate。
2. 开始新游戏并推进至00001944开场喘息对白和含$n后续对白；保存首字“测”、换行及紧邻标点截图。
3. 进入可存档位置，写入测试存档再重新启动载入；用独立memory card，记录切场景/战斗结果。
4. 小字集离线构建可作为下一轮验收素材，但不表示上述运行时门禁通过；扩大文本开放范围仍需完成对应验收，不开始全文翻译。共享槽副作用见 [KNOWN_ISSUES](KNOWN_ISSUES.md)，新素材见 [小字集QA](QA_TEXT_POC.md)。

重建命令见 [BUILDING.md](../BUILDING.md)；baseline/modified/rollback命令及literal输出见本地ignored `build/poc/VERIFICATION.txt`。
