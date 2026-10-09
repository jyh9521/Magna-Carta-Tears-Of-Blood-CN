# 普通包 TextBuffer 核查

## Verified static

- 原版 FILE.AFS SHA-256 为 `a9f7e2b34bfb5475bab2793821520295d120e2a122ccd363812f2d03c025072b`；只读遍历全部 53 项，识别 10 个普通 UE2 包，复用现有包表及 compact integer 解析。
- 10 包中的 568 个 TextBuffer export 全部按实际 serial offset/size 读取。样本全集具有 9 个零字节前缀、带符号 compact 字符数、严格相等的正文尺寸与终止符。394 项为正数单字节正文，174 项为负数 UTF-16LE 正文；严格解码及完整 serial 边界检查均通过。
- 568 个完整正文以稳定 package/export ID 保留；owner index/name、包/serial/正文 SHA-256 均保留。所有正文定位及终止验证通过，解析问题为 0。该结论限于普通包 TextBuffer，不扩展到其他对象类型或流式包。
- 排除行注释、块注释与单引号 name literal 后，双引号字面量候选为 2,993 项。保留原始引号与转义、正文字符偏移及行号；数量不是可见 UI 文本数量。全部正文保留，词法候选筛选不丢弃完整源内容。
- 6 条包含韩文音节的宽字符字面量，在逐个非 ASCII code unit 按高字节/低字节 CP949 解码后得到一致可读结果：字体名、阶段结束、位置未变、更换游戏状态及难度标签等。派生阅读视图与原始 UTF-16LE 解码正文同时保留，不替换原文；`alternative_runtime_verified=false`。
- 完整正文和字面量存于已忽略的 `work/extraction-coverage-54/script-audit/`。未复制新归档或 ISO，原始 FILE.AFS 哈希保持不变。

## High-confidence deduction

- 6 条宽字符字面量的原始 code unit 很可能保留了 CP949 双字节打包值，而非正确 Unicode 字符值。字体名和难度名称的可读派生结果支持该解释；引擎实际调用与当前游戏路径仍需核对。

## 未完成事项

- TextBuffer 包含脚本源码、注释、开发调试与工具字符串。脚本字面量可能只是参考源码，不能单独证明已编译脚本的当前执行行为。
- StrProperty export 定义、对象默认属性、脚本 bytecode 字面量和流式包 serial 仍需分别核查。普通 TextBuffer 568 项不是流式库存 1,106 次出现的全部正文定位证明。
- `complete_game_text=false`、`exhaustive_script_semantics=false` 保持关闭；568 个全文参考不直接加入批量翻译目标。
