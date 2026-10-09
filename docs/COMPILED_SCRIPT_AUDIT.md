# 普通包编译脚本全集合核查

## Verified

韩版 FILE.AFS 既定 SHA-256 下，所有 Function 5721、NativeFunction 1653、State 439、Struct 219，共 8032 个导出逐一读取。property None、UStruct 头、virtual script 大小、后置元数据与整个 serial 末端全部闭合，解析问题 0。共 316939 token，磁盘脚本 728733 B、展开虚拟脚本 992179 B。所有 compact 对象／名称引用通过表边界检查；每个原始字符串片段再次通过包绝对位置及 SHA-256 核对。

共 1207 个字符串常量，均为 token `0x1f` 的 NUL 终止单字节正文，严格 CP949 阅读失败 0；其中 5 个含韩文。Function／NativeFunction 为 1204 个，State 另外 3 个为数字 `1`，Struct 无字符串常量。它们是编译字符串参考，不等于 1207 条已确认可见正文。

| owner class | Function | 编译字符串 |
|---|---|---|
| MrtsMainSetDifficultCW | InitValue | 이지 모드、노말 모드 |
| MrtsBattleMenuCW | InitValue | 페이즈종료、위치미변경、게임재개 |

此前 packed CP949 源码阅读与 5 个 byte-hit 位置已得到独立 token 边界对应；未修改字节、翻译或导入。其他字符串包括日志、命令、标识与运行常量，尚未逐项完成可见性分类。

## 格式边界

UStruct 头复用既有普通包 property reader。后续依次为 compact Super／Next／ScriptText／Children／FriendlyName，i32 Line／TextPos、实测额外 u32、u32 virtual script size。额外 u32 实测为 0 或 1，具体用途未确认。

compact 引用按 4 B 虚拟长度累计，其他实测字段按原字节累计；虚拟大小不能直接当磁盘长度。递归最大深度 64；未知 opcode、越界引用、缺失终止符或长度不符直接失败。`0x47`／`0x48` 在当前韩版为 compact 引用字段，`0x37` 后跟一个递归表达式；不套用 UE1 conversion/Construct 名称作为已证实语义。

Function 在脚本之后为 u8 precedence 与 u32 flags，flags&0x40 时另有 u16 replication offset。NativeFunction 在相同基类尾部之后另有 u16 native index；将其前移为统一 Function 的 native 字段会错读 flags。State 为 u64 Probe／Ignore、u16 label offset、u32 flags，Struct 无额外尾部。121 个 FriendlyName 与 export name 不同，主要为运算符符号；要求二者始终相同会产生误报。

## 上游参考与证据层级

既有 UStruct/UFunction 字段阅读参考 [SurrealEngine](https://github.com/dpjudas/SurrealEngine/tree/380f52549e287aabcf6f9da409d94f4eb9b60e48/SurrealEngine/Packages/Core)，该 UE1 实现仅提供候选语法，不构成 PS2 格式验证，也未复制代码。上述结构闭合统计来自韩版原包。单字节常量用于显示的编码和函数调用含义仍需调用／运行证据，不能以 CP949 静态阅读代替执行证明。

## 尚未闭合

全部普通编译脚本结构读取不代表全部 VM opcode 语义、跳转可达性、动态拼接文本或执行行为已验证。普通 Class 默认属性／复制脚本由 REPLICATION_DEFAULT_AUDIT.md 独立核查；流式 serial、celfid 其他载荷、SFD 字幕与小 mip 视觉检查仍未穷尽。全文门禁保持 `complete_game_text=false`。

## 复现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_compiled_scripts.py --archive work/kr/FILE.AFS --out work/compiled-script-audit
```

输出限 ignored work/build 下空目录；完整编译对象、正文片段与 token 位置信息不进入 Git。工具复用原有 AFS 与 package/property reader，不生成大型游戏资源副本。
