# 美版高清贴图在韩版中的复用

## 已验证

2026-10-11，本地 PCSX2 2.8.2，韩版 SCKA-20043 / AE86E04C，当前中文测试 ISO。
用户提供的 SLUS-21221 包包含 1722 张 DXT5 DDS，合计 1,383,615,744 字节。
原包作者、版本及再分发许可未随目录提供；包仅在本地使用，不进入仓库。

模拟器的贴图根目录此前指向 `SCKA-20043/replacements`，层级过深。
PCSX2 会在根目录后追加游戏编号及 replacements。当前已改为项目下的 `pcsx2/textures`，
韩版包位于 `pcsx2/textures/SCKA-20043/replacements`。

工具将旧式 `r<64-bit region>` 转为 `r宽x高`，去掉 PCSX2 已忽略的旧 TCC 位 0x4000。
纹理数据哈希、CLUT 哈希及其他格式位全部保持；DDS 内容逐文件 SHA-256 相等。
并非将美版哈希猜改成韩版哈希。这里的名称规范化只是 PCSX2 已支持的同一键表示法。
依据：[PCSX2 2.8.2 名称解析及目录代码](https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2/GS/Renderers/HW/GSTextureReplacements.cpp)、
[SourceRegion 定义](https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2/GS/Renderers/HW/GSTextureCache.h)。

隔离配置、无手柄输入、无存档的 60 秒冷启动导出 28 个纹理键，其中 4 个完整键匹配高清包：
羽毛、光斑、背景纹理及厂商图标。相同启动启用包后导出其余 24 张，逐文件内容相等。
独立故障注入将这 4 张替换文件设为无效 DDS，模拟器逐一报告对应的加载失败；
使用原有效 DDS 后没有替换加载失败，且模拟器报告压缩替换纹理的 mipmap 提示。
这验证替换请求与有效资源加载路径，不等同于最终屏幕效果或全游戏覆盖验收。
启动标题中文图、中文提示及已汉化 UI 图集仍使用原中文资源，没有在本次观察中被美版包覆盖。

完整包已安装，但未在这次冷启动出现的 1718 张尚未逐场景验证。
若某处韩版源纹理或调色板与美版不同，该处不会命中，不会强行套用相似纹理。
未改 ISO、引擎、中文文本、字库或游戏布局。

## 本地使用

在 PCSX2 图形设置中启用“加载纹理替换”，使用硬件渲染器；本机 Vulkan 已启用。
贴图目录选择 `pcsx2/textures`，不要选择游戏编号或 replacements 子目录。
关闭游戏后重新启动当前中文测试 ISO。实际走到场景、菜单和战斗中检查；
本次自动启动停留在无记忆卡提示阶段，不作为这些流程已通过的依据。

本机使用同卷硬链接，新增安装包不再占一份约 1.29 GiB 的 DDS 数据。
不要原地编辑安装目录或原包里的 DDS，因为硬链接共享内容；需要修改时先复制到独立文件，
再替换目标文件。本地安装清单与原始 SHA-256 位于 `work/hd-texture-186/MODIFIED_FILE.json`。

## 复现和恢复

```powershell
python tools/port_texture_pack.py `
  --source C:/Users/noway/Downloads/Magna_Carta_HD_Textures/SLUS-21221/replacements `
  --dumps work/hd-texture-186/baseline/textures/SCKA-20043/dumps `
  --target work/hd-texture-rebuild/SCKA-20043/replacements `
  --manifest work/hd-texture-rebuild/manifest.json
```

默认复制；`--hardlink` 显式启用同卷硬链接。目标目录必须不存在，禁止覆盖既有包。
`--dumps` 只计算观察到的完整键匹配率，不根据近似图片或哈希前缀自动生成别名。

本次本地撤回：`python work/hd-texture-186/rollback.py`，或 Git Bash 执行
`work/hd-texture-186/ROLLBACK.sh`。脚本先校验全部安装文件，再删除安装链接并恢复原
`[Folders] Textures` 行；其他模拟器配置保持，外部原包不删，测试 ISO 保持。
文件或贴图路径被后续修改时脚本中止，不盲目覆盖。已在另一份硬链接安装及配置副本上验证恢复。

未命中区域的后续调查应开启 PCSX2“转储可替换纹理”，使用独立空替换目录，
在实际目标场景导出原尺寸纹理。必须先比较完整键和原图，再确定区域差异。
不可简单去掉 CLUT 哈希，也不可把美版英文菜单贴图覆盖到中文菜单。

证据：`work/hd-texture-186/VERIFICATION.txt`、三次隔离启动的 emulog/result、
`runtime-comparison.json`、安装清单与恢复记录。完整纹理包、导出图、BIOS及配置备份仅本地保存。
