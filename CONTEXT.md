# Research World
围绕单个科学问题积累可审核、可复现、可追溯的研究状态。
## Language
**Project**：一个科学问题及其研究状态；id 是稳定、不承载业务语义的标识符。
_Avoid_: 课题、任务
**Research Kernel**：项目研究状态的唯一写入门；解释 commands、queries 与 Pipeline，内部拥有图谱、准入、运行和投影。
_Avoid_: World 服务、CRUD 层
**节点**：图谱内容单元，固定四类：question / source / direction / experiment；实验结果并入 experiment 负载，claim 是审计单位不是节点。
_Avoid_: brief、result、setup 节点类型
**节点标题**：Pipeline 创建节点时 Agent 生成的简洁标题，与完整正文分开存于 payload；硬上限 12 token，Kernel 拒绝缺失、空白、非字符串或超限标题，不截断、不合成、不回退正文。
_Avoid_: 占位标题、正文截取
**准入**：提交节点时强制执行的审核过程；先形成 pending 候选，纯策略可立即给出结论，默认策略不裁决，由 Research Kernel 显式裁决为 admitted 或 ghost。
_Avoid_: 数据库 before-save hook、可绕过校验
**Life state**：节点准入状态：pending（仅准入审核可见，不能生长依赖）→ admitted（通过）或 ghost（驳回隔离）。
_Avoid_: 保存、发布、删除
**幽灵节点**：ghost 态节点，带驳回理由与抗辩，隔离留存，只在后续审核时做相似性匹配。
_Avoid_: 删除、隐藏
**Direction 状态机**：direction 的论证状态：proposed → supported | refuted，终态不可逆。
**谱系**：同一血脉（lineage_id）的节点链；同一谱系连续 2 次审核驳回触发 auto 暂停并升级人工。
_Avoid_: 分支、会话树
**Pipeline**：Research Kernel 解释的 stage 序列；stage 只执行 prompt / tool / spawn，policy 修饰算法，on 处理出口。
_Avoid_: 固定 workflow kind、任务、job
**Stage**：Pipeline 的最小执行单元；每个 prompt stage 启动干净 Session，只接收结构化上游引用。
_Avoid_: 长对话续跑
**双审**：两个独立 reviewer 一致 approve 才准入；分歧时 Pipeline run 转 waiting_human 由人裁决。
_Avoid_: 打分、多数投票
**抗辩**：双审意见按 reviewer 沉淀在节点 rebuttal 字段，随节点留存。
**Research event**：Research Kernel 写入的稀疏项目事实：Pipeline、Stage、Gate、节点与人工决策；科研日志是其投影。
_Avoid_: 模型消息、工具细节
**Thread**：Project 下的人机对话入口，只保存 Runtime session 指针；只有 admitted 节点可通过 `@node_id` 引用和钉入，节点不拥有对话。
_Avoid_: 节点消息表、草稿区
**Artifact**：Project 内按 SHA-256 寻址的不可变产物；相同哈希不产生跨 Project 可见性。
_Avoid_: 裸路径、覆盖写
**SourceCandidate**：文献研究 Pipeline 的结构化候选，携带书目元数据、检索谱系、与 Direction 的用途和全文 Artifact 描述；不是节点，只有 Research Kernel 提交准入后才形成 pending source。
_Avoid_: Research Round、Evidence node、Tool 直接写图
**报告投影**：Research Kernel 从 admitted claim、source 与关联 Artifact 确定性生成的交付输入。
_Avoid_: 跨表拼装、Agent 自报事实
**执行凭据**：step 的完整执行描述与结果：image、command、files、seed、limits、退出码、输出哈希。
_Avoid_: 日志片段、口头复现
**AgentSpec**：Endpoint、模型、Instructions、Skills、Tool id 与执行参数的声明；启动时编译并快照。
_Avoid_: 能力装配模块、动态挂载
**Tool**：科研人员为 Agent 选择的稳定能力；一个 Tool 可向模型展开多个 operation，AgentSpec 只保存 Tool id。
_Avoid_: Connector、MCP server、transport、模型函数名
**Tool Adapter**：Agent Runtime 内部把本地函数、MCP、CLI、浏览器、数据库或计算设施投影为 Tool 的可插拔实现；位置、协议、生命周期、配置与凭证不越过 Runtime seam。
_Avoid_: Kernel 专用后端、Pipeline 特判、前端 transport 表单
**Preset**：可复用的 AgentSpec 草稿；引用 Tool id，不拥有安装、配置或执行逻辑，保存后不随 Preset 漂移。
_Avoid_: 第二套 Agent 配置、隐式安装
**识别**：Runtime 枚举工作区当前可选择的 Endpoint、Skill 与 Tool；AgentSpec 只能引用识别结果，缺失或未就绪能力阻止 Launch。
_Avoid_: 手填 Endpoint、手填 Skill、手填 transport
**渐进披露**：Skill 与节点正文默认不进入模型请求；模型调用读取工具后才进入 Trace。
_Avoid_: 全量投喂、字符串拼接钉入
## Agent Runtime
**Session**：AgentSpec 的一次运行实例；Trace 是其唯一事实源。
_Avoid_: 消息数据库、Thread
**Turn**：一次 prompt 驱动的 Session 执行，终态为 completed、limit、cancelled 或 error。
_Avoid_: HTTP 请求、重试
**Trace**：模型可见消息、工具交互与父子 Session 关系的 append-only JSONL 事实流。
_Avoid_: 进程日志、Research event
**Launch**：人、Stage 与 Agent 共用的 Session 启动原语。
_Avoid_: workflow 专用执行入口
**评价**：Research Kernel 用冻结 case 启动普通 Session 并对 Trace/产物确定性打分；不是 Runtime 子模块。
