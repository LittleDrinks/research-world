import {visit} from 'unist-util-visit';

export function preserveMathCode() {
  return tree=>visit(tree,'code',node=>{
    if(node.lang!=='math')return;
    node.data={...node.data,hProperties:{...node.data?.hProperties,className:['language-math-source']}};
  });
}
