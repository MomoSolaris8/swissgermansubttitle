# Swiss Subtitle MVP 讨论记录

这个文件用于保存我们本地讨论过的产品思路和技术判断，不作为 GitHub 首页主文档。英文对外说明见 [README.md](README.md)。

## 当前核心判断

Swiss German 字幕的主要问题不是 token 成本，而是准确性链路：

`audio -> ASR -> 语义理解 -> Zurich Swiss German 字幕`

其中当前最大的误差通常来自 ASR。如果原始转写错了，后面的 normalize 很多时候只是把错误写得更像 Swiss German，而不是把意思真正救回来。

## 准确性要拆成四层看

1. 听得对  
   ASR 有没有把语音内容基本听对。
2. 意思对  
   字幕有没有保留原句语义，没有出现流利错译。
3. 像 Swiss German  
   输出是不是像 Zurich / Swiss German 字幕，而不是 Hochdeutsch 换拼写。
4. 可读  
   字幕是不是简洁自然，适合观看。

当前最弱的不是“像不像方言”，而是“听得对”和“意思对”。

## 对 120 秒样本的判断

- 这版结果已经能展示方向
- normalize 确实让文本更像 Swiss German
- 但语义可靠性还不够高
- 因此它更像可演示的 MVP，而不是稳定可用的字幕产品

结论：不能把“看起来像 Swiss German”直接等同于“内容准确”。

## Hochdeutsch 的位置

Hochdeutsch 适合做语义辅助层，但不适合直接取代 Swiss German 原文。

更稳的链路是：

- `raw_text`: 原始 Swiss German ASR
- `standard_text`: Hochdeutsch 辅助理解稿
- `normalized_text`: 最终 Zurich-style Swiss German 字幕

也就是：

`raw_text -> standard_text -> 用 raw_text + standard_text 一起生成 normalized_text`

不要走只靠 Hochdeutsch 再回译 Swiss German 的单一路径，否则很容易把方言信息洗掉。

## 当前优化优先级

1. 先建立一套小型 benchmark / gold set
2. 优先提升 ASR 质量，而不是先改 prompt
3. 保留 `raw_text / standard_text / normalized_text` 三层中间结果
4. 再优化 normalize 的风格和速度
5. 最后才处理 live translation

## 关于速度的判断

20 分钟视频慢，主要不是 token 用太多，而是：

- 分段多
- LLM 请求串行
- 每次都有网络往返延迟

所以后续如果只解决当前 MVP 的速度问题，最直接的办法是：

- 保留现有 ASR 分段
- 把 normalize 改成并发 batch 请求
- 不要先把音频硬切成 1 到 3 秒去做 map-reduce

## 当前产品思路

现阶段最合理的目标不是“实时翻译”，而是先把下面这件事做稳：

`离线视频 -> 准确的 Swiss German 字幕 -> 可选 Hochdeutsch 辅助层`

技术路线优先级应该是：

`先准 -> 再像 -> 再快 -> 再便宜`
