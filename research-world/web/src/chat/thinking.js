import {unified} from 'unified';
import remarkParse from 'remark-parse';
import remarkMath from 'remark-math-extended';
import {visit} from 'unist-util-visit';

const parser=unified().use(remarkParse).use(remarkMath);
const TAG=/<(\/?)(thinking|think)>/g;
const LITERAL=new Set(['code','inlineCode','math','inlineMath','html','link','image','definition','linkReference','imageReference']);

function literalRanges(source) {
  // Mask control tags only for syntax analysis; preserve offsets and the original text.
  const tree=parser.parse(source.replace(TAG,tag=>'x'.repeat(tag.length))),ranges=[];
  visit(tree,node=>{if(LITERAL.has(node.type))ranges.push([node.position.start.offset,node.position.end.offset]);});
  return ranges;
}

function markers(source) {
  if(!source.includes('<think')&&!source.includes('</think'))return [];
  const ranges=literalRanges(source);
  return [...source.matchAll(TAG)].filter(match=>{
    const escaped=(/\\+$/.exec(source.slice(0,match.index))?.[0].length||0)%2;
    return !escaped&&!ranges.some(([start,end])=>start<=match.index&&match.index<end);
  });
}

function append(parts,type,text) {
  if(!text)return;
  if(parts.at(-1)?.type===type)parts.at(-1).text+=text;
  else parts.push({type,text});
}

export function splitThinking(source,initial=[]) {
  const state=[...initial],parts=[];let cursor=0;
  for(const match of markers(source)) {
    const [,closing,name]=match;
    if(closing&&state.at(-1)!==name)continue;
    append(parts,state.length?'thinking':'text',source.slice(cursor,match.index));
    if(closing)state.pop();else state.push(name);
    cursor=match.index+match[0].length;
  }
  append(parts,state.length?'thinking':'text',source.slice(cursor));
  return {parts,state};
}

export function thinkingParts(parts) {
  let state=[];
  return parts.flatMap(part=>{
    if(part.type!=='text')return [part];
    const result=splitThinking(part.text,state);state=result.state;
    return result.parts.map((value,index)=>({...value,id:`${part.id}:${index}`}));
  });
}
