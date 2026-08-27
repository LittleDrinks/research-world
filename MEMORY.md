# 项目状态
## 产品
- 首要交付是挑战杯材料，个人研究工具是后续持续产品。
- Research Kernel 只拥有 Fact Graph 与 Graph CLI；Graph CLI 查询、写入、删除节点和关系。
- 主 Agent 动态编排 Workflow；审核是可委派 Skill，不是图谱准入或固定双审。
- Agent Runtime 是一个 Agent 的完整生命周期；Session 是会话上下文；Trajectory 记录对话、工具调用与子 Agent 工作过程。
- Pipeline run 是交付投影；两个有序切点形成 V1/V2 比较，不规定研究流程。
## 交付
- 研发最多三天，余下时间用于真实运行、证据整理和提交。
- 125 个 Project 与五个深度案例需使用同一冻结路径运行；案例不代替 125 题结果。
- 优先选择可观察的小问题、熟悉的 CS 问题或有官方指标的 benchmark Project。
## 运行
- 服务只用 `research-world/` 下 `docker compose up --build -d` 启动。
- 凭证在仓库根 `.env`，键名为 `apikey`、`baseurl`。
