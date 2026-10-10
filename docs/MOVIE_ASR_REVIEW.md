# 音频优先的影片文字核查

## 已验证流程

全帧 OCR 已停止。批量帧图清理及先前研究提交已完成，原资源与既有译稿保持不变。默认流程改为音频完整解码 → 本地原语言 ASR → 源字段/ASS时轴比对 → 低置信度片段定点 OCR。不是先向对话发送所有帧，也不把语音模型结果自动当作画面原文。

本轮清点全部46影片：45含一条音轨，991802无音轨。45条音轨均从已验证原ISO直接读取完整SFD流、匹配原SFD哈希，以单声道16kHz PCM完整解码，FFmpeg退出0且日志为空。PCM共2377.850625秒；音频长度不替代视频时轴长度。模型为Systran/faster-whisper-small，revision `536b0662742c02347bc0e980a01041f333bce120`，所有模型文件hash记录在ignored输出。faster-whisper1.2.1/CTranslate2 4.7.2，CPU int8_float32，8线程。

45片全部完成候选转写，共283片段，模型推理合计366.492秒。只做transcribe，不翻译；韩语显式ko，997777显式ja；temperature0、beam5、不跨片段继承文本，word timestamps开启，VAD关闭。模型仍可能跳过无语音片段或产生幻听，低置信度指标也不是正确率证明。历史输出的detected_language字段来自显式语言配置，概率1不表示自动识别或百分之百正确；工具现改为明确的model_reported_language/language_selection。

与20151字段只读快照比对：逐字符exact匹配0，明确标注空白折叠候选26，不据此删除源字段或认定去重完成。50份上游ASS共510 cues用于时轴关联；korean/japanese是音轨目录标签，其字幕文本可能为英文，不能冒充韩文/日文原文。字幕措辞和实际发声可能不同，例如校准片段中表达相近而动词不同；ASR仅提供发声候选和定位。

174片段触发低平均log probability、高no-speech probability、过高compression ratio或低word probability中的至少一项，进入定点OCR队列。每片段选原视频时轴上最接近ASR中点的一帧，按stage85 framehash逐帧验证，保留完整原尺寸图、OCR置信度/四边形、模型hash及decoder日志。重复索引共享帧。该选帧不是字幕边界核查或静默视觉文字穷尽证明。

## 可重现环境与命令

本地原ISO/AFS等仍由使用者提供；公开仓库不包含原语音、影片、帧图或全文研究候选。安装可选依赖`requirements-research.txt`；只安装一种ONNX Runtime，本配置为CPU。模型代码/权重归相应上游，不将第三方模型视为项目独立成果。模型下载可执行：

```powershell
work/venv/Scripts/python.exe -m pip install -r requirements-research.txt
work/venv/Scripts/python.exe -c "from huggingface_hub import snapshot_download; snapshot_download('Systran/faster-whisper-small',revision='536b0662742c02347bc0e980a01041f333bce120',local_dir='work/asr-models/faster-whisper-small',allow_patterns=['model.bin','config.json','tokenizer.json','vocabulary.*'])"
work/venv/Scripts/python.exe -c "import json; from pathlib import Path; Path('work/asr-models/faster-whisper-small/provenance.json').write_text(json.dumps({'repository':'Systran/faster-whisper-small','revision':'536b0662742c02347bc0e980a01041f333bce120'}),encoding='utf8')"
$iso=(Get-ChildItem -File -Filter '*.iso'|Select-Object -First 1).FullName
$ff=(Get-Content work/extraction-coverage-85/full-decode/movies.json -Raw|ConvertFrom-Json)[0].command[0]
work/venv/Scripts/python.exe -X utf8 tools/audit_movie_asr.py --iso "$iso" --decoded work/extraction-coverage-85/full-decode/movies.json --probes work/extraction-coverage-50/movie-audit/sfd-probes.json --executable "$ff" --model work/asr-models/faster-whisper-small --language ko --language-override 997777=ja --out work/movie-asr
work/venv/Scripts/python.exe -X utf8 tools/review_movie_asr.py --asr work/movie-asr --corpus work/extraction-coverage-86/review-audit/source-corpus.json --subs subs --out work/movie-asr-review
work/venv/Scripts/python.exe -X utf8 tools/audit_movie_spots.py --iso "$iso" --decoded work/extraction-coverage-85/full-decode --probes work/extraction-coverage-50/movie-audit/sfd-probes.json --review work/movie-asr-review/review.json --executable "$ff" --out work/movie-spot-ocr --rec-version-override japan=PP-OCRv4
```

输出必须为空的ignored目录。基础单元测试不需要模型/可选推理依赖。PCM直接转float32传入WhisperModel，不二次调用PyAV；实际初次运行遇到PyAV19的metadata_errors参数差异，记录保留并改用已核查PCM接口，不标作原SFD解码失败。

## 保留边界

有声候选、画面文字和现有结构化字段分别保留，所有新候选readonly。名单、标题、无配音文字、模型无输出区段与ASR/OCR相互矛盾项继续独立复核。`coverage_review_complete=false`、`original_verbatim_verified=false`保持；完成音频候选流水线不等于全游戏提取覆盖或逐条人工验收完成。

[Whisper上游](https://github.com/openai/whisper)、[faster-whisper/SYSTRAN](https://github.com/SYSTRAN/faster-whisper)；代码分别遵循上游MIT许可，模型实际文件与来源单独记录，不再分发权重。

## 定点 OCR 接续修正

RapidOCR3.9.2模型清单中japan识别器为PP-OCRv4，不能套用韩文PP-OCRv5。初次定点任务在该模型配置处终止，未归类为原片解码失败；显式japan=PP-OCRv4后接续，复用已完成韩文帧，不重跑全帧OCR。resume复核目标选择、原framehash字段、PNG哈希、OCR结构、decoder日志与只读状态；模型元数据在初始化后立即写出。

## 本轮定点结果

174个低置信度片段对应37片的174张定点帧，全部逐张匹配原framehash，decoder退出/日志核查通过，实际暂缓解码0。一次单帧视觉校准确认：ASR词序与画面句子相符，OCR却产生误识；只记录该帧显示原文，不自动把其OCR或全片ASR升级为核定原文。另查看片尾名单代表帧，确认名单属于独立视觉资料，语音转写不替代名单核查。
