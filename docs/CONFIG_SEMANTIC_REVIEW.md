# 配置值逐项语义分类

## Verified static

全部 29 个配置资源、1008 个值与 FILE 原档重新逐字节核对；ID、行号、section 重复序号、key、offset、长度、hash 与占位符原值保持。重新解析 568 个普通 TextBuffer：38 个配置项具有同 owner/key 的完整单行声明参考，Core.int 的 Errors/Exec 具有两个 Localize 源调用参考。源码声明与调用参考不等于当前二进制的运行执行证据。

| 候选角色 | 项数 | 判定边界 |
|---|---:|---|
| 可见文本候选 | 373 | 提示／菜单／默认文本／桌面安装标签；不是373个已确认游戏正文 |
| 内部配置 | 460 | 路径、类选择、输入命令、参数／枚举、命令行 token，含90个空值 |
| 诊断文本 | 172 | Errors及命令行帮助；错误提示可能显示，不从全文候选删除 |
| 待确认 | 3 | 两个默认玩家 Name、一个 ProtocolDescription；加载消费者未完全绑定 |

40 个 Public 描述保留完整结构；17 个 Preferences 中 Caption 单独形成候选子字段。Parent 属层级查找关系，Class／Name／Category 等属于注册或引用，不随 Caption 翻译。子字段保存绝对字节 offset 和 hash，全部只读。HelpParm／HelpCmd 即使被打印也属于命令 token；HelpUsage／HelpDesc 包含混合语法，整行仍需保护参数与格式符。

## High-confidence deduction

section、key、描述字段结构与源码声明支持上述候选角色；不能只依据 ASCII 或英文外观分类。Engine/Console 的源码说明默认 Message 可忽略输出，直接 Localize→Message 不证明玩家看见提示。桌面／编辑器／安装文字不因韩版PS2来源自动丢弃；当前仅记录功能候选。

## 未闭合部分

可见性、当前locale加载、native消费、覆盖顺序和可编辑边界仍未证明；3个待确认项完整保留。config_role_review_complete=true仅表示全部条目拥有分类记录，不表示runtime_visibility_verified或全游戏覆盖完成。editable=false、backend_eligible=false；没有翻译或写入游戏。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_config_semantics.py --corpus work/extraction-coverage-82/consolidated-audit/source-corpus.json --archive work/kr/FILE.AFS --out work/config-semantic-review
```

完整原值及证据保存在ignored输出，公开JSON只记录统计。未知section/key保留unresolved；混合描述括号、引号、重复member和边界异常均拒绝。
