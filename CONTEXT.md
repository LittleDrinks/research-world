# Research World
围绕单个科学问题积累可审核、可复现、可追溯的研究状态。
## Ownership
**Research Kernel（研究内核）**：Project 研究状态的唯一所有者，拥有 Project、Session、Message、Artifact、Record、Relation 与 LocalMap；不拥有 Agent 执行事实。
**Runtime**：Agent 执行的唯一所有者，拥有 Run、Turn、Trace、Skill、Tool、委派、Runtime Adapter 与执行快照；不拥有模型访问配置、Session、Project、Artifact 或 Research Graph 记录。
**Research World 设置 facade**：Web 与 Penguin 之间只转发模型设置操作（测试、保存、掩码读取、替换与清除）；不负责对话协调，不持久模型访问配置，不拥有 Penguin token。
**Penguin**：Runtime 使用的独立模型服务进程，持久拥有部署级模型访问配置及其原生 JSON/SSE 协议和 bearer token 生命周期；Runtime 是唯一外部调用方。
**对话协调**：服务器组合层将用户消息写入 Session、提交 Turn，并将主 Agent 终态回答投影回同一消息；不拥有 Project、Run 或 Trace。
## Language
**协作学习者**：正在从零学习本项目技术栈的项目决策者；讲解以已验证路径由粗到细展开，直到能说明各模块职责。
_Avoid_: 默认技术读者、终端用户
**Git 分支**：同一代码仓库的独立版本线；架构讨论只以当前工作目录检出的分支为事实源。
_Avoid_: 谱系、研究分支
**Project**：Research Kernel 管理的最小研究容器，包含一个科学问题及其研究状态；id 是稳定、不承载业务语义的标识符。
_Avoid_: 课题、任务
**Q001-Q125 Project corpus**：用于展示系统研究状态的固定科学问题集合；“125 问”与“《Science》125 个前沿科学问题”均指此集合。
_Avoid_: Benchmark
**Record**：Research Kernel 中可直接记录、检索和关联的研究对象；MVP 固定为 question、source、direction、experiment 四类，实验结果进入 experiment 内容。
**Research Graph（研究图谱）**：Research Kernel 在 Project 内由 Record、Relation 与关联 Artifact 构成的研究状态；不包含 Session 对话或 Runtime Trace。
**Relation**：同一 Project 中两个 Record 之间的有向关联。
**Artifact**：Research Kernel 管理的 Project 内按 SHA-256 寻址的不可变 Agent 产物；MVP 中协作学习者可查看和下载，不从浏览器上传。
_Avoid_: 裸路径、覆盖写、跨 Project 可见性
**Claim**：Record 内容中的可审核陈述；由 Source、Experiment 或 Artifact 支持、削弱或反驳，不是独立 Record。
_Avoid_: Claim 节点、Direction 等于结论
**证据关系**：连接 Record 的 `supports`、`refutes`、`depends_on` 等关系；关系不把 Direction 自动变成结论。
**复核**：人或 Agent 基于 LocalMap 检查 Record 或 Relation；发现错误时调用 Remove，不形成写入门或持久审核状态。
_Avoid_: 准入、pending、双审 Gate
**Kernel Interface**：Research Kernel 的公共接口，覆盖 Project、Session、Message、Artifact、Record、Connect、Remove 与 LocalMap；调用方不接触 SQLite、文件路径、表名或检索实现。
**Connect**：Kernel 将同一 Project 中已存在的 Record 以有效关系类型相连。
**Remove**：Kernel 移除 Record 或 Relation；移除 Record 时一并移除其直接 Relation，但保留关联 Artifact。
**LocalMap**：Kernel 按 Project 隔离、数量限制和 LocalMap Query 即时取得的匹配 Record、直接 Relation 与关联 Artifact 投影，不是第二张持久图。
**LocalMap Query**：一次 LocalMap 读取的领域输入，二选一为非空文本或 Record 引用，并带正整数数量限制；不携带 SQL、Cypher、表名或相似度参数。
**词法候选检索（闭环阶段）**：逐条执行不区分大小写的子串匹配，用于先完成 MVP 功能闭环；不计算 Embedding 或余弦相似度。
**Embedding**：模型把文本表示为数字向量，可比较意思接近程度，但不能证明两段文本陈述同一事实。
**语义候选检索（MVP 效果项）**：功能闭环通过后，以 Embedding 替换词法候选路径；只返回候选，不自动拒绝、合并或删除 Record，不保留双检索路径。
**MMR Tool operation**：Brainstorm Skill 可调用的确定性 Runtime Tool operation，用于从候选中选择多样内容；不承担 LocalMap 检索、写入或正确性判定。
**Session**：Project 下用户可读的一段主 Agent 对话；浏览器生成的稳定 `session_id` 是创建重试的幂等键，一个 Project 可有多个 Session，Runtime 为每个 Session 关联独立主 Run。Session 保存用户消息和与其 Turn 配对的主 Agent 最终回答，回答固定在对应用户消息之后，不因完成顺序改变；不持有 Adapter 绑定、原生 harness 状态或 Trace。
_Avoid_: Thread、执行 Session、节点消息表
**Message**：Research Kernel 在 Session 中保存的一条用户消息及其可选的主 Agent 最终回答；`message_id` 是稳定标识，Runtime 只按它关联 Submit 与已有 Turn，并持久校验一个 Message 只能归属一个 Session；Child Run 的 Message 不绑定 Session。
**Agent**：可被启动并完成工作的助手定义；MVP 只有一个协作学习者可见的主 Agent 配置，包含角色提示词、选中的 Skill 与 Tool。创建 Session 时提交配置，Runtime 在 Launch 时冻结执行快照；修改配置创建新 Session。Agent 不持有模型访问配置或 Runtime Adapter 绑定。
_Avoid_: Research Graph 节点、可变持久 Agent、模型配置
**主 Agent**：唯一直接与协作学习者对话的 Agent；理解意图、给出回应，并决定是否委派工作。
**Subagent**：主 Agent 为明确工作目标启动的 Agent；拥有独立 Run，可通过 Kernel Interface 读写 Research Graph，完成后把结果交回主 Agent，不写 Session，也不直接替代主 Agent 对话。
**Child Run**：Runtime 为 Subagent 委派创建、只通过 parent Run 关联的执行 Run；它表示 Runtime 的父子执行关系，不是另一种 Agent 名称。
**Child Turn**：Child Run 上的一次 Turn；其终态通过 `child_result` 关联回父 Turn，不写 Session。
**委派 (Delegate)**：主 Agent 向 Runtime 提交目标与必要上下文，由 Runtime 创建 Subagent 并把结果关联回父 Turn 的行为。
**Skill**：Runtime 内可选择的可复用 Agent 行为声明；可选择调用 Tool operation。
**Tool**：科研人员为 Agent 选择的稳定能力；一个 Tool 可向模型展开多个 operation，Agent 只保存 Tool id。
_Avoid_: Connector、MCP server、transport、模型函数名
**Tool Adapter**：Runtime 内部把本地函数、MCP、CLI、浏览器、数据库或计算设施投影为 Tool 的可插拔实现；位置、协议、生命周期、配置与凭证不越过 Runtime。
**Preset**：可复用的 Agent 草稿；引用 Tool id，不拥有安装、配置或执行逻辑，保存后不随 Preset 漂移。
**识别**：Runtime 枚举当前可选择的 Runtime Adapter、Skill 与 Tool；缺失或未就绪能力阻止 Launch。
## Agent Runtime
**Runtime Adapter**：Runtime 内部适配一种执行 harness 的同级实现，封装模型调用与 harness 配置。它只识别、启动、提交、取消和产生规范化事件；Run 恢复、Trace 持久化、上下文快照、委派与重连由 Runtime 负责。
_Avoid_: Runtime、Tool Adapter、用户自定义命令
**执行域**：Runtime Adapter 实际使用 harness 的操作系统进程环境；本机执行域复用协作学习者已有 CLI，托管执行域由 Runtime 管理连接与协议，harness 进程由 Runtime 直接管理或由 Compose 作为固定服务管理。
**Pi Adapter（开发期）**：只在本机执行域复用已安装的 Pi 及其设置，用于主机端到端确认；不进入 Docker 交付，也不构成 MVP 可用性门槛。
**Penguin Harness Adapter（Docker/MVP 默认）**：Compose 管理固定 Penguin Server 进程与 readiness，Runtime Adapter 只封装 Penguin 原生 HTTP/SSE、Penguin Session 与 Task 映射；模型访问配置由 Penguin 持久化，Penguin bearer token 不进入 Agent、Session、Trace、control 或 Web；Web password input 的明文 apikey 仅按明确请求暂存。
**模型访问配置**：部署级设置，包含 provider、model id、baseurl 与 apikey；Research World 设置 facade 只转发测试、保存、掩码读取、替换与清除，Penguin 是唯一持久所有者；明文 apikey 可短暂进入 Web password input 和明确的测试、保存或替换请求；请求结束即清空，不持久化或返回到其他边界；不随 Project、Session、Agent、Run、Turn 或 Trace 复制。
**Adapter 绑定**：Runtime 为 Run 选择并冻结的 Runtime Adapter；主 Agent 与 Subagent 的执行均基于绑定，失败不静默切换。
**Adapter 原生身份**：Runtime Adapter 为 Run 提供的当前 identifier-only JSON 恢复标识，形状固定为 `{"session_id": 非空字符串}`；Runtime 按 Adapter 归属在 Run 中一次性持久化，相同值重复绑定幂等，冲突绑定拒绝；只经 TurnRequest 传给所属 Adapter，不进入 Trace、Run public view、Kernel 或浏览器。
**Run**：Agent 及其 Adapter 绑定的持续执行上下文；Runtime 唯一维护主 Agent Run 与一个 Session 的关联，Subagent Run 只关联父 Run。一个 Run 可同时承载多个活跃 Turn，包含执行快照、原生 harness 续接状态与 Trace。
**Turn**：一次 Run 执行；创建时冻结该 Run 已终态的上下文，即终态事件持久化位次先于该 Turn 起始位次的 completed 与 limit 结果，按提交序；其他活跃 Turn 的输入和生成内容不进入该快照。每个 Turn 都有独立的 Adapter 执行句柄，事件、取消和终态均按 Turn 标识关联，终态为 completed、limit、cancelled 或 error。
**输入提交 (Submit)**：对话协调将用户消息持久化后，Runtime 根据 Session 找到或启动主 Agent Run，并为该消息创建 Turn；浏览器不选择或传递 Run id。完成创建后立即返回 Turn 标识，不等待或承载流式事件。
**事件订阅 (Subscribe)**：从指定 Turn 的 Trace 读取已发生及后续的规范化事件；断线后可重新订阅，不创建输入或新的 Turn。
**取消 (Cancel)**：只终止指定 Turn；关闭事件订阅不取消 Turn。
**Server-Sent Events (SSE)**：Server 通过长期 HTTP GET 向浏览器单向推送事件；浏览器为每个活跃 Turn 使用独立 EventSource，每条事件的 `id` 对应 Trace `seq`，自动重连从最后收到的序号继续。
**Trace**：模型可见消息、Tool 交互、Adapter 事件与父子 Run 关系的追加式执行事实流；每条事件关联一个 Turn，不是用户对话或 Research Graph 事实。持久化事件表是一条 append-only 因果日志，已提交位次从 1 开始完整连续；恢复校验在单一读事务内对照 SQLite 持久分配状态证明无缺口。
_Avoid_: 进程日志、Research event、Session
**Launch**：Runtime 创建 Run 的启动原语；协作学习者启动主 Agent，主 Agent 通过 Delegate 启动 Subagent。
