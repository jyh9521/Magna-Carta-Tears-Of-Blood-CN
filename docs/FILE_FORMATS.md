# File Formats

## CDG true native record layout and Store/Gym TUI (stage168)

CDG is header(count72,type5) plus72 records of526 bytes: discardedu32,Keyu32,Name255,numericu32,numericu32,Description255. The263-byte leading-string slices in the old corpus are not physical records; an odd slice may fingerprint the next record numeric prefix as its8-byte tail, which must remain exact. Native records are40 bytes at array118/count11c, with key0/nameFString10/descriptionFString1c. Store/Gym TUI source records areKey4/Main256/Help256, count34/27,type2; native records are28 bytes with MainFString4/HelpFString10. Their key lookup chooses physical positions, not an index guessed from numeric ID.

A valid Unicode space separator can have no ink while retaining normal glyph advance. Empty ordinary glyph rasters continue to fail; the source font cmap and input fingerprint are validated before rasterization.

## Explicit per-field literal control interpretation (stage167)

Generic control parsing defaults remain unchanged. A derived field may select numeric-percent-nonascii-angle-arrow-v1 only with original-controls quarantine and raw/reading/target/native-binding fingerprints, a verified native span, and an explicit false runtime-semantics claim. Known printf/markup tokens take precedence; unknown percent must follow digits, paired literal angles must contain non-ASCII letters, and unknown structures/control bytes fail. Validation preserves all numeric values and token order. CHT native512 write bound preserves the old fullsegment fingerprint and numeric tail; POD and ITM field extents remain512/255 respectively. No automatic codec or grammar fallback exists.

## Verified CHT/POD native text widths (stage164)

CHT original native readers consume12-byte header,count at4,then532-byte records:16bytesnumericmetadata,512bytesNUL-paddedtext,4bytesnumericmetadata. Text offsets28+532*index. Legacy first-NUL/zero-run span516 can include a zero numericword;true stringcapacity511bytes plusNUL. Alternatecatalog preserves the original fullsegmenthash (532or516including nextrecordmetadata when applicable) butwritesonly512bytes andhashes remaining tailseparately. All1608previously selected CHT targets fit this native limit (maximum172bytes);no blindcapacity enlargement is used.

POD fixed12328bytes: fiveu32 headerwords,ten512-byte strings,u32,five512-byte strings,u32,nine512-byte strings,threeu32finalwords.24sourcefield offsets remain distinct despite source text equality. Field0offset20→nativeFString18;field19offset9756→fc. OthernativeFString positions are documented in pod_text_layout(),not inferred fromtext equality.


## Native TUI lookup versus physical ordinal (stage149)

00001240.tui loader and getter share a28-byte runtime record with key at0, MainText4 and HelpText16. Original source geometry is8-byte header followed by516-byte records: u32key,256-byteMain,256-byteHelp. Native lookup scans stored keys, not physical record order. Source catalog IDs preserve both record_id and record_index: only record_id binds a compiled integer getter argument. Every half offset/hash and actual source key is independently checked against original SHIP.AFS. Sparse source keys must not be converted to ordinals in translation-consumer analysis. All serialized record IDs/order remain unchanged in imports.


## Configuration value and startup cached-file overlays (stage147)

Verified for supported source fingerprints: .int/.ini field identity consists of line number, section plus repeated-section occurrence, ASCII key, original value offset/length and SHA256. Rebuilt values may contain mapped high bytes but cannot contain0/10/13. Section/key/comment/newline structure and all unselected values remain unchanged; selected offsets are recomputed after variable-length overlays.

Startup cached configuration records observed in the original bundle use an ASCII bare filename padded with NUL to128 bytes immediately followed by a little-endian u32 file byte length. Core.int has2 matching records and1 whole body; psx2game.ini has3 records and1 body. Exact path/source hash/count profile is required; body and size words are overlaid through source-hashed segments with independent readback. Record purpose/engine consumption remains unverified; no broad binary pattern patch is authorized. SHIP mirror resizing remains rejected.


状态定义/出处见 ../TECHNICAL.md；完整审计与资源计数见 PHASE1_RESEARCH.md。

## AFS (Verified structure; upstream runtime findings)
`AFS\0`, u32 LE count @4；@8 每 entry 8 B `(offset,size)`；entry sector alignment 0x800。
Filename TOC 每项 48 B：32 B ASCII name +16 B metadata。保留 entry 顺序/metadata。
复用 cri-afs 与 lib/afs.py，不自行实现 packer。
SHIP slot0 AFSShipFileIndex.idx；LINEAR AFSLINEARFileIndex.idx；FILE AFSFileIndex.idx。
CRLF ASCII：header、self-size 0、交替 filename/decimal size。
LINEAR header 不带 .idx、listed name 不带 .lin；SHIP 用全名。
修改 payload 后同步 primary TOC、slot0 manifest 和 ISO file size/extent。
原始 SHIP .utx/.unr 等 4 B stub 的 manifest 可记录外部 package size；不能机械比较所有 entries。
FILE 的 celfid 重压缩会变 compressed size；上游 rebuild_afs 原样保留 manifest 是已复现的 metadata gap。
AFSINFO.INI preallocation caps 不可因新增资源而忽略（本阶段不新增条目）。

## FPB — PlayBook (Verified on 707 KR files)
Little-endian，无压缩。
| Offset | Type | Meaning |
|---|---|---|
| 0 | u32 | count = explicit windows +1 sentinel |
| 4/8 | u32 | preserved header fields |
| 0x0C | u32 | implicit seq0 byte length |
| 0x10 | N*12 B | `(u32 seq,u32 offset,u32 length)` |
| 0x10+N*12 | u32 | text data byte size |
| next | bytes | shared text pool |
Offsets 相对 data section，length 按编码后 bytes；可 overlap，不把窗口数量当独立去重文本数。
有隐式 seq0 时不写 synthetic window，更新 +0x0C；无 explicit window 时长度等于整个 pool。
复用 parse_fpb_raw/build_fpb/synthesize_implicit_seq0。edited catalog concatenate 的 window 重排需 runtime 对照。
上游 TECHNICAL 旧 `(seq,length,offset)` 与 padding 说明错误，代码和韩版实际字节支持本表。
韩版 708 entries：707 正常，00001945.fpb 为8 B stub。bounds/total/header checks 全707通过。

