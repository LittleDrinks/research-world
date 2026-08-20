import { useEffect } from 'react';
import { ChevronLeft,ChevronRight } from 'lucide-react';
const views=[['flow','流程'],['claim','主张'],['trace','轨迹']];
export default function ViewSwitcher({view,onChange}){
  const index=views.findIndex(item=>item[0]===view),cycle=step=>onChange(views[(index+step+views.length)%views.length][0]);
  useEffect(()=>{const handler=event=>{if(['INPUT','TEXTAREA'].includes(event.target.tagName)||event.target.isContentEditable)return;if(event.key==='ArrowLeft')cycle(-1);if(event.key==='ArrowRight')cycle(1)};addEventListener('keydown',handler);return()=>removeEventListener('keydown',handler)});
  if(!import.meta.env.DEV)return null;
  return <nav className="view-switcher" aria-label="面板视图"><button title="上一个视图" onClick={()=>cycle(-1)}><ChevronLeft size={18}/></button><span>{String.fromCharCode(65+index)} · {views[index][1]}</span><button title="下一个视图" onClick={()=>cycle(1)}><ChevronRight size={18}/></button></nav>;
}
