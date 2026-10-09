# celfid 跨包依赖连续对照

## Verified static observations

在既有 Core 根树之后，源包 oracle 从 262948 连续对应到 487115，共 224167 B。97 次根请求、5248 个新增对象自身片段集合、6496 个片段观察完成对照。6 次多终点脚本前缀通过完整下一片段字节确定唯一延续；该结果不消除前缀内部对齐路径歧义。

| 区段 | 观察 |
|---|---|
| 347159–353432 | psx2user.ini 的 264 B wrapper 与 6009 B 原配置正文精确匹配 |
| 429023–430514 | Engine WhiteSquareTexture，1491 B、4 mip；8×8 和 4×4 mip 的尺寸字段与像素数组顺序不同，限定投影完整匹配 |
| 450211–452814 | Engine SmallFont 的 2603 B 原 serial 全字节一致 |
| 468103–484572 | Engine MrtsShadow，16469 B、1 mip；源 serial 与对照投影 hash 相同 |

StructProperty／ArrayProperty 的引用在公共字段后读取；flags & 0x20 时先读取额外 u16，再读取 compact target。负引用通过完整包名、外层对象链与名称匹配，不使用同名首项。引用越界、外层循环、缺失包及多义身份均失败；结构守卫在 Python 优化模式下仍生效。

## High-confidence deduction

跨包 super、结构属性依赖以及既有 Children／Next 顺序可解释该连续区段。SmallFont 原 serial 相同支持继续以普通包作为字体结构研究输入，不证明已读取所有 Font 对象或字体可见文字。

## Unverified hypothesis / 未闭合部分

重复脚本模型和小 mip 顺序投影都是后验只读对照，不是独立 streamed reader、执行等价或一般化序列化规则。ObjectProperty／ClassProperty 的引用不按结构依赖预加载；尝试预加载后 Material 参数 Other 处字节不匹配，失败路径保留。

487115 的下一段存在同字节 native Palette 候选，身份未唯一确定，当前工具停止且不跳过。全流映射、动态图形文字、全 CG 画面文字及全文覆盖仍未闭合；complete_game_text=false，translation_gate=coverage-audit-pending。原始资源、已有译稿和测试镜像不修改。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_stream_dependencies.py --archive work/kr/FILE.AFS --out work/stream-cross-package-oracle
```

输出须位于 ignored work/build 空目录。详细引用链、片段 hash 和源身份仅保存本地；公共报告不包含原始脚本、字体、像素或配置正文。工具复用既有 AFS 与普通包解析器，新增部分仅为跨包只读诊断。
