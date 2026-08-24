import { nodeText, RUN_STATUS, shortId } from "../utils/labels";


const KIND_TONE = { question: "question", source: "source", direction: "direction", experiment: "experiment" };


export function journalEntries(nodes, runs) {
  const entries = nodes.flatMap(nodeEntries).concat(runs.flatMap(runEntries));
  return entries.sort((left, right) => new Date(right.time) - new Date(left.time));
}


function nodeEntries(node) {
  const items = [{ time: node.created_at, tone: KIND_TONE[node.kind], text: `创建${KIND_LABEL(node)}：${nodeText(node)}`, ref: node.id }];
  if (node.life_state === "admitted" && node.updated_at > node.created_at)
    items.push({ time: node.updated_at, tone: "success", text: `入图：${nodeText(node)}`, ref: node.id });
  if (node.life_state === "ghost")
    items.push({ time: node.updated_at, tone: "failed", text: `驳回：${nodeText(node)}${node.rejection_reason ? ` —— ${node.rejection_reason}` : ""}`, ref: node.id });
  if (node.direction_status === "supported") items.push({ time: node.updated_at, tone: "success", text: `方向获支持：${nodeText(node)}`, ref: node.id });
  if (node.direction_status === "refuted") items.push({ time: node.updated_at, tone: "failed", text: `方向被反驳：${nodeText(node)}`, ref: node.id });
  return items;
}


function runEntries(run) {
  const name = run.definition_snapshot?.name || run.pipeline_id;
  const items = [{ time: run.created_at, tone: "running", text: `启动运行：${name}`, ref: run.id }];
  if (["completed", "failed", "paused"].includes(run.status))
    items.push({ time: run.updated_at, tone: run.status === "completed" ? "success" : "failed", text: `运行${RUN_STATUS[run.status]}：${name}`, ref: run.id });
  return items;
}


function KIND_LABEL(node) {
  return { question: "问题", source: "来源", direction: "方向", experiment: "实验" }[node.kind] || "节点";
}


export function shortRef(ref) {
  return shortId(ref);
}
