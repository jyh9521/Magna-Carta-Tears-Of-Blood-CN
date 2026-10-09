# 普通包本地 Class 引用的纹理覆盖修正

## Verified

既有普通包纹理工具只接受 import class 名称，遗漏 Engine.u 以正 export reference 指向本地 Texture／Palette Class 的资源。原表身份不修改，新增只读 class 名称解析并验证引用范围及目标 Class 类型；mip 复核工具同步使用该解析。

全普通包重新核查后为 37 个 Texture、35 个 Palette、212 个 mip。此前 28／27／191 的统计仅覆盖 import-class 子集，不是全普通包总数。新增 Engine.u 9 个纹理、8 个调色板、21 个 mip，其中 12 个较小 mip 全部按原尺寸导出并检查。

新增首 mip 图像检查确认：WhiteSquareTexture、BlackTexture、ConsoleBdr、ConsoleBk 为纯色；MrtsShadow 为环形效果；AttackRTex 为渐变；export 4034／4035／5482 的 Texture0 为三个 Latin／符号字形图集。没有新增整句图片文字候选，不把字形排列作为正文导出。该结论只覆盖所检查图像，不表示运行时所有图片文字已覆盖。

## High-confidence deduction

正本地 Class 引用与负 import Class 引用共同构成普通包实例分类，按显示 class 字符串过滤会低估原生对象数量。该修正有助于后续 Font／Texture 结构核查。

## Unverified hypothesis

三个新增图集的全部运行使用路径和 glyph metrics 尚未逐项确认；streamed／LINEAR 原生纹理和 CG 全画面文字仍是独立覆盖项。未放行全文门禁。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_texture_mips.py --archive work/kr/FILE.AFS --out work/local-class-textures
work/venv/Scripts/python.exe -X utf8 tools/audit_mip_views.py --archive work/kr/FILE.AFS --manifest work/local-class-textures/textures.json --out work/local-class-mips
```

生成图像仅保留 ignored work/build。此前 28 个纹理的检查记录保持有效，但覆盖总数以本次重新读取为准。
