# Font metric consumer与加载候选

## 范围与来源

SCKA-20043原ELF保持，复用上游AFS/UE2读取、现有版本门禁、Font parser和有限调用参数推演。新增`tools/research_font_metrics.py`只读原ISO，输出hash、统计和局部参数，不输出原指令或font bitmap。ISA标量语义沿用 [MIPS32 Volume II-A](https://pages.hmc.edu/harris/class/e155/11/MIPS32InstructionSet.pdf)；R5900乘除/FPU未加入模型。

## Verified static — 模式分支

`0x272730`从r20+0x4C读word；`0x272734`在非零时跳至`0x2727BC`，delay `0x272738`仍执行。零分支进入`0x27273C`，通过传统page/record路径取值；非零分支调用`0x20EE80`查表，然后进入以下metric路径。

`0x2727C4..0x2727D8`包含：从+0x68读pointer、将glyph返回值ANDI 0xFFFF、从+0x54读辅助word并保存至sp+0xE0、pointer加index、LBU读取单字节metric，随后保存至sp+0xF0。+0x54的具体语义仍未确认，不标注为runtime height或glyph count。

该路径没有把glyph截为8位。另一候选`0x271584/0x2715F4`之后存在ANDI 0xFF；其入口选择与实际调用覆盖未确认，不能将这几处掩码当成全引擎统一限制，也不能直接删除。

| 片段 | 长度 | SHA256 |
|---|---:|---|
| metric 0x2727C4 | 24 B | e533b6ce738e1c72655700bbe54148a810075dafdbca10ae17e032ddc4c1089d |
| mode branch 0x272730 | 12 B | 8b3f06673b6d36fd19f206d3037b3040dfe348c02f20371b06da5cfa5cbc1190 |
| serializer邻域0x20F148 | 352 B | e374819856b35e10e62d654943b3dc6b249cb4959780ac8e3c3b988e39fa07ed |

## Verified offline model — 原metric数组

模型执行24 B片段中的五条标量指令；中间SW不执行，但其opcode、base、source和offset严格校验。没有修改原片段，也没有补造JR。辅助+0x54合成值为0，其实际语义不参与metric结果证明。合成对象+0x68指向原Font解析得到的metric bytes，内存长度严格等于2667 B，不添加padding。

两Font各2667个index逐项读取原metric byte通过，包含255以上index；metric均为无符号0–19。NormalFont有2353项值16、158项值19；KatakanaFont有2444项值19。完整直方图保存在ignored JSON。

index2667被模型以`unmapped model memory`拒绝。这是模型内存边界，不是引擎主动越界检查：该局部路径只有16位掩码与LBU，没有glyph count比较。真实扩容必须同步metrics与其他相关容量，不能只扩range/base。

## Verified static — 加载候选参数

serializer邻域的五处JALR使用对象+0x14槽，a1依次为r21+0x4C/+0x50/+0x54/+0x58/+0x5C，a2在delay slot设为4；目标及实际reader仍为条件表达式。

后续JAL `0x20F250`目标0x126E10、a1=r21+0x68；`0x20F25C`与`0x20F268`目标0x127380、a1分别为+0x74和+0x80。三者参数形状与metric/range/base三数组相容，但有限窗口没有证明运行时对象身份、包版本分支或完整反序列化布局。`0x20F1E0`调用0x1B3E80并传+0x64；该helper包含archive状态分支，不能直接将+0x64强命名为文件中的row stride。

## High-confidence deduction

+0x68单字节数组承担双字节路径的横向字宽/advance数据：LBU结果进入sp+0xF0并在`0x2727F8`后参与浮点/整数宽度累加。原候选metrics与原指令取值相容；真实实例尚未采样，仍不属于PCSX2字宽验收。

## Unverified hypothesis与下一步

两Font真实加载优先级、+0x54含义、bitmap加载与atlas/cache容量、另一8位路径用途、浮点缩放/换行、save与切场景仍待核对。下一步继续追踪+0x60 bitmap消费者和Font对象构造，不实施盲目掩码patch，不扩充生产字库，不增加批量译文。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/research_font_metrics.py --iso "<original-KR-ISO-path>" --out work/font-metrics
```

新增15项合成测试，工程163项通过；原ISO完整hash在分析前后复核。现有小字集PoC ISO、ELF和locale数据保持；没有新增PCSX2验收。
