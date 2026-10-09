# FILE 配置及国际化值全量核查

## Verified

FILE.AFS 的全部 2 个 .ini 与 27 个 .int 重新读取，共 29 个资源、1008 个 key/value 条目，918 个非空值、90 个空值。全部原字节严格 ASCII，0 解码失败。每行包括空行、注释、section 与 entry 均计入连续 byte coverage；原值空格、重复 key／section、首个等号后的其余等号和占位符保持，不以字典覆盖重复项。

3 个完整正文在 celfid 中精确镜像：psx2game.ini @528、psx2user.ini @347423、Core.int @4191737，最后一项终点等于 celfid 解压长度 4195112。其他 .int 未发现完整原正文镜像，不能据此推断不使用。

Core.int 含引擎错误、载入／保存状态与确认提示；其他资源包含编辑器、安装、声音与引擎相关值。配置项与内部类名、包名、路径、参数不作为普通正文自动翻译。占位符提取只作为候选记录，不能替代完整控制符 validator。

新增只读补充清单保存 resources.json／entries.json，使用 FILE/<name>/line/<number> 身份。此前主 corpus 的 998 个资源／19143 个字段未修改；该补充清单尚未并入可导入正文目录，不把 1008 项宣称为新增可见正文。

## High-confidence deduction

celfid 最末尾包含完整 Core.int，而不是全部为未知原生数据。必须把独立国际化文本值纳入覆盖核查；配置结构含大量非自然语言值，需要按 section／key 与运行调用共同确定可编辑范围。

## 未闭合部分

1008 个值的运行使用及可见语义仍待分类，translation_backend=false、runtime_visibility_verified=false、semantic_review_complete=false。全文提取门禁保持 false；旧版只统计资源表正文的数量不是全文最终数量。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_config_entries.py --archive work/kr/FILE.AFS --out work/config-entry-audit
```

逐条原值仅保存在 ignored work/build，公共报告只记录结构统计。工具只读原档，不生成原资源副本或测试镜像。
