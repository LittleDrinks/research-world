# q089 V1 独立评审（review-v1）
- 评审日期：2026-09-01（UTC）；评审模型：contest-qwen/gpt-5.6-sol；评审职责：独立科学 reviewer。
- 读取范围：仅 `projects/q089/project.json`、根 `readme.md` 第56–88行（协议与 rubric）、`evidence/contest-2026/q089/v1.md`。未读 Trajectory、q049、其他版本。
- 核验工具：anysearch（search/batch_search/extract）+ 直接 curl/Wayback 回读；核验记录见下文 URL。

## 六维 rubric 评分
| 维度 | 分 | 依据 |
|---|---|---|
| 问题理解 | 2 | 正确识别"无统一 current limit"的前提错误，四级边界（热力学/详细平衡/实验记录/商业）划分准确，知识缺口真实 |
| 文献证据 | 1 | 六来源全部真实可回读、关键引用无虚构；但 47.6% 省略聚光条件、"2026年8月数据"无法核实、26.7% 为过时记录、压电<20% 与 Bi₂Te₃ ZT≈1 无来源、NREL→NLR 更名未注明——存在实质缺陷 |
| Direction 质量 | 2 | 三方向机制真正不同（光谱管理 / 光子回收串联 TPV / 声子玻璃-电子晶体），各含正反证据、替代解释、可区分预测与不确定性，经损失分解框架可比较 |
| 科学推理 | 1 | "SQ 是硬性天花板、任何单结无法超越"为伪命题（聚光下单结极限≈40.7%），且与同方向引用的 665 倍聚光 47.6% 证据自相矛盾；条件混合与报告自身主张相悖 |
| 研究计划 | 2 | 数据、仿真工具（SCAPS/TCAD/Python）、双基线（Si 29.4%、0.74 eV TPV）、步骤、定量判据、产物、风险与停止条件齐全，V1 阶段纯文献分析可实施 |
| 表达与追溯 | 2 | 问题→证据→方向→取舍→计划单一主线成立，planned/executed 分离，六来源本次 6/6 可回读（缺 URL/DOI 为 Low 缺陷，不阻断回读） |
| **总分** | **10/12** | 无 0 分 |

## 来源逐条核验
| # | 来源 | 判定 | 核验 URL | 备注 |
|---|---|---|---|---|
| 1 | Shockley & Queisser (1961), J. Appl. Phys. | pass | pubs.aip.org/aip/jap/article/32/3/510/505950 | 32(3):510–519，标题、期刊、年份全对 |
| 2 | NREL Best Research-Cell Efficiency Chart | pass（带更名警告） | www.nlr.gov/pv/cell-efficiency（原 nrel.gov/pv/cell-efficiency.html，301 跳转） | 图表真实且仍为权威；DOE 2025-12-01 宣布 NREL 更名 National Laboratory of the Rockies（NLR，待国会授权），2026-05-29 起 nrel.gov 跳转 nlr.gov；energy.gov 仍挂 NREL 旧名。V1 用旧名未注明 |
| 3 | LaPotin et al. (2022), Nature | pass | nature.com/articles/s41586-022-04473-y；PMC9007744 全文回读 | 41.1±1%@2400°C、1.4/1.2 eV、2.39 W/cm²、平均 36.2%（1900–2400°C）全部属实 |
| 4 | Wikipedia: Thermoelectric materials | pass | en.wikipedia.org/wiki/Thermoelectric_materials | 页面存在，"no theoretical upper limit to ZT"原文一致 |
| 5 | Ossila: Radiative Efficiency Limit | pass（带限定） | ossila.com/pages/radiative-efficiency-limit | 页面存在；其"四大损失"含寄生电阻，但该页自己注明寄生电阻在 SQ 计算中假设为零，V1 转述时丢了该限定 |
| 6 | PV Education: Detailed Balance | pass | pveducation.org/pvcdrom/detailed-balance | 页面存在，内容匹配 |
- 来源回读率：**6/6 = 100%**；无虚构引用。

## 效率数字逐条核验
| 声明 | 判定 | 核验证据 |
|---|---|---|
| 四结 47.6% | 数字 pass，条件表述 fail | Fraunhofer ISE 新闻稿（2022-05-30）：GaInP/AlGaAs//GaInAsP/GaInAs 四结，**665 倍聚光**，电池仅数 mm²，由 ISE CalLab 测量后入 NREL/NLR 图。V1 省略聚光与小面积条件，"NREL 认证"不精确；"2026年8月数据"无法核实（结果为 2022-05，图表改版日期未能回读） |
| TPV 41.1% | pass | LaPotin 原文：1.4/1.2 eV 串联，41.1±1%@2400°C，平均 36.2% |
| SQ 33.7% @ 1.34 eV | pass | Ossila、Rühle 2016（Solar Energy 130:139）、Wikipedia 一致 |
| Si 理论极限 29.4% | pass | Wikipedia SQ 条目引用的晶硅详细平衡极限 29.4% |
| Si 记录 26.7% | 数字 pass，时效 fail | Kaneka HBC 2017=26.7%（79 cm²）属实；但 2026 年当前记录为 LONGi HBC 27.3%（2024-05，ISFH 认证）并已刷新至 27.81%（2025-04），V1 用了过时值 |
| 此前 TPV 记录 32% | pass（带限定） | LaPotin 原文"demonstrated... as high as 32%, albeit at much lower temperatures below 1,300 °C"——V1 未注明该 32% 的低温条件 |
| 空气桥反射器 >50% | pass | LaPotin 预测：Rsub=97% 时 2200°C 下 >50%；结合 Fan et al. 空气桥（>98% 反射率）可达 >56%@2250°C |
| PbTe 基 ZT>2 | pass | Tan et al. 2016 Nat. Commun.：能带工程+纳米结构 PbTe-SrTe，ZT=2.5@923 K |
| ZT 无理论上限 | pass | Wikipedia Thermoelectric materials 原文一致，领域共识 |
| 压电 <20% | unverifiable | V1 未给来源；抽查 Yang et al. 2018 Joule 最优设计 8.9%，与"通常<20%"相容，但无直接引用支持该数字 |
- 任务清单七数（47.6/41.1/33.7/29.4/26.7/ZT>2/压电<20%）：**6/7 核实 = 86%**，压电<20% 不可核实。

