export const RUNTIMES = [
  { id: "codex", name: "Codex CLI", vendor: "OpenAI", version: "0.149.0", path: "/home/q2635/.local/bin/codex", status: "ready", auth: "已认证", models: ["gpt-5.6-sol"], efforts: ["low", "medium", "high", "xhigh"] },
  { id: "claude", name: "Claude Code", vendor: "Anthropic", version: "已发现", path: "/home/q2635/.local/bin/claude", status: "adapter", auth: "未接入 Adapter", models: [], efforts: [] },
  { id: "kimi", name: "Kimi CLI", vendor: "Moonshot", version: "已发现", path: "/home/q2635/.kimi-code/bin/kimi", status: "adapter", auth: "未接入 Adapter", models: [], efforts: [] },
  { id: "dsh", name: "DeepSeek Harness", vendor: "DeepSeek", version: "已发现", path: "/home/q2635/.nvm/versions/node/v24.14.0/bin/dsh", status: "adapter", auth: "未接入 Adapter", models: [], efforts: [] },
  { id: "gemini", name: "Gemini CLI", vendor: "Google", version: "未发现", path: "$PATH", status: "missing", auth: "不可用", models: [], efforts: [], install: "npm i -g @google/gemini-cli" },
  { id: "opencode", name: "OpenCode", vendor: "社区", version: "未发现", path: "$PATH", status: "missing", auth: "不可用", models: [], efforts: [], install: "npm i -g opencode-ai" },
];

export const PROVIDERS = [
  { id: "openai-compatible", name: "OpenAI Compatible", status: "ready", auth: "环境凭证已映射", endpoint: "仓库根 .env / baseurl", models: ["qwen3.7-flash"], efforts: ["low", "medium", "high"] },
  { id: "agenthub", name: "AgentHub API", status: "adapter", auth: "未接入 catalog", endpoint: "期望支持", models: [], efforts: [] },
];

export const CAPABILITIES = {
  skills: [
    { id: "software-engineering", name: "software-engineering", source: "项目 Skill", path: ".agents/skills/software-engineering/SKILL.md", status: "ready", detail: "调查、实现与验证软件工程任务" },
    { id: "tdd", name: "tdd", source: "项目 Skill", path: ".agents/skills/tdd/SKILL.md", status: "ready", detail: "测试驱动开发流程" },
    { id: "codebase-design", name: "codebase-design", source: "项目 Skill", path: ".agents/skills/codebase-design/SKILL.md", status: "ready", detail: "深 Module 与 Interface 设计" },
    { id: "domain-modeling", name: "domain-modeling", source: "项目 Skill", path: ".agents/skills/domain-modeling/SKILL.md", status: "ready", detail: "领域术语与架构决策" },
    { id: "prototype", name: "prototype", source: "项目 Skill", path: ".agents/skills/prototype/SKILL.md", status: "ready", detail: "可丢弃的交互原型" },
  ],
  tools: [
    { id: "read-skill", name: "read_skill", source: "Runtime catalog", path: "runtime://tools/read_skill", status: "ready", detail: "读取已识别 Skill" },
    { id: "read-resource", name: "read_resource", source: "Runtime catalog", path: "runtime://tools/read_resource", status: "ready", detail: "读取受控资源" },
    { id: "graph-query", name: "graph_query", source: "Research World", path: "runtime://tools/graph_query", status: "ready", detail: "查询研究图谱" },
    { id: "read-file", name: "read_file", source: "Runtime catalog", path: "runtime://tools/read_file", status: "ready", detail: "读取工作区文件" },
    { id: "write-file", name: "write_file", source: "Runtime catalog", path: "runtime://tools/write_file", status: "ready", detail: "写入工作区文件" },
  ],
  mcp: [
    { id: "openai-docs", name: "openaiDeveloperDocs", source: "Codex 用户配置 · HTTP", path: "/home/q2635/.codex/config.toml", status: "ready", detail: "OpenAI 开发者文档" },
    { id: "open-design", name: "open-design", source: "Codex 用户配置 · stdio", path: "/home/q2635/.codex/config.toml", status: "ready", detail: "设计稿与画布服务" },
  ],
};

export const DEFAULT_DRAFT = {
  id: "agent:new", name: "Research Assistant", instructions: "围绕研究问题建立证据链，清楚区分事实、推断与待验证方向。",
  channel: "cli", runtimeId: "codex", providerId: "openai-compatible", model: RUNTIMES[0].models[0], effort: "high",
  selected: { skills: ["software-engineering", "codebase-design"], tools: ["read-skill", "graph-query", "read-file"], mcp: ["openai-docs"] },
};

export const GROUP_LABELS = { skills: "Skills", tools: "Tools", mcp: "MCP" };
