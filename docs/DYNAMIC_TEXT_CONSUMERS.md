# 动态金额提示与截取消费者

2026-10-11。输入限定韩版 ELF SHA-256 `35cc6048f0e1f68d06bf3e515b99de3263e5092be62d6215cff5e74aa0ea15f0` 与已锁定 FILE.AFS。

## Verified static：原对象重新解析

`tools/audit_dynamic_text_calls.py` 重新读取原归档、核对 package／serial／inventory hash，按既有 bytecode parser 重建对象，并逐字段与冻结 inventory 比较。在 MrtsEngine.u／MrtsGame.u 中取得349条所选 getter 调用；树内区分 field reference、结构成员、整数与 literal，不把相邻整数直接当参数。

- MrtsGame.u export7929／7961：金额转换后的字符串位于 `Concat_StrStr` 左侧，`GetDVMainText(14)` 在右侧。
- export11770：`CurPrice` 转换字符串后拼接 `GetStoreMainText(7)`。
- export6717：`GetDVMainText(9)` 被 `LeftA(...,5)`／`MidA(...,5)` 截取，金额插入中间。
- export8049及其他调用：同一编号被 `Left(...,11)`／`Mid(...,11)` 截取。

getter原函数6780／6781读 DataManager.DivinationTextList，6787／6789读 StoreTextList；将结构成员Key与参数ID匹配，分别返回HelpText／MainText成员（原property引用已核对）。原TUI文件、列表初始化、对象布局及具体成员最终绑定尚待闭合；此处不因名称相似就授权全部TUI写入，也不证明所有调用实际运行。

## Verified static：原生方法描述符复制

ELF初始化片段通过 LUI／ADDIU／SQ 保存源、目标地址，再以 LQ／LWC1／SWC1 原样复制12字节描述符。工具核对完整指令序列与源描述符值，不使用未初始化的零 callback 当函数地址。

| 方法 | 源描述符 | 名称表 | callback | 字符串辅助函数 |
|---|---|---|---|---|
| LeftA | 0x47b6c0 | 0x47c910 | 0x197190 | 0x187ea0 |
| MidA | 0x47b6b0 | 0x47c900 | 0x196fa0 | 0x1880f0 |
| Left | 0x47b640 | 0x47c890 | 0x196560 | 0x188020 |
| Mid | 0x47b630 | 0x47c880 | 0x1963d0 | 0x1823b0 |

这证明条件性静态复制关系，不证明初始化函数已在某次游戏运行中执行。

## Verified offline：原指令标量执行

`tools/audit_text_slicing.py` 从真实ELF读取片段执行，不用重新编写的Python字符截取代替原算法。693组输入覆盖0到32个ASCII／高位双字节混合字符、负数／零／超长请求；同一输入还测试MidA长度0／1／3／65535。

- LeftA／MidA按高位bit扫描：首字节高位为1就额外跳过一字节；ASCII跳过一字节。该方法不是UTF-8解码。
- Left按FString的字节长度裁定范围，不扫描双字节边界。
- 原指令的branch delay、LB符号扩展、64位移位、零寄存器、负数与越界fixture由独立合成测试覆盖；未知指令及fixture越界必须报错。
- 分配、复制完整函数、引擎对象来源与实际游戏执行不属于标量模型。

## 译文约束

`locales/zh-CN/dynamic-text-constraints.json` 绑定3条目标与原source hash。金额前置的两条字段只保留“希德币。是否占卜／购买？”，避免变成“100需要花费希德币”。消灾目标前缀为5个双字节字符“消灾需花费”，随后一个ASCII空格，合计11字节；后缀为“希德币。是否消灾？”。

因此两套已观察路径分别形成：

- 字符截取：`消灾需花费 100 希德币。是否消灾？`
- 字节截取：`消灾需花费 100希德币。是否消灾？`

