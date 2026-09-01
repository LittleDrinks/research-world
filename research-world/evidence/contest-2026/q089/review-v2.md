# q089 V2 独立评审（review-v2）
- 评审日期：2026-09-01（UTC）；评审模型：contest-qwen/gpt-5.6-sol；评审职责：V2 最终独立 reviewer。
- 读取范围：仅 `projects/q089/project.json`、根 `readme.md` 第56–88行（协议与 rubric）、`evidence/contest-2026/q089/review-v1.md`、`evidence/contest-2026/q089/v2.md`。未读 Trajectory、q049、其他案例。
- 核验工具：anysearch（batch_search/search/extract）+ 直接 curl 回读 DOI/URL；核验记录见下文 URL。

## 六维 rubric 评分
| 维度 | 分 | 依据 |
|---|---|---|
| 问题理解 | 2 | 保持"无统一 current limit"的前提纠正，四级边界（热力学/详细平衡/实验记录/商业）准确，知识缺口真实且指向 TPV 规模化与损失统一分解 |
| 文献证据 | 1 | 7 条来源全部真实、关键数字经核验通过、均带 DOI/URL；但来源 #5（Yang et al. 2018, Joule）DOI 错引：所给 10.1016/j.joule.2018.07.019 解析到一篇锂电池论文，正确为 10.1016/j.joule.2018.03.011——存在实质缺陷 |
| Direction 质量 | 2 | 三方向机制真正不同（光谱管理 / 光子回收串联 TPV / 声子玻璃-电子晶体），各含正反证据、替代解释、可区分预测与不确定性，经损失分解框架可比较 |
| 科学推理 | 2 | V1 的"SQ 硬性天花板/任何单结无法超越"伪命题已修复：明确限定 AM1.5G、非聚光、仅辐射复合假设，并给出最大聚光下单结极限≈40.7%；47.6% 与 SQ 的对比条件已对齐，不再自相矛盾；反对证据（高温依赖、系统级损失）真实影响主方向论证 |
| 研究计划 | 2 | 数据、仿真工具（SCAPS 免费/TCAD 许可注明/Python）、双基线（0.74 eV TPV 详细平衡、Si 29.4%）、R_sub 消融步骤（0→>95%）、定量判据（每 10% R_sub 的效率增益、±5% 参数扰动敏感性）、停止/回退/补证条件齐全，可直接实施 |
| 表达与追溯 | 2 | 问题→证据→方向→取舍→TPV 单主线成立，planned/executed 分离，V1→V2 变化逐条对应 review-v1 修复项；7 来源中 6 条标识符可回读（#5 DOI 缺陷计入文献证据，不重复扣分） |
| **总分** | **11/12** | 无 0 分 |

## 来源逐条核验
| # | 来源 | 判定 | 核验 URL | 备注 |
|---|---|---|---|---|
| 1 | Shockley & Queisser (1961), J. Appl. Phys. | pass | pubs.aip.org/aip/jap/article/32/3/510/505950 | DOI 10.1063/1.1736034 解析正确；32(3):510–519 全对 |
| 2 | NLR Best Research-Cell Efficiency Chart | pass | nlr.gov/pv/cell-efficiency（curl 200 回读） | 更名注释属实：DOE 2025-12-01 宣布 NREL 更名 National Laboratory of the Rockies（待国会授权），域名已切换 nlr.gov |
| 3 | LaPotin et al. (2022), Nature | pass | nature.com/articles/s41586-022-04473-y；PMC9007744 | DOI 解析正确；41.1±1%@2400°C、1.4/1.2 eV 串联、前记录 32%@<1300°C 均与原文一致 |
| 4 | Goldsmid (2014), Materials | pass | doi.org/10.3390/ma7042577 → MDPI Materials 7(4):2577–2592 | DOI 解析正确；Bi₂Te₃ 及其合金 ZT≈1（室温）为原文核心结论，支撑"商用 Bi₂Te₃ ZT≈1" |
| 5 | Yang et al. (2018), Joule | **fail（DOI 错引）** | sciencedirect.com/science/article/pii/S2542435118301260 | 论文真实、8.9% 最优设计效率属实；但所给 DOI 10.1016/j.joule.2018.07.019 解析到 Wang et al. 锂电池论文（PII S2542435118303301），正确 DOI 为 10.1016/j.joule.2018.03.011 |
| 6 | Ossila: Radiative Efficiency Limit | pass | ossila.com/pages/radiative-efficiency-limit | 页面回读一致：33.7%@1.34 eV、四损失含寄生电阻、"assumed to be zero"限定均与 V2 转述相符 |
| 7 | Fraunhofer ISE Press Release (2022) | pass | ise.fraunhofer.de/.../47-comma-6-percent-efficiency.html | 页面回读：2022-05-30、665 suns、GaInP/AlGaAs//GaInAsP/GaInAs 四结、数 mm²，全部属实 |
- 标识符级回读率：**6/7 = 86%**（#5 DOI 错引）；论文实体与内容主张 7/7 真实，无虚构引用。

