# 新增字形槽PoC — expanded-text-poc-03-udf

日期：2026-10-09。状态：构建、ISO9660/UDF双视图回读与静态验证通过；PCSX2运行时验收未完成。没有新增正式译文，不是发布版。

## 当前阶段与构建身份

中文UI、标点和长句的旧槽PoC已有局部截图；新增字库的Font、UE2包、celfid候选及镜像重建已接通。当前处于最小PoC验收阶段，批量汉化尚未启动。
本版采用D0A1–D0C1追加槽，每Font2667→2700 glyph，原韩文bitmap/metrics与原映射保持；不再覆盖旧B0A1–B0C1韩文槽。旧截图不作为新增槽显示证据。

- 原ISO：SCKA-20043，3210412032 B，SHA-256 `6242476a66a96110fb6ee1a1dd668eedd70d3df6c835f0de9192451b5f4fcd45`，只读保持。
- 候选ISO：`build/expanded-text-poc-03-udf/MODIFIED_FILE.iso`，3232653312 B，SHA-256 `e1cb3fb807fd9cf158bd3147b4ef3e6c2fabafcbc4224319f4a8a8c31445355f`。
- 同样三个原创测试目标：固定UI“测试中文。123ABC”、FPB标点“测试中文，。！？“”《》123ABC”、含一个$n和长句的FPB。沿用现有locale目标文字，实验D0映射来自独立扩容产物，原locale文件不改。
- 原text-poc-02、glyph-poc-01及失败的REJECTED_UDF_RELOCATION样本保留，实验输出均ignored，原ISO/ELF/字体/pcsx2不进入Git。

## 最短运行验收

1. 确认文件为本页新候选ISO，冷启动，不载入旧savestate；记录PCSX2版本、BIOS标识和renderer。
2. 先进入读档列表：四个空槽提示预期显示“测试中文。123ABC”。这一项不需等待完整开场；记录是否能启动、提示可读、缺字/乱码、重叠/裁切。
3. 短UI通过后再检查开场标点、显式$n、长句折行和末尾下一页；分页不算切场景。
4. 正常存档/读取、切场景、战斗、两Font切换与linked角色名仍需独立测试。空槽列表不替代存读档；没有任何项继承旧构建的runtime通过状态。

发生启动失败、卡死或乱码时记录出现阶段及日志，保留新候选和旧PoC对照；不改正文或系统地区掩盖异常。

## 混合镜像修复 — Verified static

复用上游patch_iso/rebuild_afs；`tools/udf_overlay.py`只为已验证布局追加UDF元数据overlay，不另写ISO builder。
支持一个只读物理partition、Type1 map、标准UDF File Entry和单short allocation descriptor；未知结构、ISO/UDF源extent/size不同、CRC/checksum异常及30-bit长度溢出在输出前拒绝。
从原镜像生成patch plan；上游写入后检查descriptor原bytes再应用，不盲目固定偏移套用未知镜像。

| 元数据 | 当前结果 |
|---|---|
| ISO分支 | FILE.AFS relocation、SHIP.AFS in-place |
| FILE.AFS | 22239232 B，ISO与UDF均指向LBA1567584 |
| SHIP.AFS | 45686784 B，两视图仍指向LBA1354095 |
| UDF File Entry | 原位置333/335不动，更新info length、recorded blocks、short AD length/block |
| Partition描述符 | 原主/备位置34/50，长度1567318→1578178 |
| Integrity描述符 | 原位置64，size table同步；closed状态、free-space0及其他字段保持 |
| 新尾部anchor | LBA1578443，复制原anchor的VD引用并更新tag location，另追加2048 B，不覆盖数据 |
| ISO PVD | volume size更新为1578444 sectors |

descriptor CRC长度保持，CRC16与tag checksum重算；未知字段、extended attributes、时间和其他payload保持。原尾部anchor仍保留，新尾部anchor位于扩展partition之外。
ISO9660和UDF都从新候选读回两个完整AFS并匹配本地输出；AFS顺序/metadata、slot0 manifest、两Font身份和UI副本通过既有检查。全镜像比较覆盖原区域，只有目标archive slot、ISO目录/PVD与计划UDF descriptor改变；追加区域为FILE数据、padding和新anchor。
12项新增合成UDF测试覆盖增长/缩短、双视图payload、partition/integrity、anchor、CRC/checksum、tamper与写入前条件；工程254项通过。干净源码重建同一ISOhash，独立ISO副本回滚恢复原ISOhash；修改ISO保持。

**Verified static**：上述结构、双视图回读和可复现构建。
**High-confidence deduction**：同步两视图消除已复现的旧extent/size和尾部anchor不一致；结构修复不证明PS2启动缓存接受增长Font。
**Unverified hypothesis**：本版PCSX2启动、D0字形显示、布局与缓存容量、存读档和场景稳定性。完整celfid加载语义仍未通过运行时trace核验。

## 复现与下一阶段

依次运行BUILDING.md中的Font扩容、package、bundle和expanded locale命令。字体仍为hash锁定的本地SimHei，资源不分发；发布级字体许可方案仍需完成。
事务保存在ignored `build/udf-overlay-17/VERIFICATION.txt`；旧UDF预检失败与失败镜像不删除，见 [历史失败](FONT_BUNDLE.md)。
新增槽显示及最小存读档/场景/linked名称门禁通过后，开始已确认parser覆盖的少量UI/剧情正式试译；再扩大批次，不要求先穷尽全部逆向。

## 构建链后续验证（2026-10-09）

一键构建和不依赖构建报告的二次推导已复现本页同一ISOhash，284项测试通过，隔离ELF tamper已检测。自动生成QA清单的全部运行时状态为untested，不转移旧截图结论；本页候选保留，测试同hash副本无需增加轮次。见 [一键构建与验收入口](POC_PIPELINE.md)。
