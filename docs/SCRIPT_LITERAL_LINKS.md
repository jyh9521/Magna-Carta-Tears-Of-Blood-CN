# 脚本字面量与普通包 serial 字节关联

## Verified static

- 使用 568 个完整 TextBuffer 正文中的 2,993 条双引号参考候选，逐项在同一个原始普通包的非 TextBuffer export serial 边界内检索精确正文加终止符。原始 FILE.AFS 的版本哈希保持一致。
- CP949、UTF-16LE、宽字符 CP949 打包派生阅读视图分别检索，不进行转义语义猜测。14 条带反斜线候选保留在完整源集合中，但不在本步骤解释转义。
- 形成 1,193 条有字节命中的候选/编码组合：CP949 961、UTF-16LE 227、打包 CP949 派生视图 5。共 51,765 次字节命中。短字串、后缀、相同内容、不同源代码位置可能重复命中；这些数字不是独立文本数量。
- 5 条打包派生视图全部在原版 MrtsGame.u 的同 owner `InitValue` Function export 内找到 CP949 正文加 NUL，前一字节为 `0x1f`：

| owner | Function export | 正文起点（文件偏移） | 派生阅读用途 |
|---|---:|---:|---|
| MrtsBattleMenuCW | 8409 | 0x8c648 | 阶段结束标签 |
| MrtsBattleMenuCW | 8409 | 0x8c685 | 位置未变标签 |
| MrtsBattleMenuCW | 8409 | 0x8c6c3 | 游戏恢复标签 |
| MrtsMainSetDifficultCW | 8307 | 0x8adc5 | 简单难度标签 |
| MrtsMainSetDifficultCW | 8307 | 0x8ae01 | 普通难度标签 |

- 6 条宽字符派生阅读中的字体名未在非 TextBuffer serial 形成相同 CP949 命中；不能把源码构建指令中的字体名当成当前已加载字体证据。
- 完整命中、片段哈希、export/owner、前一字节与编码保留于已忽略的 `work/extraction-coverage-55/link-audit/`；公共仓库只保存工具、测试和统计。未修改原始资源，未生成新 ISO。

## High-confidence deduction

- 同 owner 函数中的 5 条精确 CP949 命中支持源码宽 code unit 保存了 CP949 打包值的解释，并证明对应字节存在于 compiled Function serial。

## 覆盖限制

- 精确字节命中不证明字节码指令边界、运行时可达性或实际显示。前一字节 `0x1f` 只作为观察记录，不替代完整 bytecode parser。
- 源码相应按钮设置包含 `bHide=true`。运行中的可见状态尚未验证，不能直接判定为实际菜单遗漏。
- 默认属性、未保留源码的函数、转义语义与流式 serial 仍需独立核查。`bytecode_decoder_complete=false`、`execution_verified=false`、`complete_game_text=false`。
