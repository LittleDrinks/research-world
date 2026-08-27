# Research World
围绕单个科学问题积累可审核、可复现、可追溯的研究状态。
## Language
**Project**：一个科学问题及其研究状态；id 是稳定、不承载业务语义的标识符。
_Avoid_: 课题、任务
**Q001–Q125 Project corpus**：用于展示系统研究状态的固定科学问题集合；“125 问”与“《Science》125 个前沿科学问题”均指此集合。
_Avoid_: Benchmark
**Fact Graph**：Project 的可变研究记忆，保存问题、来源、方向、实验及其关系；内容可以被 Graph CLI 写入或删除。
_Avoid_: 只读证据库、工作流状态机
**Research Kernel**：Fact Graph 及其 Graph CLI；不拥有审核策略、Workflow 状态或 Agent 生命周期。
_Avoid_: 唯一准入门、编排器、CRUD 层
**Graph CLI**：Research Kernel 对 Agent 暴露的查询、写入、删除节点与关系的工具集；每次调用记录在发起 Agent 的 Trajectory。
_Avoid_: 准入审核、状态转换
**节点**：图谱内容单元，固定四类：question / source / direction / experiment；实验结果并入 experiment 负载。
_Avoid_: brief、result、setup 节点类型
**Claim**：节点负载中的可审核陈述；结论为 supported / refuted / uncertain，不是节点。
_Avoid_: claim 节点
**Direction**：待检验的研究方向；可由证据关系支持或反驳，不带强制状态机。
_Avoid_: 准入状态、终态
**证据链**：source / experiment、关联 Artifact 与指向 Direction 的 supports / refutes 关系，共同构成对 Direction 的支持或反驳。
_Avoid_: Evidence 节点、Evidence 实体
**Artifact**：Project 内按 SHA-256 寻址的不可变产物；相同哈希不产生跨 Project 可见性。
_Avoid_: 裸路径、覆盖写
**审核 Skill**：主 Agent 可委派的审阅能力，返回意见、依据和不确定性；结论是编排输入，不改变图谱写入权限。
_Avoid_: 强制双审、准入 Gate
**Workflow**：主 Agent 围绕一个 Project 动态编排的子 Agent 工作；可并行探索、复核已有输出或沿反馈换方向。
_Avoid_: 固定 stage 序列、状态机
**Pipeline run**：主 Agent 一次 Project 工作的交付投影，引用选定的 lead / child Trajectory；它只服务编号、版本比较和报告，不是执行对象、Session 或 Agent Runtime。
_Avoid_: Research Round、固定 Pipeline、运行实例
**研究版本**：同一 Project 中两个有次序 Pipeline run 的确定性对比投影；V1 / V2 只标记比较切点，不拥有节点或事实。
_Avoid_: Research Round、可变报告草稿
**Thread**：Project 下的人机对话入口，只保存 Session 引用；节点可通过 `@node_id` 引用和钉入，节点不拥有对话。
_Avoid_: 节点消息表、草稿区
**报告投影**：从指定 Fact Graph 快照、关联 Artifact 与选择的 Pipeline run 切点确定性生成的交付输入。
_Avoid_: Agent 自报事实、跨表拼装
**AgentSpec**：模型、API、harness、Instructions、Skills、Tool id 与执行参数的启动声明；启动时编译为 Runtime 快照。
_Avoid_: 能力装配模块、动态挂载
**Tool**：科研人员为 Agent 选择的稳定能力；一个 Tool 可向模型展开多个 operation，AgentSpec 只保存 Tool id。
_Avoid_: Connector、MCP server、transport、模型函数名
**Tool Adapter**：Agent Runtime 内部把本地函数、MCP、CLI、浏览器、数据库或计算设施投影为 Tool 的可插拔实现；位置、协议、生命周期、配置与凭证不越过 Runtime seam。
_Avoid_: Kernel 专用后端、前端 transport 表单
**Preset**：可复用的 AgentSpec 草稿；引用 Tool id，不拥有安装、配置或执行逻辑，保存后不随 Preset 漂移。
_Avoid_: 第二套 Agent 配置、隐式安装
**识别**：Agent Runtime 枚举工作区当前可选择的 Endpoint、Skill 与 Tool；AgentSpec 只能引用识别结果，缺失或未就绪能力阻止 Launch。
_Avoid_: 手填 Endpoint、手填 Skill、手填 transport
**渐进披露**：Skill 与节点正文默认不进入模型上下文；Agent 调用读取工具后，读取结果才进入 Session 与 Trajectory。
_Avoid_: 全量投喂、字符串拼接钉入
## Agent Runtime
**Agent Runtime**：一个 Agent 从启动到结束的完整生命周期，拥有模型、API、harness、能力快照、Session 与 Trajectory。
_Avoid_: 可复用 provider 类型、Endpoint
**Session**：一个 Agent 的会话上下文。
_Avoid_: 运行实例、消息数据库、Thread
**Trajectory**：一个 Agent Runtime 的完整工作过程，按发生顺序记录模型输入输出、工具调用、子 Agent 启动及结果。
_Avoid_: Trace、科研事实、进程日志
**Turn**：Session 中一次 prompt 驱动的连续工作。
_Avoid_: HTTP 请求、重试
**Launch**：启动一个 Agent Runtime 并创建其 Session 的原语；主 Agent 可用它动态委派子 Agent。
_Avoid_: 固定 stage 入口
