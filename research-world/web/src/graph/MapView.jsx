import { useState } from 'react';
import { GraphView } from './GraphView';
import { Inspector } from './Inspector';
import { JointInspector, JointLinks } from './JointCondition';
import { projectConditions } from './jointProjection';
import {LabelBadge} from './Labels';
import {CandidateSelection} from './CandidateSelection';

export function MapView({ localMap, selectedId, onSelect, onDeleteRecord, onDeleteRelation }) {
  const [mode, setMode] = useState('graph');
  const conditions = localMap.joint_conditions;
  const selectedCondition = conditions.find(c => c.id === selectedId);
  const selected = localMap.records.find(record => record.id === selectedId) || localMap.records[0];
  const visible=focusedMap(localMap,mode,selectedCondition?.id||selected?.id);
  const projection = projectConditions(visibleRecords(visible,mode), visible.relations, visible.joint_conditions);
  return <div className="map-workspace"><div className="graph-canvas">
    {['graph','all','focus'].includes(mode) && <div className="graph-legend" aria-label="关系图例"><span className="supports">支持</span><span className="refutes">反驳</span><span className="depends_on">依赖</span></div>}
    <div className="map-view-switch" role="group" aria-label="地图显示方式"><button aria-pressed={mode === 'graph'} onClick={() => setMode('graph')}>关系地图</button><button aria-pressed={mode==='sources'} onClick={()=>setMode('sources')}>文献 · {localMap.records.filter(r=>r.kind==='source').length}</button>{conditions.length>0&&<button aria-pressed={mode === 'list'} onClick={() => setMode('list')}>条件列表 · {conditions.length}</button>}<button aria-pressed={mode==='all'} onClick={()=>setMode('all')}>全图</button></div>
    {['graph','all','focus'].includes(mode)&&<button className="focus-record" onClick={()=>setMode(mode==='focus'?'graph':'focus')}>{mode==='focus'?'显示研究主线':'聚焦选中关系'}</button>}
    {['graph','all','focus'].includes(mode) ? <GraphView nodes={projection.nodes} edges={projection.edges} selectedId={selectedCondition?.id || selected?.id} onSelect={onSelect} /> : mode==='sources'?<SourceList records={localMap.records} onSelect={onSelect}/>:<div className="joint-list"><JointLinks conditions={conditions} onSelect={onSelect} /></div>}
  </div>{selectedCondition ? <JointInspector condition={selectedCondition} nodes={localMap.records} onSelect={onSelect} /> :
    <Inspector node={selected} nodes={localMap.records} edges={localMap.relations} conditions={conditions} artifacts={localMap.artifacts} onSelect={onSelect} onDeleteRecord={onDeleteRecord} onDeleteRelation={onDeleteRelation} />}
  </div>;
}

function focusedMap(map,mode,selectedId){
  if(mode!=='focus')return map;
  const conditions=map.joint_conditions.filter(c=>c.id===selectedId||c.target_id===selectedId||c.members.some(m=>m.record_id===selectedId));
  const relations=map.relations.filter(r=>[r.source,r.target].includes(selectedId));
  const ids=new Set([selectedId,...relations.flatMap(r=>[r.source,r.target]),...conditions.flatMap(c=>[c.target_id,...c.members.map(m=>m.record_id)])]);
  return {...map,records:map.records.filter(r=>ids.has(r.id)),relations,joint_conditions:conditions};
}

function visibleRecords(map,mode){
  if(mode==='all'||mode==='focus')return map.records;
  const linked=new Set(map.relations.flatMap(r=>[r.source,r.target]));
  for(const c of map.joint_conditions){linked.add(c.target_id);for(const m of c.members)linked.add(m.record_id);}
  return map.records.filter(r=>r.kind!=='source'||linked.has(r.id));
}

function SourceList({records,onSelect}){
  const sources=records.filter(r=>r.kind==='source');
  return <div className="source-list"><CandidateSelection records={sources}/>{sources.map(record=><button key={record.id} onClick={()=>onSelect(record.id)}><b>{record.content.title}</b><span>{record.labels?.map(label=><LabelBadge key={label.id} label={label}/>)}</span></button>)}</div>;
}
