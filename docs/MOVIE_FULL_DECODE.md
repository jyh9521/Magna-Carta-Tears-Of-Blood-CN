# 原版 SFD 全帧解码核查

## Verified static

46 个原版 SFD 从 ISO 只读流输入 FFmpeg，全量解码 72696 帧。每个输入的全部字节数与 SHA-256 对应已验证 ISO 库存；46 个退出码均为 0，error 级 decoder 日志全部为空。没有 fps 抽样、缩放、SFD 副本或新 ISO。

每帧记录 stream、DTS、PTS、duration、解码图像字节数与 SHA-256。输出逐行检查字段数量、正 duration／size、SHA-256 形状及单调 PTS；46 份记录均重新读取。按各影片实际 timebase 与首末 PTS 计算，视频时间轴合计 2425.6232 秒。该数值是全部影片时轴总和，不代表游戏主线游玩时长。

输出只包含 framehash 文本、空错误日志及 JSON 汇总；不保存 72696 张画面。FFmpeg 路径为显式参数，版本 9.0.2。ISO 身份前后保持一致。

## 覆盖边界

全帧解码证明视频流能完整解码及帧时间轴存在，不等于全部画面文字已转写、所有字幕与 FPB 已去重，亦不等于语音全量审听。此前 8 秒抽样接触表仍属于 sampled visual evidence，不能因本次完整解码升级为逐帧视觉验收。序章、尾声、名单及对白的逐条原文／时间轴审核仍待完成。complete_game_text=false，新增全文翻译仍暂停。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_movie_decode.py --iso "<original-KR-ISO-path>" --inventory work/extraction-coverage-50/disc-audit/iso-files.json --executable "<ffmpeg.exe-path>" --out work/full-movie-decode
```

工具保持视频原帧输出节奏、仅选择第一个视频流，禁用音频输出。输出目录必须为空；源身份、解码退出、源字节输入量或错误日志不符即失败。
