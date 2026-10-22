# 全部汉化动画播放结束修复

日期：2026-10-12。此记录取代“仅完成排查”的交付状态，但不替代游戏内逐场景验收。

## 交付

新测试镜像：`build/test-iso/Magna-Carta-Tears-of-Blood-zh-CN-movies-fixed.iso`

SHA256：`ae27f5b509f763df5051a106b7971c8e455599a132de13e08947917814807be1`

大小：4250683392字节。原`Magna-Carta-Tears-of-Blood-zh-CN-test.iso`及只恢复180111原片的对照ISO均未覆盖。新镜像保留原测试版全部字幕、字库、菜单、译文与剧情/战斗资源。

## 实际修复

- 全部25部汉化影片都已修复，不只23部时间戳倒退影片。
- 从完整视频ES提取picture边界和10位temporal_reference，核查I/P顺序及GOP重置；本版25部均无B帧，故按解码/显示相同的全局帧序重建PTS/DTS。29.97fps对应精确3003个90kHz ticks，不沿用旧封装器+15 ticks及扇区局部错误计数。
- 按完整ES偏移将时间戳映射回PES，处理跨扇区picture_start，不将PES片段误作新帧。
- 每部视频末尾追加B7到真实视频payload内，利用最后视频PES的既有padding空间，更新PES长度与padding长度。SFD文件尺寸、扇区位置、SofDec消息、SCR、ADX/PES音频及容器B9不变。
- 视频仅追加4字节结束码，其余已烧录中文字幕的视频字节逐字节保持，没有重新编码、改字幕内容或改布局。
- 21部原片保持逐字节一致；ISO9660/UDF目录与元数据不变，非影片字节完整一致。ELF/游戏CRC、存档格式、AFS/字库/菜单与其他汉化不改。

## 验证结果（Verified）

原版与修复镜像各46部完整视频/音频解码，92次退出0，error日志均为空。共72696帧/镜像，逐片几何、数量及帧率保持。全46视频B7与容器B9存在；25修改影片的显式PES与FFprobe解复用DTS倒退均为0。

全部46部的修复版解码图像hash序列与此前汉化版一致，证明中文字幕画面与每帧像素未变。45个ADX音轨逐字节一致，991802继续无音轨；解码PCM内容及音频时间戳也全部与原版一致（包括先前19部音频输出时轴差异）。没有丢帧、换音轨或用韩文原片代替中文字幕。

基线2182项测试通过；新增18项回归，修改版2200项测试通过。原依赖包未改，修复器是项目自有、locale-neutral的完整ES时间轴后处理；旧错误依赖的诊断字段仍可能报告26915个误读，但正式修复器不使用它计算时间戳。最终播放器文件已通过独立时间戳复检。

独立ISO副本回滚恢复旧镜像完整SHA256与25个旧影片；180111重新呈现B7缺失及2次显式DTS倒退，证明恢复的确是旧版本而不是只复制文件名。新修复镜像保持不变。回滚测试副本完成后已清理，原旧镜像作为必要回退仍保留。

## 新构建路径

`tools/movie_playback.py`：I/P MPEG-1 SFD无损后处理。检查所有帧率和GOP，B/D帧、未知格式、已添加B7、损坏输入、缺少padding均明确失败，不静默拼凑。它不是任意MPEG视频的B帧重排器。

`tools/repair_movie_playback.py`：从完整SHA256锁定的当前镜像和逐片hash审计清单构建独立ISO。只修25个已改变资源；原片、目录、版本身份与其他字节保持。rollback子命令只写新的独立副本。

`tools/build_movie_subtitles.py`与`lib/cutscenes.py`的重编码分支均接入后处理，编码显式`-bf 0`；无字幕原片复制分支不改。cutscenes缓存版本升级为2/playback_repair=1，防止旧生成SFD直接被新构建缓存复用。整个流程不编辑site-packages。

## 重现命令

```powershell
work/venv/Scripts/python.exe -X utf8 tools/repair_movie_playback.py build --iso build/test-iso/Magna-Carta-Tears-of-Blood-zh-CN-test.iso --expected-sha256 87b6b263353f7846df2b1d5e5d2c8b85c2320b1b401eebac2eb51b43699b4f36 --audit work/movie-playback-audit/baseline/movies.json --out build/movie-playback-fixed-repeat --output build/test-iso/Magna-Carta-Tears-of-Blood-zh-CN-movies-fixed-repeat.iso
```

审计清单可从原ISO与旧汉化ISO用`tools/audit_movie_playback.py`重新生成，命令见[MOVIE_PLAYBACK_AUDIT.md](MOVIE_PLAYBACK_AUDIT.md)。输出目录与目标文件须新建，未知输入hash或资源指纹不符即失败。不要把当前已修复ISO当作旧坏输入重复修补。

## 用户运行验收

2026-10-12用户反馈：本次中文字幕修复版正常，继续测试游戏。此前180111动画结束卡住的用户复测已通过；其他场景仍随继续测试记录，不将单点通过扩展为全游戏通关验收。

切换到新`movies-fixed.iso`，可用同一180111动画前即时存档进行本次受控比较。载入后检查当前光盘仍是新镜像；若恢复旧路径，使用更换光盘选择新ISO，再完整播放。应出现原先已验收的中文字幕，并在末尾正常切场景。这个镜像的全量格式/时轴缺陷已修复，游戏内180111重测及另外24部逐场景完整播放/跳过的动态结果仍由实际测试确认，未伪称已经通关。

## 可复核证据

- `build/movie-playback-fixed/DIFF_FILE.json`：25部资源hash、字节/帧保持证明、ISO/UDF/非目标字节验证。
- `work/movie-playback-repair/post-audit/`：全46部双视图、完整解码framehash、probe与原始日志。
- `work/movie-playback-repair/FINAL_GATES.json`：最终门禁汇总。
- `work/movie-playback-repair/VERIFICATION.txt`：BASELINE/MODIFIED/ROLLBACK命令、输入、实际输出、退出码与恢复行为。
- `work/movie-playback-repair/ROLLBACK.sh`：可执行的独立副本回滚测试。
- `work/movie-playback-repair/source-before/`与`SOURCE_DIFF.patch`：修改构建入口前的真实源码快照与差异，保留此前用户修改。