## Slot families (Verified upstream implementation; KR boundaries incomplete)
| ext | upstream header | segment stride |
|---|---:|---:|
| .cht |28|532|
| .odd |16|240|
| .gft |16|74|
| .cha |12|299|
| .cdg/.mdg |16|263|
| .ecd |40|548|
| .fds |12|512|
这是 text segment model，不是全部资源的 physical record spec；允许尾部部分段。
split_slot = first NUL + trailing zero run + opaque trailer；editable limit tail_at-1。
韩版观察 .cht size =12+record_count*532，文本起点另有16 B metadata；不能将28字节一概当原始文件头。
例如 .cht 00002773 1076 B / count field@4=2；00003419 544 B / count@4=1。
.cha 90007 B；.cdg 37880 B；.mdg 23678 B；这些不是简单的 header+count*上述segment stride，必须保留数字/结构。
.ecd 00011170/00011171/00011181 为8 B stub。其余文件不因尾部 partial segment 自动报损坏。
韩版真实字段用途、gft/odd/fds 分段映射未定；只读 inventory 中 segments 是上游 parser 结果，不是翻译条数承诺。

## Region families (.pod/.tui/.itm/.abi/.sgi/.nod/.dod/.cls/.att/.val)
上游 find_text_regions 仅找 USA 0x20..0x7e >=4 B runs；cap 延伸到下一非零字节/region。
不是完整二进制 parser，不区分 identifier、binary false positives，也会漏短串/高位文本。
KR/JP refs 按 USA offset best effort，不是已确认语义对齐；扩展成韩版 extractor 需结构 schema。
region writer 接受 len(s)==cap，可能没有 NUL；中文 validator 必须明确终止字节预算。
.pod 韩版148文件；上游报告 fixed 12328 B；`.tui`16、`.itm`1、`.abi`1、`.sgi`1等统计见研究报告。
上游 tui 文档同时出现240/260 stride，属于待核查旧说明，不采用它作为所有 tui geometry。
.tui menu-tab strings 不一定用于显示；很多标签是 LINEAR UE2 Texture 的像素。
.itm item text/stats 混排，未知 numeric/lookup字段保留；不允许凭 ASCII 含义进行全局覆盖。

## LIN / LIX and UE2
每 zlib chunk：u32 LE uncompressed_size、u32 compressed_size、zlib bytes；常见 unc 24576，尾块可短。
复用 celfid decompress_chunked/recompress_chunked；新 research wrapper 非第二套 compressor。
LIN 解压 buffer 通常 path header + UE2 package，package magic bytes c1832a9e，version118；offset 相对 package start。
UE2 header name/export/import counts+offsets；tables 有 signed compact integers；research_inventory 仅只读表解析。
Celfid 是多资源启动包，不假定一个 UE2 package；韩版解压4195112 B，包含主字体的精确副本。

## Custom KR Font serial (Verified layout/bitmap; runtime semantics incomplete)

完整27项range/base数组已加入只读审计门禁；B0A1..C8FE静态组合共2350，对应317..2666。该计数不包含其它区段容量，也不证明native支持任意扩容；语料使用和未观察槽的区别见 [字体容量审计](FONT_CAPACITY.md)。
独立 MrtsEngine.u NormalFont/KatakanaFont serial 起点见 TECHNICAL.md。
前三 bytes 00 00 00 为未知/待确认 serializer prefix，不直接当作三种 flag。
serial+3 六个 u32 LE：观察值1,1,glyph_count,height,width,row_stride。
+27 compact bitmap byte count；bitmap 每glyph height*stride，2bpp LSB-first，每byte4 pixels。
随后 compact metric byte count、glyph_count 个 bytes；再 compact range count、u16 keys；compact base count、u16 bases。
两字体 glyph_count2667、stride5、width19；Normal height21，Katakana height18。
27 keys A1A6/B0A1..C8A1/C8FF；bases256/317/.../2667；尾8 B b503000001000000 未知。
Width bytes 是 advance 候选（high-confidence），runtime mapping/wrap/kerning/baseline/atlas尚待trace。
NumberFont 另一种布局，不能套上述表。

## Celfid text slots / linked groups
上游英文 regex 筛大写词、FF marker、null padding；只保留USA唯一16 B marker。
cap=max_bytes-1；marker/max_bytes/source identity readonly；中文要引入明确display/internal-key属性。
shared substring和duplicates形成linked groups，template.format(base=...) cascade；关联真实性需游戏验证。
同长ASCII全bundle word-boundary rename不适用于中文字节映射；避免误改UE2 names/save keys。
SHIP重复内容与bundle precedence仍未知。上游报告615slots/67groups，非韩版完整计数。

## ISO / SFD

韩版ELF首PT_LOAD将offset0x80映射到VA0x100000，filesz0x43BB00、memsz0x4EC600；内存尾部不对应文件字节。字符串pointer、地址构造候选与函数入口分别标记，不混作binary patch offset。完整版本指纹与规则见 [native研究](NATIVE_RESEARCH.md)。
ISO9660 sector2048；directory extent/length 双端序；append relocation 更新 PVD sector16+80 volume size。
lib/iso.py 实际缩小也更新directory length（旧docstring未同步）；必须 src/out 分离。
SFD复用upstream FFmpeg MPEG-1+ADX/libass/SofdecMuxer；无需重开发。
单韩片180216静态测试成功，ADX相同，duration drift/DTS warnings/PCSX2 acceptance 未完成。

