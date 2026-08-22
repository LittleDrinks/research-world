算力资源与存储资源：`ssh smYuHangLab2; cd /data/zsm/ai4s/`，连不上先提醒接校园网。
# 项目状态
## 产品
- 一个 project 一张研究图谱：节点四类（question/source/direction/experiment），life state pending→admitted|ghost，direction 状态机 proposed→supported|refuted，边带 supports/refutes 极性。
- pipeline 是 stage 序列，不固定 kind；执行原语为 prompt/tool/spawn，policy 修饰算法，on 路由图谱状态；双审分歧升级人工，同谱系连败 2 次暂停 auto 并升级。
- 对话属于 project 下的 Thread；节点通过 `@node_id` 引用并钉入上下文，不拥有对话；ResearchRun 以内嵌引用进入消息，execution 下钻 runtime trace。
- UI：PlanWeave 风格设计系统（oklch 语义状态色 selected/running/blocked/failed/warning/success 各带 surface 变体、Geist Variable 字体、卡片节点带状态徽章、轻玻璃顶栏）；/projects 卡片页、图谱主屏（幽灵车道展示驳回轨迹）、节点对话、活动页；全量中文；前端记忆 active project（localStorage，硬刷新不丢）。
- 两个深模块：Research Kernel 拥有图谱、Thread、Pipeline、科研日志与评价；Agent Runtime 拥有凭证、能力识别、Session 与 Trace。外部动作只有识别、启动、发送、检查、向量化。
- compose 服务：control(8095)/worker/runtime(8098)/runner-controller(8096)；实验步由 runner-controller 按 Dockerfile hash 起一次性容器（cpus/memory/pids 限额）。
- 模型服务端点实体由 Runtime 持有；control/worker 无模型凭证，embedding 经 Runtime。
## 待修/卫生
- AgentSpec、Skill 与 MCP 尚未接入正式执行路径；gpt-5.4-mini 注册残留在旧数据卷，随库重建消除。
- .agents/skills 整目录未被 git 跟踪，skills-lock.json 未含 agent 四件套。
- bootstrap 无 project_id 时回退到最旧项目（projects[0]=q001）；前端已用 localStorage 规避，服务端默认顺序未改。
- 反思级联无界：auto 下 reflect 新方向准入即自动派生研究工作流，会持续消耗 token；125 题跑批需预算闸门（见下一步）。
- QA 留痕：web/scripts/qa-full-flow.mjs（Playwright 驱动真实 UI 走全流程，支持 QA_TITLE 续跑）；证据在 web/qa-results/（已 gitignore）。
- 界面选型原型：prototype/kimi/（10 套整套 UI，路由 /prototype/kimi?v=01..10，截图在 prototype/kimi/shots/，运行 cd research-world/web && npm run dev；依赖 web/node_modules 软链与 vite fs.allow 上探两级）。
## 约束
- 基座必须 Qwen。截止 2026-09-05，交付：125 题轻量结果（每题一 project）+ 5 深度题演示 + ≤20 页 PPT/PDF + 源码 + 可运行入口。
- 300 元学生券自领取起一年有效；放量前先小额验证 Qwen chat 与 text-embedding-v4 并核对券抵扣。
- API 凭证在仓库根 .env（小写 apikey/baseurl），research-world/.env 为软链；服务一律 docker compose 启动。
- 测试环境：4×A5000（24GB×4）+ 800GB 磁盘；8×80GB 任务不可全规模。
## 下一步
- 以 ADR 0026 的五个接口替换 harness；AgentSpec 只引用 Runtime 识别出的模型、Skill、Tool 与 MCP。
- 125 题跑批：每题一 project，token 走学生券，注意预算。
- 5 个深度演示题：Q49 行星轨道（JPL 星历人工返回）、Q89 能量转换效率（Matbench 链）、Q21 抗生素耐药（SciFact 链）、Q112 环保塑料（真湿实验返回，立即启动首批制片）、Q98 睡眠（Sleep-EDF+手表返回，立即启动佩戴）；备选 Q110/Q32。
- RSI（ADR 0023）与 benchmark 扩展后置。评测证据账本只在 benchmarks/README.md。
