# celfid 原生同字节候选与全 Class 根连续对照

## Verified static observations

显式 --equivalent-native 模式从 Core 根树后 262948 连续诊断到 3201448，共 2938500 B。完成 532 次 Class 根请求、28441 个新增对象自身片段集合和 36536 个片段观察。该范围混合源包对照与独立读取的表区段，计数名称改为 continuous_diagnostic_bytes，避免把表读取误称为完整源包 oracle。

| 根请求所属包 | 数量 |
|---|---:|
| Core.u | 1 |
| Engine.u | 174 |
| Gameplay.u | 13 |
| MrtsEngine.u | 128 |
| MrtsGame.u | 175 |
| UWindow.u | 41 |

既有 Core 根树另含 Object 根及其依赖；以上不是全游戏对象总数。18 次原生 serial 精确匹配、13 次限定 Texture mip 投影、1 次 INI wrapper/body 匹配、6 次包表区段读取。7 个原生片段具有多个身份候选；每个候选 serial 的全部字节及长度相同，全部身份保留，未把任意首项标记为已加载对象。候选字节或长度不同时立即停止。

6 个表区段中，4 个普通包表与既有源表一致，2 个是 00014365.usx／00014366.utx 的 parsed-table-only，原 serial 对应仍待核查。3201448 的下一处原生数据停止，不猜测长度或跳过。

## High-confidence deduction

引入按完整字节等价类保留候选而非任选对象身份，可以继续核查后续 Class 和源资源片段；已有脚本常量不因重复候选新增或去重。实际实例身份需要资源引用、加载顺序或引擎实现进一步判定。

## Unverified hypothesis / 未闭合部分

byte-identical 不证明同一实例或共享调色板；完整 Class 根顺序不证明全部 stream payload 已覆盖。小 mip 投影仍是后验模型，动态文本、图片文字、原生包 payload 和 CG 全时间轴文字仍未全部确认。全文提取门禁保持 false，无新增翻译、无资源导入、无镜像生成。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_stream_dependencies.py --archive work/kr/FILE.AFS --out work/stream-native-equivalence --equivalent-native
```

默认模式保留唯一原生身份要求并在 487115 停止。显式模式仍保留身份歧义；详细证据只保存 ignored work/build，不提交完整原生资源。
