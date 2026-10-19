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

function thinkingSpans(source) {
  const stack=[],spans=[];let cursor=0;
  for(const match of markers(source)) {
    const [,closing,name]=match;
    if(closing&&stack.at(-1)!==name)continue;
    if(cursor<match.index)spans.push({type:stack.length?'thinking':'text',start:cursor,end:match.index});
    if(closing)stack.pop();else stack.push(name);
    cursor=match.index+match[0].length;
  }
  if(cursor<source.length)spans.push({type:stack.length?'thinking':'text',start:cursor,end:source.length});
  return spans;
}

function projectSpans(source,start,end,spans) {
  const parts=[];
  for(const span of spans) {
    const left=Math.max(start,span.start),right=Math.min(end,span.end);
    if(left<right)append(parts,span.type,source.slice(left,right));
  }
  return parts;
}

export function splitThinking(source) {
  return {parts:projectSpans(source,0,source.length,thinkingSpans(source))};
}

export function thinkingParts(parts) {
  const source=parts.filter(part=>part.type==='text').map(part=>part.text).join('');
  const spans=thinkingSpans(source);let cursor=0;
  return parts.flatMap(part=>{
    if(part.type!=='text')return [part];
    const projected=projectSpans(source,cursor,cursor+part.text.length,spans);cursor+=part.text.length;
    return projected.map((value,index)=>({...value,id:`${part.id}:${index}`}));
  });
}