## 单字实验写入边界 (Verified static)
glyph317在Normal serial+33315，105 B；Katakana serial+28560，90 B。仅bitmap改变，不动metric或range/base。
19像素每行5 B，2bpp灰度量化0..3，末尾unused bits置0。
00001944.fpb pool offset0/26各写B0A1，seq0/seq2及所有header/table字节不变，文件530 B。
FILE slot0只改变celfid compressed size；SHIP索引仍保留所有external stub sizes。
ISO本次2 in-place，FILE目录LE/BE length同步，无relocation；ignored DIFF_FILE.json记录精确差分。

## 韩版00001240.tui固定记录 (Verified bytes; limited to this file)

schema3审计进一步确认863条记录的512 B载荷均由两个独立256 B NUL填充区段组成：首段863非空，次段29非空/834空。相对记录偏移+4/+260；先前29个尾部例外的非零字节均从载荷+256开始。细节和证据类型见 [TUI字段](TUI_FIELDS.md)，512 B不作生产单段容量定义。

后续全量审计确认该韩版全部16个TUI同样满足8+count*516及文件内唯一id，共863个记录；834个字段为严格CP949+clean NUL padding，29个字段首NUL后仍有非零字节，不能直接套用纯文本slot writer。完整文件表及celfid副本见 [TUI审计](TUI_AUDIT.md)。该结构验证不等于所有字段均可翻译。
文件125396 B；u32 count243 @0、u32观察值2 @4（含义未定）。其后243项516 B记录，u32 id+512 B NUL填充字段。
record index127的id176 @65540，text @65544；原有效字节18 B，其后全0直至下一id175。
本次只开放该显示字段；不能凭这个文件推断所有.tui或其他slot扩展名布局相同。
celfid解压buffer内完整125396 B资源唯一出现于3929716，字段绝对位置3995260；副本同长同步，资源ID和记录布局不变。
固定容量包含末尾NUL，本测试写入16 B，剩余496 B零填充；文件整体长度不变。

## FPB增长实验

全量韩版扫描另确认六个显式seq0资源的pool前缀不属于上游合成views；header +0x0C仍保存该前缀长度。文件列表和长度见 [FPB审计](FPB_AUDIT.md)。这些文件原版无编辑回写一致，但当前partition增长后端拒绝；gap不等于损坏或无用数据。
00001944 seq0 20→30 B；seq2 offset26→36、length80→118；文件530→578 B，pool414→462 B。
连续partition重新布局后后续窗口重定位；未编辑各窗口的bytes与控制标记保持。slot0 manifest记录实际578 B。
src/localization当前backend遇overlap/gap/duplicate seq拒绝，未假设所有FPB是partition。

### TUI native参数线索（Verified static；读取语义未确认）

00001240的局部ELF指令序列在JALR `0x30AD88`和`0x30AE1C`的delay slot分别设置a2=256，两者均构造对象+0x14间接目标并以sp+0x60作为a1；相邻调用a2=4。此证据加强双256 B字段读入假设，不扩大可写字段范围，不改变旧PoC profile。对象来源及间接槽实现待解析；见 [native研究](NATIVE_RESEARCH.md)。

### 韩版ELF `.reginfo`与候选表

Verified static：ELF32 MIPS reginfo 24 B的GP声明为0x5437F0；gp-32200指向文件背书槽0x53BA28，其初值0x53C210本身不在文件背书范围，且有store候选。默认不递归解引用原文件中的pointer。表0x4FE270/0x4FE390仅作为bounded u32候选表分析，不作为完整容器parser或可patch函数表。结构与路径证据见 [native研究](NATIVE_RESEARCH.md)。

### range/base的离线执行证据

原ELF片段0x20EE80的只读模型使用u16 range/base与动态count；原版27条表包含61个首段成员及2350个韩文成员，命中index256–2666。区段长度为相邻base差值，gap返回63，命中结果低16位。这里只确认模型与原表相容，未证明UE2加载器将序列化字段写入哪一运行时实例；合成29条表不写回资源。见 [查表模型](GLYPH_LOOKUP.md)。

### Font metric native消费者

0x2727C4候选通过+0x68 pointer与16位glyph index执行LBU；两原Font各2667 B metric可在合成对象内逐项读出。+0x54辅助word语义未定，不能按序列化字段排列强行标为runtime height。数组加载参数与+0x68/+0x74/+0x80相容，不构成完整native layout证明。见 [metric研究](FONT_METRICS.md)。

### FontObj bitmap与page候选

原Font packed数据在0x333C30邻域存在+0x60源pointer消费者；index为16位，+0x54/+0x5C的height/stride解释属于High-confidence deduction。0x333D64局部2bpp标量操作产生0/60/120/180，与乘85的离线灰阶预览不同；另有+0x94选择的bit-mask分支，实际格式未确认。动态page数组不等于全字库容量已验证。见 [bitmap研究](FONT_BITMAP.md)。

### Font序列化append-only builder

27 B头保留除glyph count @11的字段；重建compact bitmap长度、bitmap、compact metrics长度、metrics、compact range/base count与u16表，未知tail原样透传。新增glyph与metric追加在各数组尾部，旧C8FF sentinel保留，追加新范围与结束sentinel。独立资源增长还需要UE2 export offset/size更新，当前未写回包。见 [扩容实验](FONT_EXPANSION.md)。

### UE2 export追加替换（Verified static，2026-10-09）

当前MrtsEngine.u header @20为export count、@24为export offset；每项为compact class/super、i32 outer、compact name、u32 flags、compact serial size和非零size时的compact serial offset。index为1-based。新builder锁定hash、version118/licensee15、flags1，保留原表及payload，追加目标payload与新表，更新@24；目标字段compact编码长度可变化。零size项不写offset。真实7668项回读及无关7666项bytes保持通过，不等于运行时包加载成功；celfid不是完整engine package副本。见 [包级构建](FONT_PACKAGE.md)。

