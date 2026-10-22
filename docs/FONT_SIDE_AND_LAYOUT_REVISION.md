# 字形横向边界与文本换行修订

## 已验证

- 扫描14683条 reviewed 译文（包括特殊策略、compiled及header字段）；PlayBook可重排正文按 NormalFont 实际metrics计算，使用410px保守对白内容预算。不是所有UI窗口的统一宽度或全游戏实测结论。
- 2992字段、592资源改变换行，589 FPB采用原生完整记录表（包括header）重建文字池，并重定位offset/length；其余3个固定字段保持原字节长度与$n数量，只移动换行位置。所有可见文字及非换行控制的顺序保持。
- 词表最长匹配、完整数字/百分比/倍数、句子及分句优先；单个受保护词组若超过预算即拒绝构建。双换行保留段落；闭合标点前置到上一段末尾再重新测量。
- 两字体各5133字形全部解码检查，4932新增字形的上下和横向有效采样边界非零像素为0；原2667字形、编码、metrics、未知尾部保持原字节。
- full-font-profile.json 新增 horizontal_guard=1。Normal 18px/4×、Katakana 15px/native、阈值、gamma及字重不变。Normal有1773个宽字形在量化前水平拟合到16px墨迹上限，避免直接裁切；这是墨迹宽度变化，不宣称字形逐像素不变。Katakana水平拟合0。
- 两Font及两份唯一启动缓存同步。独立比较新旧ISO的62个文件，仅FILE.AFS和SHIP.AFS变化；LINEAR、ELF、25译制动画与21原始动画保持。
- 原子发布目标：build/test-iso/Magna-Carta-zh-CN-tabs-fixed.iso；新SHA256 3c94275d46b0f74133a9a43cdb9f5eb3493097af032922b375c87f433742ebc7。另一测试ISO保留。

## 推断与验收边界

截图杂线与相邻字形采样有关属于高置信推断；本轮没有同场景游戏执行证明，不能将静态透明边界证明写成视觉验收。冷启动新镜像，先复测卡恩、句末句号、三位一体驱动100%/2倍和教程招式三行，避免旧即时存档继续沿用字形及对白缓存。

## 离线预览错误（已修正）

原数字2的advance=11，而19px存储字格的非零bbox延伸到x16；11..15的像素原字库已存在，并非本轮新增。旧预览以11px步进却绘制整个19px掩码，造成覆盖邻字的多余笔画。render_font_preview.py现在只绘制[0,advance)；检查图重新生成，原数字字形和ISO不因预览错误而改变。该逻辑仅为离线metric-width展示，不伪称完全模拟运行时纹理采样。

## 可复现工具

- tools/rebuild_mapped_font.py：现有机制新增横向守护，保留旧profile默认行为。
- tools/plan_text_layout.py：读取locale目录、NormalFont、映射、FILE/SHIP指纹及locale的text-layout-config.json，生成绑定计划。
- tools/apply_text_layout.py：严格核对两个输入AFS及每条源窗口，重建FPB/同长度定槽，并检查缓存副本；增长的缓存资源拒绝隐式处理。
- tools/render_font_preview.py：2-bit解码、有效宽度绘制、整数倍最近邻。

```powershell
$py = 'work/venv/Scripts/python.exe'
& $py -X utf8 tools/plan_text_layout.py --locale-dir locales/zh-CN --font $NormalFont --map $Mapping --file $FontFileAFS --ship $BaselineShipAFS --config locales/zh-CN/text-layout-config.json --out $LayoutPlan
& $py -X utf8 tools/apply_text_layout.py --file $FontFileAFS --ship $BaselineShipAFS --profile $LayoutPlan --out $OutputAFS
```

输入使用既有稳定构建的翻译AFS及映射；规划在文本回填、字体整合之后，ISO打包之前运行。原版ISO版本锁定和稳定构建步骤沿用BUILDING.md及184/187/188/189文档。精确本机命令、hash、测试、隔离回滚、预览和输入计划存于work/font-side-190/VERIFICATION.txt；不提交完整游戏资产。
