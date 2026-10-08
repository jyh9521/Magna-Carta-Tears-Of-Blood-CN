# 增长Font的UE2包接入

日期：2026-10-09。状态：Verified static；运行时加载、celfid同步与ISO接入未验证。

## 实现与证据

`tools/package_resource.py`提供显式hash/version门禁的export替换；`tools/build_font_package.py`从原ISO复用上游AFS读取、既有package_tables与Font扩容验证，不重写AFS或ISO builder。
当前支持观察到的version118/licensee15、flags1非压缩布局；未知版本、flags、越界/重叠export、未知index、空payload和零长度目标拒绝。

原package全部bytes保持，只有header @24的export table offset改变；两个增长Font追加到EOF，随后追加新export表。目标entry保留class/super/outer/name/flags原bytes，仅重编码serial size/offset；其他7666个export metadata和payload逐字节保持。name/import表、原export表、旧Font payload和未知尾部保持原位，不进行整包紧缩。
旧Font payload仍在包内，但新export指向追加资源。该策略避免compact offset编码长度变化导致原布局的迭代重定位，代价是保留旧资源导致包体增长；不是最终空间优化方案。

| 字段 | 原包 | 修改包 |
|---|---:|---:|
| 包大小 | 2058129 B | 2713665 B |
| export表起点 | 1934811 | 2590345 |
| export数量 | 7668 | 7668 |
| NormalFont index735 offset/size | 129483 / 282852 | 2058129 / 286358 |
| KatakanaFont index736 offset/size | 412335 / 242847 | 2344487 / 245858 |

原包SHA-256：`81c25a54174d0fe7736d324a29862a7b0302df9c03ef54cd5f97bcbc2360d9c1`。
修改包SHA-256：`137c3ff27918715268e3f72e895426b6733aa3c309877d8df89f017b5258faba`。
两Font各2700 glyph，新增D0A1–D0C1；原韩文bitmap/metrics和原code→glyph保持，详见 [Font扩容](FONT_EXPANSION.md)。

17项合成测试覆盖hash/version/flags、compact边界、EOF表、旧bytes/零长度export保持、非法index/payload/表偏移和截断，工程218项通过。真实包重新解析7668个entry，两个目标payload与独立Font扩容产物完全一致；干净源码副本复现相同包hash。

## 复现

先运行BUILDING.md中的独立Font扩容命令，再运行：

```powershell
work/venv/Scripts/python.exe -X utf8 tools/build_font_package.py --iso "<original-KR-ISO-path>" --expansion-dir work/font-expansion --out work/font-package
```

输入包含原ISO、版本profile和上一命令生成的Font扩容report/两Font。原ISO只读；输出original-FILE.AFS、MrtsEngine.original.u、MrtsEngine.modified.u和font-package.json仅放ignored work/build。系统字体和完整游戏包不进入Git。
源码回滚恢复201项基线；另一个独立包副本恢复原包hash，修改包保持。事务在ignored `build/package-font-15/VERIFICATION.txt`。

## 证据边界与下一步

**Verified static**：真实包的export元数据和payload回读、无关export保持、独立Font身份、输出可复现；celfid解压buffer不包含完整原MrtsEngine.u副本，不能使用整包搜索替换。
**High-confidence deduction**：保留原对象index和entry前缀有利于保持UE引用关系；原byte不动与回读一致不等于runtime loader接受追加表。
**Unverified hypothesis**：引擎接受新表位置和增长Font、运行时cache容量，以及启动bundle实际资源索引/长度更新机制。

下一步定位celfid资源记录的边界与长度元数据，防御性更新Font副本，之后复用上游AFS slot0 manifest和ISO构建。当前没有生成新增槽ISO；旧text-poc-02继续保留，旧槽截图不验证本包或新增槽容量。

2026-10-09更新：celfid六段增长候选已静态同步；AFS增长触发真实混合ISO/UDF relocation回读失败，预检现于写入前停止。详见 [缓存与ISO门禁](FONT_BUNDLE.md)，不作为运行时包加载验收。

2026-10-09后续：增长package与celfid候选已接入带UDF同步的新ISO，两文件视图回读通过，runtime仍未验收。见 [新增槽镜像](QA_EXPANDED_POC.md)。
