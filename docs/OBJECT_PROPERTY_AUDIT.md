# 普通 UE2 实例属性核查

## Verified static

版本锁定 FILE.AFS，10 个普通 UE2 包全部实例 export 读取属性块；30,813 个实例、634 个 tag、22 个 HasStack 头，零属性解析疑问。另有 568 个 Class export 保留为 native／默认属性待解析，不以类对象正文首字节的 None 认定没有文本。

HasStack 标志为 0x02000000。当前 22 个对象均通过 Node／StateNode compact、ProbeMask u64、LatentAction u32、非零 Node 时 compact Offset 定位后续属性。此前采用 u16 LatentAction 的探索读取失败；当前原始 Entry.unr 属性名、长度和终止位置一致。

tag 复用通用规则：低四位类型，三位尺寸选择，Struct 名位于尺寸之前；Bool 高位表示值且不消耗 payload，不作为 array index。其他类型高位表示数组索引，分一、二、四字节读取。Str 类型 13 严格检查 compact 字符数、CP949／UTF-16LE 字节长度和 NUL。

仅发现一个实例 Str tag：Entry.unr 的 LevelSummary.Title，内容为编辑器标题，尚未确认游戏内显示用途。原文字节身份与完整定位仅保存于 ignored 输出。

## 明确边界

30,788 个实例具有属性终止后的 native 尾部。尾部长度／hash 已保留，但尚未解析；空属性块不等于整个对象没有文本。Class 默认属性、编译脚本、Texture／Font native serial 及流式坐标仍待独立核查。complete_game_text 保持 false。

## 上游通用格式参考

属性 tag 参考 [UEViewer UnObject.cpp](https://github.com/gildor2/UEViewer/blob/a0bfb468d42be831b126632fd8a0ae6b3614f981/Unreal/UnObject.cpp)，Konstantin Nosov，MIT；仅研究格式，不复制源码或宣称该工具支持本游戏。

执行栈对照 [SurrealEngine PackageFormat](https://github.com/dpjudas/SurrealEngine/blob/380f52549e287aabcf6f9da409d94f4eb9b60e48/Docs/PackageFormat.md)。该文档针对 UE1；实际韩版 u32 LatentAction 与属性边界由原始 22 个实例核查。通用参考不替代版本校验，也不将文档中类对象条件直接套用于本游戏。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_object_properties.py --archive work/kr/FILE.AFS --out work/object-properties/audit
```

读取原档案，输出详细对象／属性／疑问清单；不修改档案或生成 ISO。11 项新增测试涵盖八种尺寸、Bool、数组索引、结构名、宽字符、空串及截断拒绝。
