# celfid 跨包 Class header 全量源包对照

## Verified static correspondence

固定韩版 FILE.AFS 与 celfid hash 下，10 个普通 UE2 包中的全部 568 个 Class header 已按原包结构读取、核对 Super／FriendlyName 并搜索完整 header 原字节。534 个定义各有一个精确候选位置，34 个无相同 header；没有多位置歧义。匹配 header 合计 13152 B，不包含任何后继 bytecode、Children、默认属性或纹理数据的覆盖承诺。

| 普通包 | Class 数量 | 唯一 header 候选 | 无匹配 |
|---|---:|---:|---:|
| Core.u | 7 | 3 | 4 |
| Editor.u | 17 | 0 | 17 |
| Engine.u | 174 | 174 | 0 |
| Gameplay.u | 13 | 13 | 0 |
| MrtsEngine.u | 128 | 128 | 0 |
| MrtsGame.u | 175 | 175 | 0 |
| UnrealEd.u | 13 | 0 | 13 |
| UWindow.u | 41 | 41 | 0 |

Entry.unr 与 temple.utx 没有 Class 定义。6 个存在相应 streamed wrapper 的普通包，其 names、完整 imports（包含 class_package）、exports 的身份／flags／原 serial 坐标逐项一致。原 inventory 的 imports 仅保留 class/name/outer，新增对照入口从原字节读取完整 import 元数据，不直接比较形状不同的字典。

Core Object 根树 @262948 后的下一 header 对应 Engine.u export 26 `Material`（23 B），不是 Actor/Pawn。`RenderedMaterial` 的 header 位于 @263187，Actor @264290，Pawn @285945，Controller @302317，LevelInfo @312116。位置为源 header 锚点，不是根据 declared_size 推算的完整 serial 边界。

## High-confidence deduction

观察顺序包含跨包 Class 与基类相关载入，不能把 Engine 表末端或 Core 根树末端当成 Actor 的起点。独立完整 header 与已核对表身份为后续依赖树解码提供定位参考。

## Unverified hypothesis / 未闭合部分

无匹配的 Core 定义为 HelloWorldCommandlet、Time、SimpleCommandlet、Locale；另外 30 个来自 Editor/UnrealEd。无相同 header 不等于运行不可达、整个资源缺失或全游戏无对应文字。534 个 header 也不等于 534 个完整资源；流式 bytecode 存在差异，后继对象、动态字符串和视觉文字仍需各自核查。

全部记录保持 `editable=false`、`serial_mapping_verified=false`、`complete_game_text=false`。主文本集合与 6334 份初稿不变，没有追加翻译。原始 ISO、测试 ISO、模拟器与大型资产均未修改或复制。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_stream_class_headers.py --archive work/kr/FILE.AFS --out work/stream-class-headers
```

输出目录须为空且位于 ignored work/build。详细 anchors/packages 保留本地，公共 JSON 仅含计数和输入 hash。
