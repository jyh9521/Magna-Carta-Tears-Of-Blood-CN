# celfid 编译脚本前缀全量有界对照

## Verified static observations

普通包的 8032 个 Function／NativeFunction／State／Struct 全部重新按结构读取并核查。7983 个定义存在完整原 header 精确候选；49 个没有相同 header。4 个定义各有 2 个候选位置，未任意选择第一个；全部 7987 个候选均完成限定重复模型的逐字节对照，候选终点均唯一，1501 个候选内部存在至少两条对齐路径，歧义明确保留。

| 普通包 | 模型符合的定义 | header 无匹配 |
|---|---:|---:|
| Core.u | 291 | 3 |
| Editor.u | 0 | 39 |
| Engine.u | 1244 | 0 |
| Gameplay.u | 5 | 0 |
| MrtsEngine.u | 1986 | 0 |
| MrtsGame.u | 3977 | 0 |
| UWindow.u | 480 | 0 |
| UnrealEd.u | 0 | 7 |

符合模型的普通源脚本合计 720142 B，含 1193 个既有字符串常量。该计数是源定义统计，不是新增正文或运行可见字符串数量。原有 1207 个普通脚本常量的其余 14 个仍保留在原核查集合，不因 celfid 无相同 header 而删除。

## 模型与证据边界

对照保留每个源字节的顺序与值，仅允许指定位置的同值字节出现一次或两次：普通包结构解析器给出的 opcode 字节、Iterator 尾随 u16 的低字节、Context／ClassContext skip u16 的低字节。后两类位置从已核查 token 子树边界推导；其他 operand、compact reference、字符串内容及结束字节不允许任意重复、替换或跳过。所有观察字节保留 hash，工具不生成规范化 bytecode。

首次仅以 opcode 为可重复位置时有 182 个不匹配；加入 Iterator 尾随字低字节后剩 125 个；加入 Context skip 低字节后，所有有原 header 的候选符合模型。三个探索输出分别保留，不能把后验模型拟合称为引擎序列化实现已验证。各 opcode 是否必然重复、重复原因、实际执行解码、跳转语义仍未确认。

## High-confidence deduction

Core RandRange 的差异不是孤立现象；Engine、MrtsEngine、MrtsGame 等大量脚本呈现受结构位置限制的字节重复。完整源脚本值及字符串内容可在限定模型下对应，支持继续使用普通包作为只读研究 oracle，而非直接依据 virtual_size 截取流式磁盘字节。

## Unverified hypothesis / 未闭合部分

该工具不是独立 streamed bytecode reader，没有验证 Function metadata 尾部、Children／Next 的整体流顺序、跨包加载、完整 serial 或动态文本。多个 header 位置和内部对齐路径歧义均未放行。模型符合不等于运行等价、可删除重复字节或可直接导入译文。完整流／VM／全文门禁继续为 false，现有译文与字库保持不变。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_stream_script_correspondence.py --archive work/kr/FILE.AFS --out work/stream-script-correspondence
```

输出目录须为空且位于 ignored work/build。详细原定义身份、候选 offset、终点、路径歧义及 hash 仅保存本地；公共 JSON 不含完整原文字节或脚本资源。
