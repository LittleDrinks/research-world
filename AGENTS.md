# 编码

1. 不保留向后兼容。过时的直接删，不写 migration、不写 fallback。
2. 只写满足当前需求的最简实现。不要预防性抽象、不要配置层。
3. 先跑通最小端到端，再往上加。绝不为了未完成的复杂度拆掉能跑的东西。
4. 组件模块化，关注点分离。函数 <20 行。
5. 优先成熟库；已有库能满足当前需求时不自行重写。
6. 实现通用基础能力前，先检查现有依赖，再查询当前包管理器的官方 registry 与候选库一手文档；无合适依赖的结论须有查询证据。
7. 架构决策往长了做。不接受"先这样以后再换"。
8. 每个模块先查成熟产品的一手文档和代码再设计；Agent Chat 的设计与 reviewer 返工先执行 `$anysearch`，用检索证据校准修改。
9. 原子化 git commit，利用回滚和分支明确当前进度
10. 正常交付一律使用 `docker compose up --build -d`（research-world/），不裸跑本地实例；Pi 只允许在宿主机用于开发端到端验证，Docker 不包含也不支持 Pi；API 凭证在仓库根 .env（小写键 apikey/baseurl，compose 已映射）。
11. 讨论结论先落 ADR/术语，再动代码；文档没更新的实现当作不存在。
12. 计划实现的每一个模块，先检索一轮已有代码与成熟实现；需要通用依赖时先查官方 registry。
13. Git 工作流固定为 `GitHub issue → feat/<issue>-<slug> → PR → 全新独立 Codex 验收 → 合并 PR → 关闭 issue 与 Herdr worker`：开工前 issue 须包含明确验收标准；每个 issue 独占一个分支，一个分支只服务一个 issue；提交原子化并只推送 feat 分支，禁止直接 push `main` 与 force push；PR 正文须关联对应 issue；实现者自验后交由全新独立 Codex 按 issue 验收，失败不合并、不关闭；通过后合并 PR，远端回读成功后关闭 issue 与 Herdr worker。
14. TDD 临时证据统一写入 `.scratch/tdd/<ticket>/`，保存每票 red/green 命令输出和临时诊断；永久测试源码跟随所属模块并由 Git 跟踪，`.scratch/tdd/` 保持忽略。

# 文档

1. 零自我指涉：不写"本文档是…""必须遵守"。文件名就是声明。
2. 只写信息，不写关于信息的信息：来源进 frontmatter，不进正文。
3. 不写指针：外部链接/教程只是"可以参考"就别放，要放内化成结论。
4. 长度=信息密度：一句话能说清的不写一段。每多一词都问"删掉会丢信息吗"。
5. 行为规范进AGENTS.md，项目记忆进MEMORY.md，MEMORY.md永远只保留最新信息，旧内容直接删，不允许为了安全而保留。
6. 紧凑排版：段落间不留空行，不写垫话，潜台词不写明，写完读一遍"这句删掉有损失吗"。
7. 同一信息只维护一处：术语 CONTEXT.md、项目记忆 MEMORY.md、决策 docs/adr/、评测证据 benchmarks/README.md、赛题 readme.md。
8. 陌生或未定义名词先查 CONTEXT.md、ADR、现有代码与成熟产品语义，映射已有概念；区分口语、示例、验收代理与领域不变量。已有概念无法表达时，Agent 先调研事实，再向用户确认产品决策；确认后才新增术语、schema 或 ADR。

## Agent skills
### Issue tracker
Issues and specs use GitHub Issues through `gh`. See [docs/agents/issue-tracker.md](docs/agents/issue-tracker.md).
### Triage labels
Triage labels use the canonical five-role vocabulary. See [docs/agents/triage-labels.md](docs/agents/triage-labels.md).
### Domain docs
Single-context layout: root `CONTEXT.md` and `docs/adr/`. See [docs/agents/domain.md](docs/agents/domain.md).
