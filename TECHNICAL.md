# Technical Notes — Magna Carta localization

Verified(stage168)：原CDG header72/type5、8+72*526=37880B；每条先读4B至stack264，再读第二u32至nativeKey0，源Name255→native10，后续两u32→native8/c，再读Desc255→native1c；native array118/count11c/stride40，callback311100..311270按nativeKey0比较后复制两FString。原source+4是Key，不能用丢弃的首u32推lookup。CDG六个目标odd slot31/81/87/97/117/137各对应real record15/40/43/48/58/68。Store308250/Gym308950 loader path/source key/Main256/Help256及28stride、array148/16c与native lookup anchors绑定；Store key4/5/12对应physical9/10/18，Gymkey1physical1。静态存储及lookup不冒称所有UIconsumer/游戏事件已执行。

Verified(stage167)：27FPB独立原native numericKey first-match与source offset/length/hash，3CHT及48POD原native512→FString链；ITM六个Comment原record398..403、594serializedstride/255slot/native50，原numericKey经2fe510选择同一physicalindex，源slot/padding/hash保持。派生entry只解除这些已验证字段的control quarantine并附原source/reading/target/nativebinding hashes；原source bytes由import/preflight再核查。runtime_control_semantics_verified=false保留；不宣称全部renderer/事件或其他consumer已执行。

stage166的literal-control-readings审计只证明原字节CP949往返、已知$n/$D/printf token保持、数字百分比及箭头顺序、非ASCII括号名称和名词表一致；它不证明百分比/括号的所有原生consumer语义，不更改generic protected_tokens，也不解除source quarantine。原8坏边界FPB与7个有控制字节字段继续保留。

Verified：stage165四个FPB片假名窗口按实际pool offset/length/hash唯一匹配native record，再验证first numericKey；CHT字段00004044/slot12真实text offset6412，512B文本，前16B/后4B numeric保持。全角片假名可读性不等于运行时编码/事件执行证明。原8个00000106.fpb坏边界窗口继续保留。

## Native fixed dialogue storage andreal write bounds (stage164)

CHT path4b7740/native path ref2ffb38 andPartyData path4bb7e0/ref3a39ac read3headerwords andrecords with fouru32,512byte text andoneu32. Native reads512 at2ffc44/3a3ac0, conversion1a54c0 andbytecopy116c70;3a3bb0 passes the textFString int0 argument to3a3140, which copies it into aFString at+8 in68-byte child records while numericmetadata remains separate. GetNextChatData3a00e0 copies FString fields at+8/+14/+20. This is static storage, not proof ofall consumers or branchreachability.

POD path4b9070/ref329ec0 reads fiveu32 then24text slots with interleavedword separators atfield10/15 andthreefinalwords;originalsize12328. Sourcefield0/offset20 mapsnativeFString+18,field19/offset9756 maps+fc. The39source/resource/span hashes andnative anchors are reproducibly checked by audit_native_fixed_dialogue.py. Original maincorpus remains frozen;fieldlanguage/codec are explicit in a derived catalog.


## Field-local alternate reading gate (stage163)

Verified115 original FPB spans use the157 actual numeric-key chat payload copy; original ELF fingerprint andinstruction anchors are checked when deriving a source catalog. Only original decodefailed/dialogue-window fields with unique native source bindings are selected. Every selected field retains raw_hex/source hash/offset/length/key andgets ja-JP references/cp932 explicitly; source_interpretation records original failed status, raw/UTF-8reading hashes andfalse runtime encoding claim. Shared source_interpretation helpers fail on missing language/proof, wrongreadings/raw bytes or unsupportedcodec. rewrite_fpb has explicit per-sequence source_encodings without automatic fallback; untargeted/gap/header identity behavior remains. The originalprimary corpus is never overwritten. CHT37/POD2 remain separate; no nativeconsumer proof is invented for fixed fields.


## Source-hashed alternate decoding audit (stage162)

Audit154 previously failed primary-codec spans against the unchanged original SHIP archive. CP932 round trip and Hiragana/no-private-use checks alone do not prove display encoding or reachability. Explicit corpus/resource/span/reading hashes, protected token validation and original raw_hex are required.115FPB spans additionally match unique actual native records and first numeric-key lookup using the verified157chat protocol.37CHT and2POD fixed spans remain linguistic evidence without new native-consumer approval. Tool output keeps source_still_quarantined=true/import_approved=false. No change to the ordinary source catalog, active fonts or generated AFS is made in162.


## Named-resource storage andnumeric lookup (stage161)

Verified original ELF/SHIP: CHA loader30afe0/path4b79b0 reads301 records,299serialized bytes with255-byteName intoFString+44 in56-byte native records(array+28/count+2c); GetCharData310070→310170 compares numericKey. ABI30cec0/path4b7a70 reads358 records192bytes,40-byteName→+4 and128-byteComment→+24 in48-byte native records(array+4c/count+50); GetSkillData310300→3103f0 compares storedKey. ITM2fdb00/path4b76a0 reads479 records594bytes,255-byteName→+c and255-byteComment→+50 in100-byte native records(array+94/count+98). GetItemData30fdd0 calls2fe510 withnumericKey;12-byte hash node(next/key/physicalIndex),bucketmask andmissing-key fallback+564 are independent ofdisplay strings. Duplicate loading updates the numeric physical-index value at2fdca8; synthetic duplicate fixture matches this anchor, originals have unique keys.

1138 actual address-computation fixtures and481 item-hash fixtures pass. Compiled10975 sendsCharData.Name/ItemData.Name intoShowChatMessageBox;11048/12107 feedSkillData.Name/Comment intoAddList afternumericStyleData.Skill lookup andempty-name guard. This is static storage/producer evidence, not proof ofall consumer absence, runtime property initialization or reachability. Generic tool audit_named_resource_data.py remains versionlocked andlocale-neutral.


## Native FPB text consumer protocol (stage157)

Verified original ELF: registered Then_2DObjectControl_Chat callback0x37cad0..0x37d1bc calls0x342560 at0x37cb30. The numeric text key is loaded from event+0x98, FieldData pointer follows+0x78/+0x220/+0x340; independent talker field+0x94 is not derived from the text. The output FString stack+0x90 is copied to+0x80, passed to constructor0x37d4b0, copied to ChatParam+4, and enqueued via vtable+0x18. Native anchors lock this payload path; it does not use payload strings as actor lookup keys.

105 previously deferred labels/development lines uniquely bind pool offset/length/hash to actual FPB records and first numeric-key match. Locale profile does not assume seq+1: an attempted ordinal formula was contradicted by00000358 record10. Only exact source matches authorize the copy; source IDs/control sequences and translations remain unchanged. This verifies a static text-consumer protocol, not that every event/legacy record is reachable or visual layout is accepted.


## Additional text indices and bounded long callbacks (stage156)

Verified original native key lookup: RoadSign callback0x3135a0/helper0x313680 reads array0x190/count0x194; Pilot callback0x3136d0/helper0x3137b0 reads array0x19c/count0x1a0. Both use the same exact20-word28-byte record key-search template as Store/Divination/Gym. The 00011012.tui loader0x309990 binds path0x4b78f0, array0x19c, serialized256-byte MainText and HelpText into native FString+4/+16. This establishes storage, not insertion order.

MrtsPilot.SetDestList has a564-byte registered callback, so the prior512-byte return scan correctly rejected it. Registration now accepts an explicitly bounded aligned callback_limit, default512 unchanged; it never expands on failure and includes the delay slot inside the bound. CLI --callback-limit1024 binds this callback through its exact initializer. Archived MrtsPilot ScriptText references PilotTextList[2] only inside a commented-out state; comments and source references do not prove compiled consumers or unused runtime data. Remaining three dynamic TUI entries stay pending; no partial consumer proof is promoted.


## Style text and caption filter source chain (stage155)

Verified static: SGI loader0x30d350 binds ..\Sgi\00000468.sgi at0x4b7ab0. It reads source Key4B, Name100B then later Description67B; Name becomes FString+4 and description+88 in100-byte native records at array+0x40/count+0x44. Original GetStyleData descriptor binds callback0x310760, helper0x3109b0 scans Key, not physical index.249 actual scalar address computations confirm100-byte stride. Numeric key/data remain separate from strings.

