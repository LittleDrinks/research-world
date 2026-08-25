---
sources:
  - id: phoenix-project-session-traces
    title: "Phoenix project and session trace listing"
    url: https://arize.com/docs/phoenix/sdk-api-reference/rest-api/api-reference/traces/list-traces-for-a-project
---
# Trace 上下文导航
Chat 的研究运行入口只显示紧凑的运行数量并导航到 Trace，不在 composer 内展开运行内容。
入口 URL 携带 `project_id`、`thread_id` 与完整 `from` 路径；Trace 浏览页和 run 详情页都按 `project_id` 与 `payload.thread_id` 过滤 Pipeline run。
Trace 列表与详情复用当前 Project 的 bootstrap 运行投影，不建立第二套查询组件或业务接口；列表项打开既有 run、stage、session、turn、tool 详情树。
详情页从 `from` 路径返回原 Thread；没有上下文的全局 Trace 入口只按当前 Project 展示运行，不伪造 Thread 归属。
