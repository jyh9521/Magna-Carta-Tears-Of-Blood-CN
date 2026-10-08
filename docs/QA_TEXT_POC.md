# 小字集文本PoC — text-poc-02

构建日期：2026-10-08；证据更新：2026-10-09。状态：构建和静态验证通过，短UI、标点混排和长句有局部PCSX2截图证据；完整验收尚未完成，不是正式中文补丁。
旧`glyph-poc-01`构建与标签保留，旧截图结论不自动转移到此版本。

## 构建身份

- 原版ISO：SCKA-20043，3210412032 B，SHA-256 `6242476a66a96110fb6ee1a1dd668eedd70d3df6c835f0de9192451b5f4fcd45`。
- 实验ISO：同样大小，SHA-256 `73ea382c5c457e8da1f93ecda5ecc670af3cadef4ad88f3d8ce9242c3f419690`。
- 游戏版本配置：`profiles/scka-20043.json`；目标数据：`locales/zh-CN/poc-text.json`；稳定映射：`locales/zh-CN/poc-map.json`。
- 原始ISO只读、原位；输出`build/text-poc-02/`，原单字ISO位于`build/poc/`，均不进入Git。

## 测试内容

本构建仅包含三个原创测试目标，不作正式翻译：

| 资源/字段 | 测试目标 | 静态结果 |
|---|---|---|
| 00001944.fpb seq0 | 测试中文，。！？“”《》123ABC | 20→30 B，implicit length同步 |
| 00001944.fpb seq2 | 测试中文$n这是一段较长的中文测试句子，用于检查字宽、标点和换行。这是一段较长的中文测试句子，用于检查字宽、标点和换行。 | 80→118 B，保留一个$n |
| 00001240.tui record id176 | 测试中文。123ABC | 16 B写入512 B槽，保留NUL、id和文件长度 |

FPB总长530→578 B，后续window offset随前序变化重算；未编辑记录保持原bytes。
UI资源在celfid解压buffer中有一个完整副本，资源起点3929716；同一字段同步修改，不能仅修改SHIP副本。
角色显示名和linked name groups尚未改动，最小完整PoC矩阵并未全部覆盖。

## 字体与编码

33个非ASCII字符显式映射到B0A1..B0C1、glyph317..349，ASCII及受保护token直接保留；运行时输出不是UTF-8或GBK。
两Font各修改33个bitmap及对应advance候选byte，四处字体资源副本一致；geometry、range/base、其余glyph与metrics保持。
advance统一为19；字形按共同参考基线渲染，标点不逐字垂直居中。静态bounds检查不等于游戏内基线/字宽正确。
UI短串以候选width bytes估算NormalFont164、Katakana173；实验静态预算192，预算并非测得的真实UI边界。全标点样本保留在FPB，避免将较长样本直接放进窄UI字段。
字体源为hash锁定的Windows SimHei，cmap覆盖33字；系统字体和生成bitmap仅作本地实验，不分发。
此映射占用原韩文字形槽，保留的原韩文中相关字符也会变化；这是PoC限制，稳定映射数据并不消除共享槽副作用。

## 验证与证据边界

**Verified static**：源ISO及资源hash、33字cmap覆盖、编码与严格token顺序校验、FPB增长与无关记录透传、固定槽NUL和候选字宽预算、两字体及UI完整副本同步、AFS顺序/metadata/manifest、全ISO非目标bytes一致。
FILE.AFS 21716992→21581824 B；celfid压缩1239770→1104201 B；SHIP仍45686784 B。ISO走2 in-place、0 relocation。
**High-confidence deduction**：三张截图的内容与本构建三个测试目标一致，支持id176空槽提示及FPB目标的对应关系；截图未显示载入ISO路径或完整hash，不能独立绑定镜像身份。
**Unverified hypothesis**：完整字集覆盖、全部布局的advance与基线、两Font切换、跨场景稳定性、正常存档与读取；新增槽Font扩容未集成ISO，不能继承旧槽PoC截图结论。

## 2026-10-09 — 局部运行时证据

| 证据 | 观察与边界 |
|---|---|
| 截图1：读档列表 | 四个空槽提示显示“测试中文。123ABC”，中文、句号及ASCII可读；所示短串没有明显重叠或裁切。空槽列表不验证正常存读档。 |
| 截图2：开场实时场景 | “测试中文，。！？“”《》123ABC”样本可读，未见明显缺字方框或乱码；标点间距较宽，完整字宽/基线及排版验收仍待完成。不是SFD字幕pipeline证据。 |
| 截图3：开场长句 | “测试中文”单独成行，后续正文折行可见；与一个显式$n和后续自动折行相容，不扩展为全部控制符验收。 |
| 下一页末尾：反馈证据 | 长句末尾在下一页显示，未附该页截图；不记录为已复现的丢字或裁切。分页推进不等于切场景。 |
| 未测试项 | 正常存档、正常读取、切场景、战斗、长期稳定性及linked角色名称。 |

**Verified screenshot observation**仅覆盖以上截图可见内容。**Reported observation**覆盖长句末尾下一页显示；该页内容、断点和完整排版未通过截图复核。
三张截图均显示Vulkan、640×447 (1x)、FPS 30、VPS 60、速度100%；PCSX2版本、BIOS、冷启动过程、载入镜像路径及hash未包含在截图中。
本地实验ISO身份见构建身份；截图与三个目标内容的关联属于High-confidence deduction，不作为独立镜像hash验证。

原始截图均为3992×2312，原文件保持不变；副本仅保存于ignored `build/qa-text-14/evidence/`，不进入Git。

| 原始截图文件名 | SHA-256 |
|---|---|
| codex-clipboard-2dd698e3-dd2a-48f2-b7bd-e0477ae9a155.png | `80a3ccd37ef5149f76c4627fdbb436928d7f296622ce12ac554af376f9240483` |
| codex-clipboard-474e4140-b9c4-4d3f-b8f9-c809b1847b5f.png | `691fa5e9b00f13ea6615cd0eab2d429b64717ac79a67cd4165a42cfc3c451fdd` |
| codex-clipboard-99b87aa5-697a-4dcc-a2a8-eda10a2e5e48.png | `28baa344e77dd6092acc1f4b77448aa66d9813c9c12a19716510ce42e32c33aa` |

本轮无需重复完整开场；未测试项保留为后续独立验收。截图不改变共享韩文字形槽的副作用，也不验证独立Font追加后的运行时容量。

## PCSX2测试顺序

1. 确认载入文件为本页所列hash的实验ISO，记录版本、BIOS标识和renderer；先冷启动原版对照，再启动实验版，不使用旧savestate验收。
2. 进入读档列表：空槽提示应显示“测试中文。123ABC”。保存截图，检查中文、标点、ASCII顺序、缺字、重叠及裁切。
3. 开始新游戏并推进开场：seq0应出现“测试中文，。！？“”《》123ABC”标点样本，seq2应出现含$n的长句；分别记录显式换行和自动换行结果。
4. 使用独立memory card，在可存档位置写入、重新启动并读取；记录切场景和战斗表现。
5. 每项单独记录pass/fail；空槽列表不作为正常存档/读档成功证据。出现异常时保留截图/日志，不删正文或改系统地区掩盖问题。

输入、命令与回滚见 [BUILDING.md](../BUILDING.md)；当前限制见 [KNOWN_ISSUES.md](KNOWN_ISSUES.md)。精确事务记录保存于ignored `build/text-poc-02/VERIFICATION.txt`。