Name participates in UI display and a case-insensitive caption comparison, so display evidence alone was insufficient. Same MrtsFieldListBox outer5 AddStyle11161 passes StyleData.Name to AddList12251; that function assigns a_Name to List.Caption and a_ID independently to List.ID. SetSubListBox11048 compares StyleData.Name against SelectedItem.Caption. This is label consistency, not a source-language hardcoded identifier. The initial whole-resource check found eight collisions between five Korean/Hanja spelling groups, missed by the promoted-only test. Eight Hanja-form labels now add an orthographic qualifier; five exact-source glossary rows match. The full 249-name equality check, including retained names, is required before approval. AddStyleInfo12135 assigns Description to List.HelpText. Structured profile has206 names/40 descriptions; static copy approval does not claim runtime property initialization or visual fit.


## Amount consumer source chain (stage154)

Verified static: GetStoreMainText6789 and GetDVMainText6781 are compiled functions (36tokens), looping physical i and comparing array[i].Key to ID before returning MainText. Searching for intUMrtsUIInfoexecGetStoreMainText/GetDVMainText fails because those names are not native registered methods; this does not mean the consumers are absent. Original GetStore/Divination/GymTextDataIndex callbacks0x312e80/0x3130e0/0x313210 call0x312f60/0x3131c0/0x3132f0; helpers compare stored key in28byte records at arrays0x148/0x160/0x16c. All20 words each checked;360 bounded actual instruction fixtures passed. Source loaders share these arrays.

ProcessLocalMessage6717 composes computed amount plus DV key14; key9 uses LeftA5/amount/MidA5. ShowAllWindow8049 uses Left11/amount/Mid11. Gym8229/11695 obtain key17 into Index and use GymTextList[Index].MainText with LeftA3/MidA3. Store11770 composes CurPrice plus key7; initial windows also show the bare suffix before later composition, an original behavior rather than an invented constant amount. Source/hash/token profile and actual encoded native boundaries bind four translation-copy decisions. Static consumer proof is separate from runtime property initialization, allocation and visual fit.


## Map confirmation full expression (stage152)

Verified static in original FILE/MrtsGame.u/export/11986: call425 GetMapTextDataIndex, literal4 at428, output TextID430; assignment434 sets TextData from MapTextList array438 indexed by TextID439. SetMessage547 concatenates NextNodeData.Name and TextData.MainText at549. Source serial hash and all expression tokens bind the translation decision. No nearby-integer inference or runtime reachability claim. Remaining seven suffix decisions are explicitly linguistic, not newly proven consumer bindings.


## Getter and direct-array consumers are different (stage151)

Verified static: four index-method descriptor copies bind FieldMenuTextIndex0x312840→0x3127a0, CommonTextIndex0x312920→0x3127f0, MapTextDataIndex0x313340→0x313420 and BattleTextDataIndex0x313470→0x313550. FieldMenu helper compares stored keys, as stage149 established. However direct compiled ArrayElement literals select physical array ordinals, not source record IDs. These two paths must remain separate.

Reparsing all eight supported original packages with four exact property selectors produced329 getter calls and283 whole objects. Bounded ArrayElement/DynArrayElement parent-child analysis found200 text-list reads,105 literal physical indices and95 nonliteral expressions. Nine missing fields appear in explicit consumers: NotifyFromWindow12188 contains style/stat messages, BeginState10975 contains recipient/item/gift confirmation, and MrtsStateToroChanged337 plus10271/10314 use spirit-stone suffixes. Literal ordinals bind source catalog geometry independently of getter keys; this is not a runtime property-offset initialization proof.

The source stat branches check nonzero values, not strictly positive ones. Fixtures preserve signed numbers, including -5; no absolute-value rewrite or new amount is inserted. New Chinese fragments move the predicate to the pre-number particle slot and reduce the old trailing predicate to punctuation. Whole expressions and object serial hashes are retained for reproducible review. Source masks, bytecode order and resource IDs are unchanged.


## Native field text keys (stage149)

Verified static: registered intUMrtsUIInfoexecGetFieldTextData callback0x3f2c90 calls0x3f2e00, which loads the data object at this+0x2c and calls0x3127a0. That exact helper scans array0x13c/count0x140, uses28-byte stride, compares requested integer with stored key at record+0, writes the first matching physical index through output pointer. Getter copies MainText at+4 and HelpText at+16. Native loader0x30ac40 binds path0x4b7990 to ..\UIText\00001240.tui, reads keys and256-byte text halves into the same layout. This binds the field-file and native-member chain without inferred UProperty offsets.

Verified offline:120 fixtures execute the actual original lookup words, covering sparse/unsorted keys, duplicate first match, empty table and absent keys. Generic scalar execution adds checked SLL and memory-bounded SW, with regression tests. Reparsed251 getter calls and177 selected whole-function objects yield144 literal FieldTextData calls and12 nonliteral arguments. All144 literal keys differ from physical source ordinals; source archive/value hashes and geometry are checked independently. GetNationName(238) is source record key238, not ordinal238. Dynamic arguments remain unbound; presence or lack of literal calls is not reachability proof.

Verified static: helper0x1a54c0 is exactly JR ra followed by MOVE v0,a0 in its delay slot. The field loader and the previously audited Store/Divination/Gym loaders call the same helper, so this buffer conversion is identity, not a guessed encoding conversion. Full allocation/game execution and unrelated property initialization remain unverified. Current source-only audit changes no resource targets or final ISO.


## Configuration encoding and cache resizing (stage147)

Verified: 372 selected ASCII-source .int/.ini values were individually reviewed and copied with byte/hash/line/section/key binding. Seventeen preference descriptors expose quoted Caption/Parent labels while Class, Category, flags and punctuation remain machine data. Parent rewrites require an exact source caption/scalar label in the same batch; undefined Networking remains unchanged. Printf/opaque Engine macros %o/%k/%w, accelerators, literal newline escapes, paths, delimiters and wrappers retain exact token order. These checks preserve opaque syntax, not a claimed interpretation of death macros or PS2 reachability of editor/setup fields.

`MappedEncoder.encode_characters` separates explicit glyph encoding from consumer grammar validation. Default `encode` still runs the unchanged dialogue protected-token gate, including rejecting %w there. Configuration uses the primitive only after its format-specific source-bound validation and rejects NUL/CR/LF encoded bytes. The original ASCII source parser remains strict; a byte-valued configuration-line parser independently checks rebuilt identity and untargeted values.

Verified: original startup bundle contains one whole Core.int body and two matching padded128-name/u32-size records; one whole psx2game.ini body and three matching size records. Source-bound profiles record these counts and hashes. Whole-file overlays relocate unchanged intervals and update only the verified size words, allowing value-length changes. This is distinct from equal-size SHIP resource mirrors. Native/runtime interpretation of those records and selected configuration reachability remains unverified. Independent extraction confirms all372 values, two cached bodies/five new size words and no old whole bodies; 13434 SHIP targets/358 held original fields, original AFS TOC/order, two actual fonts and20 total cache mirrors also pass.


## Research status: KR_SMALL_CHARSET_STATIC_VERIFIED

截至2026-10-08：仅韩版输入；33字小字集PoC完成静态验证，旧单字版截图确认UI显示“测”，不是完整中文补丁。研究见 [第一阶段报告](docs/PHASE1_RESEARCH.md)，新版本验收边界见 [小字集QA](docs/QA_TEXT_POC.md)。

### Evidence vocabulary
- Verified：直接代码/字节/静态实验或明确截图观察；必须说明具体证据，局部截图不意味着完整运行时验收。
- High-confidence deduction：有多项证据，仍需 runtime trace。
- Unverified hypothesis：没有直接实测支持。
- Upstream-reported：来自 soyjxck 的旧实验，不作为本次独立确认。

## Input identity (Verified)
SCKA-20043 / NTSC / SYSTEM.CNF VER 1.00。
ISO size 3210412032 B。
SHA-256 `6242476a66a96110fb6ee1a1dd668eedd70d3df6c835f0de9192451b5f4fcd45`。
SHIP 13862 entries / FILE 53 / LINEAR 4099。
原版 ISO 只读、原位；游戏字节输出均放 ignored work/build。

## Attribution and actual implementation
soyjxck upstream audit commit `0e8de85bffbbd392fb43ef7608df097a0fb829b6`。
AFS/ISO/FPB/SFD沿用上游生产实现；Git历史保留，研究和PoC提交已推送origin/main，技术里程碑标签为glyph-poc-01。
上游 manifest/voice-graph/SFD 研究属于上游贡献。
库版本与重现命令见 BUILDING.md。

## Encoding and rendering

