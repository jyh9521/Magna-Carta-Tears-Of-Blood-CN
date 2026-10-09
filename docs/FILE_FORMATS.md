# File Formats

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
