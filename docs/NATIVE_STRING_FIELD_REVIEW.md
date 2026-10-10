# 地图 native 字符串与编译字段消费者核查

## stage 88 结果

两条独立只读核查链保留所有原 ID、字节哈希及源链接，不改变游戏输入或译稿。20151字段语料仍采用 stage86 快照；新上下文不直接变成可编辑正文。

### 地图字符串记录 — Verified framing

地图表身份为 `../Maps/00000118.unr`，表起点4185632、终点4188034。`4188198–4188219` 恰好为四个连续 compact-length 字符串记录，两个非空、两个空；每条长度、终止符、字节边界均验证，序列到指定终点后没有剩余字节。全部35048个候选的原始哈希重新核对。

两个此前未闭合候选各落在一条记录内，因此上下文未闭合数量从8降为6。新上下文文件为 `work/extraction-coverage-88/map-audit/contexts.json`，SHA-256 `915a22f506694a57c7157977c4f145465eaabb226c7a6525eb52ef0f4201fa82`。

Engine.u 的 GameEngine TextBuffer export5485 包含 URL 字段声明；全部568份脚本源码重新从FILE.AFS解包、解析。四条记录与 Protocol／Host／Map／Portal 的对应，以及相邻空options、7777端口、Valid值的解释属于 **High-confidence deduction**，不是已验证的native URL序列化顺序。具体文本和源字段哈希仅存ignored work。

模型数据剩余6个候选位于4188229、4188370、4188655、4188829、4190015、4190019。浮点形状或重复字节只能作为研究线索，不以任意4 B转换成功认定数值字段或丢弃候选。完整地图native边界仍未闭合。

### 编译字段消费者 — Verified reference context

全部8032个Function／NativeFunction／State／Struct重新解析，1207个字符串常量与stage86清单逐项核对。233个原待确认常量具有赋值上下文，其中225个目标是单个字段引用，8个目标为数组／成员等复杂表达式。新工具索引72个目标字段的1108次引用，保存对象ID、函数、token offset、serial hash、调用祖先与赋值左侧标记。

仅**同函数、单字段、StrProperty**赋值目标，且确有经过审查的display／lookup调用祖先，增加候选角色。赋值左侧引用不算消费者；跨函数引用仅保存、不推广；整数目标、仅TextSize测量、未知调用和复杂左值维持未确认。display与lookup混用维持未确认。

| 角色 | stage86 | stage88 |
|---|---:|---:|
| 可见文本候选 | 89 | 103 |
| 诊断文本候选 | 296 | 358 |
| 内部lookup／command候选 | 237 | 238 |
| 空值 | 265 | 265 |
| 未确认 | 320 | 243 |

新增77项为14个display片段、62个DisplayDebug诊断片段、1个FindObject资源路径。14项包括分隔符、空格、括号及数字显示片段，不是14条新增自然语言对白。此前已分类条目不覆盖重写；全部保持只读和不可导入。

输出 `work/extraction-coverage-88/compiled-audit-fixed/classifications.json` 的SHA-256为 `6f0fd4358c2ef6ddb0552daf6e06b7f442d59c78a8dc6a44b8c79446e0a2378e`。

这是静态字段引用上下文，不是赋值的reaching-definition证明：条件、覆盖赋值、跨函数传值及运行可达性没有据此闭合。常量出现在某字段赋值中且同函数存在display读取，只获得保守候选角色，不获得导入批准或运行显示结论。

## 复现

前置stage86、87输出分别按 `COVERAGE_SEMANTIC_REVIEW.md`、`STREAM_VIF_REVIEW.md` 生成；输出目录必须为空。

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_stream_native_strings.py --file work/kr/FILE.AFS --contexts work/extraction-coverage-87/vif-audit/contexts.json --out work/extraction-coverage-88/map-audit
work/venv/Scripts/python.exe -X utf8 tools/audit_compiled_field_contexts.py --file work/kr/FILE.AFS --objects work/extraction-coverage-68/compiled-audit/objects.json --strings work/extraction-coverage-68/compiled-audit/strings.json --classifications work/extraction-coverage-86/review-audit/compiled/classifications.json --out work/extraction-coverage-88/compiled-audit-fixed
work/venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -q
```

输入文件及快照哈希在运行前后验证；输出JSON逐份重开；失败研究目录保留、不覆盖。首次消费者核查发现真实import字段引用，原先仅接受正export的临时实现失败；修订为有界保留import／null未知身份，未把import字段误认本地StrProperty，详见 `PITFALLS.md`。

## 完成边界

配置1008项分类、数值资源记录几何、编码与控制结构证据仍沿用stage86输出；不据此宣布三个配置消费者、243个常量或全影片文字核查完成。完整native schema、动态脚本数据流、ELF消费者、LINEAR保留尾部及SFD画面文字仍需接续，`coverage_review_complete=false`、`complete_game_text=false`。