韩版ELF只读审计确认没有有效符号条目；native相关23个标识、13个有限地址构造候选和9个数据pointer词已定位。00001240路径候选邻域有两个256立即数，仅作双区段读取线索，尚未确认parser/字体查表函数。地址、输入hash和证据类型见 [native研究](docs/NATIVE_RESEARCH.md)。
实现层 USA latin-1，KR cp949，JP shift_jis。后两版差异仅代码/上游证据；无 USA/JP ISO。
707 可解析韩版 FPB 池中 695 严格 CP949 成功，12 失败（疑似残留日文）；不采用 errors=replace 隐藏问题。
主韩文字体含 KS X 1001 韩文范围，不能等同完整 UHC/GBK/Unicode 支持。
ELF 中 UFontObj/Canvas/UnicodeStringConst 名称为追踪线索；native 解码/宽度/换行尚未定位验证。

## Font system (Verified bytes)

字体容量/冲突离线审计确认2350个候选韩文槽，695个严格解码FPB池使用1064个槽；1286个未在该语料观察到，不能当全游戏空闲槽。当前33字map中16槽仍与目标窗口之外原文重合5140次、涉及615个FPB资源。两字体2350槽bitmap均非全零。范围、计数和证据边界见 [字体容量审计](docs/FONT_CAPACITY.md)。
FILE/MrtsEngine.u (UE2 v118) Font exports 735 NormalFont、736 KatakanaFont、739 NumberFont。
Normal: offset 129483, size 282852, 2667 glyphs, 19x21, row stride 5, bitmap 280035 B。
Katakana: offset 412335, size 242847, 2667 glyphs, 19x18, row stride 5, bitmap 240030 B。
bitmap 2bpp，LSB-first 四像素/byte；字形人工查看可读。
后跟 2667 B width 候选数组、27 u16 range keys、27 u16 base indices；尾部语义未知。
同样 serial 精确出现在 celfid bundle offset 1212059 / 1494911，必须考虑双副本加载。
NumberFont 是另一路 stock-style 数据；temple.utx 38 exports 无 Font，不能把它当主中文字库。
静态位图位置与数组长度 Verified；运行时映射公式/advance/atlas cache/kerning/baseline 均未验收。

## AFS / ISO
SHIP 和 LINEAR 的 slot 0 CRLF size manifest 必须与替换资源同步；filename TOC 和 16 B metadata 保序。
原始 SHIP UE2 stub 的 manifest size 是真实外部 package 大小，不是 4 B stub 长度，勿据此报损坏。
FILE 也有 AFSFileIndex.idx：上游 rebuild_afs 对 celfid 重压缩后保留旧 manifest；本次复现 TOC 1102180 vs manifest 1239770。
PoC复用上游rebuild_afs并定点同步FILE slot0；SHIP保留外部stub记录，不全表改成TOC size。runtime后果仍待确认。
ISO原地缩小/relocation合成测试通过；新增pycdlib只读metadata fallback，仍复用上游写入逻辑。
目前不存在ELF patch、生产中文encoding backend或完整中文翻译构建。

## Text and linked resources

TUI schema3只读审计确认两个256 B区段的全量字节布局，892非空区段CP949严格往返；段用途仍为待验证。通用fixed-slot函数的显式256 B合成测试已确认另一半/metadata保留和NUL溢出门禁，未对原版写回。旧PoC profile及ISO保留；详见 [TUI字段](docs/TUI_FIELDS.md)。

全部16个KR TUI记录几何已核对，共863项；834字段满足严格CP949和clean NUL padding，29项存在非零尾部。10个资源有一个完整celfid副本。限定FPB+TUI语料使用1084槽，当前map冲突17槽/5406次/629资源；不作为全游戏空闲或运行时证明。见 [TUI审计](docs/TUI_AUDIT.md)。

全量KR FPB离线审计：707个解析资源无编辑回写一致；701个符合当前连续partition条件，667个同时符合严格解码与控制结构前置条件。六个显式seq0资源存在合成views未覆盖的前缀，不能通过简单串接丢弃。详见 [FPB审计](docs/FPB_AUDIT.md)；仅静态证据，不改变运行时验收状态。
FPB 真正字段 `(seq, offset, length)`，header+0x0C 是 implicit seq0 length。
707 韩版 FPB 无编辑 parse/build byte-identical；8 B stub 单独跳过。
Slot constants 是 USA 分段模型；韩版仍需定位实际 record/metadata/text 边界。
Region extractor 仅 ASCII heuristic，不能直接扫描韩文作为全部可见文本。
Celfid 英文 slot detector/linked substring grouping 不是完整 UE2 identity parser；显示名和内部 key 不自动同译。
联动涉及 celfid/SHIP/LINEAR 纹理可能重叠，优先级和实际依赖须逐屏 trace。

## Recommended route (High-confidence deduction)
B：韩版 ELF/FILE/场景/音频保持完整，自定义 Unicode->韩版 byte-pair->glyph 稳定映射；先小量置换，不扩容。
C：复用上游结构 parser、压缩、AFS/ISO/SFD 和未来 references，不把目标放进 en。
A（USA runtime 扩中文）当前没有 binary comparison 输入，且修改面大，非首选。
2350 Hangul 槽的最终容量是否够用需完整字集统计；扩容是后续独立课题。

## Tests and stopping point
46 tests passed；707 FPB byte-identical roundtrips；SFD单片重建/ADX一致，但时长差0.103944 s与DTS warnings未消除。
截图确认UI单字显示；完整mapping、width/wrap、存档/切场景仍pending。详见docs/KNOWN_ISSUES.md。
只进行小字集实验，不进入全文翻译。

## Single-glyph PoC (Verified static; limited UI screenshot observation)
tools/font_poc.py使用locales/zh-CN/poc.json。B0A1/原“가”/候选glyph317置换为“测”，并非CP949直接编码中文。
两Font只改glyph317 bitmap；serial长度、其余glyph、全部metrics/range/base/tail保持原字节。
MrtsEngine.u及celfid内两font精确副本同步；压缩复用上游24576 B chunks/zlib9。
00001944.fpb seq0/seq2首个双字节字符写B0A1，530 B长度、windows、$n及其它tokens保持。
共享槽使其它原“가”也显示“测”：这是实验副作用，非正式译文；不修改resource IDs。
FILE.AFS 21716992→21579776 B；SHIP仍45686784 B；ISO仍3210412032 B。
重解析验证AFS顺序/metadata、无关entry、两font副本、manifest与FPB；全ISO对照只允许两AFS extent及FILE目录length字段变化。
ELF/LINEAR/MUSIC/SFD原字节保持。静态字形可读不等于runtime解码/advance/wrap/save通过。
实验环境PCSX2 exe版本metadata2.8.2.0；读档UI截图，四处空槽提示显示“测”。截图Vulkan/640×447（1x）；BIOS、实际载入ISO hash、冷启动流程与版本没有出现在图内。
该观察支持B0A1/index317候选映射路径（High-confidence deduction），没有证明两font加载优先级或所有双字节范围。

## Small charset PoC (Verified static; runtime unverified)
游戏profile与locale数据分离；33字符明确分配B0A1..B0C1/glyph317..349，每项对照两font的range/base。该范围全体运行时lookup尚未实测。
两font selected bitmap与advance候选byte统一19，其余字节不变；按共同参考baseline定位标点，不逐字垂直居中。
00001944.fpb seq0由20→30 B、seq2由80→118 B；seq2仍保留一个$n。隐式长度、显式offset/length与总池重建，530→578 B。
韩版00001240.tui实测125396 B=8+243*516；header第二u32为2，语义未知。243个record IDs唯一；每项u32 id+512 B字段。
record index127/id176位于65540，文本65544，原串18 B且余槽零填充；对应读档空提示的语义为高置信推断。
该完整tui在celfid解压buffer中唯一出现于3929716，不能仅替换SHIP文本；本次同步整个同长资源副本。
FILE/SHIP slot0只更新目标size、保留外部stub size；AFS条目顺序和metadata不变。ISO仅FILE/SHIP extent及FILE目录size字段改变。
当前文本层保护控制token数量/顺序/值并拒绝未知结构；已有46项自动测试。完整UI长度/自动wrap、linked names、字库扩容与存档仍待验收。

## ELF局部调用参数（Verified static / semantics pending）

