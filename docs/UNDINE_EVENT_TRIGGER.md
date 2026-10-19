# 温蒂妮首次遭遇：存档物品条件诊断（2026-10-19）

## Verified：本次存档的阻塞条件与游戏内验收

用户在原版韩语 ISO、全部作弊及补丁关闭的现场保存槽2。16个已知补丁指令位置均为原版；移除旧隐身跳转不是此现场的解决方法。玩家位于区域20024，队伍类型1，GSW[10]=5，但提前持有1个物品497「冰之世界」（韩文 얼음의 세계）。物品标识497是资源源键，不是物理记录序号305。

已加载事件 Plan16 的首次遭遇条件是：

```text
GSW[10] >= 5 AND GSW[10] < 7
AND 当前玩家位于区域20024
AND Calintz队伍的物品497数量 < 1
AND 当前队伍类型 == 1
```

本现场只有物品数量条件失败。条件满足后设置局部开关21=5，Plan2设置GSW[10]=6并启动战斗3242，战斗后走GSW[10]=7路径。后续持有该物品的剧情另需GSW[12]>=1，本现场为0，所以也没有进入后续分支。不要以持有物品为依据直接跳改剧情旗标。

附近人物是CharPlacement键20025、角色520的MrtsGamePlug，而非8个普通MrtsNpcMonsterPlug中的一个。当前地图1778、父地图1675、FieldID5946；人物可以穿过本身不足以证明发现代码损坏。

修复副本删除288条背包记录中索引278的唯一物品497记录，保留其余287条的顺序和数量。FArray数量288→287，容量和未使用尾部保持，EE内存仅14字节不同；剧情开关、代码、人物、坐标及其他ZIP成员逐一比较一致。没有全局修改游戏事件或ISO。

**游戏内验收：用户加载该副本，明确回复「已进入首次战斗」。** 这确认了本次存档的首次遭遇恢复。首战结束、通讯球后续联络与最终正常保存尚未验收，不能从首次战斗启动推定全部后续剧情成功。

## 原生代码证据

支持ELF SHA256：`35cc6048f0e1f68d06bf3e515b99de3263e5092be62d6215cff5e74aa0ea15f0`。

- `0x3758c0`/`0x375af0`：事件条件分派；101为全局开关、104为队伍类型
- `0x376210`：读取GlobalEvent.Switches；`0x376250`：读取队伍类型
- `0x38adc0`分派204至`0x38b7d0`，参数1选择Calintz队伍
- `0x3a0f80..0x3a0fc4`：GetItemCount遍历步长8的(ID,Count)记录，未找到返回0
- `0x338a20`比较分派、`0x4b94c0`跳转表：六个比较依次为 ==、<、<=、>、>=、!=；本条件选择1，即 <
- `0x39fb60`原生消耗物品路径在数量为0时调用FArray.Remove(index,1,8)，因此副本删除记录而不是在活跃数组中遗留零数量记录

复用了仓库有界标量指令执行器，在实际EE内存输入上执行原生GetItemCount与比较分支：修改前数量1/条件false，修改后数量0/条件true；独立216组比较用例通过。这是有界原指令验证，不是完整模拟器运行；游戏内验收另由上述用户回复确认。

## 可复现、只写副本的工具

`tools/audit_event_snapshot.py`以用户提供的即时存档和原版ELF为输入，动态恢复FName表、对象及反射属性，输出地图、人物、背包、事件和已知补丁点。它仅支持上述ELF，不向现场写入数据。报告包含原始游戏数据，应保留在被忽略的work目录，不提交完整报告或资产。

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_event_snapshot.py --state INPUT.p2s --elf ORIGINAL_ELF --out work/event-audit.json
work/venv/Scripts/python.exe -X utf8 tools/repair_event_item_state.py --state INPUT.p2s --profile REVIEWED_PROFILE.json --elf ORIGINAL_ELF --out work/repaired.p2s --report work/repair-report.json
work/venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -q
```

Profile schema1必须经检查绑定：state_sha256、memory_sha256、elf_sha256、inventory_array_offset、inventory_data_offset、inventory_count、inventory_index、item_id、expected_quantity。地址必须来自该份报告与现场检查，不可对其他存档照抄。工具校验完整输入hash、数组几何、唯一物品与正数数量，拒绝覆盖已有输出，回读全部ZIP成员并确认原文件不变。

本次原始状态SHA256：`2b062d63ee670dcf9513768c5bb3dd06a921a2f6fcaae09e2d3e0d91b0f7aa7d`；修复副本SHA256：`2fc93738583036683acf33754a4ba60cbf0efec6b06cefc62d3886c99810fc2a`。现场profile、差异、静态及运行验收、原样回滚证据保存在 `work/undine-trigger-197/`；不提交完整即时存档。

## 未验证假说与适用边界

额外物品为何提前存在尚未确定。物品不减作弊可能造成类似状态，但没有证明本次物品来源，也不能据此推断其他从未作弊玩家的原因。历史论坛的相似症状不能替代对其存档条件的检查。此次修复只对已绑定的单份存档成立。

保持作弊关闭，正常完成首战并检查通讯球后续联络，再写入正常游戏内存档。旧卡关即时存档仍包含旧背包，不应在推进后重新加载。
