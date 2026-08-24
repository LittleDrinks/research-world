import { useEffect,useMemo,useState } from 'react';
import { BookOpen,ExternalLink,LibraryBig } from 'lucide-react';
import ClaimView from './ClaimView';import CorpusBrowser from './CorpusBrowser';import FlowView from './FlowView';import Inspector from './Inspector';import TraceView from './TraceView';import ViewSwitcher from './ViewSwitcher';
import { categories,categoryLabel,displayTitle,visiblePaper } from './graph';
const getView=()=>new URLSearchParams(location.search).get('variant')||'flow';
function PaperOptions({papers}){
  return categories.map(category=><optgroup label={`${categoryLabel[category]} · ${papers.filter(item=>item.paper.category===category).length}`} key={category}>{papers.filter(item=>item.paper.category===category).map(item=><option key={item.paper.id} value={item.paper.id}>{displayTitle(item.paper.shortTitle)}</option>)}</optgroup>);
}
function Header({papers,paper,onPaper,onBrowse,showInferred,onToggle}){
  return <header className="app-header"><div className="brand"><BookOpen size={19}/><b>Research Kernel</b></div><button className="corpus-button" onClick={onBrowse} title="浏览论文语料"><LibraryBig size={17}/><b>{papers.length}</b></button><div className="paper-heading"><select aria-label="选择论文" value={paper.paper.id} onChange={event=>onPaper(event.target.value)}><PaperOptions papers={papers}/></select><h1>{displayTitle(paper.paper.title)}</h1><span>{categoryLabel[paper.paper.category]} · {paper.paper.modality} · {paper.paper.year}</span></div><label className="toggle"><input type="checkbox" checked={showInferred} onChange={event=>onToggle(event.target.checked)}/><i/><span>推断关系</span></label><a className="source-button" href={paper.paper.sourceUrl} target="_blank" rel="noreferrer" title="打开论文原文"><ExternalLink size={17}/></a></header>;
}
function Workspace({view,paper,onSelect}){
  if(view==='claim')return <ClaimView paper={paper} onSelect={onSelect}/>;
  if(view==='trace')return <TraceView paper={paper} onSelect={onSelect}/>;
  return <FlowView paper={paper} onSelect={onSelect}/>;
}
export default function App(){
  const [papers,setPapers]=useState([]),[paperId,setPaperId]=useState('petase'),[view,setView]=useState(getView),[selected,setSelected]=useState(null),[showInferred,setShowInferred]=useState(true),[browsing,setBrowsing]=useState(false);
  useEffect(()=>{fetch('/papers.json').then(result=>result.json()).then(setPapers)},[]);
  const source=papers.find(item=>item.paper.id===paperId)||papers[0],paper=useMemo(()=>source&&visiblePaper(source,showInferred),[source,showInferred]);
  if(!paper)return <main className="loading">加载论文语料…</main>;
  const changeView=next=>{history.replaceState(null,'',`?variant=${next}`);setView(next)};
  const choosePaper=id=>{setPaperId(id);setSelected(null)};
  return <main className="app"><Header papers={papers} paper={paper} onPaper={choosePaper} onBrowse={()=>setBrowsing(true)} showInferred={showInferred} onToggle={setShowInferred}/><div className="workspace"><Workspace view={view} paper={paper} onSelect={setSelected}/><Inspector paper={paper} node={selected} onClose={()=>setSelected(null)}/></div><ViewSwitcher view={view} onChange={changeView}/>{browsing&&<CorpusBrowser papers={papers} current={paper.paper.id} onPick={choosePaper} onClose={()=>setBrowsing(false)}/>}</main>;
}
