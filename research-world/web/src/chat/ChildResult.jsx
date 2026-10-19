import {ChatMarkdown} from './ChatMarkdown';

const STATUS={completed:'完成',error:'失败',failed:'失败',cancelled:'已取消',running:'进行中'};

export function ChildResult({result,projectId}) {
  return <details className="pi-child" open>
    <summary><b>独立 Agent 结果</b><span>{STATUS[result.status] || '状态未知'}</span></summary>
    <div className="child-result-body"><ChatMarkdown projectId={projectId}>{result.result_text || '未返回结果正文。'}</ChatMarkdown></div>
  </details>;
}
