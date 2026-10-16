---
status: accepted
issue: 334
supersedes: [42, 43]
---
# 原生研究对象导入
Source 只表示外部文献；系统自己的报告、旧版本、审查和运行账本不是 Source，不进入研究图谱作为包装节点。
每题的 Question 直接关联原始报告、全部版本、审计和脱敏轨迹 Artifact。Direction 直接关联其原报告 Artifact 与 Question；来源位置保留在可折叠详情中。
当前报告明确引用外部 Source 标识时，Direction→Source 使用 depends_on 表达参考依赖，不推断支持或反驳。没有明确对应关系的参考文献保留为独立 Source，不给它们臆造证据边。
破坏性清理仅针对导入生成的包装节点及关联边。保留 Project、Question、独立 Direction 的标识，保留原始 Artifact 与用户自行添加的对象。报告级交付状态不改写为科学结论。
