# 普通编译字符串调用上下文

## Verified static

FILE.AFS 原身份下重新解析 8032 个普通 Function／NativeFunction／State／Struct，与既有编译对象、serial hash、token、字符串片段逐项一致。1207 个字符串的祖先表达式全部重建；1025 个具有调用祖先，474 个具有赋值祖先，集合允许重叠。调用名称／对象引用与原包表核对，numeric native index 与普通 NativeFunction 元数据对应；当前调用的未解析符号 0，非零 native index 无多名称冲突。1200 个 native index 为 0 的名称不视为同一编号的可调用函数。

父 token `0x70` 的 434 个字符串处于 `Concat_StrStr` 之内；只看直接父节点会遗漏更外层的显示或日志调用。数字、空字符串、比较常量、文件／资源标识仍完整保留，没有按文字外观删除。

## 显示符号候选层

对文档 JSON 中明确列出的 17 个名称作祖先符号过滤，得到 133 个只读候选；详细正文保存在 ignored 输出。过滤是上下文索引，不是全部显示 API 名单或可见正文计数。示例包括 `Loading Data`、`Select Your Memorycard`、`SLOT 1`／`SLOT 2`、`MONO`／`STEREO`、`MAX COMBO`、`EXTRA EXP` 与 `MAIN`／`ITEM`／`EQUIP`／`STYLE`／`INFO`／`OPTION`。这些英文字面量不因源盘为韩版而排除。

5 个韩文短标签全部具有 `SetCaption` 调用祖先：MrtsMainSetDifficultCW 的 2 个难度标签、MrtsBattleMenuCW 的 3 个战斗菜单标签。`DrawText` 的 49 个符号观察包含 DisplayDebug 上下文，不能直接计作正常流程 UI。资源名、调试文字、临时占位及空白都需要保留上下文分别审核。

## High-confidence deduction

明确的 SetCaption／SetText／AddButton／AddPage 等符号祖先支持显示用途候选判定，强于裸字节搜索；方法名并不证明参数位置、调用可达性、最终覆盖顺序或韩版运行实际使用。构造后的动态文本、其他显示接口及 native 实现尚未穷尽。

## Unverified hypothesis / 门禁

全部字符串的运行可见性、导入补丁位置与动态字符串流仍未验证；compiled symbol 关联不替代数据流或游戏验收。133 候选不直接并入可编辑正文，不生成译文，不修改游戏。全文提取门禁仍为 `complete_game_text=false`。普通小 mip 的后续检查已完成，流式 serial 与 SFD 全文字覆盖仍未闭合。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_literal_contexts.py --archive work/kr/FILE.AFS --objects work/extraction-coverage-68/compiled-audit/objects.json --strings work/extraction-coverage-68/compiled-audit/strings.json --out work/literal-context-audit
```

输入对象与字符串目录必须来自普通编译脚本审计；工具重新核对原资源，不依赖既有 JSON 的自报身份。输出需为 ignored work/build 下空目录。详细上下文及原文仅保留本地。
