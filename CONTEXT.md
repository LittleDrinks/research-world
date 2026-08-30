# Research World
围绕单个科学问题积累可审核、可复现、可追溯的研究对象与 Agent 工作过程。
## Ownership
**Research Kernel（研究内核）**：Project 研究状态的唯一所有者，拥有 Project、Session、Artifact、Research Graph 记录与关系以及 LocalMap；不拥有 Agent 执行事实。
**Runtime**：Agent 执行的唯一所有者，拥有 Run、Turn、Trace、Skills、Tools、delegation、Runtime Adapters 及 Agent 执行快照（Adapter、model、instructions、skills、tools、params）；不拥有 Session、Project、Artifact 或 Research Graph 记录。
## Language
**Project**：一个科学问题及其研究状态；id 是稳定、不承载业务语义的标识符。
_Avoid_: 课题、任务
**Q001-Q125 Project corpus**：用于展示系统研究状态的固定科学问题集合；“125 问”与“《Science》125 个前沿科学问题”均指此集合。
_Avoid_: Benchmark
**Research Graph（研究图谱）**：Project 的长期研究对象图，保存 Question、Source、Direction、Experiment、Artifact 及它们的证据和依赖关系；不保存原始 Agent 对话或 Tool Call。
_Avoid_: Fact Graph、事实图谱、Research Kernel
**研究地图**：Research Graph 的可视化投影。
_Avoid_: Research Graph（页面名称）
**Question**：Research Graph 中定义研究对象、范围与约束的节点。
**Source**：Research Graph 中描述一份外部资料及其可用范围的节点。
**Direction**：Research Graph 中记录待探索解释、路线或反例的节点；不是已证实结论。
**Experiment**：Research Graph 中记录一次可复查研究操作及其结果的节点。
**Graph record（图谱记录）**：Research Graph 中可直接记录、检索和关联的研究对象。
**Artifact**：Project 内按内容寻址的不可变产物；由 Research Graph 节点引用。
_Avoid_: 裸路径、覆盖写
**Claim**：由 Source、Experiment 或 Artifact 支持、削弱或反驳的可审核陈述；报告只使用具有证据闭包的 Claim。
_Avoid_: Claim 节点、Direction 等于结论
**证据关系**：Research Graph 中连接研究对象的 `supports`、`refutes`、`depends_on` 等关系；关系不把 Direction 自动变成结论。
**删除**：主 Agent 或人类对错误 Research Graph 记录或关系的直接移除；删除记录时移除其直接关系，关联 Artifact 保留。
_Avoid_: 撤销、审核 Gate、静默改写
**Graph CLI**：主 Agent 与人类读写或删除 Research Graph 的命令接口；不理解审核策略。
**LocalMap**：Kernel 按 Project 隔离、数量限制和文本或节点引用查询得到的局部图投影，包含匹配记录、直接关系和关联 Artifact。
**LocalMap Query**：一次 LocalMap 读取的领域输入，恰含一个非空文本或图谱记录引用与正整数数量限制。
**SQLite FTS5**：SQLite 提供的词法全文检索，用于候选检索；不是向量余弦语义检索。
**双审**：主 Agent Skill/prompt 中的两个独立审查步骤；完整意见留在相应 Agent Trace，主 Agent 决定是否调用 Graph CLI。
_Avoid_: 图谱状态机、强制数据库 Gate
**Session**：Project 下用户可读的对话，保存用户消息及主 Agent 的最终回答；它属于 Research Kernel，与 Runtime 的 Run、Trace 分离。
_Avoid_: Thread、Run、Trace、研究事实
**Run**：Runtime 中一次主 Agent 或 Child Agent 的执行生命周期；主 Agent Run 可关联一个 Kernel Session，Child Agent Run 只关联父 Run。
**Turn**：由一条已持久化用户消息触发的独立 Runtime 执行；创建时冻结该 Run 先前的终态上下文，并让并发回答始终归位到其起始用户消息下。
**Trace**：Runtime 按 Run 与 Turn 保存的追加式执行事实，包含模型、Tool、Adapter 和结束事件；不承担用户可读 Session 或 Research Graph 事实。
_Avoid_: Trajectory、Research event
**Summary**：正常结束的 Agent 在其 Trace 尾部输出的工作摘要；主 Agent 默认读取该窗口，按需展开完整 Trace。异常结束时读取结束原因和 Trace 尾窗；Summary 不直接成为 Research Graph 事实。
_Avoid_: Handoff 实体、Outcome 实体
**Delegation**：主 Agent 为明确目标创建 Child Agent Run，并接收其结果的 Runtime 行为；Child Agent 不直接写入用户 Session。
**主 Agent**：直接与用户对话、决定研究方向、委派 Child Agent 并作出 Research Graph 写入决定的 Agent。
**Child Agent**：由主 Agent 通过 Delegation 启动、拥有独立 Run 的 Agent；可通过 Kernel Interface 读写 Research Graph 记录与关系，但不直接与用户对话或写入 Session。
**AgentSpec**：启动一个 Runtime Run 所需的 Runtime Adapter 绑定、模型、Instructions、Skills、Tool id 与执行参数声明；启动时快照。
**Skill**：Runtime 内可选择的可复用 Agent 行为声明；可选择调用 Tool operation。
**Tool**：Runtime 提供给 Agent 的稳定能力；一个 Tool 可向模型展开多个 operation，AgentSpec 只保存 Tool id。
**Runtime Adapter**：Runtime 内部负责识别、启动、提交、取消 Agent 执行并产生规范化事件的可插拔 Adapter；不越过 Runtime 边界持有 Kernel 数据。
**Adapter 执行句柄**：Adapter 为一个 Turn 返回、代表该 Turn 活跃执行的句柄；非 multiple-writers 的 Adapter 同时只允许一个活跃 Turn。
**Multiple writers**：Runtime Adapter 明确允许多个活跃 Turn 共享底层 harness 的能力；共享执行的取消必须携带目标 Turn 身份。
**Pi Adapter**：复用宿主机已安装 Pi、认证和偏好的 Runtime Adapter；只用于开发端到端验证，不进入 Docker 交付。
**Penguin Harness Adapter**：由 Runtime 直接启动、使用用户提供模型访问配置的 Runtime Adapter；与 Pi Adapter 同级，当前不提供实现或 fallback。
**Tool Adapter**：Runtime 内部把本地函数、MCP、CLI、浏览器、数据库或计算设施投影为 Tool 的可插拔实现；位置、协议、生命周期、配置与凭证不越过 Runtime。
**MMR**：由 Brainstorm Skill 选择调用的确定性 Runtime Tool operation，用于多样性选择，不承担 LocalMap 检索或自动合并。
**Preset**：可复用的 AgentSpec 草稿；保存后不随 Preset 漂移。
**识别**：Runtime 枚举当前可选择的 Runtime Adapter、Skill 与 Tool；AgentSpec 只能引用识别结果，缺失或未就绪能力阻止 Launch。
