# 顶部六标签底边残留修正

## Verified

当前已汉化field_part1两个副本（00001002.lin、00065533.lin）的211、233、255行仍有旧图索引残留，每副本24个非零像素。它们在上一轮46×21替换矩形之外；红色背景合成可复现分离的黑色短线。不能把只核查字格内部透明边界误当成完整采样邻域无残留。

通用build_text_texture_overlays.py增加可选clear_rect：先清零明确绑定的矩形，再保持原rect内绘字。clear_rect必须包含rect且位于256×256图集内，否则拒绝。六标签各仅向下多清1px，包含原排版格漏掉的端点行，不改UV/位置/文字尺寸/调色板。设置统一为既有coverage-mask（threshold48、edge_guard1）的紧贴描边；其他五标签绘字不变。其余图集、魅力、整理及所有非目标像素、包属性与表保持。

正式配置复用locales/zh-CN/images/field-ui-texture-profile.json。两个副本共12块、48个底边残留像素清除，修改后底边非零0。源码、输入hash、逐像素验证、离线对照和隔离恢复见work/tab-fringe-191。

使用既有版本锁定构建流程，仅换LINEAR.AFS。62个ISO文件独立比对仅LINEAR内容变化；FILE两字体/缓存、SHIP换行译文、ELF、46动画保持。现有测试ISO已改名为Magna-Carta-Tears-of-Blood-zh-CN-test.iso，本轮在核对其stage190 SHA后更新这个实际文件，不另外创建重复ISO。

## 实际验收

静态资源残留已经复现并清理；本轮未采集游戏执行帧或逐指令验证纹理过滤。冷启动新ISO进入菜单，依次切换六标签观察底部，避免旧即时存档沿用已缓存贴图。

## 重建

仍使用build_text_texture_overlays.py --archive BASE_LINEAR --profile HASH_BOUND_PROFILE --font SOURCE_FONT --out OUTPUT，按实际base archive/stream/payload/pixel/palette/font SHA锁定输入。完整原版到译文AFS的构建步骤沿用BUILDING及UI_FONT_REVISION/TAB_SHADOW_REVISION。未知输入不盲清除。
