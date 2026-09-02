---
project: q112
artifact: review-v12
role: independent-review
reviewer_session: "01a05ffb-52a9-7f70-b77b-11062ef9951c"
author_session: "01a05ff5-a944-7e0a-8c3b-9bd304e26f13"
reviewed: v10.md
reviewed_sha256: "1e2a784004dde94ea16586723f209dbeec9f3ef279ddb114e0eb691f50868ac0"
comparison: v9.md
prior_receipt: receipt-v11.md
prior_review: review-v11.md
run_record: run.md
original_question: docs/questions.json#112
reviewed_at: 2026-09-02
verdict: revise
sources:
  - id: A1
    type: local-artifact
    path: research-world/evidence/contest-2026/q112/v10.md
    sha256: "1e2a784004dde94ea16586723f209dbeec9f3ef279ddb114e0eb691f50868ac0"
  - id: A2
    type: local-artifact
    path: research-world/evidence/contest-2026/q112/v9.md
    sha256: "63c860eabec64c4e123d8013098baf7bf9579de4d6d1effda487d03ada0ccc6b"
  - id: A3
    type: local-receipt
    path: research-world/evidence/contest-2026/q112/receipt-v11.md
  - id: A4
    type: local-review
    path: research-world/evidence/contest-2026/q112/review-v11.md
    sha256: "9dfa177df6b7f4b12a0899a7edad634ed2d0508ee298172453f22f06a3b5e22f"
  - id: A5
    type: local-run-record
    path: research-world/evidence/contest-2026/q112/run.md
  - id: A6
    type: original-question-index
    path: docs/questions.json
    record: 112
  - id: E1
    type: official-standard-catalog
    title: "BS EN 13432:2000 Packaging. Requirements for packaging recoverable through composting and biodegradation. Test scheme and evaluation criteria for the final acceptance of packaging"
    url: "https://knowledge.bsigroup.com/products/packaging-requirements-for-packaging-recoverable-through-composting-and-biodegradation-test-scheme-and-evaluation-criteria-for-the-final-acceptance-of-packaging"
    result: "title-existence-and-controlled-waste-treatment-scope-verified; full-standard-text-not-accessed"
---
# q112 独立核验
## 裁定
`v10.md` 为 `REVISE`：上一轮两项主修复大体落实，但 S2 的设施认证表述仍越过可核验范围，不能用总分抵销。
## 定点核验
- `v10.md:64-71` 已移除 “This research plan”；未检出 document/report/paper/assessment 类文件自指。`The study` 指代受测比较范围，不是文件自指。
- `v10.md:77-80,164,182` 将 PLA/PHA 保持为候选，限制 S2 为题名、存在和受控废物处理范围；55–60°C、180 天和 90% 明确为预注册内部筛选门槛；取得标准正文和认可实验室映射独立认证方案是实施 gate。候选材料未冒充已获认证。
- E1 的官方 BSI 目录确认 EN 13432 的完整题名、包装/包装材料的可堆肥性范围及受控废物处理厂信息；其公开页不提供 55–60°C、180 天、90% 或设施认证依据。
- `v10.md:130` 的 “EN 13432-certified industrial composting facilities” 将认证归于设施。E1 说明标准对象是包装和包装材料，不能支持该设施认证主张；这保留了 S2 范围外断言，阻断项未闭合。
- `run.md` 在本评审前仍保留 `final: v8.md`、`final_review: review-v10.md`、`final_receipt: receipt-v10.md` 与 `status: waiting_human`；`v10.md` frontmatter 无 `status`，候选稿未取得终态所有权。
## 六维评分
| 维度 | 分数 | 依据 |
|---|---:|---|
| 问题理解 | 2/2 | 原题的宽泛替代诉求收束为 1,000 次 750 mL、0–40°C、非加压冷食服务，三路线具有可检验的功能边界。 |
| 文献证据 | 1/2 | E1 支持 S2 的有限表述，但 `v10.md:130` 的设施认证无实际来源支持。 |
| Direction 质量 | 2/2 | rPET、候选堆肥材料和可复用 PP 路线均受性能与当地基础设施 gate 约束。 |
| 科学推理 | 2/2 | `N_eff`、`R=P/N_eff+W+T+rL`、break-even 前提与不确定性分层保持一致。 |
| 研究计划 | 2/2 | LCI、性能门、试点、失败条件和 planned/executed 边界完整；实施前仍需标准正文、认可实验室和设施数据。 |
| 表达与追溯 | 2/2 | 无空行；版本比较、旧链、会话身份、题目和实际官方来源均已登记。 |
| **总分** | **11/12** | **无 0 分项；S2 设施认证断言是必须修复的定点阻断项。** |
## 修订门
将 `v10.md:130` 改为不声称 EN 13432 认证设施，并以实际设施资格、容量和当地接收规则作为待核验输入；随后重新独立评审。
RESULT: REVISE
