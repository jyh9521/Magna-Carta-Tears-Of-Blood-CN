# 容器载荷核查

## Verified static

原版 SHIP.AFS、FILE.AFS、LINEAR.AFS 的 SHA-256 与原 ISO 派生库存一致；逐项读取 13,862／53／4,099 项，共 18,014 项。只读遍历未修改原始归档，未产生新 ISO。

4,058 项读取到包表，13,944 项未识别到符合当前签名的包表，12 项压缩分帧核对失败。“未识别到包表”不是无文本结论。

包表出现次数为 7,840，其中 FILE 19、LINEAR 7,821；普通包 10、重定位流式包 7,830。该数量包含缓存／嵌入重复，不是唯一资源、可见字符串或翻译数量。Texture 11,890、StrProperty 2,228、TextBuffer 1,106 均为 export 出现次数，属性与图片正文尚未据此解码。

LINEAR 解压载荷及部分 FILE 载荷含 256 B 路径、u32 保留值、u32 原包长度，之后为 UE2 magic。观察到 version118、name offset64；名字表后紧接 import／export 表。原包头中 import／export offset 不指向流式载荷中的实际位置。顺序表解析通过全部已接受流式包的计数、名字索引及原包尺寸边界检查。

压缩读取复用上游 `translate.celfid.decompress_chunked`，普通包读取复用现有 `research_inventory.package_tables`。流式表保留 declared_size／declared_offset，不把它们当实际 serial 地址；`serial_mapping=unresolved`。

## 未解决的分帧差异

LINEAR 的 00000541、00000547、00000548、00000549、00000557、00000568、00000571、00001264、00001380、00002770、00005970、00007619.lin 共12项在一至171个有效chunk之后仍有非零剩余字节，或末帧越过 AFS 声明范围。原始项 hash、完整长度及错误记录保留在本地核查集合。该观察不证明资源损坏，也不授权截去剩余字节；manifest、尾部保存机制与实际加载路径仍需比对。

## 覆盖状态

`complete_game_text=false`。包表读取不等于对象属性、脚本字面量、图片字或流式 serial 的全部提取。ELF、celfid、多媒体与其他 ISO 载荷的覆盖门禁仍维持；6334条既有译文不变，不扩大翻译。

本地详细库存：`work/extraction-coverage-49/container-audit-v2/`。详细原始名字及属性元数据保持忽略，仅统计进入版本控制。
