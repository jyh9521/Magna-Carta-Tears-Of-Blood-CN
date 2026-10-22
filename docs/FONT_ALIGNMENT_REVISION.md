# 共用基线与字格采样边界修正

## 已验证

用户反馈正文中字形上下浮动及底部杂线。旧 `rebuild_mapped_font` 对每字独立执行 y clamp；当参考字的顶边高于某些字符时，不同字符受到不同的平移。NormalFont 原2466新增字形中2390字触及首/末行，小字体1991字触及首/末行。

当前 `full-font-profile.json` 两字体设置 `placement: shared-origin-guarded`、`edge_guard: 1`。先按原方案栅格化及量化，按完整映射集合测出量化后有效墨迹联合范围，只计算一个纵向平移；不逐字压回、裁切、缩放或补画笔画。上下各一行透明像素。原 legacy-clamped 路径保留给历史配置。

NormalFont 的96px工作画布联合范围 y=29..48（右端不包含），全局 origin_y=-28；KatakanaFont y=29..45，origin_y=-28。不同汉字的笔画顶/底自然不同，不强迫每个墨迹包围盒等高；基线是共同字体坐标，不是机械对齐每字底边。

两字体全4932新增字形独立解包后，与旧字形去除透明边界后的2-bit墨迹矩阵逐像素相同；字重、字号、超采样、gamma、阈值、增粗均未改变。原2667字形、全部metrics、字符编码、字格19x21/19x18、每行5字节及未知尾部不改。同步MrtsEngine Font及各唯一启动缓存，只FILE.AFS变化；ISO全部62文件中译文、SHIP、LINEAR、ELF及46动画保持。

## 高置信推定及验收边界

贴着首行的字形在紧密纹理中可能被相邻字形的线性采样读取，形成前一字格底部杂线。透明边界消除了新增字形首末行非零覆盖；这是一项可验证的资源修正，但尚未在用户两张截图的同场景采集修正版渲染帧，不能将该推定写成已经实测的GS采样根因。若冷启动复测仍有杂线，需要检查纹理过滤/UV及原字符字体缓存，不能继续盲改字重。

本轮2005项测试通过；基线及隔离恢复源码1998项通过。资源反向overlay恢复完整旧FILE.AFS；隔离重建旧ISO与65c1c0a8e48008016db5e8a897d4e157423a42f4ea1d58242ee4e682f9993b36完全相同。

## 复现与回退

现有 `tools/build_font_expansion.py` 配合 `locales/zh-CN/full-font-profile.json` 从支持的原ISO/原Medium OTF生成完整字库。原字形和映射保持；如联合范围超出守护区域，生成失败，不自动缩小字号或裁切。字体来源校验及其他构建步骤见 DEFAULT_FONT_INTEGRATION.md。

增量重绘已有字库时，`tools/rebuild_mapped_font.py --base ... --map ... --font ... --profile ... --out ...` 的输入profile必须绑定该base实际SHA；canonical profile的base hash记录历史基础，不可直接套给已生成的Medium字库。本轮首次被此门禁正确拒绝，随后只为此次输入派生绑定SHA的工作profile；字号等配置与canonical相同。

工作证据在work/font-alignment-188；ROLLBACK.sh只接受新的隔离work目录，恢复两字体、反向overlay并重建旧ISO，不覆盖当前测试版。前版字体在work/font-default-184/default-fonts，前版完整构建计划在work/terminology-187/iso-input-plan.json。用户冷启动当前ISO，再从普通存档进入截图场景；旧即时存档可能加载旧RAM字库，不能用于首次换字库验证。
