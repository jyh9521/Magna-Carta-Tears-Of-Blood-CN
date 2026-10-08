# FontObj bitmap转换与缓存候选

## 范围与复用

SCKA-20043原ELF、ISO与小字集PoC保持。复用上游AFS/UE2读取、原Font parser、版本门禁、有限调用推演和只读标量模型。新增`tools/research_font_bitmap.py`只输出hash、地址、统计与条件参数，不导出原字体、bitmap、纹理或完整ELF。

模型新增SRAV低32位语义，shift取源寄存器低5位并按bit31符号扩展；依据 [MIPS Technologies Volume II-A Rev3.00，第238页](https://pages.hmc.edu/harris/class/e155/11/MIPS32InstructionSet.pdf)。R5900带rd的MULT、MMI乘法、FPU、GS与纹理上传均未执行。

## Verified static — source与page邻域

`0x333A4C`调用已锁定的glyph查表`0x20EE80`；`0x333A58`将返回值限制为16位并保存在r30。`0x333C30`邻域从对象+0x28取font候选，再读取font+0x5C、+0x54和+0x60，并使用r30参与乘法寻址。+0x60在此参与源byte地址，而不是传统20 B glyph record数组。

`0x333A74`与`0x333A8C`的SLTI比较值均为65；相邻路径累计横向尺寸与+0x54候选纵向尺寸，行切换或新增page。对象+0x38/+0x3C/+0x40呈pointer/count/capacity形状；超capacity时调用既有分配helper0x1A17B0，count保持动态。64边界属于局部page布局线索，不是全字体64字或64页上限。

`0x272D00`调用`0x271B10`；该绘制候选从cache对象+0x28取font，并以16位查表结果读取metric，与另一条`0x271510`的8位路径不同。实际入口分派与各UI覆盖仍未确认。

| 邻域 | 长度 | SHA256 |
|---|---:|---|
| source 0x333C30 | 64 B | 7e71289240cdf118a534cbe02265aa04e34113c80a23349ed0203cc7ba999231 |
| page 0x333A20 | 352 B | 3e20c552d22748f9901b0febefed15503151add0b935912d83dd9901b7960bc9 |
| conversion 0x333D64 | 112 B | 1a7478c87683d03570c1a5f55842b97dc45f0d9ab2e076a665fb01c391b92f14 |

## Verified offline projection — 2bpp标量转换

只执行conversion邻域中SRAV、ANDI、SLL、SUBU、SLL五条标量操作。输入source为0–255，shift为0/2/4/6，共1024组；输出全部等于`((source >> shift) & 3) * 60`，即0/60/120/180。原片段不改，没有补造return；SB、循环、分支、源/目标地址计算和page内存写入不执行。

将原两Font的packed bitmap按已有parser的height/stride/width投影为完整19列，逐像素对照独立位提取表达式，结果一致：

| Font | 源bitmap | 投影pixel数 | SHA256 |
|---|---:|---:|---|
| NormalFont | 280035 B | 1064133 | 4da1a06dfb722787625ce406fd45db90e347721d38678b3b5617af2af8c90506 |
| KatakanaFont | 240030 B | 912114 | 0665f492fd73e5d062012a17e35eab2e03f0b05acfd90746e43c213946c45881 |

投影使用原2667 glyph、19列、5 B/row与21/18行，不包含第20个padding pixel。实际转换循环还按metric加spacing候选裁剪横向写入；完整19列投影不是实际page image、缓存纹理或上传结果。

## High-confidence deduction

该邻域属于FontObj的glyph bitmap/cache生成路径：使用查表index、metric、源bitmap和尺寸，维护动态page对象，并与16位绘制候选相容。source相对偏移形状为glyph index乘行数乘row stride，+0x54承担height、+0x5C承担stride的解释比仅按文件字段顺序猜测更强，但尚未执行完整R5900寻址链或采样真实实例。

横纵65比较与行切换支持64×64 page布局解释；需要继续核对page分配和texture对象字段，不能作为已验证GS纹理规格或缓存总容量。

## Unverified hypothesis与边界

font+0x94条件选择另一条按bit mask写0/220的候选分支或本次2bpp分支；实际Font实例的selector与原序列化尾部word尚未建立完整对应关系。原资源有2bpp几何，不足以证明本次分支在PCSX2中被执行。

已有预览将2bpp值乘85用于可读灰阶，native候选投影乘60；两者用途不同。不能直接将180解释为屏幕最终alpha，也不因该差异修改已有glyph generator。

完整bitmap加载、page创建/复用、format选择、spacing、allocator上限、texture上传、缩放/换行、save和切场景仍待验证。新增16项合成测试，工程179项通过；没有字库扩容、引擎patch或新增运行时验收。

## 重现与下一步

```powershell
work/venv/Scripts/python.exe -X utf8 tools/research_font_bitmap.py --iso "<original-KR-ISO-path>" --out work/font-bitmap
```

原ISO完整hash在前后复核，所有实验输出只写ignored目录。下一步追踪page创建helper0x334430及format selector的赋值，再决定独立扩容PoC所需的bitmap/metrics/page同步条件。
