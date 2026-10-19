import {ChatMarkdown} from '../chat/ChatMarkdown';
import {artifactViewUrl} from '../api';

export const results={pass:'通过',partial:'部分满足',fail:'失败',unverified:'未能验证',not_applicable:'不适用'};
export const verdicts={pass:'通过',revise:'需修订',inconclusive:'待补证'};

export function EvidenceLinks({items,projectId}){
  if(!items.length)return null;
  return <ul className="document-evidence">{items.map((ref,index)=><li key={`${ref.artifact_id}-${index}`}>
    <a href={artifactViewUrl(projectId,ref.artifact_id)} target="_blank" rel="noreferrer">证据 {index+1} · {ref.locator}</a>
  </li>)}</ul>;
}

export function DocumentBody({data,projectId}){
  return <><div className="document-summary"><ChatMarkdown projectId={projectId}>{data.summary}</ChatMarkdown></div>
    {data.sections.map(section=><section key={section.id} id={section.id} className="document-section">
      <h2>{section.title}</h2><ChatMarkdown projectId={projectId}>{section.markdown}</ChatMarkdown>
      <EvidenceLinks items={section.evidence} projectId={projectId}/>
      {section.checks?.map((check,index)=><CheckItem key={index} check={check} projectId={projectId}/>)}
    </section>)}
    <section className="document-conclusion"><h2>结论 · {verdicts[data.conclusion.verdict]}</h2>
      <ChatMarkdown projectId={projectId}>{data.conclusion.markdown}</ChatMarkdown></section>
  </>;
}

function CheckItem({check,projectId}){
  return <details className={`document-check result-${check.result}`}>
    <summary><span>{check.label}</span><span className="document-check-status">{check.action==='skip'?'跳过 · ':''}{results[check.result]}</span></summary>
    <ChatMarkdown projectId={projectId}>{check.reason}</ChatMarkdown>
    <EvidenceLinks items={check.evidence} projectId={projectId}/>
  </details>;
}
