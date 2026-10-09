# 韩版 FDS／GFT／ODD 补充字段提取

## 范围与证据

Verified static：输入为 catalog manifest 锁定的韩版 SHIP.AFS；六个目标资源 SHA-256 与旧 catalog 一致。上游 AFS 读库继续复用，USA slot parser／builder 保持不变。新增只读工具 `tools/extract_record_fields.py` 根据实际韩版头部、文件总长、记录分区及 NUL 填充选择布局，不提供 writer，不给字段自动授予导入权限。

六文件共 130 条记录、1,168 个字段，1,065 个非空、103 个空；字段原字节全部严格 CP949 解码成功，控制结构检查无隔离。成功解码不证明语种或显示用途；FDS 中四个字段和短 GFT 中一个字段的严格 CP949 解码结果含日文假名；日文语义不证明 CP932，详见 SOURCE_CORPUS.md。metadata-only ODD 未产生文字字段，但原记录元数据完整保留。

| 资源 | header 第二 word | 记录数 | 记录跨度 B | 字段跨度 B | 字段数 |
|---|---:|---:|---:|---|---:|
| 00003591.fds | 4 | 11 | 2052 | 512 × 4 | 44 |
| 00003633.fds | 4 | 2 | 2052 | 512 × 4 | 8 |
| 00003531.gft | 23 | 92 | 822 | 70 × 11 | 1012 |
| 00002778.gft | 23 | 4 | 10307 | 1000 × 8，255 × 1，1000 × 2 | 44 |
| 00002106.odd | 12 | 20 | 560 | 80，240，200 | 60 |
| 00001950.odd | 4 | 1 | 20 | 仅保留原元数据 | 0 |

所有文件大小均满足 `8 + count × stride`；8 B header 为两个 little-endian u32，首 word 与记录数一致，第二 word 只记录观察值，不强行命名语义。记录首 u32 ID 文件内唯一但不要求连续。每个固定文字区段有 NUL，首 NUL 及之后全零。字段容量统计不含末尾 NUL；writer 尚未启用。

## 记录分区（Verified bytes）

偏移均相对记录起点，记录起点为 `8 + index × stride`。

- FDS：`+0` 原 u32 ID；`+4` 起四个连续 512 B 区段。边界分区覆盖全部 2052 B。
- 短 GFT：`+0` 原 u32 ID；`+4` 起 11 组 `4 B 未知元数据 + 70 B NUL 字段`；`+818` 保留末尾 4 B，实际 92 条均为零。
- 长 GFT：相同组结构，字段跨度改为八个 1000 B、一个 255 B、两个 1000 B；末尾 4 B @10303，实际四条均为零。23 不等于已证明的文字字段数。
- 正文 ODD：`+0..7` 保留 8 B 元数据；文字字段起点 `+8/+88/+328`，跨度 80/240/200；`+528..559` 保留 32 B 元数据。
- 小 ODD：20 B 记录全部作为只读未知元数据。没有固定文字区段的观察结果不等于该格式全局不存在文字。

元数据 hex、记录 hash、完整字段 hash、有效原文 hash、ID、索引和偏移仅输出至 ignored 数据层。字段稳定 ID 采用 `SHIP/<resource>/record-index/<index>/field/<number>`；保留 ID 与索引两者，不用未知数字作角色语义标签。

## 与旧导出的关系

旧主 catalog 不覆写，已存在的 6334 条译文及其稳定 ID 保持。新增补充层按原字节区间关联旧主字段：56 个完全同区间、12 个完全位于旧主字段内、821 个完全字段外、176 个部分重叠、103 个空。997 个字段包含旧主字段之外的字节，不能直接当作 997 条新增对白。

这六文件此前保存的 689 个扫描候选，642 个与新字段完全同区间，47 个完全落在新字段内；没有候选仍含新字段之外的字节。该结果关闭了这些既有候选的字节覆盖缺口，不证明全部运行文字已发现、字段语义已确定或无其他编码。

High-confidence deduction：原先沿用 USA 固定槽步长的 leading-only 韩版视图混入 ID／数值、切断部分句子，是这些资源提取缺口的主要原因。真正的运行时读取实现和 GFT／ODD 元数据语义仍为 Unverified hypothesis，不开放自动重建。

## 重现与后续

```powershell
work/venv/Scripts/python.exe -X utf8 tools/extract_record_fields.py --catalog work/catalog-stage-24/catalog-final/source-catalog.json --ship work/kr/SHIP.AFS --out work/record-fields/audit
```

输出必须为空且在 ignored work/build。原文本只留在 `record-fields.json`；公开 [RECORD_FIELDS.json](RECORD_FIELDS.json) 只含聚合与布局。工具拒绝未知／歧义几何、重复记录 ID、缺 NUL 或非零填充；严格解码失败原字节保留，不用替换字符掩盖。

新增十项测试；基线 423 项、修改版 433 项、隔离回滚 423 项通过。现有源 catalog、术语、译文和测试 ISO 保持；不生成新镜像。

下一步统一审核补充字段的编码、内部标识符和显示用途，再建立合并／去重集合；剩余 CHA／MDG 候选、FPB 间隙、UE2 属性与图片、ELF、字幕缺口继续审计。全文提取门禁仍为未完成，不扩大翻译。
