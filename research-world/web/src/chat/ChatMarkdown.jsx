import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
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
  return <ReactMarkdown remarkPlugins={[remarkGfm,remarkCjkFriendly,remarkMath,preserveMathCode]} rehypePlugins={[[rehypeKatex,{trust:false}]]} components={{a:Link,table:MarkdownTable}}>{children}</ReactMarkdown>;
}

function MarkdownTable({children}){
  return <div className="markdown-table-scroll" tabIndex={0} role="region" aria-label="表格，可横向滚动"><table>{children}</table></div>;
}
