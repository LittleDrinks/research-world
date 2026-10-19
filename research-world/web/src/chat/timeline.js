import {thinkingParts} from './thinking';

export function mergeEvents(saved,live){
  return [...new Map([...saved,...live].map(event=>[event.seq,event])).values()].sort((a,b)=>a.seq-b.seq);
}

export function timeline(events){
  const parts=[],tools=new Map();
  for(const event of events){
    if(event.type==='delta'){
      if(parts.at(-1)?.type!=='text')parts.push({type:'text',id:event.seq,text:''});
      parts.at(-1).text+=event.data.text||'';
    }else if(event.type==='tool'){
      if(!tools.has(event.data.id)){
        const part={type:'tool',id:event.data.id,tool:{}};tools.set(part.id,part);parts.push(part);
      }
      Object.assign(tools.get(event.data.id).tool,event.data);
    }else if(event.type==='child_result')parts.push({type:'child',id:event.seq,...event.data});
  }
  return thinkingParts(parts);
}
