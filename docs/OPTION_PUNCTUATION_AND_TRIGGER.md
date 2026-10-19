# 选择项句号与温蒂妮触发排查（2026-10-19）

## Verified

上轮 stage180 按资源扩展名分类，把 FPB 全部归为剧情，漏掉选择项。此次逐条核对剩余941个 FPB 单句候选，显式绑定37个选择项（8道场各4项、乘坐1、购买2、确认2）及6个不带其他标点的商店折扣状态，共43字段/14资源。选择项并不因储存在剧情批次中而属于对白。相邻剧情、NPC发言、ECD/FDS人物发言和已有多片段提示保持。带逗号的“不，不乘坐。”保留句号；问号/感叹号/省略号不变。含百分号/引号/括号等其他标点的字段不纳入本次无其他标点规则，不作全局字符替换。

数据：`locales/zh-CN/proofreading/option-punctuation-review.json`，每条含源hash、native key、前后文角色、旧/新译文。源翻译批次同步，非目标对白不改。`single_clause_period` 实现现行严格条件；旧 stage180 `omit_period` 的行为保留以重放历史配方，不用旧配方自动分类新文本。

原生FPB是 count、count组(key,offset,length)、pool_size、pool。新工具按实际native key与原字节hash绑定，而不是把key当物理序号；检查现有目标字节，去掉句号后重建offset/length/pool_size，保持所有key、未选文本、空隙及tail。只SHIP.AFS变化；14资源没有启动缓存镜像，FILE/LINEAR/ELF/46影片保持。镜像通过ISO9660/UDF和非目标字节独立比对，字体/布局不回退。

## 温蒂妮：已观察事实与尚待确认

用户报告隐身开启后无法被温蒂妮发现，关闭后重新进图仍不触发。所保存即时存档中共享开关000C3FE0=0，但003F72C0/003F72C4/003F746C/003F7470四处仍为1000002C/00000000/10000054/00000000。对应原版应为8E240268/8C830220/8C900268/8F868258。因此“开关值关闭”不等于“发现指令已恢复”，此残留已由真实即时存档验证。

关闭作弊总开关后，逐帧恢复指令也不会继续执行。进出地图不重新加载ELF；即时存档保存EE内存并会重新引入旧跳转。恢复流程：保持作弊总开关与内部控制有效时，SELECT+下让OFF恢复执行；或完全结束游戏，禁用隐身后冷启动，再读取游戏内存档。不要用旧即时存档验证冷启动。

`tools/repair_detection_state.py` 校验完整原版ELF指纹，读取p2s ZIP，仅在四处为已知原版/隐身指令时在新副本恢复原指令，其他ZIP成员逐一回读一致。它不写剧情旗标、不覆盖用户存档、不证明碰撞/距离/剧情条件已经满足。真实存档副本修复前4处残留，修复后0处。

后续纠正（2026-10-19）：四处隐身残留确实存在于旧现场，但恢复它们仍未触发。原版韩语、无补丁的新现场也复现；进一步确认首次遭遇要求物品497「冰之世界」数量<1，而存档提前持有1个。仅删除该记录的副本已由用户实测进入首次战斗，详见 [UNDINE_EVENT_TRIGGER.md](UNDINE_EVENT_TRIGGER.md)。因此隐身残留不是本次卡关的充分解释，也不据此宣称其他玩家均由作弊引起。

## 重建与验证

先用当前镜像提取SHIP.AFS和FILE中的celfid.lix，核验review所有源字段与基线目标，确认14个选中资源在解压启动bundle中均无完整镜像。实际提取/回填/ISO双视图流程保存在 `work/option-trigger-196/build.py`，输入/输出hash在 `iso-report.json`。归档回填可独立重放：

```powershell
work/venv/Scripts/python.exe -X utf8 tools/patch_option_periods.py --original-ship work/kr/SHIP.AFS --original-sha256 09d2e4d1f72e40b5d12da7b872226c446a21dde12bf1601bb4dfe58887a5d33a --base-ship work/option-trigger-196/baseline-SHIP.AFS --base-sha256 a5da1484684ee925f43dc0da9ce9d9ccf65f7499230b6bca207cb1a1299c3b90 --review locales/zh-CN/proofreading/option-punctuation-review.json --map work/font-default-184/default-fonts/experimental-map.json --font work/ui-line-audit-193/NormalFont.bin --out work/option-trigger-196/reproduced-SHIP.AFS
work/venv/Scripts/python.exe -X utf8 tools/repair_detection_state.py --elf work/kr/SCKA_200.43 --state work/option-trigger-196/baseline.p2s --out work/option-trigger-196/new-restored.p2s --report work/option-trigger-196/new-state-report.json
work/venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -q
```

hash槽使用该次输入的SHA256；未知版本/旧目标不匹配即失败。仅用SHIP回填工具不会替调用者验证外部缓存，调用者必须完成上述缓存门禁。不重复生成或分发完整游戏资产。

基线、修改、独立回滚的逐条命令/字面输出/退出码与四产物在 `work/option-trigger-196/VERIFICATION.txt`。回滚使用压缩的原始差异块和完整旧/新镜像hash，拒绝不匹配输入；在另一个副本实测恢复旧镜像，不长期保留第三份ISO。

## 当前交付身份

候选镜像：`work/option-trigger-196/MODIFIED_FILE.iso`，SHA256 `226bb9116dc873c024d742c377d0a4fecaec6a0648bf4fd81e31709a19064e6b`。用户仍在测试温蒂妮，故本轮不覆盖当前打开的 movies-fixed.iso（旧hash `ee81e78ce1f7461ab39cfbf68773966529d4ef4a11de3212adc4b5ff7d7d8226`）。候选作为本轮唯一临时第三镜像保留；独立回滚测试副本不长期保留。待用户结束游戏后再替换当前测试镜像并恢复两ISO留存策略。

## 2026-10-19 清理后的镜像位置

上述候选已移动到固定测试入口 `build/test-iso/Magna-Carta-Tears-of-Blood-zh-CN-movies-fixed.iso`，SHA256 `226bb9116dc873c024d742c377d0a4fecaec6a0648bf4fd81e31709a19064e6b`。旧ee81测试镜像已替换，work下不再保留第三份ISO；原始构建报告仍记录当时的历史路径，新位置由work/option-trigger-196/ARTIFACT_LOCATION.json指明。当前只有1份测试ISO，另保留根目录原版开发输入。
