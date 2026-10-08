# 韩版 ELF 与 native 文本线索

日期：2026-10-08。状态：Verified static / 候选地址；未定位完整字符解码和字宽算法，没有ELF patch。
工具：`tools/research_native.py`，从版本锁定ISO只读提取ELF至内存，不依赖旧work中间文件，不写回游戏输入。

## Verified — 输入与映射

- ISO：SCKA-20043，SHA-256 `6242476a66a96110fb6ee1a1dd668eedd70d3df6c835f0de9192451b5f4fcd45`。
- ELF：4439344 B，SHA-256 `35cc6048f0e1f68d06bf3e515b99de3263e5092be62d6215cff5e74aa0ea15f0`；ELF32 little-endian、machine8，entry `0x00100008`。
- 首个PT_LOAD：文件offset `0x80`，VA `0x00100000`，filesz `0x43BB00`，memsz `0x4EC600`，flags7。
- 第二个PT_LOAD：VA `0x005EC600`，file/memory长度均0。
- 8个section；`.symtab`和`.strtab`长度均0，没有有效符号条目。

文件背书区间为VA `[0x00100000,0x0053BB00)`；首段其余memory区域不映射到ELF文件字节。
地址转换仅接受唯一PT_LOAD文件背书映射，拒绝将内存尾部当作文件offset。
首段同时含代码、字符串和表，flags7及可解码指令形状不证明某地址必然是可执行函数入口。
格式映射规则依据 [System V ELF ABI的Program Header](https://gabi.xinuos.com/elf/07-pheader.html)；指令字段参考 [MIPS Technologies架构手册](https://www.ece.lsu.edu/ee4720/mips32v1.pdf)。

## Verified — 标识符与数字引用

提取限定文本相关标识符23个：11个UIText资源路径、2个No font诊断串、UFontObj及9个native签名标识。
找到9个与标识符VA相等的对齐u32词；它们是数据引用，不直接当作函数地址。

| 标识符 | 匹配pointer word的VA |
|---|---|
| intUObjectexecUnicodeStringConst | 0x0047BDA0 |
| intUFontObjexecIsTextSet | 0x0048BBC0 |
| intUFontObjexecDestroy | 0x0048BBD0 |
| intUFontObjexecSetText | 0x0048BBE0 |
| intUFontObjexecSetFont | 0x0048BBF0 |
| intUCanvasexecDrawTextClipped | 0x0048BDC0 |
| intUCanvasexecDrawText | 0x0048BE00 |
| intUCanvasexecStrLen | 0x0048BE10 |
| intUMrtsDynamicTextAreaexecMrtsDrawTextLine | 0x0048DA20 |

有限LUI+ADDIU/ORI模式找到13处地址构造候选：11个UIText路径和2个No font诊断。
扫描最多8条后续word，遇未知操作、基址寄存器覆盖或普通branch停止；JAL仅额外检查紧随的delay slot。
这是保守数字模式，不是完整R5900反汇编或完整xref；未报告不表示没有引用。

| 标识符 | LUI候选VA | 对应lower候选VA |
|---|---|---|
| DrawText: No font | 0x00273288 | 0x00273294 |
| DrawTextClipped: No font | 0x00274364 | 报告中记录 |
| UIText/00001255.tui | 0x00307DA4 | 0x00307DAC |
| UIText/00001240.tui | 0x0030AC44 | 0x0030AC4C |

完整路径候选表、pointer words及局部窗口仅进入ignored JSON，不导出完整ELF或游戏对话。

## High-confidence deduction — TUI双区段线索

00001240路径候选之后的固定0x300 B扫描窗口，在VA `0x0030AD8C`及`0x0030AE20`均出现`ADDIU`形状的a2/寄存器6、zero源、立即数256。
两个常量与已确认的TUI双256 B布局一致，为后续追踪读入长度和两个字段路径提供优先线索。
常量用途、调用目标的函数语义、基本块和函数边界尚未验证；不把两个256直接声明为已定位的完整parser。

## Unverified hypothesis / 后续顺序

1. 解析00001240调用候选的对象/vtable来源与+0x14槽，验证目标是否执行资源读取；局部参数数据流已记录如下。
2. 从No font诊断候选定位DrawText周边基本块，追踪到字体查表和宽度数据访问。
3. 研究native标识表的运行时初始化关系；不将字符串pointer位置当函数入口。
4. 完整字符→glyph、自动换行、atlas缓存、扩容量及实际执行路径仍待验证。

当前没有函数地址补丁、字库扩容或运行时trace；原ISO、ELF及现有PoC保持。

## 重现与测试

```powershell
work/venv/Scripts/python.exe -X utf8 tools/research_native.py --iso "<original-KR-ISO-path>" --out work/native-research
```

ISO完整hash和ELFhash均校验，分析后复核原ISOhash。JSON只写ignored目录。
新增12项合成测试，当前工程98项通过，覆盖地址映射、BSS拒绝、header边界、立即数符号扩展、寄存器覆盖、delay slot和候选窗口。
旧运行时验收边界保持 [QA_TEXT_POC](QA_TEXT_POC.md)。

## 2026-10-08 — Verified static：调用参数与delay slot

报告schema2新增有限直线符号状态：每处JAL或规范`JALR ra,rs`最多回看8条指令，检查延迟槽后记录a0–a3的低32位表达式、已知常量及定义VA。
之前的调用/分支与其delay slot均排除在起始状态之外，不假设跨调用寄存器保留。未知指令形成屏障；未知delay slot不输出参数。
支持NOP、ADDIU、ORI、LUI、ADDU、零源DADDU move、部分标量load/store；不是完整R5900模拟器。load只形成符号表达式，不读取任意运行时内存，也不进行别名分析。

00001240窗口具有以下条件性静态参数证据；`entry_rN`表示各局部窗口开始时的未知寄存器，不表示跨窗口值恒定：

| 调用VA | delay VA | a0低32位 | a1低32位 | a2 |
|---|---|---|---|---|
| 0x0030AD70 | 0x0030AD74 | entry_r20 | entry_r2 + entry_r3 | 4 |
| 0x0030AD88 | 0x0030AD8C | entry_r20 | entry_r29 + 96 | 256 |
| 0x0030AE1C | 0x0030AE20 | entry_r20 | entry_r29 + 96 | 256 |

后两处均在调用前通过`LW r25,0(r20)`及`LW r25,20(r25)`构造间接目标；报告表达式为`load32(load32(entry_r20 + 0) + 20)`，目标地址未解析。
两个256不是后续无关常量：它们位于上述JALR的紧随delay slot，属于该条件性指令序列的调用时参数状态。
AD70的有限回看在移位指令处停止，因此r25、r2和r3来源保持未知，不拼接未支持指令的数据流。

## High-confidence deduction：双字段读入候选

同一局部区域的4字节调用参数与两个256字节调用参数，结合资源的4字节id和两个256 B区段，支持双字段读入路径的候选解释。
两个256路径使用相同形状的对象+0x14间接槽和sp+0x60暂存地址，但对象真实身份、槽的实现与连续流读取语义尚未验证；不宣称已恢复完整TUI parser。
局部直线推演不证明基本块可达、分支选择、运行时值或函数边界。通用循环、内存指针递增、各字段用途及字符串后处理仍待确认。

## 测试与保留状态

11个UIText候选窗口生成276条局部调用参数候选记录，不作为276个已命名函数或实际执行事件。
新增18项合成测试，工程116项通过；覆盖间接目标、delay参数覆盖、link寄存器时序、load覆盖、未知操作屏障、调用/分支delay排除、零寄存器和扫描边界。
原ISO、原ELF、text-poc-02 ISO、locale映射与译文保持不变；没有新PCSX2测试或ELF patch。

## 2026-10-09 — Verified static：GP槽与表指针构造

schema3增加可选`--table-va`和`--gp-displacement`，每张表限定16个u32，只读文件背书字节；GP槽区分file-backed与memory-only，不对内存尾部虚构初始零值或递归解引用。
MIPS ELF32 `.reginfo`为24 B，末尾`ri_gp_value`的结构依据 [LLVM ELFTypes定义](https://github.com/llvm/llvm-project/blob/main/llvm/include/llvm/Object/ELFTypes.h)。韩版声明值为`0x005437F0`。
启动邻域`0x100148`/`0x10015C`构造该值至r4，`0x100170`的OR形状将r4复制到gp；这不是所有后续执行时gp值恒定的运行时证明。

| GP相对位移 | 推导槽VA | 文件初值 | 有限LW候选 | 有限SW候选 |
|---|---|---|---|---|
| -32200 / 0x8238 | 0x0053BA28 | 0x0053C210，指向memory-only区域 | 90 | 0x001A4F34，源r10 |
| -29528 / 0x8CA8 | 0x0053C498 | 不在文件背书范围 | 8 | 0x001DA3B4，源r2 |

00001240的对象获取候选`0x30AC84`首先经第一槽的对象+0x0C间接调用，再将返回r2复制到r20；后续两个256调用基于该r20。
第一槽有写入候选，文件初始pointer不是运行时对象身份。`0x1DB434`从第二槽加载r10，`0x1DB44C`直接调用`0x1A4F00`，该邻域在`0x1A4F34`将r10写入第一槽。
`0x1DA3AC`构造r2=r30+0x1580，第二槽写入位于`0x1DA3B0`调用的delay slot；不能误归因于该调用的返回值。
这些链路是版本锁定字节与局部指令关系，跨函数执行顺序和alias身份没有动态确认。

## Verified static：候选vtable与转发邻域

| 表VA | +0x0C初始word | +0x14初始word | 有限常量SW候选 |
|---|---|---|---|
| 0x004FE270 | 0x001E4A10 | 0x001E4FF0 | 21 |
| 0x004FE390 | 0x0017EAE0 | 0x001E59E0 | 2 |

表word是数字pointer候选，不直接当作已命名函数。工具只追踪有限LUI/lower/SW序列，遇调用、分支、未知指令或源寄存器覆盖停止；候选数量不是完整赋值总数。
`0x1DA1E0`构造r17=r30+0x1580，`0x1DA200`/`0x1DA204`构造0x4FE270，`0x1DA208`写入r17+0。与上述GP槽初始化链一致，但不取代跨函数数据流证明。
`0x1E4A10`邻域根据两个GP相关条件分支：部分路径从对象+4再次经+0x0C间接调用；另一路径在分配标识`FArchiveFileReaderLinear`后初始化返回对象。
`0x1E4AB4`/`0x1E4ACC`构造0x4FE390，`0x1E4B10`写入返回对象+0；另一写入候选位于`0x1E58EC`，不将初始化和销毁邻域合并为同一执行事件。

在0x4FE390表的+0x14目标邻域`0x1E59E0`，字节显示：从输入对象+0x38加载另一对象，经其+0x14间接调用；delay slot保存输入r6到r16；返回后加载原对象+0x44、加r16、再写回+0x44。
这确认条件性静态转发与累计字段更新形状；目标实际读入字节数、错误处理和底层实现尚未恢复。

## High-confidence deduction / Unverified hypothesis

GP初始化链、0x4FE270的+0x0C候选以及带Linear标识的分配路径，支持文件管理器→归档reader包装层解释；0x4FE390的+0x14更像按请求长度转发并累计位置的接口。
TUI两个256参数与该包装层相容，但尚未证明TUI实际进入Linear分支；对象+4后端可走其他分支。完整reader函数定位不能只选一张静态表。
下一步追踪包装层+0x38的对象来源、替代后端以及字符渲染侧查表。保持TUI容量门禁和旧PoC范围，不依据这些候选直接patch ELF。

## 重现（schema3）

```powershell
work/venv/Scripts/python.exe -X utf8 tools/research_native.py --iso "<original-KR-ISO-path>" --out work/native-tables --table-va 0x4fe270 --table-va 0x4fe390 --gp-displacement -32200 --gp-displacement -29528
```

输入仍执行完整ISO/ELF hash门禁和原ISO复核；没有导出完整ELF。默认不选任意table/GP槽，选项使用locale-neutral地址参数。
23个标识、13个地址构造、9个pointer词及276条局部参数候选保持schema2结果；新表/槽审计独立记录。
新增15项合成测试，当前131项通过，覆盖reginfo、完整word边界、内存尾部分类、常量store屏障与地址转换、GP带符号位移、可变槽和选择上限。
原ISO、ELF、PoC ISO、映射与译文保持；无新增PCSX2验收。
