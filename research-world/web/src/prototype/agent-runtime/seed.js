export const AGENTS = [
  { id: "agent:source-researcher", name: "Source Researcher", preset: "source-researcher", runtime: "Codex CLI", model: "gpt-5.6-sol", status: "ready", modified: "12 min" },
  { id: "agent:proof-reviewer", name: "Proof Reviewer", preset: "math-proof", runtime: "Pi", model: "anthropic/claude-opus-4-1", status: "auth-required", modified: "2 h" },
  { id: "agent:legacy-scout", name: "Legacy Scout", preset: "blank", runtime: "DeepSeek Harness", model: "deepseek-v3.2-speciale-experimental-long-context", status: "unsupported", modified: "3 d" },
];

export const RUNTIMES = [
  { id: "codex", name: "Codex CLI", executable: "codex", version: "0.149.0", source: "symlink · WSL", path: "~/.local/bin/codex -> ~/.codex/packages/standalone/current/bin/codex", status: "ready", reason: "Adapter、版本与认证已确认", checked: "12:04:18", caps: ["streaming", "resume", "model-select", "auth-probe"] },
  { id: "kimi", name: "Kimi Code CLI", executable: "kimi", version: "0.38.0", source: "user-path · WSL", path: "~/.kimi-code/bin/kimi", status: "found", reason: "auth_probe_unavailable · 仅确认 executable 与 version", checked: "12:04:17", caps: ["interactive", "workspace"] },
  { id: "pi", name: "Pi Coding Agent", executable: "pi", version: "0.84.2", source: "symlink · WSL", path: "~/.nvm/versions/node/v24.14.0/bin/pi", status: "auth-required", reason: "auth_missing · 所选 provider 未配置凭证", checked: "12:04:17", caps: ["model-select", "auth-probe"] },
  { id: "gemini", name: "Gemini CLI", executable: "gemini", version: null, source: "WSL PATH", path: null, status: "missing", reason: "not_on_path · 当前 execution realm 未找到", checked: "12:04:16", caps: [] },
  { id: "custom", name: "Lab Agent CLI", executable: "lab-agent", version: null, source: "explicit · container", path: "/opt/research/runtime/bin/lab-agent-with-an-intentionally-long-executable-name", status: "error", reason: "probe_timeout · version probe 超过 2 s", checked: "12:04:15", caps: [] },
  { id: "dsh", name: "DeepSeek Harness", executable: "dsh", version: "0.1.1-rc.1", source: "shim · WSL", path: "~/.volta/bin/dsh", status: "unsupported", reason: "adapter_unavailable · Agent Runtime 尚无兼容 Adapter", checked: "12:04:15", caps: ["interactive"] },
];

export const SKILLS = [
  { id: "source-research", name: "source-research", scope: "project", path: ".agents/skills/source-research/SKILL.md", status: "ready", description: "检索当前官方一手来源，记录访问时间、版本、许可边界与可复核证据，并把事实、推断和未决点分开。" },
  { id: "codebase-design", name: "codebase-design", scope: "user", path: "~/.agents/skills/codebase-design/SKILL.md", status: "ready", description: "从领域边界、deep module contract、状态所有权和失败隔离分析架构决策。" },
  { id: "long-form-validation", name: "long-form-validation-and-independent-evidence-review", scope: "workspace", path: "/workspace/.agents/skills/validation/with/a/very/long/nested/path/SKILL.md", status: "ready", description: "对跨模块实现执行独立证据审阅，核对用户可见验收、诊断输出、移动端布局和敏感数据边界。" },
];

export const TOOLS = [
  { id: "read_skill", name: "Read Skill", source: "builtin", status: "ready", description: "按稳定 Skill id 读取正文。" },
  { id: "graph.query", name: "Graph Query", source: "builtin", status: "ready", description: "查询项目事实图谱并返回结构化结果。" },
  { id: "browser.opencli", name: "OpenCLI Browser", source: "adapter · browser", status: "ready", description: "通过 Tool adapter 驱动真实 Chrome 做页面审计与交互；不是 Agent CLI 或 execution Runtime。" },
  { id: "docs.openai", name: "OpenAI Developer Docs", source: "MCP · HTTP", status: "setup-required", description: "由 MCP Tool Adapter 提供官方 OpenAI 文档检索。Profile 仍只保存 Tool id。" },
  { id: "design.canvas", name: "Design Canvas", source: "MCP · stdio", status: "unavailable", description: "本地设计画布服务；transport 只在诊断中展开。" },
];

export const READINESS = [
  { name: "Execution Runtime", status: "ready", detail: "codex · 0.149.0" },
  { name: "Endpoint / model", status: "ready", detail: "openai-compatible · gpt-5.6-sol" },
  { name: "Skills", status: "ready", detail: "3 selected · 3 available" },
  { name: "Tools", status: "blocked", detail: "docs.openai requires setup" },
  { name: "Workspace", status: "ready", detail: "project workspace · read/write" },
  { name: "Secrets", status: "unknown", detail: "1 configured · 1 not checked" },
];

export const DEFAULT_PROFILE = {
  id: "agent:source-researcher", name: "Source Researcher", runtime: "codex", endpoint: "openai-compatible",
  model: "gpt-5.6-sol-2026-08-20-enterprise-reasoning-preview", reasoning: "high", workspace: "Project workspace",
  instructions: "只使用可复核来源建立证据链；清楚区分事实、推断、未决点和独立 QA 结论。",
  skills: ["source-research", "codebase-design", "long-form-validation"], tools: ["read_skill", "graph.query", "browser.opencli"],
};

export const PREPARE_STEPS = [
  { name: "校验 catalog revision", detail: "tool docs.openai · revision 7f2c", state: "queued" },
  { name: "确认网络来源", detail: "允许访问受控官方 endpoint；不运行任意 shell", state: "queued" },
  { name: "写入 Runtime 托管配置", detail: "仅写 Tool Adapter 配置；不写 AgentSpec secret", state: "queued" },
  { name: "执行 readiness probe", detail: "2 s timeout · 输出脱敏", state: "queued" },
];

export const TABS = [
  ["profile", "Profile"], ["runtime", "CLI / Runtime"], ["model", "模型"], ["skills", "Skills"],
  ["tools", "Tools 与 MCP"], ["diagnostics", "诊断"],
];