### celfid缓存片段与混合ISO（2026-10-09）

原bundle唯一匹配64 B engine header、123318 B export表及两个Font；两条路径记录是128 B NUL填充ASCII名称加u32实际包长度。字体增长时同步这些六段，其余bytes按新位置保持；不是完整bundle parser。韩版含ISO9660/UDF双文件树，原UDF anchors在LBA256/1567583；FILE增长relocation须同步UDF分配/文件长度/anchor及descriptor校验，不只改ISO9660。见 [缓存与镜像门禁](FONT_BUNDLE.md)。

### 有限布局UDF overlay（2026-10-09，Verified static）

支持单只读物理partition、Type1 map、标准tag261 File Entry、单short AD。File Entry info length @56 u64、recorded blocks @64 u64，AD从176+extended_attr_length开始，u32长度及u32相对partition block；元数据位置由parser确定。Partition length @192、单partition integrity size table @84；descriptor tag CRC16 @8、CRC长度@10、location@12、checksum@4。原CRC长度保持，未知bytes保留。增长镜像新anchor追加一sector、partition不含尾anchor，PVD总sector数包含它。实际ISO/UDF双视图AFS回读通过，不等于runtime验收。见 [新候选](QA_EXPANDED_POC.md)。

### 构建receipt与QA数据

pipeline.json schema1记录显式locale、原ISO/font/locale/tool SHA-256、range start、步骤command/exit/log、status/failed_step和candidate路径/hash；静态结果与runtime分开。QA_CHECKLIST.json的版本/BIOS/backend初始null，各case初始untested且evidence空。独立verification.json schema1不依赖构建receipt推导。UDF主备space bitmap/table/integrity引用需全部zero；不将非零空间管理描述符当未知padding透传。见 [构建与证据](POC_PIPELINE.md)。

## qa-validation.json — 人工记录证据索引

schema1保存candidate/receipt/locale SHA256、environment、cases的recorded_status及每项evidence路径/大小/hash。record_state为pending/recorded-complete/recorded-failure；runtime明确manual claims only/not independently verified。它不是ISO结构报告或游戏验收证明，详见 [记录格式](POC_QA_RECORDS.md)。

## 韩版角色CHA首字段实验

00000460.cha：12 B header、301条299 B记录，slot0/4/8/169/229首NUL字符串相同；前四可写258 B，第五254 B，trailer40/44 B保持。celfid含完整唯一副本；slot号和marker id不混用。具体用途/逻辑关联待运行核验，见 [名称字段](NAME_SLOTS.md)。

## name_slot_overlays — 实验性显式字段层

locale可选数组，每条resource/expected_sha256/source_text/source_encoding/expected_slots/targets明确源身份与选中slot。expected_slots为全体完全相同首字段库存，targets仅为显式子集；不自动将同文判断为linked group。每个target含slot/target，报告name_slots与原三条records分开，QA增加稳定SHIP/resource/slot/N id。见 [名称配置](QA_NAME_POC.md)。

### CHA slot0显示观察（2026-10-09）

name-slot-poc-01只修改slot0及完整缓存副本；编成、道具与角色详情菜单已有中文姓名截图。显示已观察，不将同文slot4/8/169/229自动认定为linked group，亦不推定未知trailer字段语义。见 [姓名QA](QA_NAME_POC.md)。

## text_resources与font_characters

试译配置text_resources列表按resource/kind/expected_sha256/cached_copies/targets定位。FPB targets含seq/source_sha256/target；TUI targets含record profile/target/估算像素预算，profile固定8 B头、516 B记录、+4起点/256 B跨度。自动生成QA id为SHIP/resource/seq/N或SHIP/resource/record/ID/field/0。

font_characters引用UTF-8 JSON唯一非ASCII字符列表，不含运行时编码；构建时在原Font尾部追加，字节值与glyph由同一分段规则推导。区段内trail byte A1–FE，当前D0至D3使用4段，跨段留gap和sentinel。33字旧批次的序列化结果保持兼容；具体2984 glyph资源尚无运行验收。

## source-catalog与target批次（schema1）

source-catalog记录source_locale、严格encoding、输入hash、resource hash、稳定id、source bytes/hash、references及隔离原因。FPB窗口offset相对pool，slot/TUI/candidate offset相对resource。完整FPB pool另存reference，celfid位置相对解压buffer；这些坐标不能互换。

目标批次保存locale、id、source_sha256、target、draft/reviewed状态；不将译文放入en。自动模板不等于reinsertion plan，read-only候选不开放盲写。raster_size可由font_raster_sizes按原export名指定，不修改几何/metrics或跳过bbox校验。详见 [目录](TEXT_CATALOG.md)及 [字体](SOURCE_HAN_FONT.md)。


## 本地校对交换数据（Verified）

review.jsonl 每行包含 source（完整 catalog 字段元数据）、source_text（严格解码原文或 null）、target、translation_status、reinsertion_authorized=false。空字段和 decode failed 均保留；失败字节位于 source.raw_hex。target 空表示未译，不复制原文填充。

resource-metadata.jsonl 每行保存一个资源的非 entries 元数据，包括 hash、大小、FPB 完整 pool 和 audit；celfid-candidates.json 独立保存扫描候选和完整资源镜像。HTML 经转义，只读展示。summary.json 分开统计资源 / 结构记录 / 初稿 / 未译 / 坏字节，不把候选数当可见文本数。该格式不是游戏导入格式。

## FPB 源字段混合编码观察（Verified static）

00005420.fpb 的 24 个及 00005421.fpb 的 7 个严格 CP949 窗口可按 pool offset/source_bytes 切出并核对字段 SHA-256；相同原字节以 CP932 严格回读得到日文，编码往返不改变任何字节。有效 CP949 不意味着文本为韩文。该观察不改变 FPB 指针/长度结构，不自动赋予写回权限。原窗口/完整 pool 仍保留，补充源读法用于翻译与校对。

