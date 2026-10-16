import ReactMarkdown from 'react-markdown';
import {workspaceFileLink} from './workspaceLinks';

export function ChatMarkdown({children,projectId}){
  const Link=({href,children})=>{
    const target=workspaceFileLink(href,projectId);
    return <a href={target}>{children}</a>;
  };
  return <ReactMarkdown components={{a:Link}}>{children}</ReactMarkdown>;
}
