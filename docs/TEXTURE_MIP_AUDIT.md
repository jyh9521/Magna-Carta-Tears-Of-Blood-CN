# 普通 UE2 纹理载荷核查

## Verified

韩版 FILE.AFS SHA-256 `a9f7e2b34bfb5475bab2793821520295d120e2a122ccd363812f2d03c025072b` 的普通包共有 28 个 Texture、27 个 Palette。18 个位于 temple.utx，6 个位于 Editor.u，MrtsEngine.u 与 UWindow.u 各 2 个。全部 Texture native 尾部闭合，共 191 个 mip；所有 lazy end 与原包绝对像素结束位置相等，未出现尾随字节。全部 Palette 为 256×4 B。

属性 None 之后：compact mip_count；每级依次为 u32 lazy_end、compact pixel_count、pixel_count B 索引像素、u32 width、u32 height、u8 UBits、u8 VBits。实测 pixel_count=width×height，尺寸=2^bits；相邻 mip 尺寸减半且最小为 1。首级 USize/VSize/UBits/VBits 与属性逐项匹配。Palette 通过正 export reference 关联，native 区为 compact count=256 与 1024 B 颜色。

28 个首级 PNG 及 4 张全分辨率联系表均已读取检查；其余 163 个小 mip 完成结构/hash 检查，尚未逐图检查。

| 资源 | 观察 | 处理 |
|---|---|---|
| FILE/Editor.u/export/32，Bad | 烧录英文 `BAD SIZE` | 独立图片参考标签，游戏运行可见性未验证；未加入正文或改图 |
| FILE/MrtsEngine.u/export/7239，Texture0 | 拉丁字母、数字、符号 glyph atlas；outer=NumberFont | 字形集合，不按整幅文字句子计入翻译条数 |
| 其余 26 个首级 | 场景材质、图标、背景、纯色；未观察到语言短句 | 仅首级视觉观察，不扩展为所有游戏图片无文字结论 |

## High-confidence deduction

单字节索引配 256 色 Palette 的尺寸关系支持 P8 布局。BGRA→RGB 用于审阅视图，alpha 不参与预览；原色字节与 hash 保留。实际平台调色板通道、mask/alpha 渲染与运行调用未以模拟器对照确认。

## 尚未闭合

流式包 11890 个 Texture occurrence 的 serial 映射不适用普通包 absolute lazy end 读取，尚未完成；特殊 font bitmap 不属于本轮 28 Texture 集合。首级可读不证明小 mip、流式图片、SFD 字幕或全游戏文本穷尽。`complete_game_text=false`，翻译门禁仍为 `coverage-audit-pending`。

## 复现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_texture_mips.py --archive work/kr/FILE.AFS --out work/texture-mip-audit
```

输出须为 ignored work/build 下空目录。完整纹理及 PNG 只保存于 ignored 输出，不进入 Git；仓库只保留只读工具、合成测试、聚合统计及事实记录。不修改原 AFS、原 ISO 或现有测试镜像。结构闭合结论来自韩版逐载荷验证，复用既有 AFS、package table、property reader；未复制第三方实现或声称上游为该布局提供独立运行验收。
