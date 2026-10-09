# celfid 候选字节上下文核查

## Verified static

- 输入为版本锁定的原版 FILE.AFS、完整解压 celfid.lix 与第48轮统一源集合。原始归档、bundle、源集合均通过 SHA-256 身份检查。
- 35,048 条既有候选全部逐条校验 offset/length 边界与原始片段 SHA-256，未移除或修改候选。
- 21 个 SHIP 资源在 celfid 中的完整字节镜像，逐项校验完整资源尺寸与哈希通过。2,595 条候选完全位于这些镜像范围内；这只是资源上下文，不证明具体字段含义或可见性。
- 9 个启动流式包的已解析表范围包含 16,767 条候选。该范围含名字、import/export 元数据，不将解码结果直接当成游戏对白或 UI 译文。
- 剩余 15,686 条属于其他载荷范围。该分类不表示新增可见文本数量，也不表示无文本。完整 byte_context 与候选身份保存在已忽略的 `work/extraction-coverage-57/context-audit/`。
- 原始 celfid 未修改；上下文分类不复制资源正文或生成新 ISO。

## 未闭合事项

完整资源镜像不等于已确认 linked group；相同名字、子串、复制资源和运行时同步关系需要分别论证。流式包表之外的对象 serial、INI 内容、字段缓存、字面量及二进制误命中仍需分类。`celfid_semantics_complete=false`、`linked_groups_verified=false`、`complete_game_text=false`。
