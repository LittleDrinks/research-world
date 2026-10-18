function connectedGroups(nodes, edges) {
  const neighbors=new Map(nodes.map(node=>[node.id,new Set()]));
  for(const edge of edges) if(neighbors.has(edge.source)&&neighbors.has(edge.target)) {
    neighbors.get(edge.source).add(edge.target);neighbors.get(edge.target).add(edge.source);
  }
  const pending=new Set(neighbors.keys()), groups=[];
  while(pending.size) {
    const first=pending.values().next().value, queue=[first], ids=new Set([first]);pending.delete(first);
    while(queue.length) for(const adjacent of neighbors.get(queue.pop())) {
      if(pending.delete(adjacent)) {ids.add(adjacent);queue.push(adjacent);}
    }
    groups.push(ids);
  }
  return groups;
}

function componentInput(graph, ids, index) {
  const children=graph.children.filter(node=>ids.has(node.id));
  const ports=new Set(children.flatMap(node=>node.ports.map(port=>port.id)));
  return {...graph,id:`component-${index}`,children,
    edges:graph.edges.filter(edge=>ports.has(edge.sources[0])&&ports.has(edge.targets[0]))};
}

function shiftSection(section, x, y) {
  const shift=point=>({x:point.x+x,y:point.y+y});
  return {...section,startPoint:shift(section.startPoint),endPoint:shift(section.endPoint),
    bendPoints:(section.bendPoints||[]).map(shift)};
}

function translatedParts(parts, packed) {
  const offsets=new Map(packed.children.map(child=>[child.id,child]));
  return {children:parts.flatMap(part=>part.children.map(node=>({...node,
    x:node.x+offsets.get(part.id).x,y:node.y+offsets.get(part.id).y}))),
    edges:parts.flatMap(part=>part.edges.map(edge=>({...edge,
      sections:(edge.sections||[]).map(section=>shiftSection(section,offsets.get(part.id).x,offsets.get(part.id).y))})))};
}

export async function layoutComponents(elk, graph, nodes, edges, aspectRatio) {
  const groups=connectedGroups(nodes,edges);
  const parts=await Promise.all(groups.map((ids,index)=>elk.layout(componentInput(graph,ids,index))));
  const packed=await elk.layout({id:'component-pack',layoutOptions:{'elk.algorithm':'rectpacking',
    'elk.aspectRatio':String(aspectRatio),'elk.spacing.nodeNode':'100','elk.rectpacking.trybox':'false',
    'elk.rectpacking.orderBySize':'true','elk.rectpacking.widthApproximation.optimizationGoal':'ASPECT_RATIO_DRIVEN'},
    children:parts.map(part=>({id:part.id,width:part.width,height:part.height}))});
  return translatedParts(parts,packed);
}