## 焦点问题裁决
- **NREL/NLR**：同一机构同一图表，2025-12 宣布更名、2026-05 域名切换，V1 沿用旧名旧域。非伪造，属时效缺陷。
- **SQ 是否硬性天花板**：仅在"单结 + 非聚光 AM1.5 + 仅辐射复合"假设下成立；最大聚光下单结详细平衡极限升至约 40.7%，多结/热载流子/多激子均可超越。V1"任何单结电池都无法超越"为伪命题，且与本方向引用的 665 倍聚光 47.6% 自相矛盾。
- **TPV 效率分母**：V1 的 η=P_out/(P_inc−P_ref) 与 LaPotin 定义（亚带隙光子反射回热源予以扣除）一致，正确。
- **ZT 无理论上限**：表述与来源一致，成立。
- **三方向同尺度可比性**：输入能形式不同（1-sun 太阳光 / >1900°C 热源 / 温差），V1 以损失分解为共同框架并明确拒绝直接比较效率数字，裁决为可比性成立。
- **主方向同时选 PV+TPV**：成立——二者共享光伏效应与光子管理，V1 已声明效率定义与条件差异；代价是焦点分散，V2 应明确双主线的共同量化判据。
- **计划可实施性**：基线、工具（SCAPS 免费，TCAD 需许可）、变量、判据（与记录的绝对效率差、Rsub 敏感性）均可落地；V1 声明不实验且 executed 未越界。

## Findings（按严重度）
- **High-1**：47.6% 省略 665 倍聚光与数 mm² 面积条件，却在 Direction 1 中作为"超越单结 SQ"证据与 1-sun 极限对比——违背报告自身"不混条件"的核心主张；"2026年8月数据"不可核实。
- **High-2**：Direction 1 反证据"SQ 是硬性天花板、任何单结无法超越"在聚光情形下为伪，且与同方向 47.6%（聚光电池）自相矛盾。
- **Med-1**：来源 #2 机构更名 NREL→NLR 与域名切换未注明，引用时效缺陷。
- **Med-2**：硅记录 26.7% 过时（当前 27.3%/27.81%，LONGi HBC，ISFH 认证），"接近理论极限"结论仍成立但数字需更新。
- **Med-3**：压电<20%、商用 Bi₂Te₃ ZT≈1 无来源，前者不可核实。
- **Low-1**：Ossila 四损失转述丢失"寄生电阻在 SQ 计算中假设为零"的限定。
- **Low-2**：六来源无 URL/DOI/卷期，回读需额外检索（本次 6/6 成功）。
- **Low-3**：TPV 前记录 32% 未注明其 <1300°C 条件。

## Direction 处置意见
- **Direction 1（PV 光谱管理）**：保留但改写。修正 SQ 绝对化表述并限定假设条件；47.6% 补聚光条件或改与多结聚光详细平衡极限对比；更新硅记录。
- **Direction 2（TPV 光子回收）**：保留。数字全部通过核验；补 32% 前记录的温度条件与器件/系统级效率的明确区分。
- **Direction 3（热电 PGEC）**：保留。ZT>2 核实通过；作为非主方向维持背景深度即可。

## V2 最小必改项
1. 47.6% 补全条件（665 suns、数 mm²、2022-05 Fraunhofer ISE/CalLab），删除或更正"2026年8月数据"。
2. 改写"SQ 硬性天花板/任何单结无法超越"：限定 1-sun 辐射复合假设，注明聚光下单结极限≈40.7%。
3. 硅记录更新为当前认证值（27.3%/27.81%，注明机构与年份）或显式标注 Kaneka 2017 为历史值。
4. 来源 #2 加 NREL→NLR 更名注释与现行域名 nlr.gov。
5. 压电<20% 与 Bi₂Te₃ ZT≈1 补来源，否则删数字。
6. 六来源补 URL/DOI。
7. Ossila 损失清单补"寄生电阻假设为零"限定；TPV 32% 补温度条件。

## Verdict
**deliverable（有条件通过）**：总分 **10/12**，无 0 分，关键引用（S&Q 1961、NLR/NREL 图表、LaPotin 2022）抽查全部通过，V1 运行记录与计划一致、无伪造执行结果。最高严重度 **High（2 项）**，V2 最小必改项 **7 条**，全部修复前不得作为最终版提交。