00001240候选的JALR `0x30AD88`与`0x30AE1C`，delay slot分别将a2设为256；a0为局部r20、a1为sp+0x60，间接目标形状为`load32(load32(r20)+0x14)`。相邻`0x30AD70`的a2为4，与id/双256 B资源几何一致。参数状态已由有限指令推演验证；读取语义、vtable目标和实际执行未验证。schema2报告276条窗口内调用候选，116项合成/工程测试通过。见 [native研究](docs/NATIVE_RESEARCH.md)。

## GP初始化与reader包装层候选（2026-10-09）

Verified static：`.reginfo`声明GP=0x5437F0；TUI相关gp-32200槽VA0x53BA28，文件初值指向memory-only区域且存在SW覆盖候选，不能据初值解析运行时vtable。候选0x4FE270的+0x0C值为0x1E4A10；其条件性分配路径使用Linear标识并写入表0x4FE390，该表+0x14值为0x1E59E0，邻域具有底层转发和对象+0x44累计形状。包装层解释为High-confidence deduction；实际分支、底层reader和运行时状态未验证。schema3与131项测试见 [native研究](docs/NATIVE_RESEARCH.md)。

## 字符→glyph片段（2026-10-09，Verified offline model）

VA0x20EE80的212 B版本锁定片段含双字节组合与动态范围查表。合成对象字段+0x4C/+0x74/+0x80/+0x84分别控制分支、range pointer、base pointer与条目数。原两Font各2411个双字节成员、128个ASCII、29个fallback边界以及33个PoC映射均通过；94个合成扩展编码能返回2667–2760，但真实Font数量、bitmap和metric未扩展。字节表模型为Verified offline；实际Font实例、缓存容量、宽度与换行仍待验证。见 [查表模型](docs/GLYPH_LOOKUP.md)。

## Font metric消费者（2026-10-09）

Verified static：0x272734按Font候选+0x4C选择传统page与双字节路径；非零路径使用16位glyph index从+0x68单字节数组读取。Verified offline model：原两Font各2667项metric逐项读取通过，范围0–19；模型拒绝越界不等于引擎具有检查。+0x68/+0x74/+0x80加载调用参数相容但真实对象布局仍待验证。High-confidence deduction：metric参与宽度累加。详见 [metric研究](docs/FONT_METRICS.md)。

## FontObj bitmap/cache候选（2026-10-09）

Verified static：0x333A4C查表后保留16位glyph，0x333C30邻域从Font候选+0x60取源bitmap；page邻域有65比较和动态pointer/count/capacity分配。Verified offline projection：五条标量操作对1024组输入产生0/60/120/180，原两Font完整19列投影一致。High-confidence deduction：+0x54/+0x5C为height/stride，page采用64边界；实际format selector、texture/cache容量与运行路径仍未验证。见 [bitmap研究](docs/FONT_BITMAP.md)。

## 真实Font资源追加（2026-10-09，Verified static）

两Font2667→2700 glyph，真实新增bitmap/metrics与D0A1–D0C1表；原glyph、metric、geometry及未知tail保持。原指令查表模型核对每Font2411个原双字节成员、128个ASCII和33个新增编码。未知runtime容量不作已验证上限；下一步UE2 export重定位与celfid增长副本同步，随后新增槽ISO验收。见 [扩容实验](docs/FONT_EXPANSION.md)。

## 小字集PoC运行时观察（2026-10-09）

Verified screenshot observation：短UI中的中文、句号和ASCII可读；实时开场场景的标点混排样本与长句折行可见。Reported observation：长句末尾在下一页显示，未附该页截图；不作为丢字/裁切故障记录。High-confidence deduction：截图内容与text-poc-02三个目标相容，但没有载入ISO的独立hash证据。存读档、切场景及新增槽字库运行时容量仍未验证；分页不替代场景切换，实时场景字幕不替代SFD验证。详见 [证据记录](docs/QA_TEXT_POC.md)。

## 增长Font的UE2 export接入（2026-10-09，Verified static）

原MrtsEngine.u为version118/licensee15、flags1，共7668个export。新增append-only包builder，仅改变header @24表偏移，追加两Font和新表；size/offset采用compact index，目标entry身份前缀保持。原包数据区、name/import及7666个无关export保持。2058129→2713665 B，真实包回读及干净源码复现通过；runtime/celfid/ISO尚未验证。celfid解压buffer不存在完整原engine副本，整包替换路线不适用。详见 [包级接入](docs/FONT_PACKAGE.md)。

## celfid增长片段与混合镜像失败（2026-10-09）

Verified static：celfid包含唯一engine header、export table、两Font serial与两条132 B文件路径/大小记录；六段同步及其他区间保持通过，4195112→4201631 B。完整缓存语义仍未验证。AFS集成FILE增长到22239232 B，触发上游ISO relocation；真实混合ISO/UDF回读报缺少anchor。原尾部anchor不再位于新末尾，UDF File.afs引用还指向旧区域，单补anchor不足。新增预检在ISO写入前阻止UDF size变化；242项测试不代表UDF修复或runtime扩容完成。见 [缓存证据与失败记录](docs/FONT_BUNDLE.md)。

## 韩版混合ISO/UDF同步（2026-10-09，Verified static）

保留上游ISO9660 patcher，新增单物理partition/Type1 map/标准File Entry/单short AD的防御性overlay。FILE.AFS增长重定位后同步UDF info length、recorded blocks和AD；主备partition与integrity size table增长，新anchor追加到镜像末尾而非覆盖文件，tag location/CRC16/checksum和ISO PVD同步。未知descriptor fields、时间与扩展属性保持，原源bytes/两视图extent先验证；不套用固定韩版offset到未知布局。
真实候选3232653312 B，ISO与UDF读回两AFS一致，全原区域未修改bytes通过；源ISO/ELF不改。运行时cache/显示未验收。字段、hash与测试见 [新增槽PoC](docs/QA_EXPANDED_POC.md)。

## 不依赖构建报告的PoC二次推导（2026-10-09）

Verified static：原ISO+匹配字体+显式locale独立推导Font/UE2/celfid/FPB/UI/AFS，比较候选全部archive bytes及ISO9660/UDF metadata和原区域未修改bytes；不读取DIFF_FILE或中间资源报告。一键编排复用既有阶段，干净源码复现相同ISOhash，隔离ELF单byte tamper被拒绝。UDF主备空空间管理引用已实际确认并加入门禁，非零引用不放行。
验证复用同一基础parser/writer，不能排除共同实现缺陷；284项测试不替代运行时验收。见 [构建与验证链](docs/POC_PIPELINE.md)。

## 2026-10-09 名称首字段与缓存

原00000460.cha为301×299 B记录加12 B header，在celfid完整唯一副本起点3220278。5条相同姓名首字段的容量/trailer和受控同步实验已核验；相同字节命中不等于运行时linked group，见 [名称资源实验](docs/NAME_SLOTS.md)。新增槽四图支持局部显示，完整运行时门禁仍保留。

## 2026-10-09 单slot名称接入

显式name_slot_overlays采用原资源hash及完整匹配库存门禁，仅按targets子集修改，复用slot_resource中的上游slot包装。slot0和新增Font缓存同步已接入AFS/ISO/UDF；旧三字段镜像在新工具下同hash验证通过。名称语义/运行时仍未验证，见 [候选身份](docs/QA_NAME_POC.md)。

## 姓名字段的局部运行观察（2026-10-09）

单独修改CHA slot0及缓存副本的候选在编成、道具和角色详情页均显示“测试中文”。截图中的显示为Verified observation；资源到菜单的关联为High-confidence deduction，不能区分SHIP与缓存加载优先级，不证明其他四个同名slot用途或lookup安全性。详见 [姓名QA](docs/QA_NAME_POC.md)。

## 多编码段与有界显示资源（2026-10-09）

font_resource新增append_slots/verify_slots，将字形追加拆成非零trail-byte区段，各段含独立sentinel/base。317字库存使用D0/D1/D2三组94字符和D3组35字符；两Font2984 glyph，原2667 glyph与原映射保持。多段字库的完整原映射及317个新增码离线模型通过；最大游戏缓存容量仍未验证。

display_resources按显式资源hash/窗口hash应用既有rewrite_fpb和rewrite_fixed_slot，固定字段限TUI首256 B。cached_copies必须显式为0/1并与原buffer匹配；若有完整副本则同步，不修改substring或推定linked group。AFS/ISO/SFD工具未重写。见 [有界试译QA](docs/QA_OPENING_TRIAL.md)。

## 全量目录和外部字体参数（2026-10-09）

