# celfid Core 流式字段前缀对照

## Verified static

固定 FILE.AFS 身份下，celfid 解压 hash 为 `04ed29c9c4e65b1f14c4c2ae4b8578ad147af42b7dbaecdc62f57a3af56e3536`。Core.u 普通包 hash 为 `358ac0e8be6837ac418e43f30071d50085bdf7c9d59c9a8db5d4c9d1c2d45f60`。流式表与普通包的 names、export 顺序、原始位置、大小、类、flags、Super 等元数据逐项一致。

表末端 @235026 之后的连续 2229 B 由源包片段逐字节拼接对照，144 个非空片段匹配；涉及 112 个访问对象，其中 110 个对象的自身 prefix/tail 片段匹配完成。根 Object 的尾部尚未到达，因此这不是 110 个完整子树或整个流式包的闭合证明。

具体连续位置：Core Object 的 23 B UStruct prefix 位于 @235026；EndState 完整 31 B 位于 @235049；BeginState 完整 31 B 位于 @235080；NotifyFromController 完整 31 B 位于 @235111。NotifyFromWindow 的 header＋脚本之后插入 a_Msg、a_Prm1、a_Prm2 三个参数字段，Function 的 5 B precedence/flags 尾部位于参数链之后。StructProperty A 后紧接 Quaternion Struct 与其四个 FloatProperty，自身 Next 链随后继续；直接按 declared_size 连续切片会跨入不同对象。

首次不匹配为 Core.u/export/115 RandRange，在流 @237255 的 45 B prefix 对照中相对 +40 处，普通包为 `0x16`，流为 `0xc3`。严格工具在该处停止，未跳过差异、搜索下一函数并继续假装闭合，也未丢弃余下数据。

## High-confidence deduction

当前前缀支持按 Children 与 Next 字段关系串联序列、并在 StructProperty 引用后插入结构定义的观察模型。依赖 Struct 的 Next 不跟随同一结构定义的内嵌遍历。该模型只对已匹配前缀有效；源包比较是 oracle，不是独立通用 streaming parser。

## Unverified hypothesis

RandRange 的流式脚本额外出现重复 opcode 字节；编码转换、打包器规则、运行解码语义均未确认。不能简单删重复字节、按普通 script size 跳过，或用单一偏移映射全部对象。其他 Core 对象、其他流式包、全部纹理与 celfid 的剩余正文仍未闭合。全文提取门禁保持 false。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_stream_field_prefix.py --archive work/kr/FILE.AFS --out work/stream-field-prefix
```

输出限 ignored work/build 下空目录。该工具报告首次差异作为研究结果；退出成功只表示审计结果写出，不表示全部流式序列解析通过。详细片段和引用边保留本地。原盘、资源、测试 ISO 和译文没有修改。
