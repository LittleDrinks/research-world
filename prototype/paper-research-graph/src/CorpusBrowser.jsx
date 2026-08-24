import { useMemo,useState } from 'react';
import { Search,X } from 'lucide-react';
import { categories,categoryLabel,displayTitle } from './graph';
function counts(papers){return Object.fromEntries(categories.map(category=>[category,papers.filter(item=>item.paper.category===category).length]))}
function CategoryTabs({papers,value,onChange}){
  const total=counts(papers);
  return <nav className="category-tabs"><button className={value==='all'?'active':''} onClick={()=>onChange('all')}>全部 <b>{papers.length}</b></button>{categories.map(category=><button className={value===category?'active':''} key={category} onClick={()=>onChange(category)}>{categoryLabel[category]} <b>{total[category]}</b></button>)}</nav>;
}
function PaperList({papers,current,onPick}){
  return <div className="corpus-list">{papers.map(item=><button className={item.paper.id===current?'active':''} key={item.paper.id} onClick={()=>onPick(item.paper.id)}><strong>{displayTitle(item.paper.title)}</strong><span>{item.paper.year} · {item.paper.modality}</span></button>)}</div>;
}
export default function CorpusBrowser({papers,current,onPick,onClose}){
  const [category,setCategory]=useState('all'),[query,setQuery]=useState('');
  const visible=useMemo(()=>papers.filter(item=>(category==='all'||item.paper.category===category)&&item.paper.title.toLowerCase().includes(query.toLowerCase())),[papers,category,query]);
  return <div className="corpus-overlay"><button className="overlay-close" aria-label="关闭语料浏览器" onClick={onClose}/><aside className="corpus-browser"><header><div><span>论文语料</span><strong>{papers.length}</strong></div><button title="关闭" onClick={onClose}><X size={18}/></button></header><label className="corpus-search"><Search size={16}/><input autoFocus value={query} onChange={event=>setQuery(event.target.value)} placeholder="检索标题"/></label><CategoryTabs papers={papers} value={category} onChange={setCategory}/><PaperList papers={visible} current={current} onPick={id=>{onPick(id);onClose()}}/></aside></div>;
}
