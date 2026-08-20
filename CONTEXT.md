# Research World
围绕单个科学问题积累可审核、可复现、可追溯的研究状态。
## Language
**Project**：一个科学问题一张研究图谱；id 由名称内容哈希生成，`auto` 开关决定 workflow 是否自动推进。
_Avoid_: 课题、任务
**节点**：图谱内容单元，固定四类：question / source / direction / experiment；实验结果并入 experiment 负载，claim 是审计单位不是节点。
_Avoid_: brief、result、setup 节点类型
**Life state**：节点准入状态：pending（可查看，不能生长依赖）→ admitted（双审通过）或 ghost（驳回隔离）。
_Avoid_: 保存、发布、删除
**幽灵节点**：ghost 态节点，带驳回理由与抗辩，隔离留存，只在后续审核时做相似性匹配。
_Avoid_: 删除、隐藏
**Direction 状态机**：direction 的论证状态：proposed → supported | refuted，终态不可逆。
**谱系**：同一血脉（lineage_id）的节点链；同一谱系连续 2 次审核驳回触发 auto 暂停并升级人工。
_Avoid_: 分支、会话树
**Workflow**：图谱的写入管线，固定两类：brainstorm（生成→查重→MMR 入池→双审）与 plan-execute-review-reflect（规划→分步执行→双审→反思）。
_Avoid_: 任务、job
**Step**：workflow 的最小执行步，负载为 image/command/files/seed/limits，经一次性容器执行，退出码与输出落库。
_Avoid_: 工具调用、动作
**双审**：两个独立 reviewer 一致 approve 才准入；分歧时 workflow 转 waiting_human 由人裁决。
_Avoid_: 打分、多数投票
**抗辩**：双审意见按 reviewer 沉淀在节点 rebuttal 字段，随节点留存。
**Workflow event**：append-only 运行事实（actor/type/payload/time）；Timeline 与活动页均为其投影。
_Avoid_: UI 日志、轮询快照
**对话**：节点上的草稿区消息；orchestrator 把对话决策为 workflow；产物沉淀为节点后清空。
_Avoid_: 会话记忆、长上下文
**Artifact**：按 SHA-256 寻址的不可变产物。
_Avoid_: 裸路径、覆盖写
**执行凭据**：step 的完整执行描述与结果：image、command、files、seed、limits、退出码、输出哈希。
_Avoid_: 日志片段、口头复现
**能力包**：可分发的环境能力单元：提示词段、工具、skill、MCP 白名单、可选 Dockerfile 基座。
_Avoid_: 插件
**能力库**：能力包的集合，按领域组织，供装配者选用；内置项目方认为必要的基础包。
**装配者**：按项目问题从能力库选择能力包的 meta-agent；装配决策经同一双审门准入。
_Avoid_: 调度器
**装配**：执行单元启动时固定并写入执行凭据的能力清单；运行中新增能力 = 新装配 + 新执行单元。
_Avoid_: 动态挂载、热插拔
**钉入**：人或 orchestrator 按节点 id 把节点内容注入某次派发的上下文。
_Avoid_: 检索回填、RAG
**渐进披露**：能力集与图谱内容默认不进上下文，按查询语义按需展开；披露粒度是装配与钉入的参数。
_Avoid_: 全量投喂
## Harness
**Session**：一个角色的有状态执行上下文；消息历史持久化，进程重启后可继续。
_Avoid_: 对话、线程
**Turn**：一次 prompt 驱动的 Session 执行，终态为 completed、limit 或 error；超限与工具异常都不抛栈。
_Avoid_: 请求、重试
**Trace**：Session 内模型与工具交互的 append-only jsonl 事实流；评测与排障只读 Trace，不读进程日志。
_Avoid_: 日志、Workflow event
**Benchmark**：冻结的 case 集合与结构化打分（完成率、轮次、token、耗时）；不用 LLM judge。
_Avoid_: 测试、评估
**Webhook 工具**：实现由调用方持有、harness 以 HTTP 回调调用的工具；文件工具由 harness 内建，不回调。
_Avoid_: 插件、本地函数
