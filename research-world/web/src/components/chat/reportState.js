const replacementKey = (threadId) => `report-replacements:${threadId}`;


export function createReportRequests() {
  const sequences = new Map();
  return {
    next(scope) {
      const sequence = (sequences.get(scope) || 0) + 1;
      sequences.set(scope, sequence);
      return { scope, sequence };
    },
    latest(request) { return sequences.get(request.scope) === request.sequence; },
  };
}


export function traceReportKey(report) {
  return `report-${report.turn_id || "untraced"}-${report.seq ?? "unsequenced"}`;
}


export function loadReportReplacements(threadId) {
  const value = sessionStorage.getItem(replacementKey(threadId));
  return value ? publicationIds(JSON.parse(value)) : {};
}


export function saveReportReplacements(threadId, replacements) {
  sessionStorage.setItem(replacementKey(threadId), JSON.stringify(replacements));
}


export function replacementsForThread(threadId, state) {
  return state.threadId === threadId ? state.replacements : loadReportReplacements(threadId);
}


export function replaceTrace(threadId, replacements, trace, publicationId) {
  const next = { ...replacements, [traceReportKey(trace)]: publicationId };
  saveReportReplacements(threadId, next);
  return next;
}


function publicationIds(replacements) {
  return Object.fromEntries(Object.entries(replacements).filter(([, value]) => typeof value === "string" && value.startsWith("publication:")));
}
