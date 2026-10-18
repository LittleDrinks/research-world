import {test,expect} from '@playwright/test';
import {layoutGraph} from '../src/graph/layout.js';

function disconnectedGroups() {
  const nodes=[],edges=[];
  for(let i=0;i<5;i++) {
    for(const [suffix,kind] of [['a','source'],['b','source'],['j','joint'],['t','direction']])nodes.push({id:`${i}${suffix}`,kind});
    for(const [a,b] of [['a','j'],['b','j'],['j','t']])edges.push({source:`${i}${a}`,target:`${i}${b}`,polarity:'joint'});
  }
  return {nodes,edges};
}

test('independent groups pack across the canvas without losing their edge endpoints',async()=>{
  const {nodes,edges}=disconnectedGroups();
  const layout=await layoutGraph(nodes,edges,1.4);
  expect(new Set(layout.nodes.filter(n=>n.id.endsWith('a')).map(n=>Math.round(n.position.x))).size).toBeGreaterThan(1);
  expect(layout.nodes).toHaveLength(nodes.length);
  expect(layout.routes.size).toBe(edges.length);
  for(const [index,edge] of edges.entries()) {
    const source=layout.nodes.find(n=>n.id===edge.source), target=layout.nodes.find(n=>n.id===edge.target);
    const points=layout.routes.get(`edge-${index}`);
    expect(Math.abs(points[0].x-source.position.x-source.width)).toBeLessThanOrEqual(2);
    expect(Math.abs(points.at(-1).x-target.position.x)).toBeLessThanOrEqual(2);
  }
  assertNoOverlap(layout.nodes);
});

function assertNoOverlap(nodes) {
  for(let i=0;i<nodes.length;i++) for(const b of nodes.slice(i+1)) {
    const a=nodes[i];
    const separate=a.position.x+a.width<=b.position.x || b.position.x+b.width<=a.position.x
      || a.position.y+a.height<=b.position.y || b.position.y+b.height<=a.position.y;
    expect(separate,`overlapping nodes ${a.id} and ${b.id}`).toBeTruthy();
  }
}
