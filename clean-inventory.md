---
issue: 303
parent: 302
base: 1e31789 (main, 2026-09-03)
scanned: 2026-09-03
scope: 只读扫描，1332 个 tracked 文件，~300M；未删未改任何文件
constraint: 全部删除动作等 tag `contest-2026-submission` 打点之后执行
---

# 仓库清洁扫描清单
## 目录树现状
```
ai4sci-wt-clean @ 1e31789（1332 tracked 文件，~300M）
├─ research-world/  24M/677  产品本体，compose 四服务 control/worker/runtime/runner-controller
│  ├─ evidence/     15M      contest-2026(8M,保护) + orbits-49-*(6.3M,README 引用) + 零散旧证据
│  ├─ web/          6.9M     前端；screenshots/ 5.9M 占 86%
│  ├─ projects/     1.0M     q001–q125 project.json（提交依赖）
│  └─ server+tests+worker+… 0.6M
├─ datasets/        251M     research-kernel-papers：references 242M + markdown 8.1M（#138 归档）
│                            + graphs 276K（旧 Research Kernel 实验产物）+ snapshots 424K（#139）
├─ prototype/       14M/218  9 组一次性 UI 原型（README 自述），最后改动 2026-08-24
├─ docs/            11M      adr 828K + benchmarks 68K + sjtu-booklet.pdf 8.1M + 模板 docx 1.3M(保护)
├─ runtime/         484K     ACP Agent Runtime 服务（compose + CI 在用）
├─ benchmarks/      496K     活跃账本 README + 20 个 benchmark 目录
├─ harness/         140K     独立 agent harness 服务（单 commit，未接线）
├─ screenshots/     360K     根级 2 张 map 截图（0 引用）
└─ 根文件                    AGENTS/CONTEXT/MEMORY/PROBLEM/readme/skills-lock + .github CI
```
## ① 建议删除
判定依据格式：最后改动 commit / 关联议题 / 与现行架构关系。无特别说明均等 tag 后执行。

