# q021 review-v6 终态审计回执

## 审计对象

| 字段 | 值 |
|---|---|
| reviewed artifact | `research-world/evidence/contest-2026/q021/v6.md` |
| review artifact | `research-world/evidence/contest-2026/q021/review-v6.md` |
| review Session | `01a05e07-3391-7a92-a452-9e2cfde5fd53` |
| model | `contest-qwen/qwen3.7-max` |
| calls | 18 |
| uncached input tokens | 136,322 |
| cache read tokens | 566,016 |
| output tokens | 8,019 |
| review-v6 raw SHA-256 | `0cebfb729786263162959527e18de77fea61cda8b0f87ab0ae9e64d6c0416e04` |

以上数值从 Pi Session JSONL `2026-09-01T17-32-05-393Z_01a05e07-3391-7a92-a452-9e2cfde5fd53.jsonl` 独立复算，与 `run.md` 记录一致。SHA-256 经 `sha256sum` 独立校验确认。

## review-v6 RESULT 复算

| 项 | review-v6 声称 | 独立复算 | 判定 |
|---|---|---|---|
| RESULT | DELIVERABLE | DELIVERABLE | ✅ |
| 六维总分 | 12/12 | 12/12（问题理解 2、文献证据 2、Direction 质量 2、科学推理 2、研究计划 2、表达与追溯 2；无 0 分） | ✅ |
| 终态 | `waiting_human` | `waiting_human`（协议定义在根 `readme.md` line 77：继续运行需要领域裁决、受限数据权限、安全或伦理决定；记录待决问题，不伪造替代结果） | ✅ |
| 引用有效率 | 8/8（100%） | 8/8 | ✅ |
| Banerjee DOI 三标识符交叉核验 | PMID 26197846 = PMCID PMC4560903 = DOI 10.1093/cid/civ447 | 经 anysearch 独立核验一致 | ✅ |
| 伪造临床 executed | 无 | v6.md 明确声明"未执行任何临床试验" | ✅ |

## 协议行号校正

review-v6 声称"rubric：readme.md 第 69–80 行"和"终态规则：readme.md 第 81–88 行"。独立回读根 `readme.md` 确认：
- 六维 rubric 表实际位于 **lines 65–72**（表头 line 65，六行评分 line 67–72）
- 终态定义段实际位于 **lines 73–80**（`### 终态` line 73，四种终态表 lines 75–80）
- `waiting_human` 定义在 **line 77**，非 review-v6 暗示的 81–88 区间

review-v6 行号偏高，但不影响终态判定本身的正确性。本回执以 line 77 为 `waiting_human` 的权威协议出处。

## Planned / Executed 审计

| 类 | v6.md 内容 | review-v6 确认 | 审计判定 |
|---|---|---|---|
| Planned | (1) 修正 Banerjee DOI civ478→civ447 (2) 终态 pending_review→waiting_human (3) 如实说明仅做标识符核验和文本修订 | 三项 planned 完整记录 | ✅ |
| Executed | (1) Banerjee DOI 已修正 (2) 终态已改为 waiting_human (3) 变更说明已写入 V5→V6 变化总结 | 三项 executed 与 planned 一一对应 | ✅ |
| 临床执行 | 无。v6.md 明确声明"未执行任何临床试验" | review-v6 确认"无伪造临床 executed" | ✅ |

## 最高 Finding

**None**。review-v6 列出 Critical 0、Major 0、Minor 0。唯一披露为 review-v5 的 DOI 核验遗漏（civ478 指向 Hook et al. 2015 而非 Banerjee），属于跨版本审计记录，不构成 V6 或 review-v6 自身的 finding。

## V5 科学内容保留

review-v6 逐项核验 V5 的 13 项要素（ITT 主要分析、PP 次要分析、污染处置、panel 外路径、pilot n=30、未来 RCT 330/arm、10% NI 界值标注"临时性"、Vineeth 均值术语、终点下界+待测延迟、30 天死亡率仅描述性、避免 KM 曲线、三方向完整结构、方向二主攻方向），全部保留无回退。

## 最终科学 RESULT

- 最终版：`v6.md`，六维 12/12，来源 8/8，Banerjee 关键引用三标识符通过
- 最终评审：`review-v6.md`，判定 DELIVERABLE
- 唯一终态：`waiting_human`（定义于 `readme.md` line 77）
- 待决项：IRB 审批、临床团队协调、患者招募与知情同意、BSL-2 实验室资质确认、RDT 设备与试剂资源
- 无伪造替代结果

RESULT: DELIVERABLE
