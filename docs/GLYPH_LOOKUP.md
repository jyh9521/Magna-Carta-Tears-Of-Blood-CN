# 韩版字符→glyph查表模型

日期：2026-10-09。状态：Verified offline model；不是PCSX2验收，也不是可发布的字库扩容。
工具：`tools/research_glyph_lookup.py`。上游AFS、UE2 export读取与既有韩版字体解析继续复用，没有重写容器。

## Verified — 版本锁定指令片段

原ISO与ELF使用既有SCKA-20043完整SHA-256门禁。片段VA为`0x0020EE80`，长度212 B，SHA-256为`e8131662342bdf12c1bd0688559d97efb68caff7e06356d3108f616511036c22`。
No font候选周边`0x273304`直接调用`0x272540`；该邻域的`0x272740`与`0x2727BC`直接调用本片段。另一渲染候选`0x271584`也调用本片段。
这些是静态直接调用关系，不表示完整native签名绑定、函数可达路径或实际Font实例已确认。

片段包含以下读字段与运算：

| 字段/路径 | 静态指令含义 |
|---|---|
| 对象+0x4C | u32分支值；为零时直接返回首字节的LB结果 |
| 首字节bit7 | 非零分支值下，bit7为零仍直接返回首字节 |
| 双字节值 | 高字节先出现，拼成`(first & 0xFF)<<8 | second`，低16位参与查表 |
| 对象+0x74 | u16范围起点数组pointer |
| 对象+0x80 | u16 glyph base数组pointer |
| 对象+0x84 | 动态范围条目数 |
| 未命中 | 返回index63 |
| 命中 | 返回`base[row] + code - range[row]`的低16位 |

有效区段长度由`base[row+1]-base[row]`决定；下一范围起点用于先选择区段，然后排除区段之间的gap。末尾范围/base起哨兵作用。
该片段本身不解析CP949语言语义或UTF-8；它组合字节后查询定制表。byte兼容CP949资源不等于引擎调用完整CP949解码器。

## Verified offline model — 原表与现有PoC

模型只支持该片段用到的ADDIU、ANDI、LUI、SLL、ADDU、SUBU、OR、SLT、LB/LBU/LHU/LW、BEQ/BNE及JR低32位语义，并执行classic delay slot。
共享指令语义参考 [MIPS Technologies Volume II-A Rev3.00](https://pages.hmc.edu/harris/class/e155/11/MIPS32InstructionSet.pdf)；模型不是完整R5900实现，不模拟cache、时序、浮点、异常或PS2设备。
代码与数据区域只读、互不重叠；未知指令、越界读取、非对齐访问、delay slot内控制转移和超出步数预算均拒绝。
自动测试只含合成指令，不在Git保存原版片段；实际指令从已知ISO内存读取并核对独立hash。

合成对象设置+0x4C为1，注入原版两Font各自的范围/base表；对象构造过程与实际游戏实例尚未完成动态验证。

| 每套Font | 结果 |
|---|---|
| 2411个双字节成员（61个首段+2350个韩文槽） | 全部返回预期index256–2666 |
| 128个ASCII输入0x00–0x7F | 全部返回自身index |
| 29个gap/上下边界样本 | 全部返回63 |
| 当前zh-CN map的33个编码 | 全部返回既定glyph317–349 |
| +0x4C为零、首字节B0 | 返回低32位0xFFFFFFB0，属于LB结果；未分析所有调用方归一化 |

原表成员最大执行步数272，默认预算1024。上述是原指令片段的离线执行结果，不是实际游戏显示、缺字或换行验收。

## Verified offline model — 合成范围扩展

保留原27个范围/base条目，额外添加D0A1/base2667和D0FF/base2761，得到29个条目。
两Font的模型均将D0A1–D0FE全部94个编码映射为glyph2667–2760。原Font资源仍只有2667个glyph，没有新增bitmap或metric，没有写回range/base。
该实验仅验证片段使用动态范围数且能计算原数量之外的index，不证明渲染器、字体加载器或atlas/cache能容纳这些index。
D0范围仅是隔离模型输入，不是正式locale分配规则；不能据此自动重编码现有map。

## High-confidence deduction / Unverified hypothesis

韩版自定义双字节+动态范围模型可作为中文编码层基础，不需要先将所有文本转换为UTF-8或GBK，也不需要在通用parser中硬编码Chinese名称。
查表片段没有固定2667 glyph数量，但最终命中index及表元素使用16位；这不是全引擎容量上限的完整证明。
后续优先核对字体加载时的数组构造、glyph数量与metrics读取、glyph page划分、缓存和越界检查，再决定是否实现扩容PoC。
USA/KR混合路线、真实Font实例+0x4C值、其他字符解码路径、双字节前进和自动换行仍未完成验证。
原ISO、ELF、当前PoC、locale映射与译文保持。没有新增PCSX2测试，没有批量翻译。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/research_glyph_lookup.py --iso "<original-KR-ISO-path>" --out work/glyph-lookup
```

从原ISO提取ELF至内存，FILE.AFS只写ignored输出目录，复用上游读取MrtsEngine.u及两Font；engine/font身份均校验。分析后复核原ISOhash。
输出只包含hash、地址、对象字段与统计，不导出原版bitmap或完整ELF。locale可用`--locale`显式指定mapped数据。
新增17项合成测试，工程148项通过；基线131项与独立源码回滚分别记录于ignored `build/glyph-lookup-10/VERIFICATION.txt`。
