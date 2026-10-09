# 思源黑体接入与对照镜像

## 字体输入

Adobe Source Han Sans SC Regular，固定版本 `2.005R`，官方 OTF：
[SourceHanSansSC-Regular.otf](https://raw.githubusercontent.com/adobe-fonts/source-han-sans/2.005R/OTF/SimplifiedChinese/SourceHanSansSC-Regular.otf)。
SHA-256：`f1d8611151880c6c336aabeac4640ef434fa13cbfbf1ffe82d0a71b2a5637256`。

许可证为 SIL Open Font License 1.1。完整版权声明/许可保存在 `assets/fonts/SourceHanSans-LICENSE.txt`，固定来源与 hash 保存在 `assets/fonts/source-han-sans.json`。字体文件仅位于 ignored `work/fonts/source-han-sans-2.005R/`，不进入 Git。
字形派生数据采用 OFL 1.1，派生字体的主要名称不得使用保留名 Source；原游戏 Font export 身份不因换字体而改名。开放字体许可不改变游戏原始资源或上游代码的许可边界。

## Verified static

新配置 `locales/zh-CN/opening-trial-02.json` 保持 91 个正文 target、1 个角色姓名及全部原控制符不变，仅换字体输入与栅格尺寸。317 个追加字符的编码顺序、两 Font 原 2667 个 glyph/metrics/映射保持。

直接采用旧字号时 KatakanaFont 中的“意”越过共同 baseline 边界，构建在生成 ISO 前拒绝。逐字 bbox 检查后采用 NormalFont 19 px、KatakanaFont 15 px；字宽仍为 19。`font_raster_sizes` 是可选的 locale 配置，缺省保持旧字号，不关闭裁切门禁。

两 Font、UE2 export、六段 celfid 缓存、AFS manifest、ISO9660/UDF 和不信任中间报告的独立推导均通过。五阶段只生成一份新 ISO，不复制完整镜像进行回滚。

镜像：`build/opening-trial-02-source-han/image/MODIFIED_FILE.iso`

- 大小：3,232,737,280 B。
- SHA-256：`0c2d8ebf005fb3a9bfbe12f19525594834c9e3b7c094cb9b6d749d20c910dcb2`。
- 状态：独立静态验证通过；PCSX2 未验收。
- 与上一版区别：相同译文、相同映射，中文 glyph 换为思源黑体。101 个新菜单草稿尚未进入此镜像。

## 最短字体对照

冷启动新镜像，检查空存档提示和开场对白的粗细、辨识度、标点、行距、裁切与下一页末尾。旧版截图不转移为新版字体验收。保存/读取、实际场景切换、战斗和完整字符覆盖继续分别记录。

## 重建

```powershell
New-Item -ItemType Directory -Force work/fonts/source-han-sans-2.005R
Invoke-WebRequest https://raw.githubusercontent.com/adobe-fonts/source-han-sans/2.005R/OTF/SimplifiedChinese/SourceHanSansSC-Regular.otf -OutFile work/fonts/source-han-sans-2.005R/SourceHanSansSC-Regular.otf
work/venv/Scripts/python.exe -X utf8 tools/build_poc_pipeline.py --iso "<original-KR-ISO-path>" --font work/fonts/source-han-sans-2.005R/SourceHanSansSC-Regular.otf --locale locales/zh-CN/opening-trial-02.json --out build/source-han-trial
```

构建入口严格验证字体和 ISO hash。生成字库可随批次增量推进；最终发布库存从全部经审核 target 汇总，保留既有编码，并检查缺字、容量和布局，不必等待全篇翻译才开始字体生成。
