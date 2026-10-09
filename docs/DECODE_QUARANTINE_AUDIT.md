# 活跃文本异常字节核查

## Verified static（2026-10-10）

998 个源资源及 15,121 个活跃字段全部重新核对原 SHIP 资源大小、SHA-256、切片边界和字段 SHA-256，源集合保持不变。活跃 CP949 严格解码失败为 **165**：13 个 FPB 的 127 个窗口、2 个 CHT 的 38 个字段。旧 15,635 字段目录的 236 个失败中，71 个属于已经由完整记录布局替代的源视图，不再计入活跃失败；旧目录仍保留。

12 个受影响 FPB 的完整 pool 及其中 119 个失败窗口严格 CP932 解码并逐字节往返一致。2 个 CHT 的全部 38 个失败字段也严格 CP932 往返一致。替代阅读正文仅写入 ignored 输出，canonical CP949 目录、字段 ID、offset、length、译文和导入许可均未改动。

`SHIP/00000106.fpb` 的完整 168 B pool 严格 CP949 往返一致，但 8 个失败窗口的起点或终点落在双字节字符内部。offset 是字节坐标，不是 Unicode 字符坐标；9 个显式窗口另有上游合成 seq0 视图。整池末尾含 NUL，池内存在韩文、日文及 WINMAIN 等测试样式内容。完整 CP932 解码失败，局部窗口偶然 CP932 成功不能作为整池 codec 决策。保留原始窗口及整池参考，不擅自修复偏移。

现有 101 个 source-interpretations 记录全部在活跃集合找到同 ID、同 hash，并再次严格往返通过。这 101 个记录与本轮 165 个 CP949 失败字段没有重叠，不能用既有记录数抵消失败字段数。

## High-confidence deduction

12 个完整 CP932 pool 与 38 个 CHT 字段呈现连贯日文对白或教程／设定文本，与字节级 CP932 往返证据一致；韩版资源中包含日文源内容，不应仅根据目录 locale 决定原文语言。

`00000106.fpb` 的混合文本外观符合开发测试内容，但仅凭文本外观不能确认资源未被运行时引用。

## Unverified hypothesis / 导入边界

替代 codec 的严格往返不证明运行时使用该 codec，不证明执行可达或显示可见。8 个切断窗口的引用关系、是否属于有意测试输入仍未确认。替代阅读全部保持 editable=false、reinsertion_approved=false。全文覆盖门禁仍关闭；其他包内正文、图片、SFD 与未知控制结构的核查继续进行。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_decode_quarantine.py --corpus work/extraction-coverage-48/final-audit/source-corpus.json --old-catalog work/catalog-stage-24/catalog-final/source-catalog.json --ship work/kr/SHIP.AFS --interpretations locales/zh-CN/source-interpretations.json --out work/decode-quarantine/audit
```

工具复用上游 AFS reader 与 FPB parser，不写原始资源，不重建 ISO。输出 failures.json、pools.json、superseded-failures.json、summary.json；完整原文不进入 Git。输出目录须为空且位于 ignored 路径。
