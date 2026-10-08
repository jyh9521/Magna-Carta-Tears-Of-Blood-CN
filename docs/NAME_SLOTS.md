# 角色名称字段与缓存同步实验

日期：2026-10-09。状态：Verified static；没有生成新ISO或正式角色译名。

## 原韩版的实际字节

研究使用锁定hash的SCKA-20043原ISO，复用上游slot parser/builder、AFS reader和chunked zlib。不是重新实现姓名格式。
SHIP/00000460.cha为90007 B，header三个u32为301/11/0，12 B header后301个299 B记录，完整文件在原celfid解压buffer中恰好出现一次，起点3220278。
源名的CP949字节为c4aeb8b0c3f7。5个记录的首个NUL字符串完全匹配：

| slot | 文件offset | 可写容量（留NUL） | 保留trailer |
|---:|---:|---:|---:|
|0|12|258 B|40 B|
|4|1208|258 B|40 B|
|8|2404|258 B|40 B|
|169|50543|258 B|40 B|
|229|68483|254 B|44 B|

header/其余296记录/trailer保持。记录号不等于上游marker里的id，不能把slot169直接当id169。上游FF-marker机制仍有价值，但不能只搜索英文正则或把marker缺失的首记录丢弃。
同一姓名字节在原celfid出现17次、SHIP全部entry中出现437次；这是原始字节命中数，不是可翻译文本数量，也不是运行时关联组。还存在描述内子串、数字后缀技能名称、剧情和潜在内部标识；不进行全局替换。

## 可复现实验

```powershell
work/venv/Scripts/python.exe -X utf8 tools/prepare_name_slots.py --iso "<original-KR-ISO-path>" --font "<matching-font-path>" --locale locales/zh-CN/poc-text.json --resource 00000460.cha --source-name 칼린츠 --target-name 测试中文 --expected-matches 5 --out work/name-slot-experiment
```

源ISO/profile/font/原Font/bundle均有hash门禁；D0编码从既有33字符map顺序及真实Font表推导，不修改locale。示例目标是现有PoC字符组成的测试标记，不是正式人名。
仅替换首NUL字段完全相等的5条记录；匹配数量必须等于显式参数。控制符校验、编码覆盖、容量/NUL、原文件无编辑往返、未选记录/header/trailer均核验。
缓存完整资源要求唯一，复用overlay_segments生成内存中的等长镜像并核对；不输出携带新D0文本但仍使用原Font的缓存包，以免将实验资源误当可运行镜像。
输出original-resource.bin、modified-resource.bin、name-plan.json及只读输入提取，全部ignored。没有AFS/ISO写回，不改UE2 name table、ELF、内部ASCII键或非目标姓名子串。
本轮原资源SHA256为bf86e54bcbb7c0fa9698a63be5ee41a7e6d05b43c9ecb23793441ccbfc079ef1；修改资源为49a7a7c0f0d11e973f80a7c1d3ba6ad8502d239fc606726d093b17956e7135dc；尺寸同为90007 B。

## 验证及下一步

13项合成测试覆盖增长、trailer、未目标子串、匹配数、NUL/容量和缓存唯一性；工程322项通过。干净源码复现相同资源/plan，隔离源码回滚恢复309项基线，资源副本回滚恢复原hash，修改资源保持。事务在ignored build/name-link-20/VERIFICATION.txt。
**Verified**：字节命中、上述记录边界/容量、完整缓存副本及等长同步实验。
**High-confidence deduction**：5个相同首字段属于角色名称相关数据，SHIP与完整缓存需协调；不能据此确认5个字段全部为纯显示名称。
**Unverified hypothesis**：字段作为UI显示或lookup key的具体作用、5条记录的逻辑关联、其它437处的语义及实际名称渲染路径。
下一步以显式slot配置接入新增槽候选，分资源/分记录测试名称显示与脚本连续性；原镜像、既有可测试候选保持，未确认字段不开放批量写回。

## 后续单字段镜像接入

独立资源阶段的5条替换仅是受控资源演示。后续可运行候选改用显式slot0单字段，其余4条保持，复用本页相同边界与缓存机制；不把全5条资源直接替入镜像，见 [名称定位候选](QA_NAME_POC.md)。
