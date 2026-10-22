# 菜单文字与字库存储填充修正

## Verified

本轮按资源分别处理，不全局移动字库，也不改译文或字号。

- `MrtsGameInfoWindow.NewFontObj` 默认选 KatakanaFont，顶部 HelpObj 使用该默认；`MrtsFieldMainPageWindow.ObjB`（时间）明确选 NormalFont。时间不是数字贴图。
- 两套 Font 的字宽之外存在非零存储数据，包括 KatakanaFont 空格的一个像素，以及 NormalFont 数字槽的尾部数据。全量扫描各5133字形，清除 NormalFont 30650、KatakanaFont 5636个填充像素。范围是每行 `[advance, row_stride*4)`，包含第20个打包填充像素；`[0, advance)`所有像素逐位保持。元数据、原2667字形的有效笔画、2466新增字形、编码、步进和未知尾部保持。**原字形的填充字节有修改，不能继续声称原2667字形全部字节保持。**
- `MrtsFieldTabControlVTabArea.DrawItem`（export12210）的字幕纵坐标5改4。四个信息按钮字墨迹纵范围1..18，按钮高27，坐标4时墨迹中心13.5，等于按钮中心。没有移动按钮或横向坐标。早期试配上移3px不是最终输出，最终是上移1px。
- `MrtsFieldCharListBox` 的 CharInfo、Style、Equip三个状态 DrawItem（12302/12303/12304）中，四种属性标签每种五个文字/描边调用共60个Y操作数上移2px。数字和下方横条的坐标保持；主体与描边同步移动。物攻/物防最下描边由24变22，魔攻/魔防由47变45，避免覆盖24/46起始横条。
- `field_part1` 的魅力贴图 UV `(51,128,55,16)` 在00001002.lin、00065533.lin两个副本一致。旧RGB缩小后索引量化改为coverage-mask、threshold48、edge_guard1；使用可配置color调色板选择保留金色。清理仅限原55×16矩形，非目标像素、调色板、包表与其他标签保持。
- 普通两Font、四个函数和对应celfid启动副本同步，函数长度、VM token位置与虚拟长度不变。缓存使用既有全对齐一致性方法，不把它宣称为独立缓存解码器。

原版到当前canonical字体构建已经重复执行，输出逐字节等于此次字体副本。默认 full-font-profile 追加 `bitmap_padding: zero-outside-metric`，不改变A-medium-mixed栅格化参数；历史profile没有此字段则仍保留填充。build_font_expansion、rebuild_mapped_font与verify_expanded_locale共用同一清理函数。仅字体覆盖工具明确增加`--padding-cleanup`，默认仍拒绝原字形字节改变；启用时也拒绝有效笔画改变。

## 推断与实际验收边界

填充像素是已验证的数据缺陷；FontObj原生转换存在metric+spacing裁剪候选，故清理可能消除邻字/末尾竖线，但**本轮没有复现截图同场景的GS采样，不能证明全部运行时竖线已消失**。上一轮只检查新增中文字形，漏掉原ASCII/空格及打包填充，这是本轮检查范围的补充。顶部六个图形标签底边修正保持stage191结果，不与本轮顶部说明文字混淆。

按钮中心计算和属性横条避让是原生坐标/字库静态证明；实际缩放、过滤、FontObj缓存页边界仍需要本ISO冷启动同场景验收。旧即时存档可能带旧资源缓存，不用它作为新版首次验收。

## 重建与恢复

1. `tools/build_font_expansion.py --iso ORIGINAL --font MEDIUM_OTF --locale locales/zh-CN/full-font-profile.json --out FONT_DIR`。隔离字体升级使用`overlay_font_resources.py --padding-cleanup`；严格验证原有效笔画。
2. `tools/overlay_ui_render_revision.py --file BASE_FILE --profile locales/zh-CN/proofreading/ui-render-revision.json --font-dir SANITIZED_FONT_DIR --out OUTPUT`，阶段输入FILE指纹明确锁定190；旧/新整数及函数哈希全部检查。回放旧阶段时先按旧profile构建，再应用本轮受控覆盖，避免重复修改坐标。
3. `tools/build_text_texture_overlays.py`复用现有图片配置；本轮增量hash配置在work/ui-render-192/overlay-profile.json，输入191 LINEAR。
4. `tools/build_test_iso.py`使用192 iso-input-plan和187已验收动画清单。SHIP译文、ELF、46部影片均保持。现有测试镜像实际名称是Magna-Carta-Tears-of-Blood-zh-CN-test.iso。

隔离回滚从baseline-source.zip恢复完整源文件，FILE/LINEAR副本恢复190/191输入哈希并运行基线测试。正式ISO不在回滚测试中被改动；必要时用191冻结输入计划重建上一版。源码差异、命令、字节/像素证明及恢复证据在work/ui-render-192，生成资源不提交。
