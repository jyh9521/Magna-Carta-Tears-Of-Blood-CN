# 集中提取语义补核与保留项

## 本轮已完成的有界核查

配置值、celfid尾部属性、CLS/ATT/VAL完整word区、普通编译字符串上下文及全部活跃解码失败／控制隔离项均形成可复核记录。详见CONFIG_SEMANTIC_REVIEW.md、STREAM_TAIL_CONTEXT_REVIEW.md、NUMERIC_RESOURCE_REVIEW.md及同名JSON汇总。各步骤复用已有AFS、script、property、texture与codec工具，不生成AFS、SFD或ISO副本。

| 层 | 结果 |
|---|---|
| 配置 | 1008项全分类：373可见候选、460内部、172诊断、3待确认 |
| celfid | 35048完整候选保留；39项新增字节上下文；153仍未闭合 |
| 数值资源 | 839 record／8401 word；3个CLS怪字候选落在word内 |
| 普通编译字符串 | 8032对象重新解析；1207字符串全分类 |
| 活跃解码失败 | 167：119整FPB池CP932候选、40字段CP932候选、8字符边界切断 |
| 控制隔离 | 101字段／225观测；149处物品名精确关联；validator未放宽 |
| 既有译稿 | 6334条全部exact-source-link，target及状态不改 |

编译字符串按最近已审查调用符号分类：89可见候选、296诊断候选（含49个DisplayDebug/DrawText）、237内部lookup／命令候选、265空串、320待确认。Localize的section/key/package参数即使存在外层Message，也保持lookup角色；不按外层显示方法把资源标识升级正文。比较／赋值／未审查调用不自动排除；动态数据流和参数位置仍待核查。该规则不同于此前17个显示符号的133候选过滤，不以89替代全游戏UI数。

## 最新只读快照

`work/extraction-coverage-86/review-audit/source-corpus.json`：1027资源、20151字段，SHA-256 `39884cc3e9175811800c92ee8ae7f3d1a50b96a67bb9d0d41cf0fb8f84895dc6`。原ID/hash/offset/原文/codec/controls与editable逐项保持；新增coverage_reviews，不改原读法。配置与数值候选角色被注释，其余只新增审核层；后端许可不变。

SHIP-only projection只是复用旧解码审计工具的明确输入视图，包含998资源／19143字段，不是重新遗漏配置的主快照。两个POD失败字段计入当前167；旧165仅FPB/CHT是历史集合。既有101个encoding interpretations严格往返及源关联全部再次验证，未用其数量抵消失败字段。

## 全文覆盖仍未完成

complete_game_text=false、coverage_review_complete=false、translation_gate=coverage-audit-pending。剩余StaticMesh/地图native、配置3项消费者、编译320项与动态流、ELF语义、LINEAR有效前缀及原尾部、流式图片、SFD逐条原文转写/时轴/去重继续核查。逐帧hash、源码声明、候选分类均不替代文字转写或运行显示证据；未扩大翻译或开放写回。

## 全步骤重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_coverage_review.py --corpus work/extraction-coverage-82/consolidated-audit/source-corpus.json --old-catalog work/catalog-stage-24/catalog-final/source-catalog.json --ship work/kr/SHIP.AFS --file work/kr/FILE.AFS --elf work/kr/SCKA_200.43 --interpretations locales/zh-CN/source-interpretations.json --contexts work/extraction-coverage-83/chain-audit/contexts.json --objects work/extraction-coverage-68/compiled-audit/objects.json --strings work/extraction-coverage-68/compiled-audit/strings.json --batch locales/zh-CN/opening-review-01.json --batch locales/zh-CN/menu-review-01.json --batch locales/zh-CN/interface-review-02.json --batch locales/zh-CN/character-commentary-review-01.json --batch locales/zh-CN/story-review-01.json --out work/coverage-semantic-review
```

输出须为ignored空目录，全部输入hash执行前后保持。复现依赖前述stage68/82/83产物；相应专题文档提供其生成命令。完整原文和引用上下文不进入公开仓库。

## stage90 解析器操作数

见 [解析器核查](PARSER_OPERAND_REVIEW.md)。全部8032对象/1207常量重解析；15项补充有界解析器操作数候选，最新待确认228项。101个隔离字段与validator保持不变；coverage_review_complete=false。
