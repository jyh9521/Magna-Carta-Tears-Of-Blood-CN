# 韩版字体容量与字形冲突审计

日期：2026-10-08。状态：Verified static；未验证完整运行时映射、字体扩容或原文显示效果。
输入为SCKA-20043原ISO，SHA-256 `6242476a66a96110fb6ee1a1dd668eedd70d3df6c835f0de9192451b5f4fcd45`。
工具：`tools/audit_font_coverage.py`，复用现有UE2表/字体只读分析器、上游AFS及FPB代码。现有text-poc-02 ISO和映射保持不变。

## Verified — 字体表和限定语料

两套Font均有2667个glyph；完整range/base数组与原版版本指纹匹配。
B0A1..C8FE中25行、每行94个双字节组合，对应glyph317..2666，共2350个候选韩文字形槽。
这是现有文件布局中的槽数，不是已验证的中文字库扩容上限或整个引擎的字符总容量。
两套字体这2350个槽的bitmap均非全零；未在FPB中出现的槽不等于空白字形。

| 限定语料检查 | 结果 |
|---|---:|
| FPB pool严格CP949解码及原样再编码 | 695个 |
| 排除的解码失败FPB | 12个 |
| 未解析8 B stub | 1个 |
| 695个pool使用的不同韩文槽 | 1064个 |
| 同一语料中未观察到的韩文槽 | 1286个 |

按pool统计字符，重叠窗口不重复计数。内部lookup、UI、名称、其他固定槽、region、celfid、ELF、视频字幕及解码失败FPB均未纳入使用范围。
因此1286个槽只能称为“该语料中未观察到”，不能称为全游戏空闲或直接分配给中文。

## Verified — 当前33字映射的原文冲突

当前33个映射槽中16个在上述原版FPB中出现。
排除`00001944.fpb`的两个已被PoC替换的原文窗口后，这16个槽仍出现5140次，涉及615个不同FPB资源。
该数字描述原文byte-pair与被替换字体槽的重合；不能把615个资源直接等同615个实际可触发场景，也不是已完成的游戏截图验收。
UI及其他资源未计入，因此不能据此宣称完整副作用总量。

| 原编码 | 当前目标codepoint | 排除目标窗口后的原文出现次数 |
|---|---|---:|
| B0A1 | U+6D4B（测） | 3193 |
| B0A2 | U+8BD5（试） | 380 |
| B0A3 | U+4E2D（中） | 472 |
| B0A4 | U+6587（文） | 2 |

其余冲突及资源ID保存在ignored JSON；原版对话正文不导出到报告或Git。
稳定映射只保证同一目标字符的编码不随数据重排变化，不解决共享韩文槽对未替换原文的影响。

## High-confidence deduction — 后续路线约束

仅替换当前韩文槽的bitmap并保留大量原文会导致系统性原文字形替换；现有单字截图与此字节级统计一致。
低使用率槽方案只能降低限定语料的冲突风险，不能保证未纳入资源的显示。
正式容量方案须从目标字符集合、完整资源使用集合及实际renderer能力共同推导，而不是将2350或1286直接作为可用中文容量。

## Unverified hypothesis — 未完成项

范围表其他区段、native双字节查表、增加glyph数量/修改range/base、字体缓存及atlas容量尚未完整验证。
65536个双字节组合不等于引擎可接受65536个glyph；现有glyph index数组和尾部未知字段也未证明可任意增长。
本阶段不自动改map，不生成扩容ISO，不开始批量翻译。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_font_coverage.py --iso "<original-KR-ISO-path>" --locale locales/zh-CN/poc-text.json --out work/font-coverage
```

原ISO完整hash、MrtsEngine及两Font serial hash均先校验；审计后复核原ISOhash。
输出只在ignored目录：FILE/SHIP提取副本和`font-coverage.json`，无资源写回、字体替换或译文修改。
新增8项无需游戏资源的测试，当前工程共65项通过。下一步是补全非FPB使用范围并研究native映射/容量；运行时步骤保持 [QA_TEXT_POC](QA_TEXT_POC.md)。
