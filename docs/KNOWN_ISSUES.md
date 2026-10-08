# Known Issues

研究状态：尚无可玩zh-CN构建。以下是验收缺口，不声称是已复现的中文游戏崩溃。

| 项目 | 状态 | 证据/下一步 |
|---|---|---|
| 中文显示/无乱码/不崩溃 | Partial observation | 读档UI截图显示“测”；完整字集、冷启动与长期稳定性待测 |
| 共享字形槽副作用 | Expected in PoC | 原“가”对应B0A1均显示“测”，不是正式译文；下一阶段需稳定locale mapping |
| 字宽/自动换行/标点/两font切换 | Open | bitmap/width候选已定位，runtime trace pending |
| mapping稳定/容量扩展 | Static PoC | 33字显式map重排不重分配；运行时全范围、跨场景稳定与扩容未知 |
| 小字集实验text-poc-02 | Runtime pending | 3个测试目标静态通过，新版本中文/标点/长句/固定UI槽尚无运行时截图 |
|存档/切场景/战斗回归|Open|未做中文PCSX2测试，不宣称兼容|
|完整韩文资源/linked dependency mapping|Investigating|FPB/slots/region/celfid数据性质分别见研究报告|
|USA/JP binary比较|Deferred|相应版本ISO未纳入研究输入，不作为KR PoC硬依赖；仅引用上游encoding choices|
|生产ISO命令Windows路径|Verified static|pycdlib metadata fallback与实际KR ISO两处in-place已通过；runtime仍待测|
|FILE manifest stale|Fixed in PoC static|PoC同步celfid压缩长度，保留其他manifest记录；runtime影响待测|
|SFD时长/时间戳/中文字幕|Investigating|180216静态音频一致，0.103944s drift与warning；中文ASS/游戏同步未验收|
|大规模翻译/Release|Not started|PoC门禁与阶段验收完成后才能进入批量翻译|

测试须记录PCSX2版本/backend/BIOS、原版与测试版hash、冷启动、截图和每个验收项；不能只用savestate或静态测试代替。
