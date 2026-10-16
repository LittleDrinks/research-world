---
issue: "LittleDrinks/research-world#312"
parent: "LittleDrinks/research-world#311"
supersedes: "#262 基线结论（main=2b25f54、架构线 +97/-6）"
date: 2026-02-14
---

# feat/156 架构族对 main@5e9dfb1 的继承代价核定

## Git 事实
- merge-base `a510ff5`（PR #143）。此后 main +60 commits（365 files，+33296/−36，其中 evidence 语料 333 files +32072）；feat/156 +104 commits（81 非 merge + 23 merge）。
- 架构线净载荷：**72 files，+10282/−759**（#262 时仅 +97/−6；#262 基线 `ae1a2cd` 之后新增 7 commits = PR #254 runtime-close 已并入）。
- merge-tree 实测文本冲突：**2 文件**——`CONTEXT.md`、`runtime/runtime/server.py`。双侧触碰共 4 文件：另两个 `.gitignore`、`web/playwright.config.js` 自动合并且语义正确（testIgnore t2 与 webServer 数组双侧保留）。
- #262 禁止清单现状：`feat/229`（Runtime.close）**已进架构线**；`feat/228`、`feat/256`、`feat/202`（Penguin）、`feat/109` 均不在祖先中。
- Penguin 代码零残留（无文件、无符号）；残留全部在治理文档的处方性文本中，见剔除清单。

## 逐层载荷（架构线相对 merge-base）
| 层 | 代码 | 测试 | 提交数* | PR |
|---|---|---|---|---|
| Kernel Session | `server/kernel_interface.py` +705、`kernel_http.py` +202、`kernel-contract/` 新包 +32、`app.py` 重接线 +15/−23 | +1015/−159（interface 422、http 394、kernel 67/−30、projects −45 等） | 17 | #157/148/149/159/231/200/217/201 |
| Transport | `runtime/runtime.py` +775、`run_store.py` +803、`http.py` +102、`mmr.py` +101、`trace.py` +67、`runtime_tools.py` +98、`errors.py` +5、`server.py` +8/−20 | +3710/−12（recovery 1199、turn-trace 891、close 448、ownership 305、http 244 等） | 38 | #151/153/177/235/254 |
| Adapter | `adapter/pi.py` +529、`adapter/__init__.py` +43 | `test_pi_adapter` +674 | 10 | #162/163 |
| Map | web/graph+MapPage+Inspector 重写 +190/−273、`map.css`、`labels.js`、`vite.config` | `map.spec.js` +465/−180、`localmap_backend.py` +51 | 2（多数 Map 提交跨 kernel/runtime 计入前层） | #150/164/171/172 |
| 旧栈删除 | server.py 撤 `/acp` ACP 挂载、`__main__.py` −5、app.py 撤 project_routes/bootstrap −23、SettingsPage 撤 AutoToggle −16 | `test_server` −12、`test_projects` −45 | 散布于各 PR | #148/150/235 |
| 治理文档 | ADR 0033/0034/0038/0039 +208、`governance-check.sh` +194、CONTEXT +63/−36、AGENTS +14/−11、MEMORY +2/−14、PROBLEM 14/−14、`docs/research/152` +57 | — | 14 | #183/215/219 |
\*按首中目录归桶，跨层提交计入先命中层。

## 语义冲突点（文本冲突之外）
1. **AGENTS.md 规则 10 正面对撞**：架构线版规定「模型设置转发至 Penguin、模型凭证不从仓库根 .env 注入」；main 直连产品（#288/#289、T2 `05-credential-failure`）正建立在 .env `apikey`/`baseurl` 注入上。无文本冲突（main 未改 AGENTS.md），rebase 干净但合并结果方向错误。
2. **Penguin 术语合同**：merge-base 的 CONTEXT.md 零 penguin；术语（Penguin、Penguin Harness Adapter、Research World 设置 facade、模型访问配置）由架构线引入，现为废弃方向。
3. **ADR 0038 双占**：main `0038-runtime-ref-injection` vs 架构线 `0038-web-model-conversation-closure`；架构线另有 0039，renumber 需连锁。
4. **runtime-ref 注入边界失配**：main #288 在 WS `runtime_client.py` 边界注入 `DEFAULT_RUNTIME_REF`（ADR 0038-main）；架构线新增 HTTP `RuntimeHttpClient`（`runtime_http.py`）无任何 runtime ref 注入。继承后必须在新 transport 重建该边界，否则违反已接受 ADR。
5. **双 runtime 通道并存**：旧 WS `RuntimeClient`（`threads.py`/`workflows.py`/`kernel.py` 仍用，即 main 直连 chat 后端）与新 HTTP client 在继承树中共存。旧栈删除层不做，则两套通道长期并存；做，则 main 直连 chat 必须先迁到新 transport。
6. **server.py accesslog 行**：main 的 `config.accesslog = "-"`（#287）落在被架构线整体重写的 `serve()` 上，需人工重放。
7. **验收套件正交性**：main T1/T2 驱动直连 chat 域，架构线 map.spec.js 驱动 localmap fixture 域；playwright.config.js 自动合并已兼容两域，但 Map 重写后 T2 的 map 相关断言需复跑。
8. **`governance-check.sh` +194** 为架构线自带检查工具，main 从未启用，其中检查项硬编码 Penguin 合同字符串。

