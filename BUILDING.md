# Building and Research

目前提供研究工具、单字及小字集实验ISO builder；完整游戏内验收待完成。没有batch translation。

## Inputs
研究输入仅包含韩版SCKA-20043 ISO；保持原位，不复制进跟踪目录。
已研究hash `6242476a66a96110fb6ee1a1dd668eedd70d3df6c835f0de9192451b5f4fcd45`，3210412032 B。
其它版本只能重新研究，不允许以此hash的结论无条件patch。
上游USA-base undub CLI仍保留，但依赖USA ISO；KR-only实验profile已实施，完整locale生产流程仍待完善。

## Dependencies
Windows本次Python3.14.2，pinned requirements-research.txt：cri-afs0.1.1、sfd-muxer0.1.1、pycdlib1.21.0、Pillow12.3.0、fonttools4.66.1。
SFD实验使用FFmpeg9.0.2 full (libass) 与ffprobe，同一installation。
Python -X utf8避免日语Windows的CP932默认解码问题；不需要更改系统locale。
iso.py优先使用isoinfo；缺少该程序时用pycdlib读取ISO9660 metadata，写入/relocation仍复用上游算法。
不依赖gitignored上游lib/experiments。

```powershell
python -m venv work/venv
work/venv/Scripts/python.exe -m pip install -r requirements-research.txt
work/venv/Scripts/python.exe -X utf8 tools/research_inventory.py --iso "<original-KR-ISO-path>" --out work/research
work/venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p "test_*.py" -v
work/venv/Scripts/python.exe -X utf8 tools/research_media.py --iso "<original-KR-ISO-path>" 2> work/media-stderr.log
```

Inventory只读ISO；输出提取的SHIP/FILE/ELF、ISO身份/目录、text-family census、UE2 export表、font PNG于ignored work/research。
Media wrapper只抽单片180216，直接调用upstream build_cutscene，不新增SFD实现。使用relative ASS path避免Windowsfilter escaping问题。
所有游戏数据/实验副本仅work/build；生成catalog也不跟踪。工具不输出可玩中文补丁。

## Results and acceptance
46 tests passed（原14项、单字PoC10项、小字集22项，包含真实pycdlib metadata的relocation测试）；707 KR FPB无编辑byte-identical。
SFD一片静态demux/hardsub/mux成功且ADX相同；duration drift与warning见KNOWN_ISSUES。
Font bitmap可读是static evidence；截图另已确认读档UI单字显示，wrap/save/scene等门禁仍待完成，见docs/QA_GLYPH_POC.md。

## Planned KR-only locale build (not implemented)
只读原版/verify hash → KR资源提取 → locales/<locale> target validation → stable glyph/code map →两font+bundle同步 → sparse text replacement →AFS manifest/TOC同步 →复用ISO patcher →outputs重新解析 →PCSX2验收。
source data UTF-8，runtime encoding由locale backend决定，不把中文写入en。
原版不覆盖，binary patch若后续需要必须expected bytes/hash gate。
先PoC再工具成熟与全文翻译；计划细节见docs/PHASE1_RESEARCH.md。

## 单字字体PoC（已实现；UI单字显示已观察）
`tools/font_poc.py`从已知hash原ISO直接提取，不依赖work/kr或研究中间文件。
配置在`locales/zh-CN/poc.json`，不改上游en catalog。Windows SimHei仅用于本地实验；profile锁定字体hash，不提交字体或bitmap。
fonttools检查cmap含“测”，Pillow生成两种高度的2bpp字形；不同字体版本需显式增加并验证profile。
发布级开放许可字体/获取机制仍待选择；当前不是最终发布构建方案。

```powershell
work/venv/Scripts/python.exe -X utf8 tools/font_poc.py verify --iso "<original-KR-ISO-path>" --out build/poc --state baseline
work/venv/Scripts/python.exe -X utf8 tools/font_poc.py build --iso "<original-KR-ISO-path>" --out build/poc --font C:/Windows/Fonts/simhei.ttf
work/venv/Scripts/python.exe -X utf8 tools/font_poc.py verify --iso build/poc/MODIFIED_FILE.iso --out build/poc --state modified
```

输出build/poc/MODIFIED_FILE.iso、DIFF_FILE.json与glyph-preview.png；事务VERIFICATION.txt/ROLLBACK.sh仅本地。
回滚只作用于独立ROLLBACK_COPY.iso，恢复原版hash且保留MODIFIED_FILE；不得用hardlink代替独立副本。
复用上游rebuild_afs，定点同步slot0目标资源size，保留SHIP外部package stub sizes。
本次ISO为2 in-place、0 relocation；原版不变，无ELF修改。
PCSX2目录已忽略且未跟踪。原版先冷启动，再启动实验ISO并开始新游戏；开场喘息对白与后续含$n对白首字应出现“测”。
不要从旧savestate验收。截图、日志、BIOS、memory cards与savestates仅放ignored目录。

## 小字集PoC — text-poc-02

版本指纹在profiles/scka-20043.json；三个测试目标及33字显式mapping在locales/zh-CN。tools/build_locale.py复用上游AFS/FPB/压缩/ISO，src/localization/text.py负责编码与受控字段编辑。
从原ISO直接构建，不依赖旧提取目录；字体仍使用上述锁定hash的外部SimHei。旧build/poc不覆盖，输出目录不得与其他实验混用。

```powershell
work/venv/Scripts/python.exe -X utf8 tools/build_locale.py verify --iso "<original-KR-ISO-path>" --locale locales/zh-CN/poc-text.json --out build/text-poc-02 --state baseline
work/venv/Scripts/python.exe -X utf8 tools/build_locale.py build --iso "<original-KR-ISO-path>" --locale locales/zh-CN/poc-text.json --out build/text-poc-02 --font C:/Windows/Fonts/simhei.ttf
work/venv/Scripts/python.exe -X utf8 tools/build_locale.py verify --iso build/text-poc-02/MODIFIED_FILE.iso --locale locales/zh-CN/poc-text.json --out build/text-poc-02 --state modified
Copy-Item -LiteralPath build/text-poc-02/MODIFIED_FILE.iso -Destination build/text-poc-02/ROLLBACK_COPY.iso
work/venv/Scripts/python.exe -X utf8 tools/build_locale.py rollback --iso build/text-poc-02/ROLLBACK_COPY.iso --locale locales/zh-CN/poc-text.json --out build/text-poc-02
```

modified验证需要该build目录中的原AFS副本与DIFF_FILE.json；这些由同一次构建自动产生，不是未记录的外部依赖。
回滚仅覆盖指定独立ROLLBACK_COPY，保留修改ISO。精确日志、差分、preview及事务记录均在ignored build/text-poc-02。
46项自动测试通过；此构建未获PCSX2验收。短串、长句、槽位与测试顺序见 [QA_TEXT_POC](docs/QA_TEXT_POC.md)。
