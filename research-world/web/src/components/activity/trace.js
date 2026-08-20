export function parseRecord(line) {
  try { return JSON.parse(line); } catch { return null; }
}

export function traceTurns(wire) {
  const traces = wire?.content?.trace || [];
  let previousPrompt = 0;
  let previousEnd = null;
  return traces.flatMap((trace) => groupTurns(trace)).map((turn) => {
    const prompt = responseUsage(turn.records).prompt_tokens || previousPrompt;
    const value = { ...turn, context: prompt - previousPrompt, wait: gapMs(previousEnd, turn.start) };
    previousPrompt = prompt;
    previousEnd = turn.end;
    return value;
  });
}

export function turnStats(turn) {
  const usage = responseUsage(turn.records);
  const errors = turn.records.filter((record) => record.error).length;
  const truncations = turn.records.filter((record) => record.payload?.response?.finish_reason === "length").length;
  return { tokens: usage.total_tokens || 0, context: turn.context, errors, truncations, wait: turn.wait };
}

export function responseUsage(records) {
  return records.reduce((usage, record) => record.payload?.response?.usage || usage, {});
}

function groupTurns(trace) {
  const records = trace.jsonl.split("\n").filter(Boolean).map(parseRecord).filter(Boolean);
  const indexes = [...new Set(records.map((record) => record.turn_index))];
  return indexes.map((index) => makeTurn(trace.name, index, records.filter((record) => record.turn_index === index)));
}

function makeTurn(name, index, records) {
  return { key: `${name}:${index}`, records, start: records[0]?.timestamp, end: records.at(-1)?.timestamp };
}

function gapMs(start, end) {
  return start && end ? Math.max(0, new Date(end) - new Date(start)) : 0;
}
