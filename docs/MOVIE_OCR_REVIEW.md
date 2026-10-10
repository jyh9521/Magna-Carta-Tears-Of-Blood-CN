# 全帧 OCR 候选与解码失败暂缓记录

## 已验证

stage89 为电影画面文字提供逐帧候选，不改变翻译或镜像。工具 `tools/audit_movie_ocr.py` 按 stage85 全解码索引读取原 ISO 的 SFD 流，每帧使用原尺寸 YUV420p 输入并核对 SHA-256。不存在帧率抽样或字幕区域裁切；只有连续字节完全相同的帧允许复用 OCR。输出保留帧号、PTS、duration、置信度、四边形、代表帧与模型哈希。原 ISO 执行前后校验，源文件不修改。

首部验证影片 180111：1635 帧全部与既有 framehash 匹配，1635 次 OCR，1558 帧产生候选，1079 个不同候选代表图、1391 个精确文字连续段，FFmpeg 退出 0。这些数字不是字幕数量。三个原尺寸代表帧另行人工查看；其中两帧的 OCR 存在韩文字形误识、空格或标点差异。因此 OCR 不升级为逐字原文，连续段不升级为人工确认的字幕边界；空结果不证明画面无文字。

全 46 影片另行运行，运行输出位于 ignored `work/extraction-coverage-89/full-ocr`；只有完成的单片 `summary.json`、完整帧记录及实际终止结果才能计入完成，不将正在执行的目录视为覆盖完成。默认韩文，997777 使用日文识别覆盖。逐条转写、名单、时轴和 FPB/ASS 去重仍需核对。

`tools/audit_deferred_decodes.py` 对只读 stage86 快照的 167 个失败字段重新验证原字节 hash/长度和 strict CP949 的真实异常：127 FPB、38 CHT、2 POD。登记为暂缓，不删除字段、不开放导入、不重复尝试无依据编码。保留先前 CP932 等证据，CP949 失败不等于所有编码失败。101 个控制隔离字段不因此自动暂缓。

## 重现

在原有 venv 中安装 RapidOCR 3.9.2、OpenCV 5.0.0.93；运行时二选一：CPU `onnxruntime==1.31.0` 或 Windows `onnxruntime-directml==1.24.4`，不要同时安装。语言、模型类型和 provider 显式选择，模型来源/版本/hash 由本地元数据记录。模型权重不进入仓库。

```powershell
$iso=(Get-ChildItem -File -Filter '*.iso'|Select-Object -First 1).FullName
$ff=(Get-Content work/extraction-coverage-85/full-decode/movies.json -Raw|ConvertFrom-Json)[0].command[0]
work/venv/Scripts/python.exe -X utf8 tools/audit_movie_ocr.py --iso "$iso" --decoded work/extraction-coverage-85/full-decode --executable "$ff" --language korean --language-override 997777=japan --provider directml --out work/movie-full-ocr
work/venv/Scripts/python.exe -X utf8 tools/audit_deferred_decodes.py --corpus work/extraction-coverage-86/review-audit/source-corpus.json --out work/deferred-decodes
```

输出必须为空目录。Genuine FFmpeg 解码错误生成失败记录后暂缓该片；源身份、帧哈希或模型错误仍会终止，不伪装成解码失败。运行期间不重启已有同一任务。

## 边界及上游

RapidOCR 项目代码为 Apache-2.0；使用 RapidAI 工具与 PaddleOCR/Baidu 模型，未声称自行发现识别算法或模型。模型具体许可须分别核对，不将代码许可自动扩展至所有模型。[RapidOCR 模型清单](https://rapidai.github.io/RapidOCRDocs/main/model_list/)、[许可说明](https://rapidai.github.io/RapidOCRDocs/main/model_licenses/)、[ONNX Runtime DirectML](https://onnxruntime.ai/docs/execution-providers/DirectML-ExecutionProvider.html)。DirectML session provider 已验证，不据此声称所有算子都在 GPU 执行。

完整原文、画面与模型保存在 ignored work 或本地依赖缓存。公开文档仅提供汇总。`complete_game_text=false`、`coverage_review_complete=false`；配置 3 项、地图 native 6 个字节候选、编译 243 待确认、控制 101、ELF/LINEAR 与电影原文核查继续保留。

## stage91 停止全帧 OCR 并切换音频优先

全帧 OCR 已主动停止；完成状态不由旧 progress.json 推断。清理2102张批量候选帧图，释放485360132字节，保留3张视觉校准图及JSON/JSONL、错误日志、哈希和删除清单。旧 evidence 图路径对应已清理图片，后续按源ISO定点重生成；不删除原ISO/AFS、译稿、framehash或测试镜像。

189993的3777帧全部匹配既有framehash、退出0；日志仅为rawvideo muxer重复DTS，原失败事件和日志完整保留。reconcile_movie_ocr.py验证原source hash、帧记录和代表图（清理前执行）后生成独立纠正记录；这不是实际解码失败，不修改PTS。新decoder_outcome只接受精确已知rawvideo日志且全帧/退出0，其他日志继续隔离。

后续采用本地多语言Whisper原语言转写、既有资源/ASS时轴比对、疑点定点OCR/听音复核。片尾名单、标题与无配音文字仍单列视觉核查。语音/视觉候选不自动升级原文或译稿；覆盖核查门禁继续关闭。
