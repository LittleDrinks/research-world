#!/usr/bin/env bash
set -euo pipefail

root=$(git rev-parse --show-toplevel)
cd "$root"

required=(
  AGENTS.md
  CONTEXT.md
  MEMORY.md
  docs/adr/0033-runtime-adapters-and-event-delivery.md
  docs/adr/0034-direct-kernel-fact-recording.md
  docs/adr/0038-web-model-conversation-closure.md
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
  MEMORY.md
  docs/adr/0033-runtime-adapters-and-event-delivery.md
  docs/adr/0034-direct-kernel-fact-recording.md
  docs/adr/0038-web-model-conversation-closure.md
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
  'Runtime 拥有模型访问配置' \
  'Compose 只把仓库根' \
  '只把仓库根 `apikey` 与 `baseurl` 注入 Penguin Server' \
  '仓库根 .env' \
  '仓库根 `.env` 的 `apikey`、`baseurl`' \
  '凭证只在仓库根' \
  '凭证不进入 Agent、Session、Trace、control 或 Web' \
  'Web 均不包含模型凭证或 Penguin token' \
  'Kernel 拥有 Run' \
  'Research Kernel 拥有 Run' \
  'Runtime 在调用 start 前拒绝同一 Adapter' \
  '托管执行域由 Runtime 直接启动并管理 harness' \
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
  'Research World 设置 facade' \
  '模型访问配置' \
  '部署级设置' \
  'Penguin 是唯一持久所有者' \
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
  '模型访问配置' \
  '部署级设置' \
  'Penguin 是唯一持久所有者' \
  '一个 Run 可同时承载多个活跃 Turn' \
  '关闭事件订阅不取消 Turn'; do
  require_text CONTEXT.md "$term"
done
require_text CONTEXT.md '只转发模型设置操作（测试、保存、掩码读取、替换与清除）；不负责对话协调'
require_text CONTEXT.md '明文 apikey 可短暂进入 Web password input 和明确的测试、保存或替换请求'

require_text MEMORY.md '模型访问配置是部署级设置'
require_text MEMORY.md 'Research World 设置 facade 只转发测试、保存、掩码读取、替换与清除'
require_text MEMORY.md 'Penguin 是唯一持久所有者'

require_text AGENTS.md '$anysearch'
require_text AGENTS.md 'TDD'
require_text AGENTS.md 'docker compose up --build -d'
require_text AGENTS.md 'Pi'
require_text AGENTS.md 'Review 请求返工时，修改实现前先用 `$anysearch` 检索成熟实践'
require_text AGENTS.md '同一 issue 两次返工后，第三次实现前先复核 issue 并决定拆票或重开票'
require_text AGENTS.md 'implementation+review round'
require_text AGENTS.md '被审 worker commit 的完整 hash'
require_text AGENTS.md 'reviewer result、findings/opinion'
require_text AGENTS.md 'end-to-end wall-clock duration'

require_text docs/adr/0033-runtime-adapters-and-event-delivery.md 'status: accepted'
require_text docs/adr/0033-runtime-adapters-and-event-delivery.md 'supersedes:'
for term in Launch Submit Subscribe Cancel Delegate 'Message id' 'Trace `seq`' 'Last-Event-ID' EventSource '独立 Runtime JSON/SSE 服务' '按预期 Session 作用域校验 Subscribe' '在 SSE 响应开始前完成校验' 'Adapter 原生身份恢复' 'Runtime Settings 管理面不属于五动作执行接口' 'Runtime 不得因为底层 harness 的实现方式把同一 Run 的重叠 Turn 改为互斥或拒绝' '@ai-sdk/react useChat' 'Pydantic AI UI Adapter' 'Penguin Harness Adapter'; do
  require_text docs/adr/0033-runtime-adapters-and-event-delivery.md "$term"
done

require_text docs/adr/0034-direct-kernel-fact-recording.md 'status: accepted'
require_text docs/adr/0034-direct-kernel-fact-recording.md 'supersedes:'
for term in Record Connect Remove LocalMap MMR Artifact '不持有准入、pending、admitted、ghost' '不自动去重' '不保留双检索路径'; do
  require_text docs/adr/0034-direct-kernel-fact-recording.md "$term"
done

require_text docs/adr/0038-web-model-conversation-closure.md 'status: accepted'
require_text docs/adr/0038-web-model-conversation-closure.md 'supersedes:'
for term in '稳定 UUID 幂等键' '唯一 `session_id`' '重复 Submit 返回原 Turn' '未绑定 Session、跨 Session Message 与 Child Run 目标在 Runtime Adapter 启动和 Trace 写入前失败' '非空 `completed` 或 `limit` 回答' 'Last-Event-ID' 'Web 模型设置属于本闭环范围' '测试、保存、掩码读取、替换、清除' 'Research World 设置 facade 只转发' 'Runtime Settings 管理面不属于五动作执行接口' '未配置模型时 Compose 和应用仍保持健康' 'Chat 不提交模型 Turn' 'Compose 管理 Penguin Harness Adapter 的固定 v0.2.9 server 进程' '每次启动铸造新的 bearer token' '每次新请求重新读取 token 文件' 'control/Web 不获得 token' '不设计外部生成或手工轮换' '仓库根环境文件不注入模型凭证' 'Research World/Compose 不在启动时调用 Penguin 的模型、受管 Project、Agent 或 Task API' 'Delivery entrypoint 每次容器启动生成高熵 `PENGUIN_SEED_ADMIN_PASSWORD`' '只通过进程环境传给官方 server' '不写入镜像、data root、日志或响应'; do
  require_text docs/adr/0038-web-model-conversation-closure.md "$term"
done
require_text docs/adr/0038-web-model-conversation-closure.md '以 `0600` 写入专用数据根的 token 文件'
require_text docs/adr/0038-web-model-conversation-closure.md '明文 apikey 可短暂进入 Web password input 和明确的测试、保存或替换请求'

if rg -n 'seed-admin-password|seed_file' research-world/penguin-entrypoint.sh; then
  printf 'persistent Penguin seed password path in entrypoint\n' >&2
  exit 1
fi

require_text docs/agents/domain.md 'CONTEXT.md'
require_text docs/agents/domain.md 'ADR-0033'
require_text docs/agents/domain.md 'ADR-0034'
require_text docs/agents/domain.md 'ADR-0038'
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
require_text docs/agents/domain.md '[ADR-0038](../adr/0038-web-model-conversation-closure.md)'
require_text CONTEXT.md 'Penguin Harness Adapter（Docker/MVP 默认）'
require_text docs/adr/0033-runtime-adapters-and-event-delivery.md 'Docker/MVP 默认交付 Adapter'
require_text docs/adr/0033-runtime-adapters-and-event-delivery.md '不静默切换、占位或模拟另一个 Adapter'
if rg -n 'https?://' AGENTS.md CONTEXT.md docs/agents; then
  printf 'external source URL outside ADR frontmatter\n' >&2
  exit 1
fi

printf 'governance check: PASS (%d tracked files)\n' "${#required[@]}"
