# 保留原字形的Font资源扩容实验

## 当前结果 — Verified static / offline model

`tools/font_resource.py`新增append-only builder，`tools/build_font_expansion.py`复用既有Font parser、glyph rasterizer、preview、版本门禁和原指令查表模型。两套原Font各追加33个真实bitmap及metric，glyph数量2667→2700；原2667 glyph的bitmap和metric逐字节保持，原range/base前缀、geometry、flags与未知tail保持。

新编码D0A1–D0C1映射glyph2667–2699；新增起点和结束sentinel令range/base数量27→29。原C8FF sentinel保留，其到D0A1区间的base差为零，不占用原韩文槽。

| Font | 原资源大小 | 扩容资源大小 | 扩容SHA256 |
|---|---:|---:|---|
| NormalFont | 282852 B | 286358 B | 81a6bace168e098ff719b490988baf9b0d6a3f785107d92364243320807a8a65 |
| KatakanaFont | 242847 B | 245858 B | 32e017f0a9c2ba8719c135eb095c37fb0df3fc655be6d89a945709657332c16b |

两Font扩容后的真实range/base分别接受33个新增编码，并在原212 B指令模型中核对2411个原双字节成员和128个ASCII，原index不变。cmap、共同基线bounds、非空字形及新metric19全部验证，preview已检查；不等于游戏显示验收。

独立Font阶段仅生成序列化资源；2026-10-09新增独立MrtsEngine.u包接入，见 [包级构建](FONT_PACKAGE.md)。celfid副本与ISO尚未重建，没有执行runtime loader/cache。增长资源不能塞入现有等长slice替换流程，否则会破坏UE2 export offset/size与包布局。原小字集PoC继续使用旧B0映射，原locale文件与实验ISO不改。

## 数据层与门禁

`MappedEncoder`默认仍严格接受旧PoC的已知KR Hangul几何。新增显式`font_tables`选项从实际Font的range/base/count核对code→glyph，不按语言名放宽编码，也不接受未命中表的字节。重复char/code/glyph、ASCII前导、NUL、缺字、控制符保护和旧默认门禁保持。

首次构建被旧encoder正确拒绝D0编码；新增显式Font表校验后通过。没有删除旧校验或将未知编码静默回退。22项新增合成测试覆盖compact长度、追加字形、hash、数组数量、未知tail、原metric保护、uint16容量与显式表校验，工程201项通过。

最大65535 glyph限制来自本builder的u16 base表示与sentinel，不是已验证引擎容量。D0区间仅为当前隔离实验，未设为生产locale映射，不改写既有稳定map。

## 复现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/build_font_expansion.py --iso "<original-KR-ISO-path>" --font C:/Windows/Fonts/simhei.ttf --out work/font-expansion
```

输入Font须匹配现有locale中锁定的SimHei hash；只作本地实验，不分发系统字体或生成资源。起点通过`--range-start`显式指定；追加顺序来自当前33字符map，不新增译文。

输出包括两Font的original/modified独立资源、experimental-map.json、glyph-preview.png和font-expansion.json，全部写入ignored目录。保留原输入，source Font与ISO hash校验前后通过；源码与资源回滚证据保存在ignored `build/font-expansion-13/VERIFICATION.txt`。

## 从实验转入汉化的最短路径

1. **包与镜像接入**：增长Font的UE2 export重定位已静态核对，独立包回读通过；继续同步celfid资源副本，复用上游AFS/manifest/ISO构建，生成独立新增槽PoC ISO。
2. **最小游戏验收**：冷启动测试新增槽中文、ASCII混排、标点、普通剧情、$n、长句、固定槽与可增长FPB；补齐角色显示名/linked资源同步实验，检查字宽、自动换行、存读档与切场景。
3. **受控试译**：上述门禁通过后，优先对已验证parser覆盖的少量UI/剧情进行正式试译，继续显式locale层、术语与控制符校验；其他未知资源保持只读。
4. **扩大文本规模**：试译构建和字库覆盖/容量通过后再扩大批次，不要求先穷尽全部引擎逆向；未知格式与不同渲染路径单独设门禁。

最小中文测试已经存在，不需要再等待完整三版逆向。正式试译尚未启动；新增槽资源构建、package/ISO集成和实际PCSX2验收分别记状态，不提供未经验证的完成日期。无测试环境期间优先推进第1项，不追加无关只读审计。
