---
sources:
  - id: acp-python
    title: Agent Client Protocol Python SDK
    url: https://github.com/agentclientprotocol/python-sdk
  - id: dsh-architecture
    title: DeepSeek Harness architecture
    url: https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md
  - id: penguin-traces
    title: Penguin Harness sessions and traces
    url: https://github.com/Prism-Shadow/penguin-harness
---
# Agent Runtime
系统只有两个深模块：Research Kernel 拥有项目、事实图谱、Thread、Pipeline 与评价；Agent Runtime 拥有 Agent 执行、模型凭证、能力识别、Session 与 Trace。Pipeline 解释和评价不进入 Runtime；它们通过相同的 Agent Runtime 接口启动普通 Session。
## 外部接口
| 动作 | 输入 | 输出 | ACP 映射 |
|---|---|---|---|
| 识别 | workspace | 可用 Runtime、Endpoint、模型、Skill、Tool 及 readiness | `runtime/discover` extension |
| 准备 Tool | workspace、tool_id、action、values | 更新后的 Tool 状态 | `runtime/tools/prepare` extension |
| 启动 | AgentSpec、workspace、parent、mode | session_id | `runtime/launch` extension |
| 发送 | session_id、内容块 | 实时 session update、终止原因 | `session/prompt` |
| 检查 | session_id | 从 Trace 投影的消息、Turn、Tool 树 | `runtime/inspect` extension |
| 向量化 | endpoint、texts | vectors | `runtime/embed` extension |
ACP Python SDK 负责连接、schema 与 HTTP/WebSocket 传输。Web 通过 Research Kernel 使用同一 ACP Client；Runtime 不暴露第二套 REST 会话协议。
## 内部所有权
`runtimes`、`endpoints`、`skills`、`tools`、`trace` 分别管理对应 catalog、生命周期与事实；`acp` 只翻译外部协议。外部调用方不感知这些目录。
Codex CLI adapter 只对 `0.149.1` ready；Runtime image 固定官方 `@openai/codex@0.149.1`，其他可解析版本以 `version_incompatible` 进入 unsupported，直到其 JSONL contract 被重新审计。它在 Runtime 内部使用 `codex exec --json`，不是新的外部边界。
Codex JSONL 只接受审计过的 `0.149.1` 单一 `thread.started → turn.started → item lifecycle* → terminal turn`；terminal 后第二个 turn、悬挂 item 与未知事件均拒绝。terminal 只有带完整非负 `input_tokens`、`cached_input_tokens`、`cache_write_input_tokens`、`output_tokens`、`reasoning_output_tokens` 的 `turn.completed`，或带 message 的 `turn.failed`；top-level `error` 只能由 failed terminal 收束。item 必须是完整且已知的 `agent_message`、`reasoning`、`command_execution`、`file_change`、`mcp_tool_call`、`collab_tool_call`、`web_search`、`todo_list` 或 `error` payload；`web_search` 只接受与 item `query` 相同的 query-only `search` 动作，可选 `queries` 也只含该值。`agent_message`、`reasoning`、`file_change`、`error` 只可 completed；`todo_list` 可 `started → updated* → completed`；其余可 `started → completed`，id 与 type 不变，terminal 前不得悬挂。每个接受的 item event 先作结构化脱敏，再以 `provider_item` Trace event 与 provider thread id 同 turn 持久化；failed terminal 以 `provider_terminal` 保存，inspect 从这些事件重建 item/tool 树。Trace JSONL 和 public projection 都不含凭据字段、Authorization/Bearer、cookies、DSN、URL userinfo/query secret、workspace、Codex home、路径、URI 或 Runtime continuation metadata；failed item 与 failed turn 保留为脱敏事实，但 failed stream 不产生 assistant response。`codex exec --json` 以缓冲方式收集，未实现增量输出时不声明 `streaming`。每个 version 或 login candidate 从创建开始至清理和 reader join 共享五秒 wall-time budget；stdout、stderr 各最多保留 16 KiB，超时或超出 budget 均终止整个进程组，reader join 不得越过剩余 budget；即使 leader 已退出，仍杀死其进程组并等待 reader 结束。version probe 使用只含固定 locale 与 PATH 的 child environment；login probe 另加临时受限 auth view，所有 Codex child process 都不继承宿主配置、MCP、插件、规则、Runtime API 凭据、endpoint、proxy 或其他 host secret。provider thread id 只在 `completed` 或 `limit` Runtime turn 的 `turn_end` 后写入受限 session state；取消、错误和未结束 turn 不写入或改变 resume。Runtime 凭据 store 只提供 `auth.json`；Session 在 `sessions/<session_id>/codex-home` 获得 mode `0600` 的 auth copy 与 mode `0700` home。Runtime-owned session state store 以受限权限持久保存 workspace、Codex home、Runtime binding、executable identity 和 continuation binding，供重启后的 continuation 使用；它不是 Trace，不参与 inspect 或模型事实。当前接口不删除 Session，因而不声明清理 durable state。Launch 冻结 Runtime Adapter、Endpoint、model、AgentSpec、精确 capability snapshot 和仅 Runtime 私有的稳定 Codex executable identity；新 Runtime 恢复 identity 不同即拒绝，catalog 与 capability snapshot 继续不包含路径或 identity。Codex native shell capability is disabled; Codex CLI sessions with selected Runtime Tools are rejected because this adapter does not forward Tool operations. Native capability is never a Tool.
Codex 只接受已声明 `openai-compatible` adapter 的逻辑 Endpoint 和归属 chat model；它们不提供 CLI transport 或凭证。普通 Runtime 只接受其声明 adapter 的 Endpoint。ACP 省略 AgentSpec 时，按 Runtime catalog 顺序、再按 Endpoint priority/id 和其首个 model 选择首个合格 pair，不经 `RuntimePool.default()`；process-owned Codex 取首个已声明兼容 chat Endpoint，`available` 不参与选择，其他 Runtime 只取 `available` Endpoint。无 pair 直接失败。公开 prompt result、`model_response` 和每一个 `turn_end` 均含且只含 `input_tokens`、`cached_input_tokens`、`cache_write_input_tokens`、`output_tokens`、`reasoning_output_tokens`，取消和错误为零。JSONL 收集前已知和本次返回的每个 continuation 值在任何 emit、ModelResult、Trace 或 inspect 之前从结构字段值、嵌套 object key 与独立文本出现处脱敏；key collision 保留全部脱敏值且不泄露原 key。只在完成或达上限后写入 `0600` 私有 state。缓存 binding 在每次 prompt 前重验冻结 Codex executable identity；不同即失败。缺失、无模型或不兼容的显式声明直接失败，不生成、保留、推断 Endpoint，也不 fallback。
Runtime、Endpoint 与 Model 是独立声明；Endpoint id 不承载 Runtime 或 provider 语义，Runtime 不由 Endpoint 推断。Launch 以声明 Runtime 的 endpoint adapter 兼容性和该 Endpoint 的 model ownership 校验三者；realm、adapter 或 model 不符均直接失败，不跨 adapter fallback。Codex 对 credentialless `openai-compatible` logical Endpoint 的例外只放宽 Endpoint readiness，不依赖或保留特定 Endpoint id。
Runtime adapter compatibility 是非空显式 adapter 集合；空集不兼容任何 Endpoint，Endpoint configuration 缺失或空 adapter 无效，EndpointPool 不提供默认 Endpoint。embedding 只在可用且有 provider 的 Endpoint 调用，否则返回 controlled unavailable。Runtime image 固定官方 `@openai/codex@0.149.1-linux-x64` 包中的 native `vendor/x86_64-unknown-linux-musl/bin/codex`，不保留 Node 或 `codex.js` 执行链。Codex 在 discovery 时打开并冻结 native executable；probe、launch、resume 与 identity recheck 均通过同一已打开对象执行，路径替换不能改变后续 child。Codex child PATH 只含受信任系统目录，不继承宿主 PATH。
collector 在公开边界前从已知 parent、`thread.started.thread_id` 及官方 `collab_tool_call.sender_thread_id`、`receiver_thread_ids`、`agents_states` 的 key 学习全部 continuation id；每个学到的 id 都在字段值、嵌套 key 和文本中脱敏，碰撞键保留全部脱敏值。`agents_states[*].message` 保留普通协作状态文本。raw continuation 只走私有 transport 到受限 state，ModelResult、emit、message、Trace 和 inspect 都不携带它。
## Tool Runtime
Tool Runtime 是 Agent Runtime 内部深模块。AgentSpec、Preset、设置页与 orchestrator 只理解稳定 Tool id；Adapter kind、operation 名称、MCP、HTTP、SSE、stdio、CLI、数据库驱动、位置、进程生命周期、凭证与依赖配方全部隐藏。
`catalog(workspace)` 返回 Tool id、名称、描述、来源、`ready | setup_required | unavailable` 状态及声明式安装或配置动作，不返回 URL、command、args、header、env 名或 secret。`prepare(workspace, tool_id, action, values)` 只执行目录声明的受控动作，不接受任意安装命令。宿主 GPU 驱动和外部数据库权限只检测并报告。
`open(tool_ids, context)` 解析全部 Tool、冻结 Adapter revision 与模型可见 operation schema，再返回 Session 级调用句柄；缺失、冲突、未就绪或定义漂移均硬失败，不部分启动、不 fallback。一个 Tool 可展开多个 operation，模型函数名由 Runtime 编码，AgentSpec 与 Trace 使用稳定 Tool id。
内部 `ToolAdapter.inspect/open` 与 `BoundAdapter.invoke/close` seam 复用内置函数、MCP、Lean4、浏览器、数据库、GPU 与环境实现。Adapter 返回规范化内容块、错误和 Artifact/observation 草稿，不持有 Kernel client；Tool Runtime 负责参数校验、超时、取消、错误分类、脱敏与结果大小限制，再通过 Kernel port 登记 Artifact/observation。
官方 Preset 的轻量依赖固定进 Runtime 镜像；浏览器、数据库与 GPU 等重依赖使用 Compose 中受控服务或 profile；不在运行时执行任意 `pip`、`npm` 或 shell 安装。MCP SDK、`httpx`、JSON Schema 与各设施官方客户端继续负责协议实现。
官方 `lean4` Tool 固定 Lean 与 mathlib `v4.33.1` 到无凭证 sandbox image。Catalog 只检查本地 image readiness；安装由 Provisioner 在用户确认后执行，Compose 启动、Preset 与 Session 不安装或启动 Lean。Runtime Adapter 只向 Runner port 提交固定 image、固定 command、源码与资源限制；Runner 禁止隐式 pull，以无网络、只读根、只读输入、临时目录及 CPU、内存、进程和 wall-time 限制执行。`verify(source)` 返回结构化诊断，`sorry` 和 warning 均视为未通过；源码由统一 Artifact capture seam 入库，模型只看结果摘要与 Artifact id。
## Session 与 Trace
Trace 是 Session 的唯一模型事实源，不建消息数据库。凡进入模型的内容都写入 Trace；凭证、授权头、私有环境变量、workspace、Codex home 与 continuation binding 永不写入。inspect 保留 token budget 和 input/output token 用量。事件为 `session_meta`、`turn_start`、`model_request`、`model_response`、`provider_item`、`provider_terminal`、`tool_call`、`tool_result`、`child_session`、`turn_end`、`error`。
每条事件编码成单行 JSON 后一次写入；读取时丢弃断裂尾行并截断到最后一条完整记录。UI 投影只重放 Trace；Runtime restart 从受限 session state store 恢复执行绑定。
Thread 只在 Research Kernel 保存 `project_id + session_id` 指针。新建 Thread 启动新 Session；归档 Thread 不删除 Trace。
Project 创建只接收名称与研究问题；Research Kernel 在受控 projects 根目录内分配 workspace，Web 不提交文件系统路径。
## Pipeline Run
PipelineSpec 由 Research Kernel 从 YAML 识别并校验。数据库只保存 `pipeline_id + definition_snapshot`，没有固定 kind；模板修改不影响在途 run。AgentSpec Instructions 只保存跨任务稳定的角色约束，prompt stage 保存本次操作契约；prompt stage 的 `agent` 引用已保存 AgentSpec，Research Kernel 不临时改写 Runtime、Endpoint、模型、Skill 或 Tool。启动时将完整 AgentSpec 交给 Runtime 快照。run event 只记录 stage、gate、人工决策与 session_id，模型消息和工具细节留在 Runtime Trace。
## 渐进披露
Skill 与节点正文默认不进入模型请求。模型只看到名称、描述和 `@node_id`；调用 `read_skill` 或 `read_resource` 后，读取结果才进入 Trace 与后续模型请求。只有 AgentSpec 选择的 Tool operation schema 对模型可见。
报告工具只请求 Research Kernel 的报告投影、BibTeX 导出与交付校验。Endpoint 可用性由 Kernel 查询 Runtime 识别结果后推导，Agent 和 HTTP 调用方不能自报。
