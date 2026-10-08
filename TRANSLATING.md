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
未来glyph-map将Unicode映射到稳定byte-pair/glyph index；runtime编码尚未实现，不选择GBK/UTF-8作为未经验证默认。

## Protected tokens
$n是ASCII换行token；$D04/$D06/$D08/$D20等全部保留。具体portrait/speaker含义未验证。
已确认UI的<...>可以仅改内文并保留包围符；未知markup、$、%、{0}、paths、IDs、NUL一律保护。
不自动Unicode normalization，不改内部UE2 names、save/resource keys。
保留必要token数量/值/顺序；不要用中文标点替换machine syntax。

## Length and linked text
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
