# Research World
围绕单个科学问题积累可审核、可复现、可追溯的研究对象与 Agent 工作过程。
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
**Artifact**：Project 内按内容寻址的不可变产物；由 Research Graph 节点引用。
_Avoid_: 裸路径、覆盖写
**Claim**：由 Source、Experiment 或 Artifact 支持、削弱或反驳的可审核陈述；报告只使用具有证据闭包的 Claim。
_Avoid_: Claim 节点、Direction 等于结论
**证据关系**：Research Graph 中连接研究对象的 `supports`、`refutes`、`depends_on` 等关系；关系不把 Direction 自动变成结论。
**撤销**：主 Agent 或人类因来源失效、模型复核等原因，使一个 Research Graph 节点及其依赖后继不再可用的级联操作；执行前展示影响范围并显式确认。
_Avoid_: 静默删除、改写历史
**Graph CLI**：主 Agent 与人类读写或撤销 Research Graph 的命令接口；不理解审核策略。
**双审**：主 Agent Skill/prompt 中的两个独立审查步骤；完整意见留在相应 Agent Trajectory，主 Agent 决定是否调用 Graph CLI。
_Avoid_: 图谱状态机、强制数据库 Gate
**Agent Runtime**：一个 Agent 从启动到结束的全流程生命周期，包含 model、API、harness、Tools 与执行环境。
_Avoid_: Endpoint、模型服务、传输协议
**Session**：一次 Agent 对话的上下文。
_Avoid_: Thread、研究事实
**Trajectory**：一个 Agent 的工作日志，包含模型输出、Tool Call、Tool I/O、父子 Session 关系与结束原因。
_Avoid_: Trace、Research event
**Summary**：正常结束的 Agent 在其 Trajectory 最后一段输出的工作摘要；主 Agent 默认读取该末尾窗口，按需展开完整 Trajectory。异常结束时读取结束原因和 Trajectory 尾窗；Summary 不直接成为 Research Graph 事实。
_Avoid_: Handoff 实体、Outcome 实体
**Workflow**：主 Agent 依据 Research Graph、Trajectory 与 Summary 动态编排 Child Agent 的过程；可以继续、复审、并行探索或转向，不具有固定 Pipeline、Stage 或状态机。
_Avoid_: Pipeline run、Research Round
**主 Agent**：对一个 Workflow 作全局方向与写图决定的 Agent。
**Child Agent**：由主 Agent 为一个方向、审查或操作启动的 Agent；没有固定角色或生命周期模板。
**AgentSpec**：启动一个 Agent Runtime 所需的 Runtime、Endpoint、模型、Instructions、Skills、Tool id 与执行参数声明；启动时快照。
**Tool**：科研人员为 Agent 选择的稳定能力；一个 Tool 可向模型展开多个 operation，AgentSpec 只保存 Tool id。
**Tool Adapter**：Agent Runtime 内部把本地函数、MCP、CLI、浏览器、数据库或计算设施投影为 Tool 的可插拔实现；位置、协议、生命周期、配置与凭证不越过 Agent Runtime。
**Preset**：可复用的 AgentSpec 草稿；保存后不随 Preset 漂移。
**识别**：Runtime 枚举当前可选择的 Endpoint、Skill 与 Tool；AgentSpec 只能引用识别结果，缺失或未就绪能力阻止 Launch。