## 效率数字逐条核验
| 声明 | 判定 | 核验证据 |
|---|---|---|
| 四结 47.6% @ 665 suns，数 mm²，2022-05，ISE CalLab 测量入 NLR 图表 | pass | Fraunhofer 新闻稿原文回读：665 suns、"few square millimeters"、2022-05-30，结构与 V2 一致 |
| SQ 33.7% @ 1.34 eV（AM1.5G、非聚光、仅辐射复合） | pass | Ossila 原文一致；假设条件已随数字给出 |
| 最大聚光下单结详细平衡极限≈40.7% | pass | 多源一致（SQ 全聚光极限 40.7%，太阳黑体 5759 K 假设） |
| TPV 41.1%（1.4/1.2 eV，2400°C） | pass | LaPotin 原文：41.1±1%@2400°C |
| 前 TPV 记录约 32% @ <1300°C | pass | LaPotin 原文"as high as 32%, albeit at much lower temperatures below 1,300 °C"；低温条件已补注 |
| 空气桥反射器预测 >50% | pass | LaPotin/arXiv 2108.09613：Rsub=97%、2200°C 下 >50% |
| 硅记录 LONGi 27.81%（2025-04，ISFH 认证） | pass | LONGi 新闻稿：2025-04-11 ISFH 认证 27.81% HIBC，刷新晶硅纪录 |
| Si 理论极限 29.4% | pass | Wikipedia SQ 条目、Ehrler 2020、Green 2025 一致 |
| Bi₂Te₃ ZT≈1 | pass | Goldsmid 2014 支撑（Bi₂Te₃ 合金室温 ZT≈1） |
| 压电最优设计 8.9% | pass（标识符 fail） | ScienceDirect 摘要原文"energy conversion efficiency of 8.9%"；DOI 错引见来源 #5 |
- 关键数字 **10/10 核实 = 100%**；唯一缺陷为压电来源的 DOI 标识符错误，非数字错误。

## review-v1 七项修复逐条验收
| # | V2 最小必改项 | 判定 | 证据 |
|---|---|---|---|
| 1 | 47.6% 补全条件，删"2026年8月数据" | 已修复 | 665 suns、数 mm²、2022-05、CalLab 全部补齐；不可核实的"2026年8月"已删 |
| 2 | 改写 SQ 硬性天花板，限定假设并注明聚光≈40.7% | 已修复 | 已有认识与 Direction 1 反证据均已限定条件；Direction 1 正反证据不再自相矛盾 |
| 3 | 硅记录更新 | 已修复 | 更新为 LONGi 27.81%（2025-04，ISFH 认证），核验通过 |
| 4 | NREL→NLR 更名注释与 nlr.gov | 已修复 | 来源 #2 注明更名时间与新域名，核验通过 |
| 5 | 压电<20% 与 ZT≈1 补来源或删数字 | 已修复 | 不可核实的"<20%"删除，替换为有源的 8.9%（Yang 2018）；ZT≈1 补 Goldsmid 2014；来源列表相应以一手文献替换 Wikipedia 热电与 PV Education 条目 |
| 6 | 来源补 URL/DOI | 部分修复 | 7 条全部补齐标识符，但 #5 DOI 错引（新缺陷，见 Findings） |
| 7 | Ossila 寄生电阻限定；TPV 32% 温度条件 | 已修复 | 来源 #6 局限栏与 TPV 段落均已补注 |
- 修复率：**6/7 完全修复，1/7 部分修复（引入新 DOI 缺陷）**；V1 两项 High 均已消除。

