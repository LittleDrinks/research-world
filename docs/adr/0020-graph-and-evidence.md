# 图谱与证据

## 以复现代替原始对话留存
Agent 原始对话轨迹沉淀到图谱后默认丢弃；计算实验保留代码、输入、配置、随机种子与产物哈希，质疑经独立 agent 确定性重跑处理，重跑差异与原结果并存；湿实验保留完整原始证据。依据：[HEP](https://arxiv.org/abs/2607.09195) 把假设和证据写成可回放事件，[held-out transfer](https://arxiv.org/abs/2607.17100) 以冻结产物做独立评测；[中间 token 不是忠实推理证据](https://arxiv.org/abs/2504.09762)，[工业研究记录](https://arxiv.org/abs/2608.05235)与 [agent-native 产物](https://arxiv.org/abs/2604.24658)都以证据链而非逐字会话支撑结论。

## 入图后轮换执行上下文
请求由临时工作会话执行，产出交独立 agent 审核；通过后写入图谱并删除原会话，退修只回最小审核意见，重开由新会话依据图谱和最小驳回理由继续。同一会话对自身产物的再解释仍是[内源纠错](https://arxiv.org/abs/2310.01798)；[长程记忆](https://arxiv.org/abs/2605.12493)以按问题取回的紧凑证据为接口；[轨迹蒸馏可能与结果脱节](https://aclanthology.org/2026.acl-long.1686/)。

## 审查视图按需派生
图谱是唯一持久真源；审查视图从选定快照确定性生成状态分面、异常列表、ID 查找、依赖子图与失效影响范围，每个值能回到产生它的节点或事件，自由文本模型只解释查询结果。[PROV](https://www.w3.org/TR/prov-dm/) 把事实定义为可查询关系，[Trrack](https://doi.org/10.1109/vis47514.2020.00030) 把溯源聚合为交互界面，[Workflow Cards](https://arxiv.org/abs/2608.11022) 压缩执行记录，[TRACE](https://arxiv.org/abs/2608.09153) 把失败归因回上下文组件。

## 系统拥有节点身份
Agent 只提交内容，系统对规范化内容生成不可变 UID：同内容映射同身份，UID 只表达内容身份、不推断语义重合。[JSON 规范化](https://www.rfc-editor.org/rfc/rfc8785.html)给出稳定字节表示，[安全哈希](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf)给出内容身份，[PROV](https://www.w3.org/TR/prov-dm/) 把"同一对象"与派生关系分开表示。

## 事实入图谱，审核程序入 Skill
人工纠正具体事实时新增带来源、绑定 claim/resource 的图谱证据，规划与执行 agent 不默认读取；只有可跨事实复用的检查步骤进入全局 Skill。[SciFact](https://aclanthology.org/2020.emnlp-main.609/) 把证据句绑定到具体主张，[SciFact-Open](https://doi.org/10.18653/v1/2022.findings-emnlp.347) 显示证据覆盖随语料变化。

## 时间与因果分离
审查分别呈现最早异常、关键根因和下游影响：时间线定位顺序，依赖图计算失效传播，不共用一个排序分数。[AgentRx](https://arxiv.org/abs/2602.02475) 的根因标注显示首个异常、关键根因和最终失败可以不同。
