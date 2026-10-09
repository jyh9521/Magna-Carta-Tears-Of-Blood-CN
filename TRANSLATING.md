# Translation data design

目标zh-CN；目前研究与PoC设计，未启动batch translation。
最终目标数据放locales/<locale>/，UTF-8，target字段明确表示译文，不塞进上游en。
原版reference catalog由ISO提取进入ignored work，en-US/ko-KR/ja-JP仅作为可选reference。

## Proposed records (not production schema)
```json
{
  "locale": "zh-CN",
  "base_region": "kr",
  "entries": [
    {"id": "SHIP/00001944.fpb/seq/0", "target": "测试中文", "status": "poc"}
  ]
}
```
示例为独立测试数据，不含完整原版游戏文本，不是现有patch.py可读取的catalog。
结构字段source hash、byte cap、保护类别、link group由extractor生成，不手填offset。
小字集PoC已有显式Unicode→byte-pair/glyph index编码；生产编码与容量扩展未完成，不选择GBK/UTF-8作为运行时默认。

## Protected tokens
$n是ASCII换行token；$D04/$D06/$D08/$D20等全部保留。具体portrait/speaker含义未验证。
已确认UI的<...>可以仅改内文并保留包围符；未知markup、$、%、{0}、paths、IDs、NUL一律保护。
不自动Unicode normalization，不改内部UE2 names、save/resource keys。
保留必要token数量/值/顺序；不要用中文标点替换machine syntax。

## Length and linked text

TUI新研究确认两个256 B区段，未来显式字段profile保守保留每段NUL和另一半内容，不以512 B载荷当作单段容量。旧PoC不迁移profile；字段用途和新的构建身份须独立验收。详见 [TUI字段](docs/TUI_FIELDS.md)。

TUI记录结构与可编辑文本属性分开判断；29个非零尾部字段不开放写回，另外834个可解码字段仍需确认显示文本/identifier用途。当前仍只开放PoC的id176，详见 [TUI审计](docs/TUI_AUDIT.md)。
按编码后bytes检查fixed slot/region/celfid，保留NUL和trailer；FPB可增长但UI有pixel width门禁。
韩版实际record结构须确认后才开放target编辑，不拿ASCII heuristic输出当全部display fields。
celfid模板联动与SHIP重复来源/纹理保持显式mapping，不能只因source同字/子串就合并语义。
上游同长ASCII global rename不适用于中文；显示名与internal lookup key分开。
UI width使用实际runtime fonts/scale，不能沿用英文50/60 chars warning当中文标准。

## Validator gates (planned)
ID uniqueness/source identity、token Counter等值/必要顺序、placeholder、markup、linked groups、terminator/cap、encoding errors、missing glyph、glyph capacity、pixel width、readonly identifier、unexpected empty target。
上游checks有价值但目前token只warn drops；新增/乱序/unknown token等需加强。

## PoC-only test matrix
角色名、UI短句、普通剧情、含$n、中文标点、长句、固定slot、可增长FPB。
字符样本：测试中文，。！？“”《》123ABC。
PCSX2显示/无乱码/字宽/wrap/稳定mapping/存档/切场景验收前不扩展到全文；完整步骤见docs/PHASE1_RESEARCH.md。
术语表/正式人名与风格规范在技术门禁通过后单独制定，不把测试名称当正式译名。

已实施单字实验：locales/zh-CN/poc.json保存原创“测”及B0A1候选mapping，不在en字段填中文。
00001944.fpb seq0/seq2各改一个双字节字符，其余韩文及控制符保留；不是正式catalog，不做批量译入。

## 小字集测试数据

稳定map与原文保留兼容性分别验证；不得把某一FPB语料中未出现的槽直接分配为全游戏空闲槽。当前容量与冲突数据见 [字体审计](docs/FONT_CAPACITY.md)，生产字库扩容未实施。

locales/zh-CN/poc-text.json使用target字段，显式引用game profile和poc-map.json；不写入en。map重排不改变既有字符的编码，新增字符不得自动重分配旧槽。
src/localization/text.py严格保护已识别$n/$DNN、printf placeholders、数字占位符及ASCII标签的数量、值、顺序；未知$/%/尖括号/花括号结构报错，不按普通文字编码。
空目标、NUL/原始换行控制字节、缺映射、重复char/code/glyph、固定槽缺NUL容量均拒绝；换行通过$n。
UI测试条目配置max_estimated_pixels192，两font的候选字宽均须通过预算；尚未测得runtime宽度，不能用此估算替代游戏内排版验收。宽度估算只解析$n，其他placeholder宽度未定时拒绝估算。
仅两个FPB窗口与一个已确认几何的UI字段开放测试，原标识符与其他记录不改。当前FPB backend只接受连续不重叠pool partition，重叠格式拒绝，不静默串接。
UI副本同步不是完整linked name group校验；角色名、其他固定slot与全局catalog仍未开放。完整门禁和状态见docs/QA_TEXT_POC.md。

## 新增槽实验与正式试译门禁

独立Font扩容实验使用实际Font range/base/count验证映射，旧PoC map不改。已进入独立package和celfid候选；带UDF同步的D0实验ISO已通过结构回读，基线已有局部UI/剧情显示截图，完整缓存路径与回归尚未验收。完成新增槽镜像、最小显示/换行/存读档/切场景与linked名称验证后，从已确认资源的小批量正式试译开始；不以穷尽全部引擎逆向作为前提，不越过未知格式门禁。具体顺序见 [扩容实验](docs/FONT_EXPANSION.md)。

## 单姓名字段定位例外（非正式译文）

poc-name-01.json复用现有PoC字符，只增加CHA slot0目标“测试中文”，其他同名字段不自动扩散；不作为正式人名或生产catalog。源hash/完整匹配库存/明确slot/控制符/编码/容量/缓存需校验，人物菜单及lookup/剧情作用另验。新截图仅支持基线局部显示，存读档/场景与名称仍分别保留门禁。见 [名称候选](docs/QA_NAME_POC.md)。

## 有界试译批次 opening-trial-01（2026-10-09）

阶段调整为先提供首段开场对白、露营教程和存档/操作相关UI草稿，以支持到达存档点和运行回归；正常存读档、切场景门禁保留，但不再阻止此显式限定批次。不是全库翻译授权，不按资源编号猜测剧情顺序。

locales/zh-CN/opening-trial-01.json保存91个target及原资源/窗口hash，不提交原文catalog；完整对照正文仅保留在ignored source-review.json。TUI仅选择69个首256 B字段，174条其他记录和第二字段保持。暂定术语：칼린츠→卡琳兹、풍월림→风月林、캠프 모드/캠핑모드→露营模式；人名为试译，未定稿，不自动cascade到其他资源。

正文条目的translation_status=trial-draft；需实际上下文/画面校对。保留全部$n，○键符号、80KB、PS2等成分按原功能保留。字库从字符库存生成，原33字符顺序保留后追加所需字符，避免在新批次中重排旧测试编码。