## 焦点问题裁决
- **TPV 单主方向可实施性**：成立。V2 将双主线收紧为 TPV 光子回收单主线，给出"SQ 复现 → Nature 损失分解 → R_sub 消融（0→>95%）→ 视场因子/热损失系统级外推"的完整链路，基线、工具、判据、停止/回退条件具体，构成一条可实施计划。
- **效率分母与器件/系统边界**：η_TPV = P_out/(P_inc−P_ref) 与 LaPotin 定义一致；器件级（>40%@2400°C）与系统级（视场因子、热损失）明确分层，知识缺口 #2 与计划步骤 5 呼应，无边界混淆。
- **消融/变量/判据/工具/资源具体性**：消融变量（R_sub）、判据（每 10% R_sub 的效率增益、±5% 扰动敏感性）、工具许可状态（SCAPS 免费、TCAD 商业）、资源（公开文献+NLR 库）均具体。
- **planned/executed 诚实性**：executed 仅含检索核验与报告撰写，全部模拟明确标为 planned（"本 V2 阶段不进行新实验""所有模拟仍为 planned"），无伪造执行结果。但 executed 声称"对 7 项修复点逐一进行了核验"，而 Yang 的 DOI 错引表明来源标识符未逐一回读——诚实性总体成立，核验声明强度略超实际。
- **残留时效/精度项**：LONGi 电池官方命名为 HIBC（Hybrid Interdigitated-Back-Contact），V2 写作 HBC；NLR 更名"待国会授权"（pending Congressional authorization）限定未注明。均为 Low。

## Findings（按严重度）
- **Med-1**：来源 #5（Yang et al. 2018, Joule）DOI 错引：10.1016/j.joule.2018.07.019 解析到无关锂电池论文，正确 DOI 为 10.1016/j.joule.2018.03.011。论文实体与 8.9% 数字真实，但标识符误导回读，且与 executed 的"逐一核验"声明不符。
- **Low-1**：LONGi 电池写作 HBC，官方命名为 HIBC。
- **Low-2**：NLR 更名省略"待国会授权"限定。
- **Low-3**：Direction 3 的 PbTe ZT>2 主张在 V2 的 7 条来源中无直接出处（V1 的 Wikipedia 热电来源已删，未补 Tan et al. 2016 等一手引用）；该数字本身经核验属实。

## 交付门槛核对
| 门槛 | 结果 |
|---|---|
| 总分 ≥10/12 | 通过（11/12） |
| 无 0 分 | 通过 |
| 关键引用抽查通过 | 通过（S&Q 1961、NLR 图表、LaPotin 2022、Fraunhofer 新闻稿全部回读通过） |
| 无伪造执行结果 | 通过（模拟全部 planned，executed 未越界） |

## Verdict
**deliverable**：总分 **11/12**，无 0 分，关键引用 4/4 通过，无伪造执行。最高严重度 **Med（1 项）**：来源 #5 DOI 错引，建议提交前一行修正为 10.1016/j.joule.2018.03.011（并顺手修正 HIBC 拼写），不阻断交付判定。V1→V2：10/12 → 11/12，V1 的 2 项 High 全部消除。
