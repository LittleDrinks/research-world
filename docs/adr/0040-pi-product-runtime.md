---
status: accepted
issue: 320
---
# Pi 科研工作台
Pi 是模型执行与工具循环的唯一 Runtime Adapter。采用 feat/156 的持久 Run/Turn 和 Research Graph，Session HTTP 接入浏览器；旧 ACP、Thread、Pipeline 与准入流程不再作为产品入口。
Agent 保存名称、模型、指令、thinking、Skills 和 Tools。启动 Session 时冻结 AgentSpec，编辑 Agent 只影响新 Session。模型和凭证来自 Runtime 私有 Pi 配置；界面与轨迹只返回模型标识。
主 Agent 通过显式工具桥查询和写入当前 Project 的图谱，可委派独立上下文子 Agent。子 Agent 仅有查询和文献能力，不能写图或再次委派；审查意见返回主 Agent，由主 Agent 决定写入 Direction 或 Experiment。Tool 选择在桥接服务端验证，Project 从 Session 绑定，不由模型指定。
运行日志持久保存事件，流式 HTTP 只是投影。控制面刷新时从 Runtime 回读终态并更新 Session 消息；断开浏览器连接不取消研究工作。取消显式作用于当前 Turn。
历史赛题与评测证据保留。旧产品架构说明和状态清单删除，Git 历史承担历史查阅；非流程说明只留本地并忽略；运行入口由 Compose 与可执行测试维护。
局部地图查询省略筛选时返回当前 Project 的前 limit 个研究对象；text 和 record_id 互斥。
