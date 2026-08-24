export const RUNTIMES = [
  { id: "codex", realm: "wsl:ubuntu", name: "Codex CLI", executable: "codex", version: "0.149.1", source: "installer", path: "~/.local/bin/codex", resolvedPath: "~/.codex/packages/standalone/releases/0.149.1-x86_64-unknown-linux-musl/bin/codex", status: "ready", reason: "Adapter、版本与认证已确认", checked: "2026-08-24T14:23:05Z", caps: ["streaming", "resume", "model-select", "auth-probe"] },
  { id: "codex", realm: "windows:host", name: "Codex CLI", executable: "codex.exe", version: null, source: "path", path: null, resolvedPath: null, status: "missing", reason: "not_on_path · fixture 的 Windows realm 未找到", checked: "2026-08-24T14:23:05Z", caps: [] },
  { id: "kimi-code", realm: "wsl:ubuntu", name: "Kimi Code CLI", executable: "kimi", version: "0.38.0", source: "installer", path: "~/.kimi-code/bin/kimi", resolvedPath: "~/.kimi-code/bin/kimi", status: "found", reason: "auth_probe_unavailable · config valid 不等于 authenticated", checked: "2026-08-24 18:20:00", caps: ["interactive", "workspace"] },
  { id: "pi", realm: "wsl:ubuntu", name: "Pi Coding Agent", executable: "pi", version: "0.84.2", source: "npm", path: "~/.nvm/versions/node/v24.14.0/bin/pi", resolvedPath: "~/.nvm/versions/node/v24.14.0/lib/node_modules/@earendil-works/pi-coding-agent/dist/cli.js", status: "found", reason: "auth_probe_unavailable · 未推断 authenticated", checked: "2026-08-24 18:20:00", caps: ["model-select"] },
  { id: "gemini", realm: "wsl:ubuntu", name: "Gemini CLI", executable: "gemini", version: null, source: "path", path: null, resolvedPath: null, status: "missing", reason: "not_on_path · 当前 execution realm 未找到", checked: "2026-08-24 18:20:00", caps: [] },
  { id: "lab-agent", realm: "container:runtime", name: "Lab Agent CLI", executable: "lab-agent", version: null, source: "explicit", path: "/opt/research/runtime/bin/lab-agent-with-an-intentionally-long-executable-name", resolvedPath: "/opt/research/runtime/releases/unusually-long-lab-agent-build/bin/lab-agent", status: "error", reason: "probe_timeout · version probe 超过 2 s", checked: "2026-08-24 18:20:00", caps: [] },
  { id: "claude", realm: "wsl:ubuntu", name: "Claude Code", executable: "claude", version: "2.1.237", source: "installer", path: "~/.local/bin/claude", resolvedPath: "~/.local/share/claude/versions/2.1.237", status: "unsupported", reason: "adapter_unavailable · Agent Runtime 尚无兼容 Adapter", checked: "2026-08-24 18:20:00", caps: ["interactive", "auth-probe"] },
];

export const ENDPOINTS = [
  { id: "codex-account", name: "Codex account", runtimes: ["codex"], secret: "not-required", secretReason: null, models: ["gpt-5.6-sol-2026-08-20-enterprise-reasoning-preview", "gpt-5.6-terra"] },
  { id: "openai-compatible", name: "OpenAI compatible", runtimes: ["codex", "pi", "kimi-code"], secret: "missing", secretReason: "secret_not_configured", models: ["qwen3.7-flash", "deepseek-v3.2-speciale-experimental-long-context"] },
  { id: "invalid-endpoint", name: "Invalid credential fixture", runtimes: ["codex"], secret: "invalid", secretReason: "secret_validation_failed", models: ["gpt-5.6-terra"] },
  { id: "anthropic", name: "Anthropic API", runtimes: ["claude", "pi"], secret: "configured", secretReason: null, models: ["claude-opus-4-1"] },
];

export const SKILLS = [
  { id: "source-research", name: "source-research", scope: "project", path: ".agents/skills/source-research/SKILL.md", status: "ready", description: "检索当前官方一手来源，记录访问时间、版本、许可边界与可复核证据，并把事实、推断和未决点分开。" },
  { id: "codebase-design", name: "codebase-design", scope: "user", path: "~/.agents/skills/codebase-design/SKILL.md", status: "ready", description: "从领域边界、deep module contract、状态所有权和失败隔离分析架构决策。" },
  { id: "long-form-validation", name: "long-form-validation-and-independent-evidence-review", scope: "workspace", path: "/workspace/.agents/skills/validation/with/a/very/long/nested/path/SKILL.md", status: "ready", description: "对跨模块实现执行独立证据审阅，核对用户可见验收、诊断输出、移动端布局和敏感数据边界。" },
];