## slot trailer 与主字段覆盖（Verified static）

split_slot 的 trailer 起点为首 NUL 后首个非零字节，不是语义类型。韩版 FDS／GFT／ODD 的该区域内存在可读完整句子；主字段 leading-only 之外另保留 638 个候选片段，未确认全部可见。原完整候选与片段分别保存，避免区间切分后误判双字节失败。详情与各扩展名统计见 EXTRACTION_COVERAGE.md／CANDIDATE_SPANS.json。

## 韩版 FDS／GFT／ODD 记录布局

Verified static：六资源总长均为 8+count*stride，ID 不保证连续。FDS stride2052；GFT stride822或10307，不能套用单一74 B槽视图；ODD正文stride560，三个字段与数值尾部分离。各记录分区、字段容量及元数据位置见 [RECORD_FIELDS.md](RECORD_FIELDS.md)，运行读取语义仍未验证。

## LINEAR／FILE 流式包表

Verified static：路径256 B + 保留u32 + 原包长度u32，随后UE2 version118摘要，name offset64。流式names/imports/exports顺序相邻，原头io/eo仍为原包坐标。declared export offset/size仅作原包边界检查，不对应流式serial；7,830次包表通过。详细统计及12项压缩差异见 [CONTAINER_PAYLOADS.md](CONTAINER_PAYLOADS.md)。

## MUSIC.AFS 与 SFD 的只读库存

Verified static：MUSIC filename TOC stride48、3646项，头界限及全部entry范围在归档内；复用cri_afs读法。ADX观测头为大端长度／采样率／样本数，记录参数不擅自推定语言。46个SFD的MPEG-1视频与45个ADX音频流经完整pipe输入核对，详见 DISC_PAYLOADS.md。

## FPB pool-gap 字段视图

ID使用pool offset/length，不使用推定seq。原窗包含seq0时上游synthesize_implicit_seq0不会补开头，韩版6文件因此有802 B未索引前缀；完整pool原文仍保留。补充视图不改变windows、count或运行结构，详见FPB_POOL_GAPS.md。

## SFD 画面文字与 ASS 参照

46 个原版影片完整解码为 47 张接触表并逐表审查，8 秒抽样中 25 个影片观察到文字。新增确认韩文序章／尾声、韩文及日文制作名单；现有两地区 ASS 共 510 条是上游参照行，不等于韩文原文提取。抽样间隙、完整转写及语音内容仍待核查，全文覆盖门禁保持关闭。详情见 `docs/MOVIE_TEXT_AUDIT.md`。


### ELF 完整字节候选扫描

详见 `docs/ELF_TEXT_AUDIT.md`。192,781 条跨编码候选及地址数值命中不等于游戏文本；机器代码也能严格解码。ELF 文本语义覆盖尚未闭合，完整提取门禁保持关闭。


### 普通 UE2 包脚本全文参考

详见 `docs/SCRIPT_TEXT_AUDIT.md`。568 个普通包 TextBuffer 完整正文与 2,993 条双引号候选已定位；源码与运行时显示仍需区分。宽字符中的 CP949 打包阅读视图不替换原文，流式 serial 与编译字节码覆盖尚未闭合。


### LINEAR 未解释尾部与有效前缀

详见 `docs/STREAM_TAIL_AUDIT.md`。全部 4,098 项 manifest/TOC 尺寸一致；12 个尾部疑问仍未解决，有效前缀追加 57 次包表及 87 次 Texture export。部分载荷仍保持未闭合状态，不截尾或扩大可重建保证。


### celfid 候选字节上下文

详见 `docs/BUNDLE_CONTEXT_AUDIT.md`。35,048 条候选全部校验片段身份；2,595 条位于完整 SHIP 镜像，16,767 条位于流式包表，15,686 条仍处于其他载荷。分类不推断可见文本或 linked group。


### 实例属性与 HasStack

普通实例以属性 None 终止；HasStack 0x02000000 头的 LatentAction 为 u32，非零 Node 带 compact Offset。Bool 无 payload，Struct 名先于尺寸；Str 类型 13 使用有符号 compact 数。详见 `docs/OBJECT_PROPERTY_AUDIT.md`。


### 零脚本 Class serial

version118 普通 Class 序列包含观测额外 u32，再读虚拟 ScriptSize；零 ScriptSize 后逐项解析 State／Class metadata，再读取默认属性至原 serial 末尾。详见 `docs/CLASS_DEFAULT_AUDIT.md`。


### 复制脚本虚拟／落盘长度

13 Class 复制脚本 1860 B 落盘对应 2228 B 虚拟长度；compact 对象引用展开计 4 B。未知 opcode 拒绝，不以声明长度盲跳。详见 `docs/REPLICATION_DEFAULT_AUDIT.md`。


### 活跃源异常字节核查

FPB 窗口 offset/length 使用字节坐标；00000106 的完整 CP949 pool 成功不保证每个窗口落在字符边界。12 个其他 pool 存在完整 CP932 往返阅读，CHT 38 字段同样存在 CP932 阅读。详见 [异常字节核查](DECODE_QUARANTINE_AUDIT.md)。


### CHA／MDG 怪字候选闭合

实际 8 B 头与完整记录布局核对 346 记录／391 文本字段；381 候选中 375 正文、6 数值区，零未覆盖候选。6 个怪字不属于新增正文；具体 u32 用途未完成。详见 [记录核查](NAME_RECORD_AUDIT.md)。


### 固定 region 正文遗漏补核查

44 个 ITM／ABI／SGI／NOD／DOD 文件的完整记录补导出 2360 字段，其中 498 非空字段缺少旧完整视图（488 无旧正文 byte overlap）。NUL 启发式会吞入前邻非零数值并漏提后续正文；新旧字段尚待统一集合合并，不重复计数或开始新增翻译。详见 [完整 region 字段](REGION_RECORD_AUDIT.md)。


### POD 全区块字段核查

