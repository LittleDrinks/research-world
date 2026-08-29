# 自主研究的审查带宽
## 问题
研究 Agent 能在数天内产生远超人类逐条审查能力的候选、实验和争论。线性对话把规划、证据、执行、错误和修订混在一起；运行越久，阅读成本和上下文噪声越高。研究者无法快速回答：这段时间发现了什么、尝试了哪些不同方向、失败在哪里、下一步做什么、上游错误影响了哪些结论。
长对话不是可靠记忆。无关历史挤占推理空间，错误经验会锁死搜索，完整披露会诱导局部修补；直接丢弃又会遗漏条件。Agent 的生成速度把任何延迟审查放大成下游污染，事后阅读几十 MB Trace 不能成为控制手段。
## 使用场景
一个 Project 推进一个科学问题。主 Agent 可并行委派 Child Agent 提出方向、执行实验、复现结果和独立审查；人类处理冲突、不确定结果与高风险决定。125 个问题用于广度与 OOD 覆盖，5 个选题用于深度演示；不同问题不共享一张 Research Graph。
研究者先看到一个时间窗口内的增量：新增 Direction、已完成 Experiment、被否定路线、待执行行动和异常。每项内容可逐层展开到依赖、原始证据、代码、环境、Artifact 与 Trace；质疑上游内容时，系统给出受影响的后续对象。
## 核心矛盾
- 研究吞吐需要继续增长，人工审查负担不能随 Trace 长度线性增长。
- 持久信息必须足够支持复现和追责，又不能把未审核噪声当作报告结论。
- 历史需要防止重复错误，又不能默认约束独立搜索。
- 研究结果允许不确定和冲突，系统不能把审核伪装成自动发现真理。
- 证据形态从文本、文献和代码扩展到图像、表格、日志、仪器读数与湿实验记录，保留强度取决于可复现成本。
## 产品边界
- Research Kernel 保存 Project、Session、Artifact、Research Graph 记录与关系及 LocalMap；Runtime 保存 Run、Turn、Trace、Skills、Tools、delegation、Runtime Adapters 与 Agent 执行快照（Adapter、model、instructions、skills、tools、params）。原始对话是 Session，Tool Call 和 Tool I/O 是 Trace，二者不复制入 Research Graph。
- Session 是用户可读对话来源；用户消息先持久化，主 Agent 最终回答再投影到对应消息。Runtime Submit 与 Subscribe 分离，断线重连只读取指定 Turn 的既有事件，不重复执行。
- 每个 Turn 冻结所属 Run 先前的终态上下文；并发 Turn 的回答固定归位到各自的起始用户消息。主 Agent 通过 Runtime Delegation 创建 Child Agent Run；Child Agent 可通过 Kernel Interface 读写 Research Graph 记录与关系，但不直接写用户 Session。
- 主 Agent 与人类可调用 Graph CLI；复核是 Agent 或人的行为，没有强制数据库准入 Gate 或图谱状态机。删除记录时移除直接关系并保留关联 Artifact，删除关系不影响记录。
- LocalMap 由 Kernel 直接按 Project 隔离、文本或节点引用和数量限制检索；MMR 是由 Brainstorm Skill 选择调用的确定性 Runtime Tool operation。
- 计算实验保留代码、输入、配置、环境、随机种子与不可变 Artifact；难以重跑的实验保留完整证据。
- 错误 Source 或关系由主 Agent 或人类直接删除；删除记录时移除直接关系，关联 Artifact 保留，后续判断通过新的记录和证据表达。
- 不建立全局方法 taxonomy 或固定失败类型。机制关系是带来源、可冲突的局部判断；审查视图从 Research Graph 按需派生。
- 不把 125 个问题混成一张图，不把界面节点数当作阅读成本，不以单一总分定义研究价值。
## 设计原则
最大化研究员对 Agent 系统的掌控：可读性（研究地图和 Trace）、可玩性（能力装配）、便捷性（领域内置），服务对象是不同领域的研究员。
## 成功条件
- 研究者无需阅读完整 Trace 即可通过 Summary 或异常结束的 Trace 尾窗说明本周期新增方向、关键失败、待办和影响范围，并能展开到支撑证据。
- 任一报告 Claim 都能回到关联的 Source、Experiment 或 Artifact；未审核 Direction 不被写成结论。
- 已保存的研究对象足以继续规划、独立复现和质疑；原始 Trace 仍可回放，不默认进入 Research Graph 检索。
- 错误上游 Source 被删除时，其直接关系可确定性移除，关联 Artifact 保留；后续判断不依赖模型重新阅读历史猜测。
- 研究成本同时报告机制覆盖、执行有效性、审查冲突、人工时间、计算与 Token；参数微调不能冒充新方向。
## 未决问题
- 低置信度 Research Graph 查询是否自动触发一次有预算上限的外部检索，或必须由人确认。
- 真人在原始 Trace、研究地图、研究地图加独立 Agent 预审三种条件下的正确率、时间和盲从风险。
- 计算实验跨硬件复现差异与湿实验不可重复结果的升级裁决边界。