export const TOOLS = [
  { id: "read_skill", name: "Read Skill", source: "builtin", status: "ready", description: "按稳定 Skill id 读取正文。" },
  { id: "graph.query", name: "Graph Query", source: "builtin", status: "ready", description: "查询项目事实图谱并返回结构化结果。" },
  { id: "browser.opencli", name: "OpenCLI Browser", source: "browser Tool adapter", status: "ready", description: "驱动真实 Chrome 做 WebUI 审计；不参与 Agent CLI discovery、runtime、认证、readiness 或 prepare。" },
  { id: "docs.openai", name: "OpenAI Developer Docs", source: "MCP Tool adapter · HTTP", status: "setup-required", description: "由 #43 Tool catalog 提供官方 OpenAI 文档检索；Profile 只保存 Tool id。" },
  { id: "design.canvas", name: "Design Canvas", source: "MCP Tool adapter · stdio", status: "unavailable", description: "本地设计画布服务；transport 只在诊断中展开。" },
];

const SOURCE_PROFILE = {
  id: "agent:source-researcher", name: "Source Researcher", preset: "source-researcher", runtime: "codex", realm: "wsl:ubuntu",
  endpoint: "codex-account", model: "gpt-5.6-sol-2026-08-20-enterprise-reasoning-preview", reasoning: "high",
  workspace: "Project workspace", sandbox: "workspace-write", instructions: "只使用可复核来源建立证据链；清楚区分事实、推断、未决点和独立 QA 结论。",
  skills: ["source-research", "codebase-design", "long-form-validation"], tools: ["read_skill", "graph.query", "browser.opencli"], modified: "12 min",
};

export const PROFILES = [
  SOURCE_PROFILE,
  { ...SOURCE_PROFILE, id: "agent:proof-reviewer", name: "Proof Reviewer", preset: "math-proof", model: "gpt-5.6-terra", instructions: "复核证明步骤、工具证据与反例边界。", skills: ["codebase-design"], tools: ["read_skill"], modified: "2 h" },
  { ...SOURCE_PROFILE, id: "agent:windows-codex", name: "Windows Codex Snapshot", preset: "blank", realm: "windows:host", modified: "1 d" },
  { ...SOURCE_PROFILE, id: "agent:legacy-scout", name: "Legacy Scout", preset: "blank", runtime: "kimi-code", endpoint: "openai-compatible", model: "deepseek-v3.2-speciale-experimental-long-context", reasoning: "medium", skills: [], tools: [], modified: "3 d" },
];

export const DRAFTS = {
  preset: { ...SOURCE_PROFILE, id: "agent:source-researcher-copy", name: "Source Researcher Copy", rationale: ["Preset 推荐 Codex ready runtime 与 account endpoint。", "推荐 source research Skills 和 browser.opencli WebUI Tool。"], goal: "" },
  blank: { id: "", name: "", preset: "blank", runtime: "", realm: "", endpoint: "", model: "", reasoning: "", workspace: "", sandbox: "", instructions: "", skills: [], tools: [], modified: "now", rationale: ["空白草稿不推荐或预填 runtime、Endpoint、model、Skill、Tool、MCP。"], goal: "" },
  orchestrator: { ...SOURCE_PROFILE, id: "agent:source-auditor", name: "Source Auditor", preset: "orchestrator", endpoint: "openai-compatible", model: "qwen3.7-flash", tools: ["read_skill", "browser.opencli", "docs.openai"], rationale: ["目标需要官方来源核验，推荐 source-research Skill。", "browser.opencli 只用于真实 WebUI；docs.openai 是 MCP 来源 Tool。"], goal: "" },
};

export const PREPARE_STEPS = [
  { name: "校验 CLI catalog revision", detail: "gemini · fixed source revision 7f2c", state: "queued" },
  { name: "确认下载与网络边界", detail: "官方 package source · 需要网络 · 不读取 secret", state: "queued" },
  { name: "写入受控 CLI installation", detail: "仅目标 realm；不写 Profile 或 Tool catalog", state: "queued" },
  { name: "执行 version probe", detail: "2 s timeout · stdout/stderr 解析后丢弃", state: "queued" },
];

export const TABS = [
  ["profile", "Profile"], ["runtime", "CLI / Runtime"], ["model", "模型"], ["skills", "Skills"],
  ["tools", "Tools 与 MCP"], ["diagnostics", "诊断"],
];
