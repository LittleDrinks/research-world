---
status: accepted
issue: 326
---
# 历史研究材料导入
Q001-Q125 的 canonical Project、候选报告、独立审计、运行账本和深度案例版本按现有 Project/Research Graph/Artifact 接口导入。历史文件作为不可变 Artifact；报告作为 Source；独立研究方向的提取按 ADR0043，引用文献作为未重新核验的 Source。Direction→Question 与 Direction→Source 使用 depends_on，不从引用列表推断 supports/refutes。
导入保留每个版本的原始终态、模型、作者 Session、来源路径和文件哈希。completed 是该历史运行的交付状态，不意味着科学问题解决；partial 和 waiting_human 原样保留。
原始 Pi/Codex 日志保留在原目录；导入清单记录相对原用户主目录的 source_path、实测哈希与账本校验结果，有账本哈希的逐一校验，没有的明确标记未验证历史哈希；系统中只导入脱敏的历史轨迹 Artifact，并记录原始与脱敏哈希。它们不创建当前 Runtime 的可恢复 Session，也不冒充本次运行。
单次导入用文件哈希和相对路径标识对象，重复执行复用已有对象；同一标识内容改变时失败。Project 使用不透明内部id，qNNN 只作为外部来源标识与名称。
ADR0037 对赛题运行期间“不实现专用导入层”的范围由本次显式导入请求取代；Research Graph 与 Trajectory 的所有权保持不变。
导入前备份当前数据库，在隔离数据目录完整导入并重复执行验收后，导入当前 Compose 服务。原始数据不删除。共享审计、停止尝试与跨案例评审保持其原有范围，不将整份共享轨迹的成本归到单题。
