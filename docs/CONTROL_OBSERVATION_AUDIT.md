# 隔离控制结构逐项核查

## Verified lexical（2026-10-10）

最新 19,137 字段源集合中的全部 101 个 controls=quarantined 字段重新按字符位置遍历。225 个未被现有 token grammar 接受或属于控制字符的观测逐项保留：49 个数字百分号、153 个非 ASCII 尖括号包围片段、1 个箭头片段和 22 个控制字符。7 个字段包含 NUL／TAB／LF 等控制字符。

149 次尖括号观测的内部文字与完整 ITM 名称字段逐字符精确相同，保存 item 源 ID、hash、record key 关联。149 是出现次数，不是独立物品或已确认 linked group 数量。4 次未精确匹配：公告标题一次、两处同名火系符名称、另一处河系符名称；不通过 trim、错字修正或相似匹配强行关联。

已知 `$n`、`$Dnn`、已支持 placeholder 与 ASCII tag 沿用现有 grammar，不当成未知标记。所有原始片段和顺序保留。审计只增加观察数据，**validator 没有放宽，所有字段仍不获导入许可**。

## High-confidence deduction

数值百分号的上下文主要是折扣、技能倍率和驱动槽比例；尖括号包围内容主要引用物品／符名称。单纯对 `$%<>` 统一拒绝会隔离这些候选文字，但不能因此把标记删除或认定不存在运行时解释。ITM 与 POD 精确名称关联可以作为统一术语核对的静态线索，尚非必须同步改写的引擎约束证据。

## Unverified

百分号和非 ASCII 尖括号的引擎解释、名称是否参与查表、箭头和实际 TAB／LF 的渲染行为仍须 native／运行时证据。未匹配物品名可能存在文本差异或不同资源来源，不擅自定稿。NUL 尾部的窗口边界问题与显示换行不是同一问题。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_control_observations.py --corpus work/extraction-coverage-65/consolidated-audit/source-corpus.json --out work/control-observations/audit
```

输出仅进入 ignored 路径，源集合执行前后 hash 相同。旧目录 123／前版 105 个隔离字段属于历史视图，不沿用为当前集合数量。全文覆盖门禁继续关闭。
