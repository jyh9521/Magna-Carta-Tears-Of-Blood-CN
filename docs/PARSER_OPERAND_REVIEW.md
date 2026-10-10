# 编译解析器操作数核查

## Verified static

stage90 再次完整解析 FILE 的 8032 个编译对象并逐项匹配 1207 个常量及 stage88 上下文。三个有界函数体保留完整 token、引用与 serial hash：GetTextNum、ProcessSpecialWord、ParseAmpersand。核对所需 InStr/InStrA、Mid/MidA、RemoveSpecialWord(A)、SplitRowAt 的解析引用，不仅凭函数名或字符串外观分类。

15 个原待确认常量补充 internal-parser-operand-candidate 角色：10 个直接 Case 子节点的单字符分支判别值、3 个 InStr/InStrA 分隔符搜索参数、1 个 ParseAmpersand 的转义比较值、1 个 ProcessSpecialWord 的生成控制序列拼接值。只匹配最内层已审查调用；普通比较和 UI 拼接片段仍保持未知。原 ID/hash/offset/文本、其他分类与写入门禁不变。

最新分类：103 可见候选、358 诊断、238 lookup/command、15 parser operand、265 空串、228 待确认。它们不是全游戏显示字符串数量。

## 边界

函数体中发现大写标记分支及生成序列，不将其规范化为现有校验器的小写标记；不据此修改 token grammar。不同函数接受的字符集并不一致，也未证明所有资源经过这些函数。101 个控制隔离项仍保留，百分号、非 ASCII 尖括号、TAB/LF/NUL 的完整 native 解释尚未闭合。操作数位置核查不是完整 VM 执行、reaching-definition 或运行显示证明。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_parser_operands.py --file work/kr/FILE.AFS --objects work/extraction-coverage-68/compiled-audit/objects.json --strings work/extraction-coverage-68/compiled-audit/strings.json --classifications work/extraction-coverage-88/compiled-audit-fixed/classifications.json --out work/parser-operand-audit
```

输出为空的 ignored 目录。完整原文与函数体仅保存在 work；公开文档提供汇总。工具锁定输入 hash，重新解析而非仅引用历史标签。新增 16 项测试覆盖错 owner、错范围、重复 ID、其他类别不变、最内层调用、普通比较/UI 拼接保留、无导入许可。