148 POD 的 24 槽布局共 3552 字段（333 非空），补出 2 个 CP932 日文槽和 1 个问号槽。40 B metadata 的具体用途仍未验证；首 u32=31 不套用其他格式 count。详见 [POD 核查](DIALOGUE_BLOCK_AUDIT.md)。


### 普通 Texture 载荷核查

28 Texture／27 Palette／191 mip 全部结构闭合；28 首级图已检查，Editor Bad 含 `BAD SIZE`，NumberFont 为 glyph atlas。163 小 mip 尚未逐图检查，流式 Texture 未覆盖；全文门禁不变。详见 [普通纹理核查](TEXTURE_MIP_AUDIT.md)。


### 普通编译脚本完整结构核查

8032 个 Function／NativeFunction／State／Struct 全部 serial 闭合，1207 个字符串常量、5 个含韩文、0 解码失败；运行可见性与流式脚本未完成。详见 [编译脚本核查](COMPILED_SCRIPT_AUDIT.md)。


### celfid 流式字段前缀对照

Core.u 表后连续 2229 B 与普通包的 144 个源片段逐字节对应，观察到 Children／Next 参数链及 Struct 依赖内嵌。RandRange 脚本首次差异处严格停止，根 Object 和完整流未闭合；不能按 declared_size 连续切片或删重复 opcode。详见 [流式前缀](STREAM_FIELD_PREFIX.md)。


### Core Object 依赖树对照

源包 oracle 对应连续 27922 B／1715 个字段对象自身片段；27898 B 原字节相同，24 B RandRange 差异脚本保留 opaque。局部根树闭合不代表跨包或全流覆盖，默认严格模式仍在差异处停止。详见 [依赖树对照](STREAM_DEPENDENCY_ORACLE.md)。

### celfid 跨包 Class header 全量对照

568 个普通 Class header 全部核查，534 个唯一精确锚点、34 个无相同 header；6 包完整表元数据一致。Core 根树后首先对应 Engine Material，而非 Actor/Pawn。锚点不等于 serial 边界或全文覆盖，门禁保持 false。详见 [Class header 对照](STREAM_CLASS_HEADER_AUDIT.md)。

### celfid 编译脚本前缀全量有界对照

8032 个普通脚本定义全部重读；7983 个有 header 对应的定义、7987 个候选均符合限定重复模型，49 个 header 无匹配。4 个多位置定义与 1501 个内部路径歧义保留；1193 个既有常量位于符合模型的源定义中。后验拟合不是独立解码或 VM 等价证明，门禁仍为 false。详见 [脚本有界对照](STREAM_SCRIPT_CORRESPONDENCE.md)。


### celfid 跨包依赖连续对照

源包 oracle 在 Core 根树后连续对应 224167 B／5248 个新增对象片段集合；INI 与 SmallFont 精确匹配，两个 Texture 完成限定 mip 顺序投影。负引用按完整外层身份解析，487115 的多义 Palette 候选未放行。后验对照不等于独立流解析或全文覆盖，门禁保持 false。详见 [跨包连续对照](STREAM_CROSS_PACKAGE_ORACLE.md)。


### celfid 原生字节等价候选扩展

显式模式保留全部同字节身份，连续诊断 2938500 B／532 次 Class 根请求；7 个身份歧义和 2 个 parsed-table-only 区段未伪装为完整资源映射。下一处原生数据在 3201448 停止，全文门禁仍为 false。详见 [原生字节等价对照](STREAM_NATIVE_EQUIVALENCE.md)。


### 普通包本地 Class 纹理覆盖修正

旧纹理计数只覆盖 import-class 子集。本地正 Class 引用补核后，总计 37 Texture／35 Palette／212 mip；新增 9 个 Engine 纹理的 21 个 mip 全部检查，其中 3 个 Latin／符号图集、无新增整句候选。全文门禁保持 false。详见 [本地 Class 纹理审计](LOCAL_CLASS_TEXTURE_AUDIT.md)。


### celfid 全候选字节上下文复核

35048 个启发式候选全部复核字节身份，38499 个区段索引提供只读上下文；1233 个仍为未闭合字节上下文。候选命中不等于可见正文，所有语义判定继续 pending，全文门禁保持 false。详见 [全候选上下文核查](STREAM_CANDIDATE_CONTEXTS.md)。


### FILE 配置及国际化值补充核查

全部 29 个 .ini／.int 导出 1008 个值（918 非空、90 空），ASCII 严格读取且全部行字节闭合；Core.int 原正文位于 celfid 末尾。配置标识与可见提示尚待区分，补充清单不等于 1008 个可翻译正文，主 corpus 暂保持不变。详见 [配置条目审计](CONFIG_ENTRY_AUDIT.md)。


### celfid wrapper 与配置镜像上下文补核

9 包及 3 配置正文的双 132 B wrapper 全部逐字节核查，首部 2 文件记录与源文件大小对应。35048 候选中的未知字节上下文降至 972，仍不是可见语义闭合；原包声明 size 不可直接作为流式 serial 长度。详见 [wrapper 补核](STREAM_WRAPPER_CONTEXTS.md)。


### 配置值统一源快照补全

29 个配置资源／1008 个值并入只读快照后，结构化统计为 1027 个资源／20151 个字段（15552 非空、4599 空）；原资源、候选及 6334 条译稿链接不变。新增字段保持 und／pending／不可导入；该数量不是全文最终可翻译数量，全文门禁仍为 false。详见 [配置值快照](CONFIG_CORPUS_CONSOLIDATION.md)。


### celfid 尾部资源链补核

37 个单 132 B wrapper 与 SHIP 正文连续闭合 966382 B；780 个候选补充明确字节上下文，未闭合数降至 192。单记录资源 wrapper 与双记录包 wrapper 必须区分；字节镜像不代表可见正文或可编辑许可。详见 [资源链核查](STREAM_RESOURCE_CHAIN.md)。


### celfid 原生尾部纹理补核

