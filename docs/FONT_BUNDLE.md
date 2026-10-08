# 增长Font的启动缓存候选与ISO门禁

日期：2026-10-09。状态：Verified static fragment overlay；缓存流语义与运行时加载未验证。ISO构建预检因UDF同步缺口停止，没有新的可验收ISO。

## celfid片段证据

复用上游decompress_chunked/recompress_chunked、AFS读取和既有Font/UE2工具。原bundle解压4195112 B，SHA-256 `04ed29c9c4e65b1f14c4c2ae4b8578ad147af42b7dbaecdc62f57a3af56e3536`。
原engine完整包在bundle中出现0次，但64 B包头、完整export表和两个Font serial各出现1次。路径`../System/UFile/MrtsEngine.u`的128 B NUL填充名称及u32原包大小组成132 B记录，出现2次。两Font相邻位置与原package的serial顺序一致；这些是字节匹配事实，不等于完整缓存格式解析。

`tools/bundle_resource.py`新增hash门禁和不重叠片段overlay；`tools/build_font_bundle.py`同步下表六段。其余区间按新位置逐字节核对，保持不变。

| 片段 | 原buffer位置 | 原长度→新长度 |
|---|---:|---:|
| 文件大小记录0 | 751393 | 4→4，2058129→2713665 |
| 文件大小记录1 | 751525 | 4→4，2058129→2713665 |
| package header | 751529 | 64→64 |
| export table | 835001 | 123318→123320 |
| NormalFont serial | 1212059 | 282852→286358 |
| KatakanaFont serial | 1494911 | 242847→245858 |

新解压buffer4201631 B，SHA-256 `59c2f16ef21defc3c965e4ed7bb6eac052b28a2036c842b041e4b747f0feed59`。
压缩celfid：1239770→1104696 B，新SHA-256 `eff38902d830d1add74d8f97c878d9689f5add390bcd3c80319178e290d62f53`；上游压缩往返完全一致。
**High-confidence deduction**：这些片段构成package加载缓存的一部分，文件大小记录需与实际package保持一致。
**Unverified hypothesis**：六段更新已经覆盖全部缓存读取状态；运行时seek/缓存调度、Font增长和cache容量仍须冷启动验收。未将片段匹配描述为完整LIX parser。

## AFS/ISO集成尝试与失败证据

`tools/build_expanded_locale.py`复用上游AFS/slot0 manifest/ISO writer和既有FPB/fixed-slot/字宽估算器。仅沿用原三个测试目标，使用D0追加槽映射，不新增译文；UI完整bundle副本同步。FILE.AFS为22239232 B，大于原21716992 B；SHIP.AFS保持45686784 B。
第一次实际构建走1 in-place、1 relocation，ISO大小3210412032→3232651264 B；pycdlib回读报`Expected at least 2 UDF Anchors`。失败样本仅保留于ignored `build/expanded-text-poc-03/REJECTED_UDF_RELOCATION.iso`，不作为可测试版本。
原镜像包含UDF，anchor位于LBA256及1567583；ISO增长后原尾部anchor不再位于新尾部。UDF文件树中存在`File.afs`及`Ship.afs`；仅更新ISO9660的extent/size与PVD、清空旧slot会留下UDF文件引用不一致，添加尾部anchor本身也不充分。

`tools/iso_validation.py`增加ISO9660 in-place/relocation的payload、padding、PVD及全镜像未修改区间验证；10项合成ISO测试含UDF预检。混合UDF镜像的size变化在写ISO前拒绝，负向实测退出1且MODIFIED_FILE.iso不存在。该门禁用于阻止不一致输出，不作为UDF修复完成证据。

## 复现

先完成 [Font扩容](FONT_EXPANSION.md) 和 [UE2包构建](FONT_PACKAGE.md)，再运行：

```powershell
work/venv/Scripts/python.exe -X utf8 tools/build_font_bundle.py --iso "<original-KR-ISO-path>" --package-dir work/font-package --out work/font-bundle
```

输出bundle.original/modified.bin、celfid.original/modified.lix和font-bundle.json仅保存于ignored work/build。
集成预检命令：

```powershell
work/venv/Scripts/python.exe -X utf8 tools/build_expanded_locale.py --iso "<original-KR-ISO-path>" --expansion-dir work/font-expansion --package-dir work/font-package --bundle-dir work/font-bundle --out build/expanded-text-preflight
```

当前韩版输入预期结果：`UDF size/relocation metadata synchronization required before ISO build`，退出1，不生成ISO；AFS候选用于静态检查，不能替代可用镜像。
14项缓存合成测试和10项ISO测试新增后工程242项通过；干净源码复现缓存bytes/hash，源码回滚恢复218项基线，独立celfid副本恢复原压缩bytes/hash。事务位于ignored `build/bundle-font-16/VERIFICATION.txt`。

## 下一步

保留上游AFS/ISO实现，针对混合镜像新增小范围UDF metadata同步：两套文件视图的extent/size、allocation descriptor、partition/integrity状态、尾部anchor和descriptor CRC/checksum分别核验。补齐合成混合镜像与真实韩版回读后，再生成新增槽测试ISO。原ISO、旧text-poc-02、ELF、locale文件和现有tag保持；没有新增运行时验收或批量翻译。
