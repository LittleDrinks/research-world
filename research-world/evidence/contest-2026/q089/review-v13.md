---
project: q089
artifact: review-v13
role: independent-review
reviewer_session: "01a05fe9-e149-7ec3-abde-b5d8ff3a8ca4"
author_session: "01a05fe5-4488-7240-af78-40caadd1eadb"
reviewed: v10.md
verdict: deliverable
sources:
  - role: reviewed-candidate
    path: research-world/evidence/contest-2026/q089/v10.md
  - role: prior-candidate
    path: research-world/evidence/contest-2026/q089/v9.md
  - role: prior-independent-review
    path: research-world/evidence/contest-2026/q089/review-v12.md
  - role: run-record
    path: research-world/evidence/contest-2026/q089/run.md
  - role: original-question
    path: docs/questions.json
  - role: candidate-linked-primary-source
    id: S9
    organization: LONGi
    date: 2025-04-13
    url: https://www.longi.com/en/news/isfh-hibc-conversion-efficiency/
---
# q089 核验结论
## review-v12 修订项
1. **S9：通过。**`v10.md` 的 S9 将 LONGi 2025-04-13 官方页面、27.81% HIBC 与 ISFH 绑定；Direction 1 同样以 S9 锚定该数值。来源局限明确为企业发布，未取得 ISFH 原始证书，不能把企业页面等同于可供复核的认证原件。
2. **TPV planned 基线：通过。**基线冻结 2400°C 黑体、平行平面单位面积、device-level view factor=1、1.4/1.2 eV tandem、R_sub=95% 及 0/50/80/90/95/98% sweep、eta=P_elec/(Q_inc-Q_ref)、Python 3.12、NumPy、SciPy、冻结脚本和依赖锁、输入 JSON、CSV 输出、能量收支误差<0.1%。system-level 另扫 view factor=0.3/0.5/0.7/1.0，且明确不得与 device efficiency 混用。
3. **科学计划修订：通过。**S9 证据与可复现的 TPV 计划属于明确的科学计划正文修订，不受“纯删除”限制。候选不写 `status` 合规；运行记录在独立通过前保留 `v8.md`/`review-v11.md` 旧链属于正确的终态所有权顺序，不能据此扣分。
## 六维评分
| 维度 | 分数 | 依据 |
|---|---:|---|
| 问题界定 | 2/2 | 原题涉及的 PV、热电、压电和 TPV 均覆盖，热力学、器件、实验记录与商业效率边界清楚。 |
| 来源 | 2/2 | S9 具有精确的 LONGi 日期与 URL，并在正文绑定 HIBC/ISFH/27.81%；原始 ISFH 证书缺失被限定为证据局限。 |
| Direction 与比较 | 2/2 | PV 光谱管理、TPV 光子回收和热电输运各有机制、反证、替代解释、可区分预测和不确定性，主方向取舍清楚。 |
| 科学推理 | 2/2 | SQ 条件、TPV 温度边界、R_sub 因果消融及 device/system 效率边界一致。 |
| 计划 | 2/2 | TPV 参数、实现、输入输出、误差阈值和预注册 sweep 已冻结；全部模拟、曲线、外推仍标为 planned，未冒充执行结果。 |
| 表达与追溯 | 2/2 | v10 的修订目的、来源局限和执行边界可追溯；候选与 run 记录的终态职责未混淆。 |
| 合计 | 12/12 | 三项修订条件均满足。 |
## Residual risk
- LONGi 页面所称 ISFH 认证尚无已取得的 ISFH 原始证书；停止新增检索限制了对该认证原件的独立核验，但不改变候选已作出的透明限定。
RESULT: DELIVERABLE
