# 构建存储与保留清单

- 原版ISO、PCSX2、BIOS、正常存档和即时存档不属于build清理对象。
- docs/BUILD_RETENTION.json记录build相对路径、大小、SHA-256与保留角色；现有两项均保留，局部显示通过不等于完整运行验收。
- 待测候选和已测基线都必须明确登记；新候选生成后及时更新清单，不按目录名或“可重建”判定可删除。
- 清单外文件均为unreviewed，不意味着可删除。旧事务可包含尚未完成测试的镜像，必须核对具体文件身份和测试状态。
- 小型源码回滚与合成测试不再创建完整ISO副本；新镜像仅在实际资源变化需要运行验收时构建。历史验证日志不会在大产物清理后自动继续存在。
- 保留报告、截图和日志优先于保留可重建的大型中间资源；清理路径另行逐项确认。工具不执行删除。

## 只读盘点

```powershell
work/venv/Scripts/python.exe -X utf8 tools/build_storage.py --root build --manifest docs/BUILD_RETENTION.json --verify-hash
```

标准输出JSON包含相对文件路径、大小、protected/unreviewed、ISO数量和总字节数；默认只检查保留文件大小，只有--verify-hash才重算hash。缺少保留文件、大小/hash不符、路径穿越、符号链接或Windows reparse point立即报错，不写出成功盘点。

schema1报告mode=read-only、deletion_authorized=false；它不生成删除命令，不调整文件或QA记录。总字节为普通文件逻辑大小，不等于磁盘分配量；盘点期间新增/修改文件不构成一致性快照。

## 2026-10-09 实测

两份保留ISO各3232653312 B；hash与清单一致。只读盘点确认iso_count=2、protected_count=2，没有新ISO副本。本地报告位于build/name-qa-22/storage.json，文件只包含路径与hash，不包含游戏资源。
