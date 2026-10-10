# celfid 尾部属性及跨界候选补核

## Verified static

35048个候选的完整原字节hash重新核对，39个原未闭合上下文补核后剩余153个：StaticMesh附近145个、地图native区8个。候选原ID、offset、长度与hash均保留；跨界候选另列完整分片，而非截断候选或静默丢弃。

- 4185028–4185368的340 B与普通Core.u Commandlet根及递归Children/Next字段逐片精确匹配。已有super不重新发出，不跳过未知native。
- 地图表身份为00000118.unr，package_offset=4185632、table_end=4188034。五个132 B wrapper完整核对路径、零padding与原声明8165 B；8165不是本地4 B stub的正文长度，也不作为流式载荷跳过长度。
- 4190811–4191209连续读取398 B、六个完整属性记录：LevelInfo、DefaultPhysicsVolume、Light、PlayerStart、MrtsPlayerStart、LevelSummary。前五项stack类引用与包表相符，属性终点、引用边界与各声明长度一致。
- LevelSummary.Title保留Untitled原值；MrtsPlayerStart.Char_ID的type7值呈有界字符串布局，读取为字符标识值，不将type7全局推广为StrProperty规则。对象运行身份仍未独立确认。
- 3214774–3218646的Texture/Palette重新按已有严格解析器读取，4 mip几何一致；26个扫描候选位于像素／属性区，不是26句正文。
- 初始配置末尾与Engine wrapper跨界候选、地图表末尾与wrapper跨界候选均保存完整两段context与各段hash。

## 未闭合部分

3201448–3214774的StaticMesh完整native布局、4188166–4190811的Level/Model等native字段仍未闭合。不将孤立float外观或可解码短串直接排除为内部数据。属性记录闭合与整体地图、对象执行及可见性是不同证据；complete_game_text=false。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_stream_tail_contexts.py --file work/kr/FILE.AFS --contexts work/extraction-coverage-83/chain-audit/contexts.json --out work/stream-tail-context-review
```

原档及stage83快照固定hash；越界、原字节不一致、引用或属性长度不符均停止。新增上下文只作用于未闭合候选，既有上下文不被改写。