新增一个有界 P8 纹理／Palette 与 4 mip 全部检查；8×64 等细长 mip 先读 dimensions，再读 pixel count，不能沿用此前宽高同时不超过 8 的观察作为全局规则。图像未发现完整正文，StaticMesh 与全文门禁仍未闭合。详见 [尾部纹理核查](STREAM_TEXTURE_TAIL.md)。


### SFD 全帧解码补核

46 个影片全量解码 72696 帧，全部输入 hash／退出码通过，error 日志为空；实际视频时轴合计 2425.6232 秒。逐帧 hash 不等于逐帧文字转写，抽样视觉结论未升级，全文门禁仍为 false。详见 [全帧解码核查](MOVIE_FULL_DECODE.md)。


### 有界数值及地图属性补核

CLS count213/kind24/stride100，ATT count456/kind5/stride24，VAL count170/kind1/stride8，8 B头后全word区精确闭合；具体native字段语义仍未完整验证。地图尾部六属性记录共398 B边界已闭合，但不可按声明8165 B跳过未知流式载荷；MrtsPlayerStart.Char_ID的type7阅读是局部有界观察，不套全局Str规则。详见NUMERIC_RESOURCE_REVIEW.md与STREAM_TAIL_CONTEXT_REVIEW.md。

## 流式 DMA_RET 与 VIF 输入长度

见 `STREAM_VIF_REVIEW.md`。13个包、320条命令及65个UNPACK输入段有界闭合，145个候选上下文补齐；剩余地图native候选8个。完整网格schema与运行时执行尚未验证，全量覆盖门禁保持待核查。

## stage88 地图字符串／字段消费者

见 `NATIVE_STRING_FIELD_REVIEW.md`。地图compact-string记录补齐两个候选，上下文未闭合8→6；8032编译对象重新解析，77项取得同函数字段消费者证据，未确认320→243。新角色仍为只读候选，完整native序列化、reaching-definition及运行显示尚未证明，覆盖门禁保持待核查。

### leading-only回填指纹边界

Verified static：旧slot提取的slot_sha256包含整个segment，trailer_bytes及trailer_sha256描述首NUL后零区之外的opaque trailer。observed_byte_capacity+1是可替换的leading范围，不是完整指纹范围。import_audited_fields按两范围分别验证，非选择trailer保留；这不证明所有leading字段的运行显示用途或缓存关系。

## CHT按字段替代文字解释

CHT00004044 slot16、00004059 slots0/3/10/19/21存在严格CP949和CP932双向可往返的相同字节；后者形成完整日文问题及人物说明，前者主参考保留。此发现不改变CHT分区、NUL/opaque trailer、源hash或整个资源默认解码。Verified为字节往返与$n序列不变；High-confidence为按场景词汇选择CP932读法。译文记录只绑定原源ID/hash，不把回译字符写回源语料。

## FPB有序不重叠窗口与保留区（stage141）

Verified static：原SHIP的00004668／00004669／00004800／00004994／00005047／00006436六FPB，已选择窗口均有序不重叠，首窗口前存在非空pool前缀。旧partition-only backend因此拒绝72条已审校目标，不是实际重叠。原header、table、pool及geometry诊断保存在work/visible-text-141/fpb-geometry-frontier.json。

通用rewrite_fpb现在接受有序不重叠且全部in-bounds的窗口：窗口间／前／后的未选择pool字节按原顺序完整保留，只有明确seq目标改变；后续offset重新计算，length及sentinel重新写入，未选择窗口逐字节核对。重叠／逆序／重复seq／越界继续拒绝，不采用模糊diff重映射、不合成不存在的seq身份。

六个原prefix未翻译，原字节及首窗口offset（header+0x0c所用边界）保留。未编号不等于未显示，header默认视图与显式seq0的消费关系仍须原生消费者证明；本项不授权把6个reference源字段从最终范围静默排除。

## 原生FPB首记录核查（stage143）

**Verified（版本锁定静态证据）**：原ELF的`..\FPB\%08d.fpb`唯一地址配对指向加载函数0x3007c0。函数读取count后，循环count次读取key四字节及offset/length各四字节。因此+0x04/+0x08/+0x0c不是padding，而是第一个实际record；后续才是旧parser称为windows的record。目的数组为FieldData的+0x19c或+0x1a8，record stride16、字符串在+4。独立的完整qualified method注册复制链绑定GetPlayBookDataText→0x3424d0→0x342560；getter以10000分数组并对第二数组的key减10000，按key首个匹配返回，不按文件record序号索引。不是UIInfo.GetFieldTextData的TUI消费者。

实际SHIP扫描707个可解析FPB、1个8字节文件00001945.fpb仍不支持；19个header key非零，没有重复native key。六个原pool-gap对应真实首record：00004668 key13、00004669 key10、00004800 key11、00004994 key1、00005047 key2、00006436 key1。这些前缀不能继续归为无编号不可见padding；已有源hash/字节坐标保持，后续补译并增加明确header-record回填路径。其余13个非零首key已有legacy seq/0几何链接，旧ID是catalog alias而非native key，不能直接重命名或与显式0合并。

`tools/audit_native_method_registration.py`与`tools/audit_native_playbook.py`可从原ELF/SHIP/冻结corpus复核；指令原words和完整源hash是依据，Capstone对R5900 LQ/SQ的通用反汇编仅探索参考。证据在work/visible-text-143/native-playbook.json。未声称加载函数已在游戏执行、所有资源场景都可达、字符转换或画面排版通过。953资源候选AFS继续保留；此证据尚不自动改写六prefix或生成最终ISO。

## 原生首record补译与独立回填（stage144）

六个真实header record已在locales/zh-CN/header-dialogue-review-01.json按冻结source hash补译并逐句reviewed，native key13/10/11/1/2/1和pool-gap旧ID分别保留。江之英雄约书亚／救赎之光／光之树／格兰朱／马拉卡特／埃琉内德圣会／普诺森／莫莉沿用名词表。04800原Japanese汉字问号缺损按上下文解释，不声称恢复原字；原bytes严格CP949往返，CP932读取失败。$n顺序和数量保持、未知说话者不新增性别。

