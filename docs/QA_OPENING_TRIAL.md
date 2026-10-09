# 开场与存档UI有界试译 — opening-trial-01

日期：2026-10-09。状态：Verified static；本版本PCSX2未验收。译文为试译草稿，不是全文汉化或发布版。

## 构建身份

- ISO：build/opening-trial-01/runnable/image/MODIFIED_FILE.iso。
- 3232739328 B；SHA-256：ebb3a71de5b90d1f446fe7628283eef1dded6c111d77f9ffc474624b5f9c6ff3。
- 配置：locales/zh-CN/opening-trial-01.json；字符库存：locales/zh-CN/opening-characters.json。
- 原版ISO、ELF、两份此前测试镜像和此前locale保持；本轮仅新增一份ISO，无完整镜像回滚副本。

## 实际覆盖

| 资源 | 修改范围 | 条数 | 缓存副本 |
|---|---|---:|---:|
| SHIP/00001944.fpb | seq0–8，首段开场对白 | 9 | 0 |
| SHIP/00004060.fpb | seq0–12，露营/友好度教程 | 13 | 0 |
| SHIP/00001240.tui | 显式选择的菜单/操作/存档提示，首256 B字段 | 69 | 1 |
| SHIP/00000460.cha | slot0首姓名字段，暂定“卡琳兹” | 1 | 1 |

正文共91字段，加1个姓名字段。六个菜单页签字段可能与纹理查找有关，保留原字节；草稿仅列在deferred_texture_labels，不应用到游戏。TUI其余174条记录、全部次256 B字段、CHA其余300条记录、其他FPB均保持。旧测试串替换为实际对白/提示；没有全局姓名替换，也没有把角色说明identifier翻译进运行时。

开场第一句：“哈……哈……哈……哈……”。首段对白到seq8的回忆旁白结束；不代表后续全部开头剧情已汉化。露营教程的出现时机和地点未确认，资源编号不当作剧情时序证明。

原文露营教程明确说明：靠近存档点，按○键进入露营模式；可选择同伴交谈或送礼。其他已提取原文亦说明露营模式支持存档，但未在本候选中修改该其他资源。存档点具体位置不作推测。

### UI范围与局限

存档/读取/覆盖/完成/失败、记忆卡检查/空间/格式化、是/否、取消/确定、休息/交谈/送礼/保存/读取及部分菜单字段已试译。菜单图片文字可能来自LINEAR纹理，即使TUI同文已改也可能保持韩文；不能宣称主菜单已全中文。

未修改物品名、装备名、其他角色名、地点导航、战斗教程整体、SFD/CG或其字幕。未清除格式标记、数字80KB、PS2等运行时文本成分。译文未经过完整上下文校对。

## 字库与构建

保留旧33字库存顺序，新增所需字符后总317个；两Font各2667→2984 glyph，原bitmap、metrics和原映射保持。新增编码分四段：D0A1–D0FE、D1A1–D1FE、D2A1–D2FE、D3A1–D3C3。每段保留sentinel和间隔；不跨trail-byte=00。完整原码、ASCII及317个新码离线查表通过，不等于新字集游戏内全部通过。

资源按完整SHA-256绑定；FPB另校验原窗口hash，复用原parser/builder重算offset/length。TUI按record id/index、256 B源字段hash锚定，保留NUL和第二字段；控制符数量/值/顺序保持。UI宽度预算440为候选估算门禁，不是已测窗口宽度，需实际画面确认裁切/换行。

UE2/celfid、AFS、slot0 manifest、ISO relocation沿用既有实现；有限UDF同步和独立再推导通过。FILE一次relocation、SHIP一次in-place。独立验证以原ISO＋外部字体＋locale推导完整资源，不信任构建receipt。

```powershell
work/venv/Scripts/python.exe -X utf8 tools/build_poc_pipeline.py --iso "<original-KR-ISO-path>" --font "<matching-font-path>" --locale locales/zh-CN/opening-trial-01.json --out build/opening-trial-new
```

输出目录必须新空目录；不需要旧work/kr提取资源。系统SimHei仍限本地实验，未分发字体或原资源。

## 测试步骤

1. 冷启动上述新ISO，检查空存档槽“没有存档。”；不要载入旧即时存档验收。
2. 新游戏检查首段真实中文对白、$n和字幕分页。首段之后韩文仍属本批次未覆盖，不标记为丢失译文。
3. 主角菜单预期“卡琳兹”；检查新增字形是否正常、UI是否重叠或裁切。译名为暂定，未作全项目术语定稿。
4. 继续推进至实际存档点，按○键进入露营模式；保存后关闭游戏，再启动同一ISO读取正常存档。保存与读取结果分别记录。
5. 场景切换、战斗、正常存档后的姓名显示和新增范围缓存稳定性单独登记。若存档点前仍有阻碍理解的韩文对白/提示，记录画面用于下一批资源定位，不按未证实的编号顺序全库翻译。

QA_CHECKLIST.json初始98项untested（91正文＋1姓名＋6运行项目），不能从旧截图自动升级。PCSX2版本、BIOS标识、renderer与画面证据另行填写。

**Verified static**：源身份、受控字段、控制符、原字形保持、多段查表、资源回读、AFS/manifest、ISO/UDF和独立推导。

**High-confidence deduction**：存档提示及露营教程试译可以减少回归测试的语言障碍；TUI副本同步能覆盖先前已观察的空存档提示路径。

**Unverified hypothesis**：新317字集的所有实际渲染、窗口宽度、所有菜单字段可见性、教程时序、实际存档点到达流程、存读档/场景/战斗稳定性。

## 验证记录

369项自动测试和干净索引源码369项通过；干净源码独立复核同一新ISOhash，未重建第二份ISO。旧名称候选在新工具下保持a47d5b…hash并通过独立验证。独立源码回归恢复353项基线，Font工具在独立副本恢复原字节，修改源码保留；未执行整盘回滚。直接回读确认243个TUI id/第二字段及6个暂缓页签记录保持。实际98项QA记录校验为pending，不是运行通过。精确命令、literal输出、退出状态及四个小型事务文件位于ignored build/opening-trial-01/VERIFICATION.txt。
