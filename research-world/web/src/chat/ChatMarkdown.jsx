import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math-extended';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import remarkCjkFriendly from 'remark-cjk-friendly/parseOnly';
import {workspaceFileLink} from './workspaceLinks';

export function ChatMarkdown({children,projectId}){
  const Link=({href,children})=>{
    const target=workspaceFileLink(href,projectId);
    return <a href={target}>{children}</a>;
  };
  return <ReactMarkdown remarkPlugins={[remarkCjkFriendly,remarkMath]} rehypePlugins={[[rehypeKatex,{trust:false}]]} components={{a:Link}}>{children}</ReactMarkdown>;
}
