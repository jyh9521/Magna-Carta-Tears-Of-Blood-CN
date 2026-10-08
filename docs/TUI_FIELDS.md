# 韩版 TUI 双区段结构

日期：2026-10-08。输入SCKA-20043原ISO，SHA-256 `6242476a66a96110fb6ee1a1dd668eedd70d3df6c835f0de9192451b5f4fcd45`。
只读工具：`tools/audit_font_coverage.py`，报告schema3保留schema2历史统计，另增加双区段结果。

## Verified — 全量字节布局

16个TUI共863条516 B记录：u32 id，随后两个各256 B区段。
区段相对记录起点为+4、+260；相对512 B载荷起点为+0、+256。
此前29个“首NUL后非零”字段，后续非零内容全部恰从载荷+256开始，并非任意位置的残留。

| 区段 | 严格CP949并原样再编码 | 空段 | 非零填充/缺NUL/解码失败 | 最大有效长度 |
|---|---:|---:|---:|---:|
| 首段 | 863 | 0 | 0 | 151 B |
| 次段 | 29 | 834 | 0 | 40 B |

每段分别具有NUL及全零余量；892个非空区段均严格CP949往返一致。
首段4项含当前未识别控制结构；892段中2项含原始控制字符。解码成功不等于编辑条件满足，保护机制继续保留。
字段hash、区段offset、长度、分类只存ignored JSON；原版文本正文不进入Git。

## High-confidence deduction — 字段用途与容量

一致的256 B边界、独立终止符和29个可解码次段支持“双文本字段”结构判断；首段/次段是否分别是标题、描述或其他用途仍待逐条确认。
未来显式字段schema宜分别配置256 B跨度，包含末尾NUL时目标上限255编码bytes；不把512 B记录载荷当成单段可覆盖容量。
该保守边界来自全量字节布局和合成测试，不作为native读取长度或所有字段用途的运行时证明。

## Verified — 通用写入函数的限定测试

现有`rewrite_fixed_slot`已能通过显式profile配置text_offset=4或260、text_bytes=256处理单一区段，无需新增TUI专用writer。
新增合成测试确认：单段修改保持另一半和id/header全部不变；源字段hash不匹配时拒绝；256 B跨度中254 B双字节目标可写并保留NUL，256 B目标溢出时拒绝。
这些测试未对原版TUI写回，也未开放新的locale条目。

## 现有PoC与兼容性

00001240 id176首段原有效长度18 B、次段为空；现有目标16 B完全位于首段。
旧PoC profile中的512 B描述覆盖记录载荷，先前依赖两半余量全零；它不是所有TUI文本的生产容量定义。
本次保留旧profile、target/map、DIFF身份及实验ISO，不使旧构建验证失效；下一次显式版本化profile修订须配置单段边界并重新生成/验收构建。

## 字形使用更新

FPB加全部892个非空区段合计仍使用1084个候选韩文槽，另外1266个仅为该限定语料未观察槽。
当前map与目标首段/FPB窗口之外原文重合17槽、5420次、629个资源；比schema2增加14次，但没有新增冲突槽或资源。
完整celfid副本不重复累计；其他格式、12个失败FPB及native硬编码仍未纳入。

## Unverified hypothesis

两段的native索引/显示关系、包含控制字符字段的语义、是否存在文本与内部identifier联动、字体容量扩展和实际渲染效果均未完成验证。
本次不调整映射、不扩大翻译量、不生成新ISO；PCSX2验收状态保持待完成。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_font_coverage.py --iso "<original-KR-ISO-path>" --locale locales/zh-CN/poc-text.json --out work/tui-pair-audit
```

版本及engine/font/bundle hash门禁保持，原ISO审计前后hash相同。当前86项测试通过（原75项+8项区段审计+3项显式字段写入测试）。
旧范围与历史数据见 [TUI审计](TUI_AUDIT.md)，运行时步骤见 [QA_TEXT_POC](QA_TEXT_POC.md)。