Verified static：19类SHIP资源998文件导出15635字段/候选，FPB窗口7998、TUI两字段1726；解码失败及未知token隔离，candidate不等于display text。celfid完整镜像21资源，独立候选35048，不推断linked group。数量及覆盖缺口见 [文本目录](docs/TEXT_CATALOG.md)。

Source Han Sans SC Regular 2.005R替换新增glyph输入，NormalFont 19px/KatakanaFont 15px，原字形及字宽保持，317追加映射不变；共同baseline裁切门禁保持。五阶段/独立回读通过，运行外观待验收，见 [字体对照](docs/SOURCE_HAN_FONT.md)。

## 混入日文的局部源解码（Verified static，2026-10-09）

00005420/00005421.fpb 共 31 个 CP949 严格解码字段实际呈现日文乱码。完整 pool 切片 SHA-256 与字段 source_sha256 相同；CP932 严格解码与重新编码逐字节往返成功。此结果属于源字段解释，不是游戏解码器改造结论。原 catalog 不改写，译文通过相同 ID/hash 关联，局部编码清单见 `locales/zh-CN/source-interpretations.json`；补充校对文件见 [文本目录](docs/TEXT_CATALOG.md)。其他资源的 CP932 解释、CP949 失败字段、引擎运行编码仍逐项待核对。

## 集中提取覆盖证据

只读审计工具 audit_extraction_coverage.py 复用上游 AFS reader 与现有 extract_resource；ISO 三个 AFS 流式 hash 对照后，998 个已支持资源重提取与原 catalog 完全一致。库目录一致性不等于语义覆盖，候选、包、ELF、SFD 和图片文字仍分层审计。具体数量与门禁见 docs/EXTRACTION_COVERAGE.md。

## slot 候选字段外字节（Verified static）

3,162 个候选按主字段有效字节并集分类：2,302 完全同区间、222 完全覆盖、527 字段外、111 部分重叠。638 个未覆盖片段均位于当前上游 slot profile 的 observed-trailer；抽查 FDS／GFT／ODD 存在完整韩文句子，leading-only 导出不能代表该区间全部内容。韩版字段结构、显示用途仍待确认；不改变 writer 或启用盲写。详见 docs/EXTRACTION_COVERAGE.md。

## 韩版多字段记录（Verified static）

FDS 两文件为 8 B 头及 2052 B 记录，四个 512 B 字段；GFT 两文件分别为 822／10307 B 记录、11 个字段；ODD 正文为 560 B 记录、80／240／200 B 三字段，小变体保留 20 B 元数据。六文件集中补充导出 1168 字段，旧 689 个扫描候选全部被新字段覆盖。只读补充层不替换上游 USA parser/writer，不扩大翻译或导入；详细边界与证据见 docs/RECORD_FIELDS.md。

## 只读 source-corpus 修订层

六资源的新结构字段按完整资源hash替代活动视图，旧资源metadata/entries保留superseded层。alias要求资源、offset、length、字段SHA256完全相同；相同文字、不同位置或部分重叠不自动关联。6334既有初稿ID/hash保持；CP949解码可含日文，不能凭语义改成CP932。机器聚合见 docs/SOURCE_CORPUS.json，流程见 docs/SOURCE_CORPUS.md。

## 全容器载荷核查

Verified static：三个本地归档逐项读取18,014项；4,058项包表接受、12项分帧差异保留。LINEAR嵌入包的声明offset不是解压流实际offset；顺序表读取与serial解码分开，详见 [容器核查](docs/CONTAINER_PAYLOADS.md)。全文覆盖尚未完成。

## 全盘与音视频流库存

Verified static：62个ISO文件全部hash；MUSIC 3646项逐项读取，3645项ADX头、1项manifest。46个SFD完整输入ffprobe packet核查均exit0，46视频流／45音频流；不等于字幕／图片字覆盖完成。详见 [全盘核查](docs/DISC_PAYLOADS.md)。

## FPB pool 补集

Verified static：708项FPB逐项身份核对，707普通pool共433271 B；原字段并集之外6个前缀共802 B全部导出，未伪造seq0。8 B零FPB与三个[0,9]空ECD单独记录，详见 [补集核查](docs/FPB_POOL_GAPS.md)。

## SFD 原版画面抽样

46 个原版影片完整解码为 47 张接触表并逐表审查，8 秒抽样中 25 个影片观察到文字。新增确认韩文序章／尾声、韩文及日文制作名单；现有两地区 ASS 共 510 条是上游参照行，不等于韩文原文提取。抽样间隙、完整转写及语音内容仍待核查，全文覆盖门禁保持关闭。详情见 `docs/MOVIE_TEXT_AUDIT.md`。


### ELF 完整字节候选扫描

详见 `docs/ELF_TEXT_AUDIT.md`。192,781 条跨编码候选及地址数值命中不等于游戏文本；机器代码也能严格解码。ELF 文本语义覆盖尚未闭合，完整提取门禁保持关闭。


### 普通 UE2 包脚本全文参考

详见 `docs/SCRIPT_TEXT_AUDIT.md`。568 个普通包 TextBuffer 完整正文与 2,993 条双引号候选已定位；源码与运行时显示仍需区分。宽字符中的 CP949 打包阅读视图不替换原文，流式 serial 与编译字节码覆盖尚未闭合。


### 脚本源字面量与编译 serial 关联

详见 `docs/SCRIPT_LITERAL_LINKS.md`。5 条宽 code unit 派生标签在同 owner Function serial 命中 CP949 字节；字节存在已确认，指令边界、执行可达性与菜单可见性尚未确认。短字符串精确匹配也可能命中其他数据或后缀，不能据命中次数计算翻译量。


### LINEAR 未解释尾部与有效前缀

详见 `docs/STREAM_TAIL_AUDIT.md`。全部 4,098 项 manifest/TOC 尺寸一致；12 个尾部疑问仍未解决，有效前缀追加 57 次包表及 87 次 Texture export。部分载荷仍保持未闭合状态，不截尾或扩大可重建保证。


### celfid 候选字节上下文

详见 `docs/BUNDLE_CONTEXT_AUDIT.md`。35,048 条候选全部校验片段身份；2,595 条位于完整 SHIP 镜像，16,767 条位于流式包表，15,686 条仍处于其他载荷。分类不推断可见文本或 linked group。


### 普通 UE2 实例属性

10 个普通包 30,813 个实例属性块、634 个 tag、22 个执行栈静态核查，零属性解析疑问；568 个 Class 与 30,788 个 native 尾部尚未解析。详见 `docs/OBJECT_PROPERTY_AUDIT.md`。


### Class 默认属性

568 个 Class 中 555 个零脚本类默认属性精确闭合，1473 tag／119 Str；13 个非零脚本类默认属性仍待核查。详见 `docs/CLASS_DEFAULT_AUDIT.md`。


### 普通 Class 默认属性闭合

13 个复制脚本边界已核查，全部 568 个 Class 默认属性读取至精确 serial 末尾；1634 tag／132 Str。通用 Function 字节码与流式正文仍未闭合。详见 `docs/REPLICATION_DEFAULT_AUDIT.md`。


### 活跃源异常字节核查

活跃 CP949 失败为 165，而非旧视图 236；12 个完整 FPB pool 和 38 个 CHT 字段存在严格 CP932 往返阅读，另 8 个 FPB 窗口切断 CP949 字符。替代阅读不改 canonical 编码或导入许可。详见 [异常字节核查](docs/DECODE_QUARANTINE_AUDIT.md)。


### CHA／MDG 怪字候选闭合

实际 8 B 头与完整记录布局核对 346 记录／391 文本字段；381 候选中 375 正文、6 数值区，零未覆盖候选。6 个怪字不属于新增正文；具体 u32 用途未完成。详见 [记录核查](docs/NAME_RECORD_AUDIT.md)。


### 固定 region 正文遗漏补核查

44 个 ITM／ABI／SGI／NOD／DOD 文件的完整记录补导出 2360 字段，其中 498 非空字段缺少旧完整视图（488 无旧正文 byte overlap）。NUL 启发式会吞入前邻非零数值并漏提后续正文；新旧字段尚待统一集合合并，不重复计数或开始新增翻译。详见 [完整 region 字段](docs/REGION_RECORD_AUDIT.md)。


### POD 全区块字段核查

148 POD 的 24 槽布局共 3552 字段（333 非空），补出 2 个 CP932 日文槽和 1 个问号槽。40 B metadata 的具体用途仍未验证；首 u32=31 不套用其他格式 count。详见 [POD 核查](docs/DIALOGUE_BLOCK_AUDIT.md)。


