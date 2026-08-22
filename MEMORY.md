算力资源与存储资源：`ssh smYuHangLab2; cd /data/zsm/ai4s/`，连不上先提醒接校园网。
# 项目状态
## 产品
- 一个 project 一张研究图谱：节点四类（question/source/direction/experiment），life state pending→admitted|ghost，direction 状态机 proposed→supported|refuted，边带 supports/refutes 极性。
- pipeline 是 stage 序列，不固定 kind；执行原语为 prompt/tool/spawn，policy 修饰算法，on 路由图谱状态；双审分歧升级人工，同谱系连败 2 次暂停 auto 并升级。
- 对话属于 project 下的 Thread；节点通过 `@node_id` 引用并钉入上下文，不拥有对话；ResearchRun 以内嵌引用进入消息，execution 下钻 runtime trace。
- UI：正式 Web 已迁入 `/projects`、地图/科研日志、Thread 对话、五层轨迹、Agent、设置；左栏上部是一列大模块，下部是当前模块记录，左下保留项目设置与切换；前端用 localStorage 记忆 active project。
- 两个深模块：Research Kernel 拥有图谱、Thread、Pipeline、科研日志与评价；Agent Runtime 拥有凭证、能力识别、Session 与 Trace。外部动作只有识别、启动、发送、检查、向量化。
- compose 服务：control(8095)/worker/runtime(8098)/runner-controller(8096)；实验步由 runner-controller 按 Dockerfile hash 起一次性容器（cpus/memory/pids 限额）。
- running run 以 30 秒租约认领，worker 每 5 秒续租；stage 按节点、审查、计划写检查点，runtime session 与实验 execution 用稳定操作 ID 恢复。
- 模型服务端点实体由 Runtime 持有；control/worker 无模型凭证，embedding 经 Runtime。
## 待修/卫生
- gpt-5.4-mini 注册残留在旧数据卷，随库重建消除。
- .agents/skills 整目录未被 git 跟踪，skills-lock.json 未含 agent 四件套。
- bootstrap 无 project_id 时回退到最旧项目（projects[0]=q001）；前端已用 localStorage 规避，服务端默认顺序未改。
- 反思级联无界：auto 下 reflect 新方向准入即自动派生 research run，会持续消耗 token；125 题跑批需预算闸门（见下一步）。
- Q49、Q89、Q21 已从正式 UI 完成项目创建、节点钉入、真实对话、brainstorm、轨迹返回、地图与科研日志；Q21 在 review 阶段强杀 worker 后恢复同一 run，9 个 runtime session 全部可读，4 个方向入图且无重复；Q21 的跨容器共享 `/tmp` 计划经人工驳回后暂停 run、ghost experiment，不改变 direction 且不产生证据边；Q89 research 负路径以 3 次容器执行复现量纲错误，双审拒绝实验并写入 refutes 边后暂停谱系。
- 界面选型原型：prototype/kimi/（10 套整套 UI，路由 /prototype/kimi?v=01..10，截图在 prototype/kimi/shots/，运行 cd research-world/web && npm run dev；依赖 web/node_modules 软链与 vite fs.allow 上探两级）。
## 约束
- 基座必须 Qwen。截止 2026-09-05，交付：125 题轻量结果（每题一 project）+ 5 深度题演示 + ≤20 页 PPT/PDF + 源码 + 可运行入口。
- 300 元学生券自领取起一年有效；放量前先小额验证 Qwen chat 与 text-embedding-v4 并核对券抵扣。
- API 凭证在仓库根 .env（小写 apikey/baseurl），research-world/.env 为软链；服务一律 docker compose 启动。
- 测试环境：4×A5000（24GB×4）+ 800GB 磁盘；8×80GB 任务不可全规模。
## 下一步
- 125 题：每题一 project，由多 Agent 分组逐题启动、处理人工闸门并验收至少 4 个方向节点；不使用后台批处理脚本。
- 深度演示题：补完 Q49 JPL、Q89 Matbench 的 research pipeline；再做 Q21 SciFact、Q112 湿实验返回、Q98 Sleep-EDF+手表返回；备选 Q110/Q32。
- RSI（ADR 0023）与 benchmark 扩展后置。评测证据账本只在 benchmarks/README.md。
