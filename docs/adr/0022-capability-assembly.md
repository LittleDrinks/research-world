---
sources:
  - id: dsh
    title: "DeepSeek Harness"
    url: https://github.com/deepseek-ai/deepseek-harness
  - id: dsh-arch
    title: "dsh 架构文档"
    url: https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md
---
# 能力库与装配
环境能力打包为**能力包**（提示词段、工具、skill、MCP 白名单、可选 Dockerfile 基座），入**能力库**并内置项目方认为必要的基础包；**装配者**（meta-agent）按项目问题选包，**装配**清单在执行单元启动时固定、写入执行凭据；运行中确需新能力 = 新装配 + 新执行单元。装配决策经同一双审门准入。能力集固定但描述**渐进披露**：工具详情不进默认上下文，agent 按需查询；人或 orchestrator 按节点 id **钉入**图谱内容。
动机是研究员向的领域定制（可玩性、便捷性），不是防换基模——模型相关的防御性设计归入可替换的 skill/提示词资产。借 dsh 的 bundle/profile 分离与"模式=插件组合"思想 [dsh; dsh-arch]，不迁 runtime：v0.1 官方预告 breaking changes，交付前 20 天不换底座。
## Considered Options
- 运行中动态暴露工具：省 token，但工具集是执行凭据的一部分，中途变化使复现比较失效——拒绝；token 诉求由渐进披露解决。
- 每领域手写环境模板：125 题规模不可行，只作装配者的先验。
- 迁移 dsh 作为 runtime：引入预告 breaking changes 的 v0.1 依赖——拒绝，只移植设计思想。
## Consequences
- 项目间隔离为配置级（装配清单）；依赖级隔离沿用 runner-controller 的 Dockerfile hash 镜像，不做 per-project venv。
- 装配落在 harness Session 级（tools + prompt_segments）；worker 每角色一次性 session 跑单轮，session 级即执行单元级。钉入由 worker 按节点 id 解析后拼进 prompt 上下文，harness 无钉入概念。
- 工具描述查询接口未做：v1 工具 schema 随 session 直接声明，描述清单由 control 的 GET /api/v1/library 提供；工具规模大到需要时再议。
- projects 表加 assembly 列，不迁移旧库：重建数据卷后项目由 projects/*/project.json 重新创建。
