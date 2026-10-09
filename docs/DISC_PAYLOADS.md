# 全 ISO 载荷库存

## Verified static

原 ISO SHA-256为6242476a66a96110fb6ee1a1dd668eedd70d3df6c835f0de9192451b5f4fcd45，核查前后不变。62个文件全部逐字节计算hash，总文件载荷3,188,718,429 B；ISO总体尺寸包含文件系统及对齐，二者不要求相等。

文件类型：AFS4、SFD46、ELF主程序1、IRX7、IMG1，以及CNF／DIR／INI各1。SHIP／FILE／LINEAR详细核查见CONTAINER_PAYLOADS.md。新增MUSIC.AFS只读TOC库存3646项，3645项具有ADX头，另外1项为AFSMUSICFileIndex.idx。全部项读取实际长度、hash及前64 B；没有复制1261092864 B归档。

MUSIC通过借用ISO只读流复用cri_afs.Afs的filename TOC及entry reader。ADX头记录采样率、声道、样本数及名义长度；头存在不等于音频全解码或对白转写完成，不能按音频扩展名排除语言内容。

46个SFD全部经本地ffprobe完整输入及packet计数检查，46项exit0、stderr为空，输入hash与全盘库存一致。识别46个mpeg1video视频流与45个adpcm_adx音频流；991802.SFD没有识别到音频流。不转码、不重新mux，不生成SFD副本。

## 覆盖状态

包清单／音视频流元数据不等于画面文字与语音内容全提取。上游ASS对照及无ASS影片仍需视觉／内容审查；图片字、celfid、ELF及包内字段门禁保持。`complete_game_text=false`，既有6334条初稿未修改。

本地详细原始记录：work/extraction-coverage-50/disc-audit/ 与 movie-audit/。详细内容保持忽略，仅聚合结果进入版本控制。
