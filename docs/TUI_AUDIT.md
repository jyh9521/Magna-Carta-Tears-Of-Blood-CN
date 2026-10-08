# 韩版 TUI 固定记录与字形使用审计

日期：2026-10-08。证据：Verified static，输入仅SCKA-20043原版ISO。
ISO SHA-256 `6242476a66a96110fb6ee1a1dd668eedd70d3df6c835f0de9192451b5f4fcd45`。
`tools/audit_font_coverage.py`扩展只读审计，沿用上游AFS/FPB和现有字体分析；不替换资源、不调整locale映射。

## Verified — 记录结构

SHIP全部16个`.tui`均满足：8 B头部，u32 count @0、观察值2 @4，随后count个516 B记录。
每条记录为u32 id和512 B字段；同一文件内id均唯一，共863条记录。
该结论限定于该版本的这16个资源，第二个头字段语义及记录id的运行时用途仍未确认。

| 资源 | count | celfid中的完整精确副本数 |
|---|---:|---:|
| 00000682.tui | 34 | 1 |
| 00001238.tui | 63 | 1 |
| 00001239.tui | 34 | 1 |
| 00001240.tui | 243 | 1 |
| 00001249.tui | 27 | 1 |
| 00001255.tui | 37 | 1 |
| 00002380.tui | 9 | 0 |
| 00002381.tui | 6 | 1 |
| 00002382.tui | 4 | 0 |
| 00002459.tui | 28 | 0 |
| 00002788.tui | 26 | 1 |
| 00002789.tui | 156 | 0 |
| 00002792.tui | 49 | 0 |
| 00009962.tui | 47 | 1 |
| 00011012.tui | 3 | 1 |
| 00014107.tui | 97 | 0 |

10个资源有一个完整副本；6个资源未找到完整精确副本，不排除局部副本或其他封装，也不证明加载优先级。
统计逻辑只计SHIP字段一次，不因celfid副本再累计字符。

## Verified — 字段分类

834个字段满足首次NUL后全部为0、前段严格CP949解码并原样再编码；另外29个字段在首次NUL后仍有非零字节。
29个字段全部保留为例外，不把尾部覆盖为0，也不将第一段当作完整可编辑文本。
6个资源包含这些例外：00000682、00001238、00001239、00001240、00001249、00002788。
审计JSON记录record id、位置、字段hash、首次NUL及后续非零位置，不导出字段正文。

834个可解码字段中4个含当前token规则未识别的结构；字形使用统计仍能读取其字节，但不据此开放翻译。
可解码字段不等于全部界面显示字段：标签、内部identifier与显示文本的用途仍须分别确认。

## Verified — 限定语料合并

834个TUI字段使用586个不同候选韩文槽，与695个严格解码FPB合并后共1084个，比仅FPB增加20个。
2350个候选槽中其余1266个未在这个合并语料观察到；29个例外字段、其他资源和12个失败FPB未纳入，因此仍不是全游戏空闲槽。

当前33字map在TUI中有12个冲突槽。排除已替换的00001240 record id176后，原文重合266次、涉及14个TUI资源。
与FPB合并后，33字map中17个槽在目标字段之外发生重合，共5406次、涉及629个资源（615 FPB + 14 TUI）。
该数字是原版byte-pair出现次数，不是运行时触发次数或已复现的显示异常总数；完整副本不重复计数。

## High-confidence deduction / Unverified hypothesis

后续schema3全量字节检查已将29个尾部例外定位为载荷+256起始的独立区段，全部有独立NUL并严格CP949往返一致。双区段结果及保守字段边界见 [TUI双区段](TUI_FIELDS.md)；原schema2排除结果保留为历史，段用途仍待确认。

**High-confidence deduction**：有完整celfid副本的显示字段修改需要显式同步考虑，不能仅根据SHIP替换结果推断运行时会加载新文本。
**Unverified hypothesis**：29个字段的非零尾部是否属于多段文本、其他结构或填充残留；记录id与显示功能的关系；10个副本的加载优先级；非FPB范围外字符使用与真正可用容量。
当前builder仍只开放已验证的00001240 id176；本次不扩大写回范围。

## 重现与验证

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_font_coverage.py --iso "<original-KR-ISO-path>" --locale locales/zh-CN/poc-text.json --out work/font-tui-coverage
```

报告schema2保留原FPB统计，另存TUI和合并统计；输出`font-coverage.json`及提取AFS只在ignored目录。
版本ISO、engine/font/bundle身份均校验；审计后原ISOhash复核。新增10项合成测试，当前工程75项通过。
现有text-poc-02 ISO、原映射与译文不变；PCSX2验收见 [QA_TEXT_POC](QA_TEXT_POC.md)。
