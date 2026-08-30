#!/usr/bin/env bash
set -euo pipefail

root=$(git rev-parse --show-toplevel)
cd "$root"

required=(
  AGENTS.md
  CONTEXT.md
  docs/adr/0033-runtime-adapters-and-event-delivery.md
  docs/adr/0034-direct-kernel-fact-recording.md
  docs/agents/domain.md
  docs/agents/issue-tracker.md
  docs/agents/triage-labels.md
  docs/agents/governance-check.sh
)

for path in "${required[@]}"; do
  git ls-files --error-unmatch -- "$path" >/dev/null
  [[ -f "$path" ]] || {
    printf 'missing tracked file: %s\n' "$path" >&2
    exit 1
  }
done

require_text() {
  local file=$1
  local text=$2
  rg -Fq -- "$text" "$file" || {
    printf 'missing text: %s: %s\n' "$file" "$text" >&2
    exit 1
  }
}

current=(
  AGENTS.md
  CONTEXT.md
  docs/adr/0033-runtime-adapters-and-event-delivery.md
  docs/adr/0034-direct-kernel-fact-recording.md
  docs/agents/domain.md
  docs/agents/issue-tracker.md
  docs/agents/triage-labels.md
)

for needle in \
  'AgentSpec' \
  'multiple writers' \
  '不支持多写者' \
  '非 multiple-writers' \
  '同一 Adapter 的重叠 Turn' \
  'Runtime 拥有 Session' \
  'Runtime owns Session' \
  'Kernel 拥有 Run' \
  'Research Kernel 拥有 Run' \
  'Runtime 在调用 start 前拒绝同一 Adapter' \
  'Child Agent'; do
  if rg -n -F -i -- "$needle" "${current[@]}"; then
    printf 'forbidden current-governance text: %s\n' "$needle" >&2
    exit 1
  fi
done

for term in \
  'Research Kernel（研究内核）' \
  'Runtime**：Agent 执行的唯一所有者' \
  '一个 Run 可同时承载多个活跃 Turn' \
  '浏览器不选择或传递 Run id' \
  'Research Kernel' \
  'Runtime' \
  'Session' \
  'Run' \
  'Turn' \
  'Trace' \
  'Message' \
  'Runtime Adapter' \
  'Pi Adapter' \
  'Penguin Harness Adapter' \
  'Server-Sent Events (SSE)' \
  'Record' \
  'Connect' \
  'Remove' \
  'LocalMap'; do
  require_text CONTEXT.md "$term"
done

for term in \
  '**Message**：' \
  '**Research Graph（研究图谱）**：' \
  '**Subagent**：' \
  '**Child Run**：' \
  '**Child Turn**：'; do
  require_text CONTEXT.md "$term"
done

require_text CONTEXT.md '拥有 Project、Session、Message、Artifact、Record、Relation 与 LocalMap'
require_text CONTEXT.md '覆盖 Project、Session、Message、Artifact、Record、Connect、Remove 与 LocalMap'
require_text docs/adr/0033-runtime-adapters-and-event-delivery.md 'Research Kernel 拥有 Project、Session、Message、Artifact、Record、Relation 与 LocalMap'
require_text docs/adr/0034-direct-kernel-fact-recording.md 'Research Kernel 是 Project 研究状态的唯一深模块，拥有 Project、Session、Message、Artifact、Record、Relation 与 LocalMap'
require_text docs/adr/0034-direct-kernel-fact-recording.md 'Kernel Interface 只接受 Project、Session、Message、Artifact、Record、Connect、Remove 与 LocalMap'

for term in \
  'Agent 不持有模型访问配置或 Runtime Adapter 绑定' \
  '一个 Run 可同时承载多个活跃 Turn' \
  '关闭事件订阅不取消 Turn'; do
  require_text CONTEXT.md "$term"
done

require_text AGENTS.md '$anysearch'
require_text AGENTS.md 'TDD'
require_text AGENTS.md 'docker compose up --build -d'
require_text AGENTS.md 'Pi'

require_text docs/adr/0033-runtime-adapters-and-event-delivery.md 'status: accepted'
require_text docs/adr/0033-runtime-adapters-and-event-delivery.md 'supersedes:'
for term in Launch Submit Subscribe Cancel Delegate 'Message id' 'Trace `seq`' 'Last-Event-ID' EventSource 'Runtime 不得因为底层 harness 的实现方式把同一 Run 的重叠 Turn 改为互斥或拒绝' '@ai-sdk/react useChat' 'Pydantic AI UI Adapter' 'Penguin Harness Adapter'; do
  require_text docs/adr/0033-runtime-adapters-and-event-delivery.md "$term"
done

require_text docs/adr/0034-direct-kernel-fact-recording.md 'status: accepted'
require_text docs/adr/0034-direct-kernel-fact-recording.md 'supersedes:'
for term in Record Connect Remove LocalMap MMR Artifact '不持有准入、pending、admitted、ghost' '不自动去重' '不保留双检索路径'; do
  require_text docs/adr/0034-direct-kernel-fact-recording.md "$term"
done

require_text docs/agents/domain.md 'CONTEXT.md'
require_text docs/agents/domain.md 'ADR-0033'
require_text docs/agents/domain.md 'ADR-0034'
require_text docs/agents/issue-tracker.md 'gh issue view <number> --comments'
for file in "${current[@]}"; do
  rg -q '^# ' "$file" || {
    printf 'missing document title: %s\n' "$file" >&2
    exit 1
  }
done
require_text AGENTS.md 'docs/agents/domain.md'
require_text AGENTS.md 'docs/agents/issue-tracker.md'
require_text AGENTS.md 'docs/agents/triage-labels.md'
require_text AGENTS.md '[docs/agents/domain.md](docs/agents/domain.md)'
require_text AGENTS.md '[docs/agents/issue-tracker.md](docs/agents/issue-tracker.md)'
require_text AGENTS.md '[docs/agents/triage-labels.md](docs/agents/triage-labels.md)'
require_text docs/agents/domain.md '[CONTEXT.md](../../CONTEXT.md)'
require_text docs/agents/domain.md '[ADR-0033](../adr/0033-runtime-adapters-and-event-delivery.md)'
require_text docs/agents/domain.md '[ADR-0034](../adr/0034-direct-kernel-fact-recording.md)'
require_text CONTEXT.md 'Penguin Harness Adapter（Docker/MVP 默认）'
require_text docs/adr/0033-runtime-adapters-and-event-delivery.md 'Docker/MVP 默认交付 Adapter'
require_text docs/adr/0033-runtime-adapters-and-event-delivery.md '不静默切换、占位或模拟另一个 Adapter'
if rg -n 'https?://' AGENTS.md CONTEXT.md docs/agents; then
  printf 'external source URL outside ADR frontmatter\n' >&2
  exit 1
fi

printf 'governance check: PASS (%d tracked files)\n' "${#required[@]}"
