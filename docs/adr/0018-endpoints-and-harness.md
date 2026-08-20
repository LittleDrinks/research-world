# 端点与 harness

## 模型服务为端点实体
同一模型的多个端点按优先级容灾，agent 绑定端点而非模型名；本地 SDK 注册为 runtime 按 capability 派工。演示与提交链路只用 Qwen 端点，OpenAI 兼容端点只作开发对照。[千问调用](https://help.aliyun.com/zh/model-studio/first-api-call-to-qwen)需要同时确定模型 ID、host、鉴权与[可用模型集合](https://help.aliyun.com/zh/model-studio/models)，模型名不能表达这些运行边界；[兼容接口不等于完整运行能力](https://arxiv.org/abs/2605.12493)。

## 执行内核独立为 harness 服务
执行内核从 research-world 进程内拆为独立 HTTP 服务（`harness/`）：有状态 session/turn 契约、fs+webhook 工具协议、append-only trace、SQLite 持久化与结构化评测。worker 经 `HARNESS_URL` 调用；webhook 工具实现由调用方持有，harness 以 HTTP 回调分发，按执行单元签发 Bearer 任务 token；embedding 客户端与 harness 各自持有模型凭证，凭证不进图谱存储。[Harness 可靠性是模型外的运行边界](https://arxiv.org/abs/2604.25850)，[端到端科研基准要求可重复执行环境](https://arxiv.org/abs/2606.07591)，[容器边界隔离凭证与控制平面](https://csrc.nist.gov/pubs/sp/800/190/final)。已知限制：benchmark 并发执行的 trace seq 追加竞态，需要时先换文件锁再开并行。
