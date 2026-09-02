---
artifact: contest-submission-evidence
source_base_commit: e45fd95abbb237d3b240a14e39531a29847061ba
template:
  path: docs/赛道一-方向1A-科学假设生成与研究计划设计-提交要求及模板.docx
  sha256: 430ef9a8ec504a3b693e00653a8c3b55a34e00c888ebd616cc06cea7f75c2884
sources:
  - path: all/index.md
    sha256: b508c1b713f5275d90a6602e23cab609cacc1995603f61f1dea21f17fa95cdab
  - path: all/run.md
    sha256: 5a5d5a24df5d45b1b73b389ede91837895706d0e8ddba5cfb8a40b33e24056c6
  - path: deep-cases.md
    sha256: 24087ba92fe24b69d9e6ed54eb5c69b7c709c89d29c1e33ab6db464b2304a1f7
  - path: q049/v1.md
    sha256: 74e43718d54c346a857f763ce1b3a9fbbac53937dc944a36b1007427306bcce5
  - path: q049/review-v1.md
    sha256: 96268a2457f613e15cec52a04fa2989568e24883db95906fe5d82568e949ae74
  - path: q049/v8.md
    sha256: e0a6d83a65ae80f11c585f2b0c63053923b9e60b1fc8240cfb0f6627ebe65643
  - path: q049/review-v8.md
    sha256: 987bc5c279da17f1bf157561bfbe6f62650bf97377206f4364810ee8351779e4
  - path: q049/receipt-v10.md
    sha256: 514ebcf41b3b7e6866801a230deb4fa04afca9df748514c6c4c5223df1ead103
  - path: q049/run.md
    sha256: 38e5ee1a70204627ea2042313a68d727d3c100b2b506c70e7861d44a6c7dc23c
