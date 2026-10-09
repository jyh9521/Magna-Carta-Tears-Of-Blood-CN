# 统一集合补入 FPB 池余段

## Verified

既定 SHIP.AFS 身份下重新核查 708 FPB，707 个有效池合计 433271 B。原字段并集覆盖 432469 B，剩余 6 段／802 B 已按实际 offset、长度、片段 hash 纳入统一源集合，严格 CP949 阅读全部通过。00001945.fpb 为此前记录的 8 B 全零 stub，解析异常独立保留，不猜造空对话。

源集合保持 998 资源，活动字段从 19137 增为 19143，非空 14634。6334 条既有初稿全部保持精确源关联，未重映射、覆写或新增翻译。新池余段没有索引窗口：sequence_id=null、editable=false、backend_eligible=false；按源引用保存，不伪造剧情序号或擅自导入。

新集合 SHA-256：`a9c7a9b0344cfebeda01014ffab83c00dd94e7e4b5de4d286eedc3447d031c18`。

| FPB | 余段字节数 | 内容观察 |
|---|---:|---|
| 00004668 | 177 | Joshua 对话片段 |
| 00004669 | 217 | 八英雄段落，含 $n |
| 00004800 | 86 | 日文片段，CP949 可严格阅读，含 $n |
| 00004994 | 32 | 韩文片段 |
| 00005047 | 167 | 珠宝商／书相关片段 |
| 00006436 | 123 | 信件段落，含 $n$n |

正文、raw span、hash 与完整池余段数据仅存 ignored 输出；未以内容观察代替引用关系或运行可见性确认。

## 活跃异常全集合更新

当前全部 19143 字段重新核验源片段及 CP949 阅读。167 个失败包括 FPB 127、CHT 38、POD 2。119 个为 CP932 完整池／字段 roundtrip 阅读，40 个为 CP932 独立字段 roundtrip 阅读，8 个为 CP949 完整池窗口切断双字节字符。101 个既有替代阅读全部通过源 hash 和 codec roundtrip 核对，但未覆盖上述 167 个失败。

历史主 catalog 的 236 个失败中 165 个保留、71 个旧槽视图已被完整记录替代；新 POD 两个失败计入当前 167。165 和 236 不能继续作为当前失败数量。替代阅读不自动变更运行 codec 或导入许可。

## 尚未闭合

有效 FPB 池全部字节进入索引字段并集或非索引引用补充层，不代表所有余段有运行引用或全部游戏文本完成。compiled string、图片、SFD、流式包与 celfid 其他载荷的语义边界仍需核查。全文门禁保持关闭。

## 复现

先按 AUDITED_CORPUS.md 重建完整固定字段集合，然后运行：

```powershell
work/venv/Scripts/python.exe -X utf8 tools/append_pool_references.py --corpus work/consolidated-audit/source-corpus.json --ship work/kr/SHIP.AFS --batch locales/zh-CN/opening-review-01.json --batch locales/zh-CN/menu-review-01.json --batch locales/zh-CN/interface-review-02.json --batch locales/zh-CN/character-commentary-review-01.json --batch locales/zh-CN/story-review-01.json --out work/pool-reference-corpus
```

本工具重新读取原资源求覆盖余段，未依赖历史 pool-audit 中间结果。新源集合追加时验证资源 hash、区间范围、重复 ID、已有字段 overlap 和不可编辑状态；输入文件及既有译文 hash 保持不变。
