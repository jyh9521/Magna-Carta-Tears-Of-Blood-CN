# 默认字体 A-medium-mixed

## 选定配置

当前构建复用 `locales/zh-CN/full-font-profile.json`，其 `fonts` 对象直接复制自用户选定的实验 `work/font-render-experiment-183/shortlist/A-medium-mixed/profile.json`。未另建平行默认配置。

| 字库 | 字体 | 字号 | 栅格化 | 字格 | 步进 |
|---|---|---:|---|---|---|
| NormalFont | Source Han Sans SC Medium 2.005R | 18 px | 4 倍超采样、Lanczos | 19×21 | 正文18，七种标点10 |
| KatakanaFont | 同上 | 15 px | 原生旧路径 | 19×18 | 同上 |

NormalFont 仅设置 supersample=4，沿用默认 gamma=1、量化阈值43/128/213、增粗0；KatakanaFont 保持无 raster_options 的旧量化路径 `(v*3+127)//255`，不是强行添加同一组阈值。最终均为原2-bit四级灰度，每行5字节。字体输入 SHA-256：`1df61d31687d04fd2f928a3bb6ca6cd61f0e988cc267cf317f32406edbb49f70`。

## 可复现生成与集成

```powershell
work/venv/Scripts/python.exe -X utf8 tools/build_font_expansion.py --iso '마그나카르타 - 진홍의 성흔.iso' --font '<SourceHanSansSC-Medium.otf>' --locale locales/zh-CN/full-font-profile.json --out work/font-default-184/default-fonts
work/venv/Scripts/python.exe -X utf8 tools/overlay_font_resources.py --file work/ui-font-182/integrated-afs/FILE.AFS --expected-sha256 bbcad1f225511a36d309b17fa6d14f6111954a79c5294f5974f63a0bf6605408 --base-font-dir work/font-default-184/fallback --font-dir work/font-default-184/default-fonts --out work/font-default-184/integrated-afs
work/venv/Scripts/python.exe -X utf8 tools/build_test_iso.py --iso '마그나카르타 - 진홍의 성흔.iso' --profile profiles/scka-20043.json --input-plan work/font-default-184/iso-input-plan.json --movies work/visible-text-153/accepted-movie-overrides.json --out work/font-default-184/test-iso-candidate
```

输出目录必须为空；重跑应改用新的输出目录并同步输入计划的路径/哈希。OTF 由使用者提供，工具校验精确输入指纹，不自动下载或换字体。现阶段完整汉化链依赖此前阶段的已验证输入，尚不是干净检出的一条命令发布构建。

生成器在有 fonts 配置时复用 rebuild_mapped_font 的栅格化逻辑，无 fonts 的历史配置仍走原路径。原2667字形逐字节保留，2466新增字形沿既有映射生成，两套各5133字形。新输出与选定实验的两份完整字库逐字节相同。

overlay_font_resources 防御式校验源AFS、旧字库、几何与所有metrics/tail，只更新两套追加字形bitmap及各一个唯一启动缓存副本；celfid 解压缩往返验证。FILE.AFS 只有 AFSFileIndex.idx、MrtsEngine.u、celfid.lix 成员变化；引擎包不是引擎可执行文件，其变化限Font序列。所有包外间隔与其余成员保持。ISO62文件中仅FILE.AFS内容变化，SHIP/LINEAR、25中文影片/21原片、ELF、译文及剧情/战斗脚本与前版相同。

## 已验证与回退

- 基线1964、修改1972、隔离源码回滚1964项测试通过。
- ISO9660/UDF回读及非目标字节验证通过；独立对照前版62文件、两实验字库、映射与106受保护输入通过。
- 当前ISO：build/test-iso/Magna-Carta-zh-CN-test.iso，4250691584字节，SHA-256 `ff00bdff03ff455aaed77986a8795d94efa4dca0e0fd7462bb2d0685218b673f`。
- 宋体完整ISO、两字体、旧配置和报告保留在 work/font-default-184/fallback。旧ISO hash `dcf769e5d15ee3a548a48137e1ead344ffad2f0b1116f1891a83b28d7950b43e`。
- `work/font-default-184/ROLLBACK.sh <新的work目录中的恢复ISO路径>` 只在独立副本验证恢复，不改当前ISO。源码基线zip同时保留本任务前已有修改，而非回到GitHEAD。经确认要切回宋体时，可原子复制此备份ISO到测试路径，并恢复对应报告/哈希；重新生成宋体继续使用 serif-font-profile.json。
- 完整命令、输出、退出状态与输入见 work/font-default-184/VERIFICATION.txt。

## 运行检查边界

运行检查使用隔离PCSX2配置、禁用纹理替换、冷启动新ISO，不加载旧即时存档。日志与结果保留在 work/font-default-184/runtime-probe-2；独立诊断启动并非菜单、正文、换行及全部场景的视觉验收。实际检查应从新ISO冷启动：标题后进入正常存档/新游戏，查看没有存档、读取提示、姓名、道具、流派与人物介绍，同时核对普通字体和小字体的清晰度、标点及裁切；最后正常存读档。旧即时存档可能保留旧RAM中的字体，不能代替首次冷启动。