数量仅为验证fixture，不是写入游戏的固定价格。实际mapped glyph必须仍为双字节；前缀不可任意润色、加标点或改成UTF-8。当前三个字段仍 `pending-role-review`，直到列表／成员绑定闭合才可解除。其余4条金额／流派拼接待核查，不把本报告推广为全部动态文字已完成。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_text_slicing.py --elf work/kr/SCKA_200.43 --out work/text-slicing/report.json
```

getter完整命令、输入hash、literal输出和隔离回滚位于work/visible-text-137验证记录；原归档与ELF未改写。

## stage138：原生加载与序列化成员链

`tools/audit_native_text_loaders.py` 只读并锁定原ELF／FILE.AFS完整hash，不依赖反汇编显示文本。三段加载函数逐项核对路径构造、虚调用及delay slot读长、数组地址、28字节record索引计算和两个字符串对象的转换调用。

| 原TUI路径 | 加载函数 | this内数组偏移 | record内布局 |
|---|---|---|---|
| `..\UIText\00001239.tui` | 0x308250 | 0x148 | 4字节Key、256字节输入一、256字节输入二 → 0／4／16 |
| `..\UIText\00000682.tui` | 0x308600 | 0x160 | 同上 |
| `..\UIText\00001249.tui` | 0x308950 | 0x16c | 同上 |

Verified static：Core.u `MrtsTextData` 真实serialized NextField链为Key(IntProperty)→MainText(StrProperty)→HelpText(StrProperty)，均ArrayDim=1；MrtsEngine.u四个ArrayProperty及其内层StructProperty指向MrtsTextData，链为StoreTextList→BlacksmithTextList→DivinationTextList→GymTextList→MapTextList。descriptor末尾必须完全消费，链缺项、循环、越owner和原指令漂移均失败。

High-confidence deduction：三个loader的源输入顺序／record布局与struct字段链一致，Store／Divination／Gym native数组地址差也符合连续12字节数组布局。但本轮没有模拟完整UProperty链接初始化，**具体运行期成员offset尚未确认**；0x1a54c0转换的完整语义尚未核清。因此本轮不提升7个拼接字段的pending policy，不以普通源名称或原路径搜索无命中证明未使用。

额外getter／索引函数重新解析取得251条调用。道场文本不是假定的GetGymMainText：实际GetGymTextDataIndex在MrtsGame.u export8229／11695使用ID17，export10282等使用其他ID。它返回索引，后续数组取成员与拼接还需沿调用者核查；不能把名称当作直接取MainText的证明。

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_native_text_loaders.py --elf work/kr/SCKA_200.43 --archive work/kr/FILE.AFS --out work/native-text-loaders/report.json
```

## stage139：道场金额插入位置修正

原对象重新解析而非按调用名称猜测：MrtsGame.u export8229 `ProcessPreShowWindow`／export11695 `NotifyfromMessageBox`先以GetGymTextDataIndex(17,Index)取索引，再取GymTextList[Index].MainText；原表达式两端明确是LeftA(...,3)和MidA(...,3)，中间拼接ASCII空格及GymData.nMoney转换值，然后SetMessage(strMsg)。索引参数／两端数量与数组成员以真实token层级区分，不把邻近整数当参数。

旧目标“修炼需要花费希德币。是否修炼？”前三字为“修炼需”，剩余“要花费…”被金额隔开，会形成“修炼需 100要花费…”。目标改为“修炼需希德币。是否修炼？”，形成“修炼需 100希德币。是否修炼？”。金额仅为fixture。第四个dynamic constraint绑定源hash、3字符边界及目标；source／status／pending policy／control均不变。

通用原对象调用审计增加可选 `--function`，输出所选名称的所有原token，覆盖getter之后的成员读取／拼接／SetMessage语句；同名对象不会静默选第一项，报告保留各自完整ID。指定名称不存在即失败。本次251调用与72个同名候选对象重解析，消费树最终使用确切export8229／11695。记录见work/visible-text-139。这里证明编译表达式和离线字符截取，不冒称完整property初始化或游戏执行已验证；pending继续保留。

## stage149：Field原生Key与文本buffer identity

实际Field loader0x30ac40读取00001240.tui到array0x13c/count0x140，Key0/Main4/Help16/stride28。GetFieldTextData callback→0x3f2e00→0x3127a0逐条比Key并写出首匹配ordinal；getter按该ordinal复制两字段。120实际指令fixture通过。251原调用与177整对象重新解析，144literal全部不能直接当physical index，12动态参数继续保留。ShowChatResult92/93/208后SetMessage/SetText是CharName+MainText；ShowRecordInfo300/301/303是分UI组件SetText，不是假定连续拼接成一个字符串。完整tokens及source hashes在work/visible-text-149。

0x1a54c0确认仅JR ra和delay MOVE v0,a0，所有已观察TUI loader调用它时保持原buffer字节；原先未核清的此函数转换语义已闭合。此证据不自动解除其他pending property/consumer门禁，不改动态中文译文或最终ISO状态。
