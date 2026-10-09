# 普通包 Class 默认属性核查

## Verified static

FILE.AFS 版本锁定下清点全部 568 个普通包 Class export。555 个零字节码类按 metadata／默认属性顺序读取至 serial 精确末尾；1,473 个默认属性 tag，其中 119 个 Str 属性，零结构解析疑问。13 个非零字节码类保留完整身份与未解析区间，不盲用虚拟脚本长度跳过磁盘字节。

字段顺序为：Super、Next、ScriptText、Children、FriendlyName compact 引用；Line／TextPos i32；一个观测 u32；虚拟 ScriptSize u32。Super 与 export table、FriendlyName 与对象名逐项一致。零 ScriptSize 后为两 u64 mask、u16 label offset、u32 state flags、u32 class flags、16 B GUID、dependencies、package import names、Within、ConfigName、HideCategories，最后为 None 终止默认属性。

119 个属性包含编辑器提示、命令行帮助、通用引擎消息、类路径和少量窗口标题。属性字节定位已经确认；游戏内可见性没有自动确认，全部保持 reference／editable=false。路径和类标识符不直接纳入翻译正文。

## High-confidence deduction

观测 ScriptSize 之前的额外 u32 可能来自定制 Struct metadata；本轮保持 observed_pre_script_word，不将其语义强行定为 StructFlags。此前少读此 u32 导致全部 568 类 metadata 错位；修正坐标后 555 个零脚本类精确闭合。

## 未解决

Engine.u 的 Pawn、Actor、Controller、LevelInfo、PlayerController、PlayerReplicationInfo、Mover、GameReplicationInfo、TeamInfo、Teleporter、WarpZoneInfo、Admin、DemoRecSpectator 共 13 类有非零编译脚本。字节码虚拟长度可能因 compact 引用扩展与落盘长度不同；默认属性必须待真实字节码边界解析，不能猜测偏移。

上述读取只适用于 version 118 的普通包，不适用于流式 serial。complete_game_text、class_defaults_complete 和 bytecode_decoder_complete 均保持 false。

## 格式参考及重现

通用 Class／Struct／State 结构参考 [Unreal-Library](https://github.com/EliotVU/Unreal-Library/tree/3207a17e9b294be3d1bf26b18e07ccff7e1d4b0c/src/Core/Classes)，Eliot van Uytfanghe；只研究格式，不复制代码，不宣称完整支持该 PS2 定制布局。零脚本的实际边界由全部 555 类原始 serial 验证。属性 tag reader 见 OBJECT_PROPERTY_AUDIT.md。

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_class_defaults.py --archive work/kr/FILE.AFS --out work/class-defaults/audit
```

只读输入，详细 class／string／question JSON 保存于 ignored 输出；不生成 ISO、不追加翻译。8 项新增测试覆盖引用校验、精确默认属性边界、虚拟长度拒绝盲跳、未知 word、源定位、截断和版本门禁。
