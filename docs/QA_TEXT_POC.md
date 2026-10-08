# 小字集文本PoC — text-poc-02

日期：2026-10-08。状态：构建和静态验证通过；此构建的PCSX2验收尚未完成，不是正式中文补丁。
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
**High-confidence deduction**：id176对应读档空槽提示；现有双字节映射可扩展到这33字。前者依据字段原文与旧截图，后者依据字节结构及旧单字观察，仍需此ISO实测。
**Unverified hypothesis**：此版本所有字形显示、标点/ASCII混排、长句自动换行、advance与基线、剧情触发、跨场景稳定性、正常存档与读取。

## PCSX2测试顺序

1. 确认载入文件为本页所列hash的实验ISO，记录版本、BIOS标识和renderer；先冷启动原版对照，再启动实验版，不使用旧savestate验收。
2. 进入读档列表：空槽提示应显示“测试中文。123ABC”。保存截图，检查中文、标点、ASCII顺序、缺字、重叠及裁切。
3. 开始新游戏并推进开场：seq0应出现“测试中文，。！？“”《》123ABC”标点样本，seq2应出现含$n的长句；分别记录显式换行和自动换行结果。
4. 使用独立memory card，在可存档位置写入、重新启动并读取；记录切场景和战斗表现。
5. 每项单独记录pass/fail；空槽列表不作为正常存档/读档成功证据。出现异常时保留截图/日志，不删正文或改系统地区掩盖问题。

输入、命令与回滚见 [BUILDING.md](../BUILDING.md)；当前限制见 [KNOWN_ISSUES.md](KNOWN_ISSUES.md)。精确事务记录保存于ignored `build/text-poc-02/VERIFICATION.txt`。
