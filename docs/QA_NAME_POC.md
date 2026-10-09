# 单姓名字段定位PoC — name-slot-poc-01

日期：2026-10-09。状态：Verified static；PCSX2三个菜单的姓名显示已有直接截图。不是正式人名翻译或发布版。

## 构建身份与唯一新增变化

候选build/name-slot-poc-01/image/MODIFIED_FILE.iso，3232653312 B，SHA256 a47d5bdbe0c903a351f7d8f716f118994dfe4627aadefdd8e8c1b5dff4d8ef46。
locale配置locales/zh-CN/poc-name-01.json；原poc-text.json、原ISO/ELF及已测试expanded-text-poc-03-udf候选保持。
两Font仍2700 glyph、同一33字符D0 map；原三个UI/剧情目标保持。唯一新增文本修改为SHIP/00000460.cha的slot0首字段，源6 B改为8 B“测试中文”（d0a1d0a2d0a3d0a4），留NUL，40 B trailer保持。
其余300条CHA记录保持，包括slot4/8/169/229的原姓名。原CHA90007 B、SHA256 bf86e54bcbb7c0fa9698a63be5ee41a7e6d05b43c9ecb23793441ccbfc079ef1；本候选CHA同尺寸、SHA256 3f5d927d4224ce0460296f1e1ab6dfad616020157e0770b300fc70f764d76a9c。
新增槽bundle中的完整CHA唯一副本起点3226797；只同步此资源的相同修改。它与原bundle位置3220278不同，不能复用旧绝对offset。UE2 name table、ELF和其他姓名子串不改，不推定所有同名资源属于一个linked group。
AFS、slot0 manifest、ISO relocation/UDF仍复用既有流程；五阶段编排及报告独立推导同时处理显式slot配置，不另写ISO builder。

## 最短新增测试

1. 冷启动本页新ISO，以新游戏推进，不使用旧即时存档作为验收。
2. 取得角色控制权后打开人物状态/资料菜单，记录主角姓名是否出现“测试中文”；附整个菜单截图，便于确认文字所属字段。原UI和开场测试文字不作为姓名显示证据。
3. 姓名仍为原文也是有效定位结果，可能该菜单使用另一个记录/纹理；不要据此全局替换其它姓名或直接认定乱码。记录菜单名称与画面即可。
4. 检查首次可控阶段和菜单开关后剧情是否能继续；启动/加载异常记录最早出现阶段。正常存读档、场景、战斗及其它姓名联动继续分别登记。

“测试中文”只作字段定位标记，不是正式译名。本候选的三个菜单已有姓名截图；旧版本显示截图不自动证明名称候选通过。

## 三个菜单的运行观察（2026-10-09）

测试反馈为通过，新增三张3992×2312截图均可见主角姓名“测试中文”：

| 本地证据 | 直接可见内容 | SHA-256 |
|---|---|---|
| build/name-qa-22/evidence/1.png | 编成页主角卡片姓名，HP337/337、LV5 | 007df9c98be9c144030a0524daa2600a1478471f75b1d8d4147c427990fa2c6b |
| build/name-qa-22/evidence/2.png | 道具页主角卡片姓名，右侧物品列表仍显示韩文 | c4e282ac63b0e5b5885bc8cad607804db6fa18527ae528508d162fcec18f4f21 |
| build/name-qa-22/evidence/3.png | 角色详情页标题姓名，属性、装备与介绍仍显示韩文 | e45c82d84c5a079ad52ca32464a0103fccb9fd080864e4c10317954e54c1f513 |

**Verified observation**：三个指定菜单中的中文姓名可读，截图未见该姓名缺字、乱码或裁切；状态栏可见Vulkan和640×447（1x）。截图不证明菜单关闭后的继续运行、正常存读档、跨场景或战斗。

**High-confidence deduction**：结合候选仅修改CHA slot0及缓存副本的静态差分，三个菜单共享该修改的显示效果。截图没有ISO路径/hash，候选关联来自名称测试上下文；保留ISO本轮重新核对为上述a47d5b…hash。独立SHIP与缓存的加载优先级不能由同步修改实验区分。

**Unverified hypothesis**：slot4/8/169/229的用途、其他姓名依赖、内部lookup语义、完整两Font路径及长期稳定性。冷启动过程、PCSX2版本和BIOS身份未出现在截图中；不补填为已确认。10项自动生成QA记录不整体升级为通过。

下一步优先正常存档→关闭游戏→启动同一ISO→读取正常存档，以及一个实际场景切换；现有三个菜单不重复要求同样截图。正式姓名、物品和UI试译批次在回归门禁补齐并确认后另行开始，不进行全局姓名替换。

## 复现与验证

```powershell
work/venv/Scripts/python.exe -X utf8 tools/build_poc_pipeline.py --iso "<original-KR-ISO-path>" --font "<matching-font-path>" --locale locales/zh-CN/poc-name-01.json --out build/name-slot-poc
```

同一个原ISO、锁定字体、固定依赖即可构建，不依赖上轮名称实验输出或旧private工作文件。配置name_slot_overlays记录resource hash、source text/encoding、预期同名slots与显式targets；只允许targets子集，不自动cascade。
name_slots报告独立于原records=3统计，记录选中slot/cap/trailer/编码/缓存offset；QA增加SHIP/00000460.cha/slot/0 case，全部10项初始untested，环境仍null。人工记录validator同时检查新case inventory/expected；结构通过不代表运行时通过。

21项新增合成测试覆盖单slot保护、多目标、原hash、完整同名库存、重复/越界选择、控制符、编码、缓存唯一性及QA case整合；工程343项通过。真实五阶段构建、全ISO回读、独立验证通过；旧三字段候选在新工具下同hash再次验证通过。
干净源码复现本候选ISOhash；隔离源码回滚恢复322项基线，隔离ISO副本回滚恢复原ISOhash，修改候选保持。事务ignored build/name-iso-21/VERIFICATION.txt。
**Verified static**：版本/资源身份、只选slot0、trailer/其他记录保持、缓存同步、AFS/ISO/UDF及可复现性。
**High-confidence deduction**：单字段候选可用于区分名称显示来源，比同步全部同名字段更便于定位。
**Unverified hypothesis**：slot0纯显示/lookup角色、未观察菜单的显示来源、改名后的加载与脚本连续性；未启动批量翻译。
