---
sources:
  - id: qwen-models
    title: Qwen models
    url: https://help.aliyun.com/zh/model-studio/models
---
# 模型端点
模型服务是端点实体：`provider + model_id + base_url + auth_ref + capabilities`。AgentSpec 绑定 Runtime 识别出的端点，不保存密钥，不用模型名代替运行边界。
凭证只进入 Agent Runtime。Research Kernel、worker、图谱、AgentSpec、Trace 均不持有凭证。OpenAI 兼容端点由 Runtime 环境变量提供；Codex 的认证与配置由 Runtime 私有读取。
embedding 由同一端点层执行，Research Kernel 只调用 Runtime 的向量化接口。