## Penguin 继承剔除清单
必须剔除/改写（架构线引入的处方性 Penguin 合同）：
- `AGENTS.md` 规则 10（恢复 .env 直连表述）
- `CONTEXT.md`：Penguin、Penguin Harness Adapter、Research World 设置 facade、模型访问配置四条目
- `MEMORY.md`：「Penguin 是唯一持久所有者」等
- `docs/adr/0033`：§76/84/88（Penguin=默认 Adapter、模型配置唯一持久所有者、Penguin Session 对账段；Runtime/Kernel 边界部分保留）
- `docs/adr/0038`(架构线版)：Penguin Harness v0.2.9 引用与 0033 关联段
- `docs/adr/0039`：范围声明中 Penguin 并列项
- `docs/agents/governance-check.sh`：Penguin 检查项字符串（59/64/90/94 行）
- `docs/research/152`：两处 Penguin fallback 表述（历史验收记录，可保留但需标注废弃）
不动（与 main 共享）：`datasets/research-kernel-papers/*`、`docs/adr/0026`。

## 三路径评估
### ① 整体 rebase feat/156 → main
- 规模：replay 104 commits，净载荷 +10282/−759。
- 文本冲突 2 文件（CONTEXT.md、server.py），预计 rebase 过程中 server.py/playwright.config.js 在少量提交上反复出现，均机械。
- 语义工作 8 项（上节），集中度：治理文档 5 项、transport 边界 2 项、套件复验 1 项。
- 结论：**技术可行且文本代价最小**；但「继承即接受」Penguin 治理文档回潮与 ADR 撞车，必须捆绑剔除清单 + ADR renumber + runtime-ref 边界重建作为一个语义清理 pass。建议以 rebase + 清理 pass 的单 PR 序列执行。

### ② 按模块 cherry-pick
| 层 | 与 main 文本冲突文件 | 语义依赖 |
|---|---|---|
| Kernel Session | 0 | `create_app` 签名重接线；与 main threads/workflows 的并存关系需重新决策 |
| Transport | 1（server.py） | 依赖 Kernel Session 的 session/ownership 模型（ownership 305 行测试在 runtime 侧）；runtime-ref 边界重建 |
| Adapter | 0 | 依赖 Transport 的 canonical adapter contract 与取消/恢复语义 |
| Map | 1（playwright.config.js，自动合并成立） | 依赖 Kernel Session 的 kernel_http surface 与 localmap fixture |
| 旧栈删除 | 1（server.py） | 删 `/acp` 即断 main 直连 chat 后端（WS RuntimeClient 的对端），等于强制先做 transport 迁移 |
- 依赖序强制为 Kernel Session → Transport → Adapter → Map → 删除；前两层合计 ~5.7k 行、55 个提交，且 TDD 成对提交不可拆。
- 结论：**不推荐**。冲突文件数虽少（合计 3 个），但每层都需复跑 T1/T2 与 runtime-ref 对齐，总工作量 > 路径①，唯一收益（跳过 Penguin 文档）可由剔除清单以更小代价获得。旧栈删除层的语义依赖使「部分继承」不成立。

### ③ main 重建（丢弃架构线）
- 丢弃全部 +10282/−759；在 main 直连合同上按 #259 新合同重写。
- 需重写价值内核：Adapter ~572 行 + 674 测试、Transport 恢复/cursor/exactly-once ~2k + 3.7k 测试、Kernel Session ~1k + 1k 测试；Map 与旧栈删除可不做。首版可裁剪至 delegate/child-run/恢复最小面，但当量仍 ~6–10k 行。
- 损失：17 个已验收 PR 的评审积累与 ~6.3k 行 TDD 测试资产；Pi RPC 协议错误、取消、恢复边界（架构线 30+ 个 fix 提交踩坑所得）需重踩。
- 结论：**不推荐整体重建**。仅当 #259 合同推翻「Session/Run 恢复 + 事件溯源」核心语义时才成立。

## 建议
路径 ①（rebase + 语义清理 pass）为基线建议；路径 ② 的逐层表保留作为①执行时的分批落序参考（按 Kernel Session → Transport → Adapter → Map → 删除分 PR 落地，每批复跑 T1/T2）。#262 基线结论更新为：feat/156 继承代价从「+97/−6 近零冲突」变为「+10282/−759、文本冲突 2 文件、语义对齐 8 项、Penguin 剔除清单 8 处」；`feat/156 → main` promotion gate（#274）验收必须包含剔除清单与 ADR renumber。
