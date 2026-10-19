# 普通PS2记忆卡：受指纹约束的物品移除

## Verified（2026-10-19）

本次用户提供的Mcd001.ps2为8650752字节，原始SHA256 `884416653641aabbf9c51a850e51d163a7cf9ce5fccaf894be0371b7136e9348`。本工具只写另一个新副本，不改已挂载的记忆卡、游戏ISO或用户源文件。

目标文件：`/BKSCKA-20043_Save_00/BKSCKA-20043_Save_00`，版本43。33个卡内文件中仅此文件内容改变；另外32文件的路径和完整字节保持。MrtsSummary、MrtsVersion和图标也保持不变。

这个具体文件由连续的压缩块组成，每块为小端u32解压长度、小端u32压缩长度、对应zlib数据。原始块长20480和9832，合计30312字节。检查每块边界、zlib结束及解压长度后合并处理，再按最大20480字节重分块，并由zlib重算流校验。

本现场背包数组计数位于解压流0x69，UE compact正数288编码6004；记录从0x6b起，步长8，格式为小端i32(ID,Count)。全部288条与此前已检查的现场EE背包逐字节一致。索引278/流偏移0x91b是唯一物品497、数量1。计数改为287（5f04），删除该8字节记录，余下序列前后缀保持；重分块后的解压总长度30304。不修改第二处出现的497：它不属于此目标背包数组。

验证：保留其他287条顺序/数量；将记录和计数逆向还原后整个解压流与原始完全相等。卡文件系统检查通过，13个发生变化的物理页，其512字节数据对应的12字节ECC均独立重算完全相等。另一个副本回滚后整卡SHA256恢复原样，交付修改版仍保持改变。

修改版整卡SHA256 `fbddb3e88427b67d202b7e143691bd79026fbccd7be47c4409bff4558c94f5ab`。不把静态结构验证当成游戏内读取/触发验收；这张普通记忆卡仍待用户测试。

## 重放接口

```powershell
work/venv/Scripts/python.exe -X utf8 tools/repair_card_item.py --card INPUT.ps2 --profile REVIEWED_PROFILE.json --mymc-root PATH_TO_PINNED_MYMC_PY --out work/repaired-card.ps2 --report work/card-report.json
work/venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -q
```

Profile schema1绑定card_sha256、save_path、save_sha256、unpacked_sha256、version、count_offset、count、index、item_id、quantity、inventory_sha256。所有偏移由对应现场检查取得；拒绝未知输入、重复键、非正数记录、原数量不符、已有输出或报告覆盖输入。工具从卡目录重新读取全部文件并核对；通用代码不硬编码中文名或此存档偏移。

实例输入、profile、四项产物及确切命令/输出/退出状态位于被忽略的 `work/card-item-198/`。完整记忆卡、原始存档和游戏资产不提交。

## 上游与复用

卡文件系统读写及ECC依赖调用者提供的 [G4brym/mymc-py](https://github.com/G4brym/mymc-py)，本次固定提交 `0b9380399447f722e93461b440cbc480699ea05c`。维护者Gabriel Massadas；其README记载这是Ross Ridge的mymc移植；仓库MIT许可，原mymc为public domain。此项目未复制其代码，依赖位于忽略的work checkout。独立新增的是当前游戏压缩存档的指纹绑定、选中数组记录移除、全卡其他文件核对及本次差异页ECC重算验证；不把上游文件系统/ECC发现归为本项目原创。

## 手工测试

结束当前游戏后，在PCSX2记忆卡设置中将修改版插入槽1，从游戏标题画面读取卡内存档，不加载旧即时存档。检查物品列表及温蒂妮触发；原始卡单独保留。此操作仅用于验证本份存档，不是面向所有玩家的原版事件全局补丁。
