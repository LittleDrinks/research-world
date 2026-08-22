# 实现与 ADR 差距

基线：`5d35e8e`。规格出处：`docs/adr/0017-research-world-redesign.md`（0017）、`docs/adr/0018-endpoints-and-harness.md`（端点）、`docs/adr/0020-graph-and-evidence.md`（图谱）、`docs/adr/0021-review-pipeline.md`（管线）。

对应 issue：G1=#12 G2=#13 G3=#14 G4=#15 G5=#16 G7=#18 G8=#19 G10=#21 G11=#22 G12=#23 G13=#24 G14=#25 G15=#26（github.com/LittleDrinks/ai4sci）。

## G1 review 无原子断言审计
规格：claim 是审计单位而非节点；review 启动时把 direction 主张文本与 experiment 结果文本拆成逐条原子断言，审计结果回写状态机与极性边（0017 数据模型）。
现状：`workflows.py:335-339` REVIEW_PROMPT 只对整体要 decision/quality/diversity/rebuttal，全库无断言拆分逻辑。
处置：review 前置断言拆分步，逐断言判定后聚合回写。

## G2 查重重合候选的「转 reflect/合并」是空头文案
规格：余弦 >0.8 转 reflect/合并并渐进披露阻断理由（0017）；披露重合点新建反思会话（管线·分离盲创与反思）。
现状：`workflows.py:147-151` 只把候选 ghost 化，驳回理由字符串自称「已阻断并转入 reflect/合并」，无对应逻辑、无反思会话。
处置：重合候选进反思会话，携带相似节点切片与最小阻断理由。

## G3 reflect 新 direction 挂在 experiment 下
规格：reflect 产新 direction 候选挂父 direction 下、同谱系（0017）。
现状：`workflows.py:269` `parent_id=experiment["id"]`，图谱上 direction 变成 experiment 的子节点。
处置：parent_id 改父 direction id。

## G4 图谱 supports/refutes 边方向渲染反转
规格：边带极性，证据指向结论（0017 数据模型）。
现状：服务端建边 experiment→direction（`workflows.py:247,250`）；前端 `MapPage.jsx:96-99` orientEvidence 在 source 的 parent 是 target 时反转，supports 画成 direction→experiment，语义反向。
处置：删反转逻辑，按极性语义渲染。

## G5 活动流行内摘要兜底为 raw JSON
规格：活动轨迹按 Duration/Turns/Calls、TOOL/ASSISTANT 行呈现（0017 三视图）。
现状：`ActivityPage.jsx:124-129` eventSummary 兜底把整个 payload JSON.stringify 塞进行内摘要；reviewer 与 tool_result 两类高频事件不命中任何已知键。
处置：为 reviewer/tool_result 事件加摘要映射；原文收进展开视图。

## G7 节点上下文面板平铺无分组
现状：`ChatPage.jsx:85-89` NodeRail 全量平铺（实测 48 条），ghost 仅淡化仍混入；ContextPane 平铺 payload 全字段。
处置：按类型分组、ghost 默认收起、当前谱系置顶。

## G8 PATCH life_state 可一步 admitted
规格：人与 agent 经同一命令接口创建待审节点，人工提交不跳过审核（管线·人机共用节点提交接口）。
现状：`app.py:118-119` UPDATE_KEYS 含 life_state，人工 PATCH 即 admitted；人工创建的 pending 节点无审核准入路径。
处置：life_state 移出 UPDATE_KEYS，人工节点走与 brainstorm 候选相同的双审准入。

## G10 执行凭据未接入活路径
规格：结果审核检查输入边界、代码、环境、日志与产物哈希，以规范化内容哈希复跑（管线·分离执行、结果审核与评分）。
现状：`artifacts.py` 依赖 schema 没有的表且无调用方；活路径 RunnerClient→runner-controller 无产物哈希、replay 校验和输入边界检查，只有 exit_code==0。
处置：删除 `artifacts.py`；执行凭据与产物哈希直接进入活路径。

## G11 规划一次提交全部步骤、步骤执行前无审核
规格：规划一次只提交一个候选行动，行动经独立审核后原子且幂等地创建一次执行（管线·规划产生行动，行动触发执行）。
现状：PLAN_PROMPT 一次要 steps 列表全量落库（`workflows.py:180-181`），步骤执行前无审核。
处置：逐步「提交-审核-执行」，或修订 ADR 说明整计划一次过的理由。

## G12 双审是同 prompt 跑两次
规格：机制重合审核与执行有效性审核分开；执行、结果审核与评分分离（管线）。
现状：`_double_review` 同一 REVIEW_PROMPT 跑两次（`workflows.py:216-228`），decision/quality/diversity 同一次调用返回。
处置：按审核维度拆分调用。

## G13 驳回内容不参与查重、阻断理由无披露路径
规格：被驳回内容保留为隔离记录，只在后续入图审核时用于相似性匹配；执行 agent 只收到最小阻断理由（管线·入图前审核）。
现状：brainstorm 查重显式排除 ghost（`workflows.py:130`）；无任何路径把阻断理由发给执行/规划 agent。
处置：查重候选池纳入 ghost（仅相似性匹配）；阻断理由进 brainstorm/reflect 上下文。

## G14 无端点实体、凭证越界
规格：模型服务为端点实体，agent 绑定端点；模型凭证只进 harness 容器（端点）。
现状：`MODEL_API_KEY` 同时挂给 control 与 worker（`compose.yaml:7-8,30-31`）；worker 的 embedding 直连模型端点绕开 harness（`workflows.py:312-317`）；无端点实体与容灾。
处置：embedding 移入 harness 或经 harness 代理；凭证从 control/worker 摘除。端点实体化另议。

## G15 节点对话与主对话职责重叠（待决策）
规格：地图右侧栏为带节点上下文的轻量对话；对话页定位 orchestrator（0017 三视图）。实现两者并存。
问题：右下角节点对话是否过度设计——保留（围绕节点的轻讨论）还是删除（对话只走主对话页、节点面板只读）？删除需同步修订 0017。
