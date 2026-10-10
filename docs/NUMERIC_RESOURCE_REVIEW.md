# CLS／ATT／VAL 完整数值区核查

## Verified geometry / native address observations

三个原资源全部读取并核对hash，8 B count/kind头及固定word区精确闭合到文件末尾；逐record与word值保存，只读且不依赖NUL文本启发式。

| 资源 | count | kind | stride | word数 |
|---|---:|---:|---:|---:|
| CLS | 213 | 24 | 100 B | 25 |
| ATT | 456 | 5 | 24 B | 6 |
| VAL | 170 | 1 | 8 B | 2 |

共839个记录、8401个u32；有符号阅读另存，不替换原值。CLS的三个旧韩文字候选全部位于record40、47、135的word3低两字节，完整u32均为16791；其后高两字节为零令NUL扫描误识别音节。候选ID/hash仍保留，角色改为fixed-word-payload-not-translatable，不作为新增正文。

版本锁定ELF中的三个完整资源路径及各唯一LUI/lower地址构造候选均重新核验；邻近160 word以内的JAL/JALR保留既有保守参数trace，不推断未知vtable实现。地址构造上界VA分别为VAL 0x30b464、CLS 0x30b9c4、ATT 0x30d184。逐指令及调用证据仅存ignored输出。

## High-confidence deduction

重新读取Core Object源码中的MrtsClassData、MrtsTargetData、MrtsValueData结构参考及INPUT_STYLE_SLOT=3。VAL两int、ATT六int和实际word几何相容；CLS的数值／引用成员支持内部角色判定。脚本struct的内存定义不是已确认磁盘schema；CLS末word、运行时新增字段、具体读写顺序不得仅按名称猜定。

## 未闭合部分

native reader完整控制流、字段用途及键到运行对象的映射尚未证明。当前闭合的是固定word几何和三个候选的数值包含关系，不宣称全游戏不存在其他文本。未修改原档、ELF或镜像。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_numeric_resources.py --corpus work/extraction-coverage-82/consolidated-audit/source-corpus.json --ship work/kr/SHIP.AFS --file work/kr/FILE.AFS --elf work/kr/SCKA_200.43 --out work/numeric-resource-review
```
