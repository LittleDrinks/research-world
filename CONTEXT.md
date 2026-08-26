# Research World
围绕单个科学问题积累可审核、可复现、可追溯的研究状态。
## Language
**主品牌**：`“强国有我”思政案例库`；面向用户的应用名称，侧栏和项目选择页使用这一精确文本。
_Avoid_: Research World（应用主品牌）
**Project**：一个科学问题及其研究状态；id 是稳定、不承载业务语义的标识符。
_Avoid_: 课题、任务
**Q001–Q125 Project corpus**：用于展示系统研究状态的固定科学问题集合；“125 问”与“《Science》125 个前沿科学问题”均指此集合。
_Avoid_: Benchmark
**Research Kernel**：项目研究状态的唯一写入门；解释 commands、queries 与 Pipeline，内部拥有图谱、准入、运行和投影。
_Avoid_: World 服务、CRUD 层
**节点**：图谱内容单元，固定四类：question / source / direction / experiment；实验结果并入 experiment 负载。
_Avoid_: brief、result、setup 节点类型
**Claim**：节点负载中的可审核陈述；结论为 supported / refuted / uncertain，不是节点。
_Avoid_: claim 节点
**节点标题**：Pipeline 创建节点时 Agent 生成的简洁标题，与完整正文分开存于 payload；硬上限 12 token，Kernel 拒绝缺失、空白、非字符串或超限标题，不截断、不合成、不回退正文。
_Avoid_: 占位标题、正文截取
**准入**：提交节点时强制执行的审核过程；先形成 pending 候选，纯策略可立即给出结论，默认策略不裁决，由 Research Kernel 显式裁决为 admitted 或 ghost。
_Avoid_: 数据库 before-save hook、可绕过校验
**Life state**：节点准入状态：pending（仅准入审核可见，不能生长依赖）→ admitted（通过）或 ghost（驳回隔离）。
_Avoid_: 保存、发布、删除
**幽灵节点**：ghost 态节点，带驳回理由与抗辩，隔离留存，只在后续审核时做相似性匹配。
_Avoid_: 删除、隐藏
**Direction 状态机**：direction 的论证状态：proposed → supported | refuted，终态不可逆；证据不足时保持 proposed。
**谱系**：同一血脉（lineage_id）的节点链；同一谱系连续 2 次审核驳回触发 auto 暂停并升级人工。
_Avoid_: 分支、会话树
**Pipeline**：Research Kernel 解释的 stage 序列；stage 只执行 prompt / tool / spawn，policy 修饰算法，on 处理出口。
_Avoid_: 固定 workflow kind、任务、job
**Pipeline run**：Pipeline 的一次执行实例；按发生次序区分多次 run，不形成独立研究轮次。
_Avoid_: Research Round、轮次实体
**研究版本**：同一 Project 中两个有次序 Pipeline run 的确定性对比投影；V1 / V2 只标记比较次序，不拥有节点或事实。
_Avoid_: Research Round、可变报告草稿
**Auto**：Research Kernel 在冻结预算内根据证据与反馈选择并启动后续 Pipeline run 的控制策略；可暂停、恢复、停止，并以明确终止原因结束。
_Avoid_: 跳过确认的布尔值、无限 reflect 级联、无人批准高风险动作
**Auto 终止原因**：Auto 一次执行的唯一终态解释，区分目标完成、预算耗尽、无改进、人工介入、用户停止与失败。
_Avoid_: 最后一条日志、模型自报完成
**Stage**：Pipeline 的最小执行单元；每个 prompt stage 启动干净 Session，只接收结构化上游引用。
_Avoid_: 长对话续跑
**双审**：两个独立 reviewer 一致 approve 才准入；分歧时 Pipeline run 转 waiting_human 由人裁决。
_Avoid_: 打分、多数投票
**抗辩**：双审意见按 reviewer 沉淀在节点 rebuttal 字段，随节点留存。
**Research event**：Research Kernel 写入的稀疏项目事实：Pipeline、Stage、Gate、节点与人工决策；科研日志是其投影。
_Avoid_: 模型消息、工具细节
**Thread**：Project 下的人机对话入口，只保存 Runtime session 指针；只有 admitted 节点可通过 `@node_id` 引用和钉入，节点不拥有对话。
_Avoid_: 节点消息表、草稿区
**证据链**：admitted source / experiment、关联 Artifact 与指向 Direction 的 supports / refutes 关系，共同构成对 Direction 的支持或反驳。
_Avoid_: Evidence 节点、Evidence 实体
**Artifact**：Project 内按 SHA-256 寻址的不可变产物；相同哈希不产生跨 Project 可见性。
_Avoid_: 裸路径、覆盖写
**报告投影**：Research Kernel 从 admitted claim、source 与关联 Artifact 确定性生成的交付输入。
_Avoid_: 跨表拼装、Agent 自报事实
**执行凭据**：step 的完整执行描述与结果：image、command、files、seed、limits、退出码、输出哈希。
_Avoid_: 日志片段、口头复现
**AgentSpec**：Runtime、Endpoint、模型、Instructions、Skills、Tool id 与执行参数的声明；`runtime` 精确为 `{id: "codex", realm}`，不把 Endpoint 或模型当作 Runtime；启动时编译并快照全部声明。
_Avoid_: 能力装配模块、动态挂载
**Tool**：科研人员为 Agent 选择的稳定能力；一个 Tool 可向模型展开多个 operation，AgentSpec 只保存 Tool id。
_Avoid_: Connector、MCP server、transport、模型函数名
**Tool Adapter**：Agent Runtime 内部把本地函数、MCP、CLI、浏览器、数据库或计算设施投影为 Tool 的可插拔实现；位置、协议、生命周期、配置与凭证不越过 Runtime seam。
_Avoid_: Kernel 专用后端、Pipeline 特判、前端 transport 表单
**Preset**：可复用的 AgentSpec 草稿；引用 Tool id，不拥有安装、配置或执行逻辑，保存后不随 Preset 漂移。
_Avoid_: 第二套 Agent 配置、隐式安装
**识别**：Runtime 枚举工作区当前可选择的 Codex Runtime、Endpoint、Skill 与 Tool；公共结果只含安全状态、版本、来源与不可用原因，AgentSpec 只能精确引用识别结果，缺失或未就绪能力阻止保存与 Launch。
_Avoid_: 手填 Endpoint、手填 Skill、手填 transport
**渐进披露**：Skill 与节点正文默认不进入模型请求；模型调用读取工具后才进入 Trace。
_Avoid_: 全量投喂、字符串拼接钉入
## Agent Runtime
**Runtime**：执行 AgentSpec 的产品 Adapter 与 execution realm 稳定引用；本阶段只有 Codex Runtime，协议细节不越过 Agent Runtime seam。
_Avoid_: Endpoint、模型服务、传输协议
**Session**：AgentSpec 的一次运行实例；Trace 是其唯一事实源。
_Avoid_: 消息数据库、Thread
**Turn**：一次 prompt 驱动的 Session 执行，终态为 completed、limit、cancelled 或 error。
_Avoid_: HTTP 请求、重试
**Trace**：模型可见消息、工具交互与父子 Session 关系的 append-only JSONL 事实流。
_Avoid_: 进程日志、Research event
**Launch**：人、Stage 与 Agent 共用的 Session 启动原语。
_Avoid_: workflow 专用执行入口
**评价**：Research Kernel 用冻结 case 启动普通 Session 并对 Trace/产物确定性打分；不是 Runtime 子模块。
