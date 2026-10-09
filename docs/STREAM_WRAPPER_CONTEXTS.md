# celfid wrapper 与配置镜像上下文补核

## Verified

全部 9 个 streamed 包的 264 B wrapper 均由两个相同的 132 B 记录构成：128 B ASCII 路径及零填充，随后 u32 原包大小。两个记录逐字节相同且声明大小与已读取包表 original_package_size 一致。该字段是原包大小，不是可直接用于跳过流式 serial 的磁盘长度。

3 个完整配置正文镜像前也存在相同双记录，其 name 与 size 对应独立 FILE 原资源。首部 0 与 132 的两个单记录分别对应 psx2game.ini／psx2user.ini 及原文件长度。新增 29 个独立补充区段全部验证，未按可打印字符串猜测 wrapper。

全 35048 个启发式候选重核后，250 个命中完整配置正文、11 个命中已验证 wrapper／首部记录，未闭合字节上下文从 1233 减少到 972。前部未知候选全部获得字节上下文；后部原生区域仍未闭合，跨区段候选不拼接处理。全部 semantic_review=pending、editable=false，不以 wrapper 核查代替运行可见文本判断。

## High-confidence deduction

celfid 同时包含初始化文件记录、双记录 wrapper、包表、交织对象和原资源镜像。原始 package size 与流式字节数不同，直接依声明 size 截取 StaticMesh 等 native serial 会产生错误边界。

## 未闭合部分

972 个后部候选仍需要原生格式与镜像覆盖核查。全包 wrapper 的闭合不等于包 payload 闭合、全文提取完成或所有资源可导入。门禁继续 false。

## 重现

复用 [全候选上下文核查](STREAM_CANDIDATE_CONTEXTS.md) 的命令，使用新的空输出目录。源 corpus 与既有两个 oracle 输入 hash 保持不变，新增补充区段直接从原 FILE 内容与 celfid 包表核查。
