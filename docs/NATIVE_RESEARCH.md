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

1. 从00001240候选窗口追踪调用目标与寄存器数据流，核对256是否实际用于每段读取。
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
