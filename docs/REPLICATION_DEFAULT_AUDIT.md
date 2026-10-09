# Class 编译复制脚本与默认属性边界

## Verified static（2026-10-10）

版本锁定 FILE.AFS 的 13 个非零脚本 Class 逐 token 读取，实际落盘 1,860 B 对应声明虚拟长度 2,228 B；1,181 个 token、181 个对象引用全部在表边界内。脚本结束后 State／Class metadata 和默认属性精确闭合至 serial 末尾。

全部 568 个普通 Class 默认属性因此形成完整静态集合：1,634 个 tag，132 个 Str 属性；相比零脚本读取增加 161 tag／13 Str。默认属性集合 complete 为 true，不代表全游戏文本 complete。属性正文、数字 opcode 轨迹和字节 hash 保存于 ignored 输出。

## 解码边界

此 reader 是 13 个已观察复制脚本的有界结构实现，不是通用 Function 编译脚本反编译器。0x48 的 compact 引用计为 4 B 虚拟数据；具体 opcode 的运行语义不强行命名。递归层级、引用边界、虚拟总长和后续属性末尾都检查；未知 opcode 拒绝，不自动跳过或猜测。

>=0x70 参数序列直到 0x16；0x18 带 u16 与子表达式；0x19 带表达式、3 B 与子表达式；0x2e 带对象引用和子表达式；0x24 带一字节；0x2d／0x39／0x3a 带子表达式。静态边界验证不证明执行可达、token 名称或游戏可见性。

## 失败记录

将 0x72／0x77 错作“高位 native 加第二字节”会吞掉实际首参数；直接参数规则修正后边界闭合。通用 native 阈值参考 [SurrealEngine UStruct.h](https://github.com/dpjudas/SurrealEngine/blob/380f52549e287aabcf6f9da409d94f4eb9b60e48/SurrealEngine/Packages/Core/UStruct.h)（FirstNative=0x70）。通用参考仅用于格式对照；本游戏 0x48 等定制语义仍未确认，没有复制第三方代码。

## 重现与剩余缺口

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_replication_defaults.py --archive work/kr/FILE.AFS --out work/replication-defaults/audit
```

旧 audit_class_defaults 默认仍拒绝盲跳非零脚本；新入口传入有界 reader。全部普通 Class 默认属性核查已闭合；Function／State／Struct native 字节码、流式正文、图片及 SFD 原文核查继续保持未完成。不新增译文或 ISO。
