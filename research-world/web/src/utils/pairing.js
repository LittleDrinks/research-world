export function pairedEvents(events) {
  const results = new Map(events.filter((event) => event.type === "tool_result").map((event) => [event.entity.id, event]));
  return events.filter((event) => event.type !== "tool_result").map((event) => event.type === "tool_call" ? { ...event, pair: results.get(event.entity.id) } : event);
}
