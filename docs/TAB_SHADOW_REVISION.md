# 顶部五标签暗色杂点修正

用户截图中的编成、道具、装备、流派、信息来自field_part1图集，不是普通2-bit中文字库。仅重绘这五个标签的两个副本（00001002.lin、00065533.lin），设置、魅力、整理、其他图集、正文/小字库、译文与影片不改。

## 已验证的生成原因与修正

旧路径在RGB黑底上绘制白字与RGB(4,4,4)描边，再Lanczos缩小，对任何非零RGB映射到非透明调色板项。极低亮度的振铃因此成为不透明暗色索引，且全调色板匹配可能选到其他UI的彩色条目。离线原图可见分离的暗色杂点；该生成机制已在原代码及像素复核中确认，不等于已经采集修正版同场景游戏帧。

通用工具build_text_texture_overlays增加显式可选 `raster_mode: coverage-mask`。目标标签使用原思源宋体Regular输入及18px设定、4倍栅格化，只绘L覆盖率，再缩小；覆盖率低于48设为透明。紧贴有效字形生成一像素暗色轮廓（索引1），文字颜色仅匹配饱和度跨度<=12且平均亮度>=30的原有中性灰阶。上下左右各保留1px透明边界。轮廓不是偏移投影，没有新增远离字形的黑点；不改变原调色板。将墨迹和轮廓共同约束在原46x21的UV格内，几何和消费者代码不改。其他标签保留legacy-rgb历史渲染路径。

语言配置沿用locales/zh-CN/images/field-ui-texture-profile.json；五标签在两个stream中均添加上述可选参数，不创建重复正式配置。本次增量profile只绑定当前已汉化LINEAR的hash和对应payload/pixel hashes；从历史基础重新生成的canonical流水线也会选用新参数。

## 验证与产物

两stream只修改10个明确矩形；调色板、所有非目标像素、资源属性及包表保留。档案清单按实际第一成员AFSLINEARFileIndex.idx更新两流长度并独立验证；首轮核查误用了FILE.AFS的清单名称，失败记录在工作目录，修正实际身份而不是跳过清单校验。

ISO62文件只有LINEAR.AFS改变，FILE字库/缓存、SHIP文本、ELF及46动画相同。2013项测试通过；baseline/隔离恢复2005项通过，LINEAR.AFS恢复到原SHA。旧测试ISO保持af65484a8507a26fcc522e3035f620decb2a77cd30953e8b282484bc62659f40。

新ISO单独命名为build/test-iso/Magna-Carta-zh-CN-tabs-fixed.iso，未覆盖旧ISO或旧构建报告。详细命令、hash和四项事务证据在work/tab-shadow-189，离线对比图tabs-comparison.png已检查。冷启动新ISO进入菜单复测，不加载旧即时存档；同场景游戏视觉验收仍需实测。

后续stage191纠正：先前只检查46×21内部，211/233/255端点行旧图残留并未消失。六标签明确清除底边采样邻域，详见TAB_FRINGE_REVISION.md。