### 统一源集合更新

已核查布局重组为 998 资源／19137 字段（14628 非空），6334 草稿全部保留精确关联；167 CP949 失败／101 控制结构隔离。旧 15121 字段为前一版集合，非全游戏无遗漏结论。详见 [统一集合](docs/AUDITED_CORPUS.md)。


### 未知控制结构完整观察

当前 101 个隔离字段全部遍历，共 225 个标记／控制字符观察；149 次尖括号内部文字与 ITM 名称精确关联。运行语义未确认，validator 保持不变，不移除标记或批量放行。详见 [控制观察](docs/CONTROL_OBSERVATION_AUDIT.md)。


### 普通 Texture 载荷核查

28 Texture／27 Palette／191 mip 全部结构闭合；28 首级图已检查，Editor Bad 含 `BAD SIZE`，NumberFont 为 glyph atlas。163 小 mip 已完成原尺寸逐图检查（见 SMALLER_MIP_AUDIT.md），流式 Texture 未覆盖；全文门禁不变。详见 [普通纹理核查](docs/TEXTURE_MIP_AUDIT.md)。


### 普通编译脚本完整结构核查

8032 个 Function／NativeFunction／State／Struct 全部 serial 闭合，1207 个字符串常量、5 个含韩文、0 解码失败；运行可见性与流式脚本未完成。详见 [编译脚本核查](docs/COMPILED_SCRIPT_AUDIT.md)。


### FPB 池余段纳入统一源引用

当前统一集合为 998 资源／19143 字段（14634 非空），6 段／802 B 非索引池余段已保留，6334 初稿关联不变。167 活跃解码失败重新核验；非索引片段不伪造 sequence ID 或导入。详见 [池余段统一集合](docs/POOL_REFERENCE_CORPUS.md)。


### 普通包全部 mip 视觉核查

163 个非首级 mip 经 7 张原尺寸 contact sheet 全部检查；普通包 191 mip 视觉覆盖闭合，未观察到新增独立短语候选。流式 Texture／SFD 仍未覆盖，全文门禁不变。详见 [小 mip 核查](docs/SMALLER_MIP_AUDIT.md)。


### 普通编译字符串上下文核查

1207 字符串的祖先表达式及调用符号已完整核对；1025 有调用祖先，474 有赋值祖先，133 显示符号候选保留只读。英文 UI 候选不能因韩版来源排除；运行可见性与动态文本流未证明。详见 [字符串上下文](docs/LITERAL_CONTEXT_AUDIT.md)。


### celfid 流式字段前缀对照

Core.u 表后连续 2229 B 与普通包的 144 个源片段逐字节对应，观察到 Children／Next 参数链及 Struct 依赖内嵌。RandRange 脚本首次差异处严格停止，根 Object 和完整流未闭合；不能按 declared_size 连续切片或删重复 opcode。详见 [流式前缀](docs/STREAM_FIELD_PREFIX.md)。


### Core Object 依赖树对照

源包 oracle 对应连续 27922 B／1715 个字段对象自身片段；27898 B 原字节相同，24 B RandRange 差异脚本保留 opaque。局部根树闭合不代表跨包或全流覆盖，默认严格模式仍在差异处停止。详见 [依赖树对照](docs/STREAM_DEPENDENCY_ORACLE.md)。

### celfid 跨包 Class header 全量对照

568 个普通 Class header 全部核查，534 个唯一精确锚点、34 个无相同 header；6 包完整表元数据一致。Core 根树后首先对应 Engine Material，而非 Actor/Pawn。锚点不等于 serial 边界或全文覆盖，门禁保持 false。详见 [Class header 对照](docs/STREAM_CLASS_HEADER_AUDIT.md)。

### celfid 编译脚本前缀全量有界对照

8032 个普通脚本定义全部重读；7983 个有 header 对应的定义、7987 个候选均符合限定重复模型，49 个 header 无匹配。4 个多位置定义与 1501 个内部路径歧义保留；1193 个既有常量位于符合模型的源定义中。后验拟合不是独立解码或 VM 等价证明，门禁仍为 false。详见 [脚本有界对照](docs/STREAM_SCRIPT_CORRESPONDENCE.md)。


### celfid 跨包依赖连续对照

源包 oracle 在 Core 根树后连续对应 224167 B／5248 个新增对象片段集合；INI 与 SmallFont 精确匹配，两个 Texture 完成限定 mip 顺序投影。负引用按完整外层身份解析，487115 的多义 Palette 候选未放行。后验对照不等于独立流解析或全文覆盖，门禁保持 false。详见 [跨包连续对照](docs/STREAM_CROSS_PACKAGE_ORACLE.md)。


### celfid 原生字节等价候选扩展

显式模式保留全部同字节身份，连续诊断 2938500 B／532 次 Class 根请求；7 个身份歧义和 2 个 parsed-table-only 区段未伪装为完整资源映射。下一处原生数据在 3201448 停止，全文门禁仍为 false。详见 [原生字节等价对照](docs/STREAM_NATIVE_EQUIVALENCE.md)。


### 普通包本地 Class 纹理覆盖修正

旧纹理计数只覆盖 import-class 子集。本地正 Class 引用补核后，总计 37 Texture／35 Palette／212 mip；新增 9 个 Engine 纹理的 21 个 mip 全部检查，其中 3 个 Latin／符号图集、无新增整句候选。全文门禁保持 false。详见 [本地 Class 纹理审计](docs/LOCAL_CLASS_TEXTURE_AUDIT.md)。


### celfid 全候选字节上下文复核

35048 个启发式候选全部复核字节身份，38499 个区段索引提供只读上下文；1233 个仍为未闭合字节上下文。候选命中不等于可见正文，所有语义判定继续 pending，全文门禁保持 false。详见 [全候选上下文核查](docs/STREAM_CANDIDATE_CONTEXTS.md)。


### FILE 配置及国际化值补充核查

全部 29 个 .ini／.int 导出 1008 个值（918 非空、90 空），ASCII 严格读取且全部行字节闭合；Core.int 原正文位于 celfid 末尾。配置标识与可见提示尚待区分，补充清单不等于 1008 个可翻译正文，主 corpus 暂保持不变。详见 [配置条目审计](docs/CONFIG_ENTRY_AUDIT.md)。


### celfid wrapper 与配置镜像上下文补核

9 包及 3 配置正文的双 132 B wrapper 全部逐字节核查，首部 2 文件记录与源文件大小对应。35048 候选中的未知字节上下文降至 972，仍不是可见语义闭合；原包声明 size 不可直接作为流式 serial 长度。详见 [wrapper 补核](docs/STREAM_WRAPPER_CONTEXTS.md)。


### 配置值统一源快照补全

29 个配置资源／1008 个值并入只读快照后，结构化统计为 1027 个资源／20151 个字段（15552 非空、4599 空）；原资源、候选及 6334 条译稿链接不变。新增字段保持 und／pending／不可导入；该数量不是全文最终可翻译数量，全文门禁仍为 false。详见 [配置值快照](docs/CONFIG_CORPUS_CONSOLIDATION.md)。


### celfid 尾部资源链补核

37 个单 132 B wrapper 与 SHIP 正文连续闭合 966382 B；780 个候选补充明确字节上下文，未闭合数降至 192。单记录资源 wrapper 与双记录包 wrapper 必须区分；字节镜像不代表可见正文或可编辑许可。详见 [资源链核查](docs/STREAM_RESOURCE_CHAIN.md)。


### celfid 原生尾部纹理补核

新增一个有界 P8 纹理／Palette 与 4 mip 全部检查；8×64 等细长 mip 先读 dimensions，再读 pixel count，不能沿用此前宽高同时不超过 8 的观察作为全局规则。图像未发现完整正文，StaticMesh 与全文门禁仍未闭合。详见 [尾部纹理核查](docs/STREAM_TEXTURE_TAIL.md)。


### SFD 全帧解码补核

46 个影片全量解码 72696 帧，全部输入 hash／退出码通过，error 日志为空；实际视频时轴合计 2425.6232 秒。逐帧 hash 不等于逐帧文字转写，抽样视觉结论未升级，全文门禁仍为 false。详见 [全帧解码核查](docs/MOVIE_FULL_DECODE.md)。


### 集中提取语义补核

