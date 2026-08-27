---
sources:
  - id: qwen-models
    title: Qwen models
    url: https://help.aliyun.com/zh/model-studio/models
---
# 模型端点
模型服务是端点实体：`provider + model_id + base_url + auth_ref + capabilities`。AgentSpec 在 Launch 前绑定可用端点，不保存密钥，不用模型名代替运行边界。
凭证只进入 Agent Runtime。Research Kernel、Fact Graph、AgentSpec 与 Trajectory 均不持有凭证。OpenAI 兼容端点由 Agent Runtime 私有读取。
