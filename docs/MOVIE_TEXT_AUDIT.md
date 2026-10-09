# SFD 画面文字核查

## Verified static / sampled visual

46 个原版 SFD 全部从 ISO 只读流输入 FFmpeg，源字节数及 SHA-256 与全盘库存一致。采用 `fps=1/8,scale=384:-1,tile=6x6` 生成 47 张本地接触表，合计 27,911,619 B；46 项解码退出码为 0。全部接触表已打开审查，并通过文件 hash 与 PNG 结构验证。没有生成原版 SFD 副本或新 ISO。

抽样画面中，25 个影片观察到文字：21 个影片包含韩文对白字幕，180101 包含韩文序章滚动文字，991804 包含韩文尾声滚动文字，189992 包含韩文制作名单，997777 包含日文制作名单。其余 21 个影片仅记录“抽样画面未观察到可辨认正文或 UI 文字”，不据此排除采样间隙中的文字。详细逐影片身份及结论见 MOVIE_TEXT_AUDIT.json。

## 上游字幕参照

完整读取 `subs/korean/` 与 `subs/japanese/` 各 25 个 ASS，导出 238／272 条 Dialogue 行，共 510 条带原文件 hash、行号、时间及原样标签的参照项。目录名指影片地区，不代表字幕文本语言；例如 korean/180111.ass 的正文是英文。参照项设为 `original_verbatim_verified=false`，不冒充韩文原文。

180101、991804、997777 没有对应的上游 ASS。189992 虽有 ASS，画面中的制作职位、姓名与标题仍需另行核对，不能以 ASS 文件存在判定滚动名单全覆盖。两个地区 ASS 的行拆分不同，510 条是参照行数，不是 510 条新增游戏对白。

## 覆盖门禁

8 秒采样不是逐帧文字提取；完整解码不是完整字幕转写或语音审听。序章、尾声、名单及对白的原文、出现区间和已有 FPB 的对应关系仍需核对。`complete_game_text=false`，6334 条既有翻译初稿保持不变。

核查命令：

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_movie_frames.py --index work/extraction-coverage-52/movie-sheets/index.json --observations work/extraction-coverage-52/movie-sheets/visual-observations.json --sources work/extraction-coverage-50/disc-audit/iso-files.json --subs subs --out work/extraction-coverage-52/frame-audit
```

接触表、原始转写、英文参照及详细本地索引保持在忽略目录。聚合记录不包含原版画面或完整资产。