| 路径 | 体积 | 判定依据 |
| --- | --- | --- |
| `harness/`（22 文件） | 140K | 唯一 commit feeb191（2026-08-20），此后零改动；不在 compose.yaml 服务、不在 .github/workflows/ci.yaml、全仓无 import（benchmarks/sedimentation_smoke 的 `from evaluation import harness` 是另一模块）。Agent Runtime 职责已由 `runtime/` 承担（ADR 0026）。⚠️ 需确认：benchmarks/README.md「harness 仪表链路」行（36 runs/54 sessions/255472 tokens）疑由本服务产生，删除前确认该行证据已归档 |
| `screenshots/`（根，2 文件） | 360K | a8402e4（2026-08-12「capture research world visual baseline」）；`map-music-*.png` 全仓 0 引用；web/screenshots 已有更全的 map 系列截图 |
| `research-world/web/screenshots/` 未引用的 28 个 png | 3.5M | 43 个中 15 个被 docs/agent-runtime-settings.md 引用（保留），其余 map-*/review-*/report-*/issue63-competitor-* 等 28 个 0 引用；QA 截图属已合并 issue 的一次性验证物 |
| `research-world/evidence/activity-desktop.png` + `activity-mobile.png` + `doctor.json` | 344K | 7bbcc35（2026-08-12「complete agent-native research execution and final evidence」）；0 引用；readme.md:55 只承认 `orbits-49-*` 为保留的历史证据，提交证据已由 contest-2026/ 取代 |
| `prototype/`（9 组，218 文件） | 14M | README 自述「一次性原型，用于回答设计问题」；最后改动 2026-08-24；对应 UI 均已在 research-world/web 实现。三组互为重复（dpskv4p/dpskv4vi/kimi 同为前端选型集）。⚠️ 两处牵连：ADR 0025 引用 kort-ai-ascii（删除需同步修订 ADR）；dpskv4p 依赖 docs/questions.json |
| `datasets/research-kernel-papers/graphs/` | 276K | 60 篇论文的反向分解图，语料 README 自述用于「验证同一 Research Kernel 能否表达不同研究模态」；Research Kernel 已被 Research Graph 取代（MEMORY.md，9dcab0b「narrow research graph supersession scope」）；references/markdown/manifest 部分保留（见 ③） |
| `docs/sjtu-booklet.pdf` | 8.1M | a8402e4（2026-08-12）；仅 prototype/research-world-readability.html 引用；未进 readme 提交链。若为组委会手册唯一本地副本需人工确认后外链替代 |
| `docs/implementation-gap.md`（41 行） | 4K | 822947e（2026-08-26）；issue 状态快照表，与 GitHub Issues（唯一活源）重复维护，基线停在 `07ea3e9`；readme 提交链不引用 |
| `research-world/web/src/prototype/` 未路由部分：`ConversationOrchestrationPrototype.jsx`、`MapAuthoringPrototype.jsx`、`chat-runtime-kimi/` | 220K | App.jsx 只路由 `prototype/agent-runtime`（32 行）；其余组件 0 引用；设计已实现进正式组件 |
| 死依赖：research-world/pyproject.toml 的 `python-dotenv`、`mcp`；web/package.json 的 `d3-force` | — | server/worker/Dockerfile/compose 对两者 0 import；web src 对 d3-force 0 引用（chat.css 命中为 `.failed` CSS 误报）；`mcp` 仅 runtime/ 使用，不该重复声明在 research-world。**勘误（review 307-R1）**：`markdown` 为活依赖——`scripts/build-results-site.py`（#293 结果站唯一构建路径）在用，pyproject 声明即为此，保留 |
| `docs/答疑-常见问题.md`（56 行） | 8K | a8402e4（2026-08-12）组委会/报名 FAQ 团队笔记；0 引用；依赖时点是报名答辩结束，非仅 tag |
## ② 建议合并/精简
| 对象 | 现状 | 建议 |
| --- | --- | --- |
| `docs/agent-runtime-settings.md`（206 行）+ web/screenshots/issue63-* 15 张（1.6M） | 24d97e0（issue 63 QA）；frontmatter `status: proposed`，正文一半是竞品调研（OpenDesign/Multica/CC-Switch 等 6 家截图）；issue 63 已关闭、功能已实现 | 把仍有效的 Runtime 设置设计约束压进 ADR 0022/0026 或删除整篇；竞品截图随文档一并处置 |
| `docs/design-explainer.html`（575 行，48K） | 6f684de（2026-08-20「固化研究图谱与执行架构决策」）；独立 HTML 宣传页，仅被 datasets 引用归档清单反向提及；内容与 ADR 0027/0037 重叠 | 内容并入 ADR 或删除；若留作 P1「可选宣传链接」资产则移入 contest-2026/ 统一管理 |
| `prototype/dpskv4p/shots/` + `prototype/kimi/` 截图集 | 约 6M 原型验证截图 | 随 `prototype/` 整体删除；若用户裁定保留选型档案，先剥离截图只留 HTML |
## ③ 保留（活跃资产）
| 对象 | 理由 |
| --- | --- |
| `research-world/`（除上表删除项） | 产品本体：compose 四服务、CI 测试对象、125 问 project.json 与 contest-2026/ 证据链（保护对象） |
| `research-world/evidence/orbits-49-*`（6.3M） | readme.md:55 显式声明的保留历史 Artifact/Trajectory（提交依赖） |
| `docs/questions.json`、`docs/submission-reference-manifest.json`、`docs/赛道一-…模板.docx`、`docs/答疑`之外的提交链文档 | readme.md 提交链 P1–P20 直接引用（提交依赖/保护对象） |
| `research-world/web/src/prototype/agent-runtime/` | App.jsx 活路由 |
| `runtime/` | compose 服务 + CI 测试对象 |
| `benchmarks/` | 活跃账本 README（readme P5/P18 引用）；20 个子目录是账本行的证据代码或远端指针 |
| `datasets/research-kernel-papers/{references,markdown,scripts,snapshots,manifest.json,docs-references.manifest.json}` | #138 一手来源归档（baa60c7 持续维护），报告引用可回溯（提交依赖） |
| `docs/adr/`（18 篇 + 0029 资产） | 领域决策单一上下文；0029 的 current/prototype 截图被正文逐一引用 |
| `docs/benchmarks/`、`docs/agents/` | design.md 被 readme P5 引用；agents/ 是 issue 跟踪与分诊规范 |
| 根文件 `AGENTS.md` `CONTEXT.md` `MEMORY.md` `PROBLEM.md` `readme.md` | 行为规范/术语/项目记忆/赛题/提交主链（保护对象） |
| `.github/` `skills-lock.json` `.agents/skills/research-report/` `.gitignore` `.gitattributes` `.dockerignore` | CI 与 Agent 工具链配置 |
## 临时文件散布点（.scratch 之外）
| 位置 | 数量/体积 | 性质 |
| --- | --- | --- |
| `screenshots/`（根） | 2 个/360K | 基线捕获遗留，0 引用 |
| `research-world/web/screenshots/` | 43 个/5.9M | QA 截图混在 src 树里，28 个已无引用 |
| `prototype/dpskv4p/shots/`、`prototype/kimi/` | ~6M | 原型验证截图 |
| `docs/adr/assets/0029-trace-ui/prototype/` | 5 个/504K | playwright QA 截图，ADR 正文引用（保留） |
| `research-world/evidence/{activity-*.png,doctor.json}` | 3 个/344K | 2026-08-12 证据快照遗留，0 引用 |
无 `__pycache__`/`.DS_Store`/`*.tmp`/`*.bak`/node_modules 入库；worktree 无 untracked 文件。临时目录唯一约定尚未建立（#302 Not yet specified）。
## 死依赖线索
| 声明处 | 死依赖 | 核查方式 |
| --- | --- | --- |
| research-world/pyproject.toml | `markdown`、`python-dotenv`、`mcp` | server/worker/scripts 全量 import 扫描 0 命中；Dockerfile/compose 无 dotenv 引用 |
| research-world/web/package.json | `d3-force` | src 0 引用 |
| runtime/pyproject.toml | 无 | 7 项依赖全部命中 |
删除依赖行同样等 tag 后随代码清理一并执行。
