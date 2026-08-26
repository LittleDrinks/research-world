export function node(id, kind, state = {}) {
  return { id, project_id: "project:test", parent_id: null, lineage_id: `lineage:${id}`,
    kind, payload: { text: `${kind} 节点 ${id}` }, life_state: "admitted", direction_status: kind === "direction" ? "proposed" : null,
    working: 0, rejection_reason: null, rebuttal: null, created_at: "2026-08-16T00:00:00Z", updated_at: "2026-08-16T00:00:00Z", ...state };
}


export function project() {
  return { id: "project:test", name: "测试项目", title: "测试项目", root: "/projects/test", question: "如何验证新方向？",
    auto: 0, node_count: 2, run_count: 1, active_run_count: 1, created_at: "2026-08-16T00:00:00Z" };
}


export function thread(state = {}) {
  return { id: "thread:t1", project_id: "project:test", title: "讨论方向", session_id: "s-thread", agent_id: "research-assistant",
    archived: 0, created_at: "2026-08-16T00:00:00Z", updated_at: "2026-08-16T00:00:00Z", nodes: [node("node:q", "question")], ...state };
}


export function threadDetail(state = {}) {
  return { ...thread(), runtime: { session: { agent_spec: { id: "research-assistant", model: "qwen3.7-flash" } }, status: "completed",
    messages: [{ role: "user", content: "先看文献" }, { role: "assistant", content: "已带入问题上下文" }], turns: [], events: [] }, ...state };
}


export function run(state = {}) {
  return { id: "run:r1", project_id: "project:test", node_id: "node:q", lineage_id: "lineage:node:q", pipeline_id: "brainstorm",
    definition_snapshot: { id: "brainstorm", name: "生成研究方向", stages: [{ id: "generate", type: "prompt", agent: "research-assistant", output: "candidates" }] },
    stage: "generate", status: "running", payload: { thread_id: "thread:t1" }, auto: 0,
    created_at: "2026-08-16T00:00:00Z", updated_at: "2026-08-16T01:00:00Z",
    steps: [{ id: "step:s1", run_id: "run:r1", ordinal: 1, stage: "generate", status: "completed", confirm: 0,
      payload: { command: "collect sources" }, started_at: null, completed_at: null, output: { exit_code: 0 } }],
    events: [{ id: 1, run_id: "run:r1", actor: "planner", type: "agent_session",
      payload: { session_id: "s-abc", turn_id: "t-1", stage_id: "generate", usage: { prompt_tokens: 120 } }, time: "2026-08-16T00:30:00Z" }], ...state };
}


export function sessionInspect() {
  return { session: { agent_spec: { id: "research-assistant", model: "qwen3.7-flash" }, workspace: "/projects/test" }, status: "completed",
    messages: [{ role: "user", content: "生成候选" }, { role: "assistant", content: "候选如下" }],
    turns: [{ id: "t-1", input: [{ type: "text", text: "生成候选" }], output: "候选如下", status: "completed",
      events: [
        { type: "turn_start", seq: 1, time: "2026-08-16T00:30:00Z", session_id: "s-abc", turn_id: "t-1", data: { prompt: [{ type: "text", text: "生成候选" }] } },
        { type: "tool_call", seq: 2, time: "2026-08-16T00:30:01Z", session_id: "s-abc", turn_id: "t-1", data: { tool_call_id: "call-1", name: "graph_query", arguments: "{\"action\":\"search\"}" } },
        { type: "tool_result", seq: 3, time: "2026-08-16T00:30:02Z", session_id: "s-abc", turn_id: "t-1", data: { tool_call_id: "call-1", name: "graph_query", content: "[]", is_error: false } },
        { type: "model_response", seq: 4, time: "2026-08-16T00:30:03Z", session_id: "s-abc", turn_id: "t-1", data: { message: { role: "assistant", content: "候选如下" }, usage: {} } },
        { type: "turn_end", seq: 5, time: "2026-08-16T00:30:04Z", session_id: "s-abc", turn_id: "t-1", data: { status: "completed", result_text: "候选如下", usage: {} } }] }],
    events: [] };
}


export function catalog() {
  return { endpoints: [{ id: "openai-compatible", name: "OpenAI 兼容端点", available: true }, { id: "codex", name: "Codex CLI", available: true }],
    models: [{ id: "qwen3.7-flash", endpoint: "openai-compatible" }, { id: "gpt-5.2", endpoint: "codex" }],
    skills: [{ id: "skill-review", name: "文献综述", description: "检索并综述相关文献", source: "workspace" }],
    tools: [{ id: "read_resource", name: "读取引用节点", status: "ready" },
      { id: "graph_query", name: "查询研究图谱", status: "ready" },
      { id: "lean4", name: "Lean4", description: "形式化验证", source: "runtime", status: "ready" }],
    presets: [preset()] };
}


export function preset(state = {}) {
  return { id: "math-proof", name: "数学证明", description: "形式化证明 Agent：将命题形式化为 Lean4 定理并调用 Lean4 Tool 验证。",
    spec: { id: "math-proof", name: "数学证明助手", instructions: "把研究中的数学命题形式化为 Lean4 定理并调用 Lean4 Tool 验证。",
      skills: [], tools: ["lean4"] },
    tools: [{ id: "lean4", status: "ready" }], ...state };
}


export function agentDraft(state = {}) {
  const value = preset();
  return { preset_id: value.id, reason: value.description,
    spec: { ...value.spec, endpoint: "openai-compatible", model: "qwen3.7-flash",
      options: { reasoning_effort: "medium", sandbox: "read-only", max_rounds: 12, token_budget: 200000 } },
    tools: value.tools, skills: value.skills || [], confirmable: true, issues: [], ...state };
}


export function agents() {
  return [{ id: "research-assistant", name: "研究助手", endpoint: "openai-compatible", model: "qwen3.7-flash",
    instructions: "围绕研究问题进行严谨讨论。", skills: [], tools: ["read_resource"],
    options: { reasoning_effort: "high", sandbox: "read-only", max_rounds: 12, token_budget: 200000 } }];
}


export function bootstrap(state = {}) {
  return { projects: [project()], active_project_id: "project:test",
    nodes: [node("node:q", "question"), node("node:d", "direction", { parent_id: "node:q" })],
    edges: [], runs: [run()], pipelines: [{ id: "brainstorm", name: "生成研究方向", stages: [] }, { id: "research", name: "规划与验证", stages: [] }],
    threads: [thread()], slots: [{ index: 1, run: null }, { index: 2, run: null }], ...state };
}


export function sse(frames) {
  return { headers: { "content-type": "text/event-stream" },
    body: `${frames.map(([event, data]) => `event: ${event}\ndata: ${JSON.stringify(data)}`).join("\n\n")}\n\n` };
}


export async function mockBase(page, body = bootstrap()) {
  await page.route(/\/api\/v1\/bootstrap/, (route) => route.fulfill({ json: body }));
  await page.route(/\/api\/v1\/agents$/, (route) => route.fulfill({ json: agents() }));
  await page.route(/\/api\/v1\/runtime\/catalog/, (route) => route.fulfill({ json: catalog() }));
  await page.route(/\/api\/v1\/runtime\/sessions\/[^/]+$/, (route) => route.fulfill({ json: sessionInspect() }));
}