通用rewrite_fpb_header和tools/import_fpb_headers.py使用明确native key、首record源hash、原AFS/corpus/已回填copy hash及物理font mapping；仅替换header window，显式record keys/order/body字节、内部gap和tail不改，offset统一加delta，header length和pool size同步。拒绝key/hash/offset/overlap/bounds/control/empty mismatches。实际在stage141的六个正文已译副本上继续回填，header-copies2/headers.json权威；两次构建六输出byte-identical，新增目标无glyph缺口，现有两font已覆盖。11新tests、1471测试通过（baseline/rollback1460）。

此特殊header batch与24普通batch独立：普通13383 reviewed不变，新增6 reviewed→合计13389，实际普通回填13025+header6。冻结corpus中旧reference语义不改写，通过native绑定特殊header policy授权副本。下一步把六副本合并到当前953资源完整import receipt/AFS构建和独立验证，不能拿旧stage142AFS当已含六prefix的最终ISO。860普通缺口、358pending及其他scope/layout/movieintegration未闭合。

CHT定槽内非NUL内容可以包含末尾0A（07533slot8/16768slot16）。512byte native槽、16byte前数值与4byte后数值边界不变。terminal-line-feed-v1保持译文末尾0A并随后NULpadding；当前只验证原字节/FString存储，LF在界面的实际解释未据此推断。

stage170：两条TUI制表符源字段00000682 key17/physical16与00001240 key192/physical9补译，native256/MainFString4及真实Key查询绑定。single-tab-byte-v1只允许一个TAB，保留09字节并保持数字、protected tokens在TAB两侧顺序，默认API仍拒绝控制字节。风之符咒依名词表部件统一，不写护符；全角空格保留。14616reviewed、2013terms、2464chars/两5131glyph；5control→3control，8decode/其他scope/动画ISO继续，最终验证见170/VERIFICATION.txt。原文中的TAB实际排版语义不因静态存储确认而冒称已验收。

stage171：00000218.fpb实际header key0/offset0/length43绑定，37B可见韩文场景测试对白后6个NUL。terminal-null-padding-v1以source/reading/target/native hashes启用，仅源末尾零字节；目标正文无NUL，rewrite_fpb在译文bytes后追加原6zero并更新native header长度，不删除源padding、不改原档、不推断事件未使用。普通14239/含FILE14617reviewed、2013terms；剩2control与8decode集中00000106源异常窗口，其他scope及ISO继续。完整验证171/VERIFICATION.txt；默认FPB API原行为不变，无自动padding判断。

stage172：00000106.fpb十个原生记录明确列为retain-source-fault（8个CP949 bytewindow截断字符、1个非语法测试残片えうれおいつえれｄ+3NUL、1个9NUL全零记录）。prepare_source_fault_retention按原SHIP/ELF/nativeKey/physical/span/fullpool/hash核查，派生catalog只添加retention proof，原decode/controls/editable/backend/offset/raw均不改变。scope单列源异常保留10，不计已翻译、不授予import、不声明事件未使用；普通scopereview仍不能跳过quarantine。171字库/AFS实际bytes不改，14617reviewed/2013terms/1011资源14614fields。新scope不再有deferred-decode/control，原8failed/2quarantine如实保留；10Latin/3configsemantics/3pending/compiled/native/image/layout与已验收动画/最终ISO继续。证据172/VERIFICATION.txt。

stage173：余10Latin范围收拢：9条可读英文补译（CommonSid1/GFTOrhaText2/FDS原型6），vbvb b source-bound literal保留（累计139）。GFT原92*822+8、native180/arrayf4，GetGiftData按首Key0比较；0/1键唯一，OrhaText源70/nativea8，Core结构最后StrProperty，compiled10958 BeginState的SetChatText参数，不是内部tag。CommonGetCommonTextIndex312920→3127f0/array130，key19实际physical18。FDS03633为2*2052+8四512文本原型，与active03591同定槽schema；不宣称其游戏加载已执行。Sid→希德币、Orha1/2→奥尔哈1/2、pparkjju/2→朴柱/2项目统一，不推断人物身份性别，数字与机器metadata保留。14626reviewed/2018terms；最终字库/AFS验证173/VERIFICATION.txt。10源异常仍保留，3configsemantics/3pending/compiled/native/image/layout及动画ISO继续。


## Configuration metadata retention

The derived source-corpus config_metadata_retention object binds source_sha256, original semantic, role, static native window verification and decision hash. It preserves original source/encoding/import eligibility. Scope recognizes retain-config-metadata only with a valid proof and rejects translations unless retain-original is explicit. No runtime invisibility claim is encoded.

## Exact expression spans and source-bound cached overlay (stage178)

Compiled grammar can optionally return token end and virtual_end at recursive return, before parent operands/trailers. Inferring the end from the next token is incorrect for nested Context and Iterator. Default inventory schema is unchanged. Literal payload lengths contribute equally to disk and VM deltas; compact references do not.

Cached prefix rewriting requires a unique complete source header and unique permitted end. All original alignments under the observed repetition grammar must yield one identical output; no first-path selection or deletion of repeated bytes occurs. Unknown bytes, different outputs, edited literal-interior jump destinations and unsupported object classes fail closed. Package metadata tables/summary/two padded-name size records are distinct guarded overlays. All remaining cache bytes remain unchanged.


## stage180 标题与 UI 反馈修正

本次标题 P8 资源为256×256单mip。已验证前三palette通道按RGB组成截图对应的金／灰配色，仅此资产结论，不泛化全部格式。LINEAR原生清单使用无扩展名资源ID，更新大小时移除.lin后缀。详见 UI_TITLE_REVISION.md。