配置1008项全分类、普通编译1207常量上下文分类、CLS/ATT/VAL的839记录完整word几何及尾部398 B地图属性均已补核；153个celfid候选上下文仍未闭合。原文与6334条译稿链接不变，完整覆盖门禁仍为false。详见 [语义补核](docs/COVERAGE_SEMANTIC_REVIEW.md)。

## 流式网格 DMA／VIF 上下文

见 `docs/STREAM_VIF_REVIEW.md`。13个包、320条命令及65个UNPACK输入段有界闭合，145个候选上下文补齐；剩余地图native候选8个。完整网格schema与运行时执行尚未验证，全量覆盖门禁保持待核查。

## stage88 地图字符串／字段消费者

见 `docs/NATIVE_STRING_FIELD_REVIEW.md`。地图compact-string记录补齐两个候选，上下文未闭合8→6；8032编译对象重新解析，77项取得同函数字段消费者证据，未确认320→243。新角色仍为只读候选，完整native序列化、reaching-definition及运行显示尚未证明，覆盖门禁保持待核查。


## stage89 全帧文字候选与暂缓解码

见 [全帧 OCR 候选核查](docs/MOVIE_OCR_REVIEW.md)。167 个真实 strict CP949 失败字段保持原字节及其他编码证据并暂缓；首片 1635 帧匹配通过。全片 OCR 不等于人工原文转写，覆盖门禁保持未完成。

## stage90 解析器操作数

见 [解析器核查](docs/PARSER_OPERAND_REVIEW.md)。全部8032对象/1207常量重解析；15项补充有界解析器操作数候选，最新待确认228项。101个隔离字段与validator保持不变；coverage_review_complete=false。

## stage92 音频优先接续

见 [音频优先核查](docs/MOVIE_ASR_REVIEW.md)。全46影片库存：45音轨完成本地原语言候选转写，1片无音轨；283片段、174低置信度片段定点OCR队列，26个空白折叠源匹配不作exact去重。停止全帧OCR，批量清理有哈希清单；原资源/6334译稿不改。音频候选流程完成不等于全游戏覆盖完成，继续保留静默视觉文字与未知native语义。

## 全量测试准备阶段的有界写回

见 `docs/FULL_TEST_PREPARATION.md`。字幕回封装直接复用sfd-muxer，27个候选保留原ADX完整字节与解码帧数；不声明容器时轴或PS2播放器验收。固定字段写回绑定资源hash、完整slot/field hash、原offset/容量、source hash与控制符，只写独立副本；4个FPB命名字段复用已有重建器。当前844字段/13资源未接入缓存、AFS和ISO，不开放未知格式的盲写。

### 当前回填增量

十批2128字段通过当前4901glyph两Font映射写入227个独立资源副本，容量溢出0。CHT/ECD的完整segment指纹与leading可写范围分别验证；trailer不增加容量。Source-alias支持仅接受唯一别名，别名/规范ID碰撞作为重复拒绝，不改既有ID/hash/status。1126项单元测试通过，非缓存/AFS/ISO或运行验收。

## stage137 动态提示的金额与原生截取

原FILE对象重解析349条getter调用；原ELF描述符静态复制绑定四个截取方法，693组标量原指令离线执行验证双字节字符／字节截取差异。三条金额译文按调用顺序修订，列表初始化与成员最终绑定未闭合，不提升pending policy。详见 [动态消费者](docs/DYNAMIC_TEXT_CONSUMERS.md)。

2026-10-11 stage138：3个TUI原生loader逐原word核对，Core MrtsTextData三成员／四ArrayProperty内层及NextField链重解析。函数路径与record读入顺序静态已验证，运行期成员offset和转换完整语义未确认，不授权pending回填。见docs/DYNAMIC_TEXT_CONSUMERS.md。

## 原生FPB首记录核查（stage143）

**Verified（版本锁定静态证据）**：原ELF的`..\FPB\%08d.fpb`唯一地址配对指向加载函数0x3007c0。函数读取count后，循环count次读取key四字节及offset/length各四字节。因此+0x04/+0x08/+0x0c不是padding，而是第一个实际record；后续才是旧parser称为windows的record。目的数组为FieldData的+0x19c或+0x1a8，record stride16、字符串在+4。独立的完整qualified method注册复制链绑定GetPlayBookDataText→0x3424d0→0x342560；getter以10000分数组并对第二数组的key减10000，按key首个匹配返回，不按文件record序号索引。不是UIInfo.GetFieldTextData的TUI消费者。

实际SHIP扫描707个可解析FPB、1个8字节文件00001945.fpb仍不支持；19个header key非零，没有重复native key。六个原pool-gap对应真实首record：00004668 key13、00004669 key10、00004800 key11、00004994 key1、00005047 key2、00006436 key1。这些前缀不能继续归为无编号不可见padding；已有源hash/字节坐标保持，后续补译并增加明确header-record回填路径。其余13个非零首key已有legacy seq/0几何链接，旧ID是catalog alias而非native key，不能直接重命名或与显式0合并。

`tools/audit_native_method_registration.py`与`tools/audit_native_playbook.py`可从原ELF/SHIP/冻结corpus复核；指令原words和完整源hash是依据，Capstone对R5900 LQ/SQ的通用反汇编仅探索参考。证据在work/visible-text-143/native-playbook.json。未声称加载函数已在游戏执行、所有资源场景都可达、字符转换或画面排版通过。953资源候选AFS继续保留；此证据尚不自动改写六prefix或生成最终ISO。

## 原生首record补译与独立回填（stage144）

六个真实header record已在locales/zh-CN/header-dialogue-review-01.json按冻结source hash补译并逐句reviewed，native key13/10/11/1/2/1和pool-gap旧ID分别保留。江之英雄约书亚／救赎之光／光之树／格兰朱／马拉卡特／埃琉内德圣会／普诺森／莫莉沿用名词表。04800原Japanese汉字问号缺损按上下文解释，不声称恢复原字；原bytes严格CP949往返，CP932读取失败。$n顺序和数量保持、未知说话者不新增性别。

通用rewrite_fpb_header和tools/import_fpb_headers.py使用明确native key、首record源hash、原AFS/corpus/已回填copy hash及物理font mapping；仅替换header window，显式record keys/order/body字节、内部gap和tail不改，offset统一加delta，header length和pool size同步。拒绝key/hash/offset/overlap/bounds/control/empty mismatches。实际在stage141的六个正文已译副本上继续回填，header-copies2/headers.json权威；两次构建六输出byte-identical，新增目标无glyph缺口，现有两font已覆盖。11新tests、1471测试通过（baseline/rollback1460）。

此特殊header batch与24普通batch独立：普通13383 reviewed不变，新增6 reviewed→合计13389，实际普通回填13025+header6。冻结corpus中旧reference语义不改写，通过native绑定特殊header policy授权副本。下一步把六副本合并到当前953资源完整import receipt/AFS构建和独立验证，不能拿旧stage142AFS当已含六prefix的最终ISO。860普通缺口、358pending及其他scope/layout/movieintegration未闭合。

## 全资源副本与首record合并（stage145）

通用tools/merge_resource_imports.py验证原953副本及6header overlay的source/base/output hash、相同physical-font/map、当前翻译batch hash，重复/已应用overlay、delta不一致、正文越界或body/gap/tail改变均拒绝；更新普通field new_offset、member size和selected field计数，但header字段另列，绝不把native key伪装成旧seq/0。每个输出副本重新读取。

实际953资源／13031字段已完整整合候选FILE/SHIP AFS，包括6首record及18 whole缓存镜像；两font仍5086 glyph，原member顺序/TOC metadata、manifest sizes、compression roundtrip通过。独立从AFS再提取并核对13025普通目标+6header目标、358pending原bytes、2font及18cache。权威work/visible-text-145/integrated-afs/integration.json；旧142候选不再是最新。8新tests，1479通过（baseline/rollback1471）。860普通缺口和358pending角色等范围／换行溢出／已验收动画整合／最终ISO仍需完成，不称当前candidate为全量最终ISO。

## ABI剩余字段补译与实际整合（stage146）

剩余ABI403字段/217原文值逐项完成reviewed；185处口语占位描述只译你能懂吗，不杜撰技能效果，2处否定占位只译说了也不懂。问号残损Hanja名称按用户授权采用项目选名，不宣称恢复原汉字。音效标记中的sound+莉丝是角色标签，不能机械命中独立soundless=无声；新增完整compound exact-source词条解决该语境。人物/怪物/江火雷天地名称沿用既有词表，数字/下划线/Test保留，未知奥尔哈性别不新增。194新词条，名词表1862项；25普通batch13786+6header独立batch→13792 reviewed/0draft。全25普通批重新source/hash/control/glossary/source-font检查通过。

