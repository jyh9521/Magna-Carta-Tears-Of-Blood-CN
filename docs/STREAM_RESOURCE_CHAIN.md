# celfid 尾部原资源链核查

## Verified

解压 offset 3218646 至 4185028 连续包含 37 个单记录 wrapper 及资源正文。每个 wrapper 为 128 B ASCII 路径及零填充，加 u32 原资源大小；正文与 SHIP 同名资源逐字节一致。总区段 966382 B，其中 wrapper 4884 B、正文 961498 B。此处不是前部 UE2 包的双记录 wrapper。

资源包括既有 VAL、CHA、ABI、ATT、SGI、CLS、ITM、FDS、CDG、MDG、TUI、NOD，以及 JMU、SEQ、SOP、EMS、BSD、QSD、UIL、ESC、FND、PAT、LVT、BTI。原档全容器清单已包含上述资源；本次补齐 celfid 镜像身份及连续边界，不把数值表、标识符自动升级为文本。

35048 个候选的原字节哈希再次全量复核。此前未闭合上下文中的 740 个对应已知原资源正文、40 个对应路径 wrapper；未闭合总数由 972 降至 192。既有上下文分类保持不变，跨边界候选没有强行归入单个资源。全部记录保持不可编辑，运行可见语义未验证。

## 未闭合部分

前部 StaticMesh／Texture 等原生区段与资源链之后的对象区段尚未闭合。37 个精确正文镜像不等于 37 个新增文本资源，192 个剩余候选也不等于 192 条可见文本。完整提取门禁继续 false。未翻译、未导入、未生成 ISO。

## 通用格式参考

[UEViewer 的 StaticMesh 序列化实现](https://github.com/gildor2/UEViewer/blob/a0bfb468d42be831b126632fd8a0ae6b3614f981/Unreal/UnrealMesh/UnMesh2.cpp)用于比较通用 UE2 字段；作者 Konstantin Nosov，MIT。该实现跳过部分碰撞尾部，且没有本游戏 PS2 分支，不能作为本游戏原生 serial 全边界证明；本次工具未复制其代码。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_stream_resource_chain.py --file work/kr/FILE.AFS --ship work/kr/SHIP.AFS --contexts work/extraction-coverage-81/context-audit/contexts.json --out work/stream-resource-chain-audit
```

三份输入均检查固定身份。工具拒绝路径形状、填充、重复身份、正文大小或原字节不符，输出 chain.json／contexts.json／summary.json 后逐一重开核查。原字节只在内存读取，输出为忽略目录的研究元数据，不创建原档或 ISO 副本。
