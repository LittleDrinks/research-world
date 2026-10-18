import { useState } from 'react';
import { GraphView } from './GraphView';
import { Inspector } from './Inspector';
import { JointInspector, JointLinks } from './JointCondition';
import { projectConditions } from './jointProjection';

export function MapView({ localMap, selectedId, onSelect, onDeleteRecord, onDeleteRelation }) {
  const [mode, setMode] = useState('graph');
  const conditions = localMap.joint_conditions;
  const selectedCondition = conditions.find(c => c.id === selectedId);
  const selected = localMap.records.find(record => record.id === selectedId) || localMap.records[0];
  const projection = projectConditions(localMap.records, localMap.relations, conditions);
  return <div className="map-workspace"><div className="graph-canvas">
    {conditions.length > 0 && <div className="map-view-switch" role="group" aria-label="地图显示方式"><button aria-pressed={mode === 'graph'} onClick={() => setMode('graph')}>关系地图</button><button aria-pressed={mode === 'list'} onClick={() => setMode('list')}>条件列表 · {conditions.length}</button></div>}
    {mode === 'graph' ? <GraphView nodes={projection.nodes} edges={projection.edges} selectedId={selectedCondition?.id || selected?.id} onSelect={onSelect} /> : <div className="joint-list"><JointLinks conditions={conditions} onSelect={onSelect} /></div>}
  </div>{selectedCondition ? <JointInspector condition={selectedCondition} nodes={localMap.records} onSelect={onSelect} /> :
    <Inspector node={selected} nodes={localMap.records} edges={localMap.relations} conditions={conditions} artifacts={localMap.artifacts} onSelect={onSelect} onDeleteRecord={onDeleteRecord} onDeleteRelation={onDeleteRelation} />}
  </div>;
}