重新冻结scope：普通缺口860→457（INT370/TUI65/INI2/ITM15/ODD5），358pending不变；101控制/167解码/3语义/266Latin等独立缺口未被取消。原corpus分类和源hash不修改，新ABI文本的语义名称解释不等于每个label已证明运行可达。

现有2419字符顺序保留、追加11→2430；两actualfont2667→5097glyph，既有5086bitmap/metrics/tail与旧2419map全保持。11字形紧凑实际glyph预览已查看，两font对13792目标编码/反解完全往返。实际953资源13428普通字段+6header→13434已回填和重整AFS，overflow0/held0，358pending保持原bytes。两font已物理整合package/startup bundle，18缓存镜像、manifest sizes、原AFS member顺序/TOC metadata保持；独立AFS再提取全13434target、2font及18cache通过。权威work/visible-text-146/integrated-afs/integration.json；旧145字体和AFS不再代表新增ABI字段的最新版。

7新数据回归tests，1486通过（baseline/rollback1479）；实际font/resources/AFS工具命令记录build-commands.json。最终ISO未生成：继续457普通候选、358pending、其他scope/control/compiled/image/native和换行/溢出，再整合25已验收SFD并生成用户测试ISO。

stage169 terminal-line-feed-v1：07533.cht slot8与16768.cht slot16原文本末尾均含byte0A。native CHT512读入/identity转换/FString拷贝已有版本锁定证据；本次严格保留0A于译文字节末尾、NUL前，不擅改分页码。explicit policy通过raw/source reading/target/native binding哈希验证；default grammar与普通编码路径不变，运行布局仍待测试。

stage170：两条TUI制表符源字段00000682 key17/physical16与00001240 key192/physical9补译，native256/MainFString4及真实Key查询绑定。single-tab-byte-v1只允许一个TAB，保留09字节并保持数字、protected tokens在TAB两侧顺序，默认API仍拒绝控制字节。风之符咒依名词表部件统一，不写护符；全角空格保留。14616reviewed、2013terms、2464chars/两5131glyph；5control→3control，8decode/其他scope/动画ISO继续，最终验证见170/VERIFICATION.txt。原文中的TAB实际排版语义不因静态存储确认而冒称已验收。

stage171：00000218.fpb实际header key0/offset0/length43绑定，37B可见韩文场景测试对白后6个NUL。terminal-null-padding-v1以source/reading/target/native hashes启用，仅源末尾零字节；目标正文无NUL，rewrite_fpb在译文bytes后追加原6zero并更新native header长度，不删除源padding、不改原档、不推断事件未使用。普通14239/含FILE14617reviewed、2013terms；剩2control与8decode集中00000106源异常窗口，其他scope及ISO继续。完整验证171/VERIFICATION.txt；默认FPB API原行为不变，无自动padding判断。

stage172：00000106.fpb十个原生记录明确列为retain-source-fault（8个CP949 bytewindow截断字符、1个非语法测试残片えうれおいつえれｄ+3NUL、1个9NUL全零记录）。prepare_source_fault_retention按原SHIP/ELF/nativeKey/physical/span/fullpool/hash核查，派生catalog只添加retention proof，原decode/controls/editable/backend/offset/raw均不改变。scope单列源异常保留10，不计已翻译、不授予import、不声明事件未使用；普通scopereview仍不能跳过quarantine。171字库/AFS实际bytes不改，14617reviewed/2013terms/1011资源14614fields。新scope不再有deferred-decode/control，原8failed/2quarantine如实保留；10Latin/3configsemantics/3pending/compiled/native/image/layout与已验收动画/最终ISO继续。证据172/VERIFICATION.txt。

stage173：余10Latin范围收拢：9条可读英文补译（CommonSid1/GFTOrhaText2/FDS原型6），vbvb b source-bound literal保留（累计139）。GFT原92*822+8、native180/arrayf4，GetGiftData按首Key0比较；0/1键唯一，OrhaText源70/nativea8，Core结构最后StrProperty，compiled10958 BeginState的SetChatText参数，不是内部tag。CommonGetCommonTextIndex312920→3127f0/array130，key19实际physical18。FDS03633为2*2052+8四512文本原型，与active03591同定槽schema；不宣称其游戏加载已执行。Sid→希德币、Orha1/2→奥尔哈1/2、pparkjju/2→朴柱/2项目统一，不推断人物身份性别，数字与机器metadata保留。14626reviewed/2018terms；最终字库/AFS验证173/VERIFICATION.txt。10源异常仍保留，3configsemantics/3pending/compiled/native/image/layout及动画ISO继续。


## 配置元数据消费者（stage174）

Verified static：URL初始化26c120..26c670逐键读取；ProtocolDescription key VA4b5a30，26c1c8..26c254保存至5c3bd0；Name key4b5a48，26c254..26c2e0保存至5c3bf0。DefaultPlayer/User段通过26f250配置段读取，26f2d0单键覆盖，见205858..205878、205930..205948与2b35b4..2b35d8的原instruction窗口。保留Player默认身份与协议描述，不把它们替换为故事人物名。消费者绑定不是运行执行或全路径不可见证明；存储role决断与可见性分开。


stage175 typed-bank decision: Gym loader308950/array16c/lookup3132f0，actual30→23、31→24；Pilot loader309990 path4b78f0/array19c/lookup3137b0，actual1→1，read256→nativeMain+4，readHelp256→+10，buffer identity1a54c0。指令anchors与actual source keys逐字节验证。仅证明存储/索引/回填几何，不冒称placeholder替换与compiled运行可达性。


## 原VM编译文字回填前置（stage176）

原builtin注册不是已有a0/v1连续复制模板：initializer4d2130..4d3fe4使用R5900 SQ/LQ保存指针，再LWC1/SWC1复制3-word PMF。新增只读audit_native_stack_registration.py严格拒绝未知指令/call/branch，独立绑定6个builtin：Jump18ab70、JumpIfNot18abf0、Context18b180、StringConst18bdd0、Case18aaa0、Assert18acd0。static copy verified，不表示initializer执行。Jump将u16与frame node+3c代码基址相加；Context有3Bskip头并按相对位移跳过表达式；Assert的u16用于断言位置，不误当跳转。StringConst调用1a54c0身份转换并推进至原NUL，再+1。编译字符串变长不能只写字符串：virtual跳转、Context skip、header长度、缓存流及package表需要同时处理，尚未写入这些脚本。


## 脚本显示字面量范围

stage90的visible-text-candidate不是所有参数都应翻译：SetSentinel的4个MrtsGame类路径属于机器调用参数，按原值保留。47条真正语言标签及9个保留参数通过原FILE/package/export/body与ancestor symbols复核，未以附近字符串猜call位置；IDs/serial/source hashes和原NUL位置不改。字体新增需求见177/compiled-font-inventory；当前175正式asset不包含这47条新脚本译文。

## Compiled Function variable-length backend (stage178)

Verified static: original47display literals in24Functions reparse with unchanged references/opcode/depth topology. Optional include_spans records the exact recursive return boundary; default extraction output remains identical. Every original jump/case target must be a token/VM-end boundary; Context/ClassContext and Skip preserve the original relative target, including observed short historical distances. Only literal bytes, script size and relocated u16 fields change; properties, diagnostic Assert operands and Function tails remain exact. Replicated Functions, Iterator and label tables fail closed in this limited backend.

Compact object/name references occupy4VM bytes irrespective of their disk compact-index width. Source/code coordinates are not package offsets or cached-stream physical offsets. For24selected cache prefixes, every valid bounded original alignment produces identical translated prefix bytes. Duplicated opcode/context-low bytes remain duplicated; modified size/jump/skip words follow the original multiplicity. Metadata after the observed prefix is untouched, including cases where the ordinary Function tail is not contiguous in the stream. All3ordinary/cached tables and wrapper sizes reparse after overlay; untargeted intervals and archive members are exact. This does not prove an independent stream serializer or game execution.


## stage180 标题与 UI 反馈修正

标题菜单是 LINEAR 的 P8 位图而非普通字符串。00013133.lin 五状态菜单、00015559.lin 小标题及 00000624.lin 一致缓存同步，三流九数组；palette、lazy 指针、包表和非目标像素保留。00015560.lin 为不同指纹变体，不按同名猜测覆盖。详细证据见 docs/UI_TITLE_REVISION.md。
