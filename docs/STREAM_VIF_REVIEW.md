# celfid DMA／VIF 字节上下文核查

## 已验证范围

stage 87 在既有 stage 86 上下文快照上进行只读核查。固定 FILE.AFS 与解压 celfid 的哈希，重新核对全部 35048 个候选的原字节哈希；不删除候选、不写游戏资源、不改变译稿或导入资格。

`3201559` 的 little-endian u32 为 13200。下一字段为包数 13，其后三个 u32 为 159、199、187；三个字段的引擎语义仍未确认。`3201579–3214763` 共 13 个相邻 DMA_RET 包，逐包用 QWC 计算边界，同时独立解析两条 tag 内 VIF 命令及 payload 内命令。

| 包起点 | QWC | 终点 |
|---:|---:|---:|
| 3201579 | 64 | 3202619 |
| 3202619 | 65 | 3203675 |
| 3203675 | 65 | 3204731 |
| 3204731 | 65 | 3205787 |
| 3205787 | 68 | 3206891 |
| 3206891 | 67 | 3207979 |
| 3207979 | 67 | 3209067 |
| 3209067 | 68 | 3210171 |
| 3210171 | 68 | 3211275 |
| 3211275 | 67 | 3212363 |
| 3212363 | 58 | 3213307 |
| 3213307 | 71 | 3214459 |
| 3214459 | 18 | 3214763 |

QWC 合计 811；`16 + 13×16 + 811×16 = 13200`。16 B 为 count 与三个未解释字段，13×16 B 为 DMA tags。包内 320 条 VIF 命令包含 NOP 177、STCYCL 65、UNPACK 65、MSCNT 13；65 个 UNPACK 的输入长度（含 word padding）合计 11800 B。每个包自行声明 STCYCL，解析完整到包终点；未知 opcode、DMA ID、保留位、越界、数量不符或未声明 cycle 均失败，不采用未知长度跳过。

### 候选归属

- 144 个原未闭合候选完整位于 UNPACK 输入段。
- 1 个候选跨命令与输入边界：3214073 起点、4 B，前 2 B 为命令尾部，后 2 B 为 UNPACK 输入。保存原完整候选及两个片段哈希，不把该组合当作单独字符串。
- 未闭合候选从 153 降为 8，全部位于地图原生前缀；stage 86 的配置、wrapper、纹理、Palette、Commandlet、地图属性证据保持不变。

这是 transfer 字节布局证据，不是完整 StaticMesh schema 或运行时 VU/DMA 执行证据。145 个候选维持只读、不可导入；UNPACK 输入中的可解码字节不自动升级为显示文本。其浮点／颜色／顶点属性的具体业务含义尚未全部确认。

## 上游格式参考

参考 PCSX2 Dev Team 的公开实现，固定提交 `cf3c372043ae4fe0f2561de80d223755b5d7bf94`：

- [Dmac.h](https://github.com/PCSX2/pcsx2/blob/cf3c372043ae4fe0f2561de80d223755b5d7bf94/pcsx2/Dmac.h)：QWC、ID 字段与 RET=6。
- [Vif_Unpack.cpp](https://github.com/PCSX2/pcsx2/blob/cf3c372043ae4fe0f2561de80d223755b5d7bf94/pcsx2/Vif_Unpack.cpp)：UNPACK vector 格式及输入长度，NUM=0 表示 256、WL=0 表示 256，CL=0 不作同样转换。
- [Vif_Codes.cpp](https://github.com/PCSX2/pcsx2/blob/cf3c372043ae4fe0f2561de80d223755b5d7bf94/pcsx2/Vif_Codes.cpp)：STCYCL 字段。

上游文件标注 GPL-3.0+。工具独立实现只读长度核查，未复制上游执行器代码；上游不是本游戏的完整 native serializer oracle。各包的实际字节、数量及终点匹配为本地独立验证；游戏资源加载顺序与执行路径仍需本游戏证据。

## 复现

先按 `docs/COVERAGE_SEMANTIC_REVIEW.md` 生成 stage 86 输出，再执行：

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_vif_contexts.py --file work/kr/FILE.AFS --contexts work/extraction-coverage-86/review-audit/stream/contexts.json --out work/extraction-coverage-87/vif-audit
work/venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -q
```

输出目录必须为空。输出 `packets.json`、`contexts.json`、`summary.json` 均重开校验。完整原始候选只位于 ignored work；工具和本页不发布原版资产。

最近上下文哈希：`292279727338500d9717a3f6426b5f88ecfa01f2258fc5c7c17a418182e6478a`。源语料仍为 stage 86 的 20151 字段快照，不把 transfer 候选并入译文正文。

## 尚未闭合

`3201448–3201559` 的网格 native 前缀、三个块头字段与 `3214763–3214774` 的对象／依赖边界尚未完整解释；此处没有剩余启发式字符串候选也不等同于全部字段已验证。地图 `4188166–4190811` 仍有 8 个未闭合候选。后续还需处理配置消费者、动态脚本常量、ELF、编码与控制结构、SFD 画面文字；`coverage_review_complete=false`、`complete_game_text=false`，门禁不开放。
