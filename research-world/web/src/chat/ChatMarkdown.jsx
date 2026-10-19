import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math-extended';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import remarkCjkFriendly from 'remark-cjk-friendly/parseOnly';
import {preserveMathCode} from './preserveMathCode';
import {workspaceFileLink} from './workspaceLinks';

export function ChatMarkdown({children,projectId}){
  const Link=({href,children})=>{
    const target=workspaceFileLink(href,projectId);
    return <a href={target}>{children}</a>;
  };
  return <ReactMarkdown remarkPlugins={[remarkCjkFriendly,remarkMath,preserveMathCode]} rehypePlugins={[[rehypeKatex,{trust:false}]]} components={{a:Link}}>{children}</ReactMarkdown>;
}