---
# P13-P20 提交证据
## P13 全量运行与案例选择
Q001-Q125 各用一个独立 Pi 作者 Session 运行同一轻量协议：读取 canonical 问题，输出证据边界、三个可区分 Direction、横向比较、研究计划、来源和候选结论；传输失败只重试一次，停止与错误 Session 保留。五个独立审计 Session 各复核连续 25 题，`run.md` frontmatter 独占 Project 终态。共同结果均为 Qwen 候选与 planned 研究方案，不是已验证发现；全量结果与代价见 P19。
旗舰 `q049` 覆盖错误前提校正、来源核验、三机制比较、限定计算、独立评审、修订和直接回答对照。`q089`、`q021`、`q112`、`q098` 分别补充能量转换边界、冲突文献、湿实验规划和人体时序数据边界；五例不能代表需付费全文、受限数据、伦理审批、实验设施或领域阈值裁决的题目。
## P14 旗舰问题与第一轮设置
**问题**：Why don’t the orbits of planets decay and cause them to crash into each other?
**对象与约束**：太阳系八大行星；区分保守引力动力学、微弱耗散、混沌失稳和太阳演化时间边界；优先同行评议或机构一手来源，精确主张需可回读标识符；未执行的模拟和实验标为 planned。
**V1 设置**：`contest-qwen/qwen3-max` 在独立 Session 中形成三个机制 Direction、比较和研究计划；独立 reviewer 使用固定六维 rubric 评价问题理解、文献证据、Direction、科学推理、研究计划、表达与追溯。
## P15 V1 原始结果
| Direction | 核心陈述 | V1 处理 |
|---|---|---|
| D1 | N 体混沌可能导致低概率失稳 | 降级；概率归因与来源链需修正 |
| D2 | 潮汐、引力波等微弱耗散长期累积 | 不选；功率量级和计划判据错误 |
| D3 | 太阳演化先于耗散决定内行星命运 | 选为主方向；所引 Rasio 结论被反向转述 |
V1 为 9/12，五条来源仅 2/5 通过；三方向、对照、步骤与停止条件存在，但地球—太阳引力波功率误写为约 `10^-20 W`，来源与判据不足以执行。N 体积分、广义相对论修正、太阳质量损失、潮汐和 Monte Carlo 均为 planned。
## P16 独立评审与修订
| 独立 finding | 科学影响 | 修订结果 |
|---|---|---|
| Deienno/Nesvorný DOI 属于另一论文 | 关键来源不可用 | 删除错配来源 |
| Lecar arXiv 号 `0111602` 错，应为 `0111600` | 来源不可回读 | 修正标识符并补齐来源记录 |
| Rasio “Earth may well not survive” 被反向转述 | 太阳演化论据方向错误 | 按原文限定重写 |
| 引力波功率错约 22 个数量级 | 耗散比较与计划门槛失真 | 用 Peters 公式、完整输入和独立复算替代 |
| `dE/dt < 10^-20 W` 判据无效 | 会把真实约 200 W 错判为显著 | 改为 inspiral 时间与太阳寿命比较 |
后续版本保留每轮 review 与被拒原因；最终主线改为“保守近可积系统不自然衰变”为主、微弱耗散为补充、混沌为稀有失稳，太阳演化只作外部时间边界。
## P17 最终版与执行边界
最终 `v8` 为 12/12、来源 6/6，独立 `review-v8` 判定可交付。唯一科研计算执行项是 Peters 地球—太阳圆轨道计算：`P=196.291 W`，`t=3.374e30 s=1.069e23 yr`，退出码 0，输出 SHA-256 `7a546ef6f2dd84fdaf967de502583353a6d35abea74b10f3f209412dbb2a2361`；reviewer 独立复算一致。N 体积分、相对论、太阳质量损失、潮汐和 Monte Carlo 仍为 planned。结论只支持“耗散时间远超太阳寿命，轨道不会因该机制在相关时标内螺旋坠日”；不把候选机制或计划写成新科学发现。
V1→独立 review→final 修复了错配引用、反向转述、数量级和判据；代价是多轮检索、修订与审核。约 1% 水星失稳概率的来源归因已修正，限定计算脚本未作为 Artifact 保存，但输入、公式、命令、输出、退出码、输出哈希与独立复算均保留，因此停止继续修订。
## P18 两个近似资源对照
| 指标 | 直接回答 attempt 2：实算近似 | 直接回答 attempt 6：长度近似 | Workflow V1 |
|---|---:|---:|---:|
| 模型 | `qwen3-max` | `qwen3-max` | `qwen3-max` |
| 字符 | 2388 | 4708 | 4970 |
| calls | 21 | 27 | 25 |
| 非缓存输入 token | 113326 | 1182967 | 98844 |
| rubric | 4/12 | 6/12 | 9/12 |
| 显式来源 / Direction / 计划 | 0 / 0 / 无 | 0 / 0 / 无 | 5 条（2/5 有效）/ 3 / 有但判据错误 |
attempt 2 与 V1 同题、同模型、同检索权限，各有五次成功搜索和一次 write；calls 少 16.00%、非缓存输入多 14.65%，但长度仅为 V1 的 48.05%，只近似计算量。attempt 6 长度与 calls 分别为 V1 的 94.73% 与 108.00%，但通过七次 Crossref `curl` 检索，非缓存输入为 V1 的 11.968 倍，只近似长度。没有单一直接回答同时严格匹配计算量和长度；两者均不可直接作为学术答案。最终 12/12 发生在独立评审、修订和限定计算之后，不能只归因于 Workflow。
外部 benchmark 只提供任务、迭代实验、复现、搜索和端到端阶段的评价方法；仓库 benchmark 只证明相应组件门。二者均不作为本项目科学结果、五案例成绩或完整系统分数。
## P19 全量结果、深度案例与边界
| 全量轻量运行 | 结果 |
|---|---:|
| 有候选结论 | 125/125 |
| `completed` | 8 |
| `partial` | 117 |
| `waiting_human` | 0 |
| `failed` | 0 |
| 作者 / stopped / 审计 Session | 125 / 5 / 5 |
| Session 总计 | 135 |
| calls | 2592 |
| 非缓存输入 / 缓存读取 / 输出 token | 27871295 / 99870206 / 581255 |
全量 `partial` 表示已有可提交、可回读结论，但来源层级、主张映射、结构、元数据、canonical 身份或 planned/executed 边界至少一项未过轻量门槛，不等于未运行。五个 stopped Session 是 q041-q045 恢复前的人工暂停记录，不是 Project `failed`；恢复后用全新作者 Session 形成唯一候选。全量未做同题重复运行，不能据此声称跨采样稳健性。
| 深度案例 | final | 来源门 | 深度终态 | 科研执行边界 |
|---|---:|---:|---|---|
| `q049` | 12/12 | 6/6 | `completed` | 仅 Peters 地球—太阳计算 executed；其余仿真 planned |
| `q089` | 12/12 | 9/9 | `completed` | 仿真、扫描、图表和器件实验 planned |
| `q021` | 12/12 | 8/8 | `waiting_human` | ICU pilot、招募、检测与临床结局比较 planned |
| `q112` | 12/12 | 9/9 | `waiting_human` | LCA、实验室测试、试点与比较分析 planned |
| `q098` | 12/12 | 8/8 | `waiting_human` | 人体时序 pilot、招募、检测与健康结论 planned |
深度案例使用完整 rubric、来源门和人工 Gate，不与全量轻量终态混算。结果是候选解释与研究计划；付费墙、来源精度、领域外推、受限数据、伦理审批、实验设施和人工阈值仍限制泛化。
## P20 可核验入口与人工补充
| 交付项 | 当前可核验入口 | 边界 |
|---|---|---|
| 源码、依赖、运行 | [Research World](../../README.md)、[Compose](../../compose.yaml)、[服务端](../../server/)、[前端](../../web/)、[Runtime](../../../runtime/) | 在仓库根配置被忽略的 `.env`（小写 `apikey`、`baseurl`）后执行 `cd research-world && docker compose up --build -d`；启动不自动生成 Workflow 或调用模型 |
| Qwen 调用证据 | [125 题运行账本](all/run.md)、[五案例汇总](deep-cases.md)、[q049](q049/run.md)、[q089](q089/run.md)、[q021](q021/run.md)、[q112](q112/run.md)、[q098](q098/run.md) | 账本记录实际模型、Session、calls、token、候选与 raw SHA-256；不含凭证 |
| 125 题逐题输出 | [索引与口径](all/index.md)、`all/q001.md` 至 `all/q125.md`、五份 `all/audit-*.md` | 全部终态与缺口保留，不以深度案例替代全量 |
| 旗舰版本链 | [输入](../../projects/q049/project.json)、[V1](q049/v1.md)、[首轮独立评审](q049/review-v1.md)、[final](q049/v8.md)、[最终评审](q049/review-v8.md)、[回执](q049/receipt-v10.md)、[运行与对照账本](q049/run.md) | 原始版本、失败 attempt、哈希、限定计算和 planned/executed 边界均保留 |
| 方法与组件评价 | [指标账本](../../../benchmarks/README.md)、[评价设计](../../../docs/benchmarks/design.md) | 不外推为科学结果或完整系统分数 |
提交前人工补充：为当前 checkout 配置 `.env`，完成 Compose 配置、启动与健康检查；公开可达且按 exact HEAD 实测的 API 地址、示例请求/响应；可交互前端地址与页面截图；不泄露密钥的阿里云百炼/Qwen 调用凭证截图；仓库未收录但已记录 SHA-256 的 raw JSONL 脱敏副本；报名信息、20 页内最终排版与可选演示视频。当前 checkout 缺少被忽略的 `.env`，Compose 声明的本地端口不等于公开服务可用，运行账本不等于供应商凭证截图。
