# 四项译名统一修订（stage187）

现行译名：卡林兹、朱斯蒂娜、阿米拉、伊菲利亚。
适用于完整姓名、复合名称、书名、物品/流派名称及已翻译的原版开发标签。
性别、代词、原 source ID、源文件指纹、控制码和字库映射保持。

## 全量检查结果

| 原译名 | 新译名 | SHIP 实际物理词串替换 |
|---|---|---:|
| 卡琳兹 | 卡林兹 | 442 |
| 朱丝蒂娜 | 朱斯蒂娜 | 52 |
| 阿蜜拉 | 阿米拉 | 77 |
| 伊佩莉亚 | 伊菲利亚 | 56 |

280 个 SHIP 资源共 627 处，FILE 启动缓存中的七个完整资源副本另同步 35 处。
数量是物理存储词串，不是实际播放次数，也不将同一 FPB 的重叠窗口重复计数。
已从实际候选 ISO 独立回读 FILE/SHIP，确认所有旧名编码零残留、新名增量逐项相等；
全部旧、新编码长度相同。FPB 索引、长度、窗口及固定槽、非目标间隔保持。

全部现有中文字符映射已包含新名所需字符，因此不重绘字体，不复用或删除旧字形槽。
MrtsEngine、两字库及原映射、LINEAR/UI图片、ELF保持。
本轮不改其它译文内容、剧情逻辑、战斗系统或UI布局。

名词表及当前翻译批次同步新名，相关上下文测试更新预期，不放宽原性别、代词和控制码检查。
历史 UI 标点 recipe 中的原目标是用于核对旧基线的事务数据，保留原值；
它不是现行游戏文字，最终名称由独立 source-hash 绑定修订处理。

## 动画

检查全部 25 部中文字幕影片及其实际 ASS，以下四部出现旧名：

- 180101：卡林兹、阿米拉、伊菲利亚。
- 181307：卡林兹、朱斯蒂娜。
- 182223、1825381：卡林兹。

四部已重新渲染字幕和编码 SFD，更新原验收目录下的同名 MP4。
新 ASS 逐字节等于旧 ASS 仅替换四项名称的结果；字体、字号、位置、断行、分页、时序及样式不变。
原 ADX 与此前验收 SFD 的音轨逐字节相等，完整解码帧数一致。
其余 21 部中文字幕影片、21 部无中文字幕影片与基线逐文件一致。
定点成片帧已检查，完整游戏播放及本次新成片的人工验收没有冒称完成。

`build_test_iso.py` 区分已有人工接受的影片与明确验证过的名称修订：新四部
`manual_movie_acceptance=false`，以 `validated_revision` 绑定旧接受清单、原/新 ASS、
原音轨及解码证明，不通过伪造人工验收字段绕过门禁。
旧/新 SFD 的 rawvideo framehash 严格 `-xerror` 均遇到既有非单调 DTS；复核使用已有
`decoder_outcome` 窄规则要求退出 0、完整相同帧数，保留日志且不声明容器时轴已验收。

## 构建复现

本次是以 stage184 指纹锁定的译档为基线的增量构建，不是对未知文件作全局盲替换。
旧版本输入仍保留，profile 的原/新编码与明确文本范围可复核。

```powershell
work/venv/Scripts/python.exe -X utf8 tools/apply_term_revision.py `
  --file work/font-default-184/integrated-afs/FILE.AFS `
  --ship work/ui-font-182/integrated-afs/SHIP.AFS `
  --profile locales/zh-CN/proofreading/term-revision-01.json `
  --out work/term-rebuild/integrated-afs
```

影片使用现有 `build_movie_subtitles.py`，输入 `movie-dialogue-01.json`、
`movie-story-01.json` 与现有字体/原ISO/原影片 probes/decoded 元数据；只选择上述四部。
实际完整命令保存在 `work/terminology-187/dialogue-command.json` 与 `story-command.json`。
例如重制后验证单片：

```powershell
work/venv/Scripts/python.exe -X utf8 tools/movie_revision.py `
  --baseline-manifest work/visible-text-153/accepted-movie-overrides.json `
  --movie 181307 --candidate build/movie-term-187-dialogue/181307/181307.SFD `
  --terms-profile locales/zh-CN/proofreading/term-revision-01.json `
  --decoder '<ffmpeg.exe>' --proof '<本地proof.json>'
```

最终使用现有 `build_test_iso.py`、`profiles/scka-20043.json`、
`work/terminology-187/iso-input-plan.json` 和同目录 `movie-manifest.json` 重建。
完整原资产/SFD/ISO/字体、生成清单和验证输出不进入 Git。

## 镜像与恢复

覆盖路径：`build/test-iso/Magna-Carta-zh-CN-test.iso`，4250691584 B。
SHA-256：`65c1c0a8e48008016db5e8a897d4e157423a42f4ea1d58242ee4e682f9993b36`。

ISO9660/UDF 双视图及非目标字节检查通过；与此前完整中文 ISO 的 62 个文件比较，
只有 FILE、SHIP 和四部目标 SFD 共六文件变化。剩余文件内容保持。
1998 项测试通过，隔离源码回滚 1984 项通过；实际 ISO 回滚副本恢复旧 SHA 完全一致。

必要的上一版 Medium ISO 保留在 `work/terminology-187/baseline-test.iso`，
源配置基线为同目录 `baseline-source.zip`，四个旧预览在 `baseline-previews`。
`ROLLBACK.sh <本任务目录内的另一份ISO路径>` 在独立副本上恢复旧 ISO/源配置/四旧预览；
不覆盖当前新版本。验证后的额外 ISO 副本已删除，不长期堆积。

完全关闭游戏，冷启动同名测试 ISO，再使用游戏内正常存档。
旧即时存档可能保留旧文字与缓存，不适合作为首次更新验证。
四个新预览仍位于 `build/movie-review/videos`，无需另找分散目录。

完整命令、输入、原始输出、退出状态、原资产指纹、独立回读及恢复结果在
`work/terminology-187/VERIFICATION.txt`。推送身份以本轮 `publication.json` 为准。
