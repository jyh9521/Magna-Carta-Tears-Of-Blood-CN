# celfid 原生尾部 P8 纹理有界核查

## Verified

3214774–3217619 的 2845 B 区段按现有属性 tag 与严格 P8 规则完整读取，随后 3217619–3218646 为 1027 B Palette，恰好接上已验证的单记录原资源链。属性 Palette=2 与相应纹理包的 Palette6 export 对应；4 mip 的尺寸、bit count、像素数、逐级减半与原 lazy offset 全部一致。原始包表记录 range_256／serial offset 403／size 2845，但没有独立普通包正文作同字节对照，因此运行对象身份仍非独立验证。

4 个 mip：16×128／2048 B、8×64／512 B、4×32／128 B、2×16／32 B。第一层为 lazy→count→pixels→dimensions，其余为 lazy→dimensions→count→pixels。后者 lazy 字段仍计原始 pixels-before-dimensions 的逻辑终点，不是实际流中像素终点。两种布局均按 bounds、尺寸、像素数、lazy 和前层几何检查，只有唯一匹配才接受。

全部 4 张逐像素图已检查，呈深色渐变带，未发现完整文字候选。图像使用既有 BGRA 调色板显示解释，不宣称实际 PS2 采样路径已验证。纹理及 Palette 源哈希见配套 JSON。

## High-confidence deduction

前期普通包对应纹理只观察到宽高同时不超过 8 的 mip 重排；此区段明确出现宽度不超过 8、但高度为 64／32／16 的重排。将先前观察当成全局宽高阈值会在第二层错误解读 pixel count。本次只接受逐记录唯一几何匹配，没有把宽度阈值写成通用引擎规则。

## 未闭合部分

此处闭合的是纹理与调色板字段几何，不是前面的 StaticMesh 完整边界、碰撞或渲染数据语义，也不是整个 celfid loader。未发现图像正文不代表全游戏不存在其他位图文本。complete_game_text=false。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_stream_texture.py --file work/kr/FILE.AFS --out work/stream-texture-tail-audit
```

固定原档及 celfid 哈希检查通过后输出 4 张小型 mip PNG 与 summary.json；输出重新打开验证。原档保持只读，不生成 ISO。工具复用既有属性、P8 Palette 和图像显示逻辑。
