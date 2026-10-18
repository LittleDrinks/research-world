export function projectConditions(records, relations, conditions) {
  const ids = new Set(records.map(record => record.id));
  const nodes = [...records, ...conditions.map(condition => ({id:condition.id, kind:'joint', condition}))];
  const edges = relations.filter(edge => ids.has(edge.source) && ids.has(edge.target));
  for (const condition of conditions) {
    for (const member of condition.members.filter(member => ids.has(member.record_id))) {
      edges.push({id:`${condition.id}:${member.record_id}`, source:member.record_id, target:condition.id,
        polarity:'joint', role:member.role, jointId:condition.id});
    }
    if (ids.has(condition.target_id)) edges.push({id:`${condition.id}:target`, source:condition.id,
      target:condition.target_id, polarity:'joint', role:'目标陈述', jointId:condition.id});
  }
  return {nodes, edges};
}
