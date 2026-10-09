# Core Object 流式依赖树源包对照

## Verified static byte correspondence

固定韩版 FILE.AFS/celfid/Core.u hash 下，扩展源包 oracle 对照 Core Object 根定义。表末端 @235026 至 @262948 连续 27922 B 均被保留：27898 B 对应 1924 个普通包原字节片段，另外 24 B 为单独保留的 RandRange 差异脚本。1715 个字段对象的自身 prefix/tail 片段完成匹配，根 Object 的尾部到达；没有将差异脚本归为原字节相同或 VM 语义已验证。

Children 链在 Function metadata 尾部前展开，Next 链串联后继字段；ArrayProperty 的 Inner 字段与 StructProperty 的目标结构在当前属性之后展开。Super 为本包正引用时，对应基结构先出现。已经载入的 Struct 在之后遇到所属 Next 链时不重新写 body，但仍跟随后继字段。这些关系与原包的引用值、片段身份及连续源流位置共同核对，不通过搜索相似汉字定位置。

默认严格前缀模式仍在 RandRange @237255 停止，2229 B 旧结果不变。扩展模式只允许固定源脚本 hash 和固定 24 B 观察片段，并把该段写入 `opaque`；差异片段任何变化都会停止，未删除重复 opcode，未改写游戏。前一次只靠长度 512 限制 Next 链会提前截断同级链；同级 Next 不计为嵌套深度，已载入与已跟随后继分别记录。

## High-confidence deduction

局部依赖序列不是按 export 编号排序，也不是 declared_size 逐项切片。Children、Next、Inner、Struct、Super 关系共同决定观察到的序列。Core Object 依赖树的 source-oracle 闭合为后续普通包与流式资源的对应研究提供参考，不等于独立 streaming loader。

## Unverified hypothesis / 未闭合部分

RandRange 的 24 B packed 脚本与普通 20 B 脚本不同，原因、实际执行解码及语义仍未确认。Core 的其他定义、后继 Engine/Mrts 包、跨包依赖、纹理与其他流式 serial 未在本工具覆盖；TextBuffer 引用也不表示整个源 buffer 被写入该树。1715 不是全游戏可见正文数量，不新增译文或可编辑条目。全文门禁保持 false。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_stream_field_prefix.py --archive work/kr/FILE.AFS --out work/stream-dependency-oracle --extended-oracle
```

输出限 ignored work/build 下空目录；详细分段映射和 opaque 记录仅在本地保存。扩展模式为局部研究对照，不作补丁生成或完整格式验证入口。
