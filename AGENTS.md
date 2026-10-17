# 编码
1. 不保留向后兼容。过时的直接删，不写 migration、不写 fallback。
2. 只写满足当前需求的最简实现。不要预防性抽象、不要配置层。
3. 先跑通最小端到端，再往上加。绝不为了未完成的复杂度拆掉能跑的东西。
4. 组件模块化，关注点分离。函数 <20 行。
5. 优先成熟库。没有明确理由不自己重写。
6. 先翻已有依赖能做什么，再考虑加新包。
7. 架构决策往长了做。不接受"先这样以后再换"。
8. 先看成熟产品怎么解决同一问题，别从零发明。
9. 原子化 git commit，利用回滚和分支明确当前进度
10. 服务从 `research-world/` 使用 `docker compose up --build -d` 启动；Pi 模型与凭证来自宿主 `~/.pi/agent/`，Runtime 私有副本持有凭证，禁止输出凭证。
11. 实现前更新对应 GitHub issue 的决策和验收标准。
12. 计划实现的每一个模块，都去检索一轮已有代码，作为参考
13. Git 工作流固定为 `GitHub issue → feat/<issue>-<slug> → PR → 全新独立 Codex 验收 → 合并 PR → 关闭 issue 与 Herdr worker`：开工前 issue 须包含明确验收标准；每个 issue 独占一个分支，一个分支只服务一个 issue；提交原子化并只推送 feat 分支，禁止直接 push `main` 与 force push；PR 正文须关联对应 issue；实现者自验后交由全新独立 Codex 按 issue 验收，失败不合并、不关闭；通过后合并 PR，远端回读成功后关闭 issue 与 Herdr worker。
# 文档
1. 零自我指涉：不写"本文档是…""必须遵守"。文件名就是声明。
2. 只写信息，不写关于信息的信息：来源进 frontmatter，不进正文。
3. 不写指针：外部链接/教程只是"可以参考"就别放，要放内化成结论。
4. 长度=信息密度：一句话能说清的不写一段。每多一词都问"删掉会丢信息吗"。
5. 版本化文档只保留 AGENTS.md、CONTEXT.md、Skill 指令与工作流配置；临时说明和状态笔记进入 gitignore，研究证据独立保留。
6. 紧凑排版：段落间不留空行，不写垫话，潜台词不写明，写完读一遍"这句删掉有损失吗"。
7. 同一信息只维护一处：术语 CONTEXT.md、需求、决策与验收 GitHub Issues、评测证据 benchmarks/、赛题研究产物 research-world/evidence/。
8. 陌生或未定义名词先查 CONTEXT.md、相关 issue、现有代码与成熟产品语义，映射已有概念；区分口语、示例、验收代理与领域不变量。已有概念无法表达时，Agent 先调研事实，再向用户确认产品决策；确认后先更新 issue，再新增术语或 schema。
## Agent skills
### Issue 跟踪
Issue 使用 `LittleDrinks/research-world` 的 GitHub Issues。见 `docs/agents/issue-tracker.md`。
### 分诊标签
标准分诊角色使用 `needs-triage`、`needs-info`、`ready-for-agent`、`ready-for-human` 与 `wontfix`。见 `docs/agents/triage-labels.md`。
### 领域上下文
命名领域概念或修改方案前，按 `docs/agents/domain.md` 读取上下文。
