# 菜单图片与宋体试用修正

## 本版变化

- 六个顶部标签：编成、道具、装备、流派、信息、设置；另补整理与魅力。
- 使用 Adobe Source Han Serif SC Regular 2.003R。输入 SHA-256 为 `78aa7a328fd974df2d688c8a9fd74a33d8334dfa84ab24d9d11efb2ffc464117`，许可 OFL 1.1，见 assets/fonts/SourceHanSerif-LICENSE.txt。来源：https://github.com/adobe-fonts/source-han-serif/releases/tag/2.003R 。OTF 为外部构建输入，不入库。
- 两套字体仍各 5133 字形，仅重绘映射中的 2466 个新增字符；原 2667 字形、编码顺序、表和未知尾部保持。正文参考字墨迹顶部置于 0，中文 advance 为 18，常用标点为 10；实际墨迹逐字验证不超字体格。
- 原思源黑体两套资源、映射与配置备份在 work/ui-font-182/sans-backup；同目录 Magna-Carta-zh-CN-sans.iso 保留上一版完整测试镜像。
- 地系符咒说明改为“我方一人恢复井然有序，$n解除混乱状态。”；角色评语将“总得有人照顾他们。”放在同一显式行，四个原 $n 保留，最后一个移至末尾。
- 好感标签绘制横坐标操作数由 244 调为 241；46px 框内两个 18px advance 的逻辑中心为 259。纵向通过字体墨迹位置调整。

## 已验证的资源与消费者

顶部标签来自 field_part1 图集，并非已经翻译的普通 caption 字段。MrtsFieldSentinelWindow.SetDefaultTexture 绑定 1002；MrtsFieldTabControlHTabArea.DrawItem 使用 46×21 图块。MrtsFieldButtonListBox.Paint 的整理图块在 global_part1，UV 为 (219,122,36,18)。魅力图块位于 field_part1 的 (51,128,55,16)，被角色列表及升级信息页引用。

00001002.lin 与 00065533.lin 各含同一 field_part1 副本，均更新；00001008.lin 的 global_part1 更新整理。三个流、15 个矩形采用源 hash 绑定。索引 0 是透明遮罩，索引 1 保留暗色轮廓；原调色板、非目标像素、包属性与表保持。

好感横坐标来自 MrtsGame.u export 12302，MrtsWindowStateCharInfo/MrtsFieldCharListBox 的 DrawItem，函数内偏移 3521。IntConstByte `2cf4` 改为 `2cf1`，长度不变；普通函数和唯一可重建的 celfid 前缀同步，重新解析通过。不是对未知镜像盲写偏移。

## 复现与验证

1. tools/rebuild_mapped_font.py：以 locales/zh-CN/serif-font-profile.json、此前完整字库与映射、指定 OTF 重绘，生成两套字体。独立重复构建逐字节相同。
2. tools/build_text_texture_overlays.py：按 locales/zh-CN/images/field-ui-texture-profile.json 生成索引图替换。
3. tools/apply_ui_layout_copies.py：按 locales/zh-CN/proofreading/ui-layout-revision.json 同步字体、两个正文槽及好感坐标的普通资源和缓存。
4. tools/build_test_iso.py：从受支持原 ISO、阶段输入计划与已验收动画重建。详细实际命令和输出保存于 work/ui-font-182/VERIFICATION.txt。

1955 项自动测试、ISO9660/UDF 双视图及非目标字节检查通过。独立从实际生成的 ISO 回读三个 AFS，验证两套字库、两个正文槽、一处 VM 操作数、三个 UI 图片流和旧标题图，黑体备份不变。

这是字体格、资源与镜像静态证明。所有 UI 的实际视觉居中、动态自动换行和末尾 $n 的显示效果仍需冷启动本版游戏验收；没有用字体预览代替运行截图。动画使用已验收版本，不重新制作。
