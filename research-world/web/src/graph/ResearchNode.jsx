import { BookOpen, CircleHelp, Compass, FlaskConical } from "lucide-react";
import { Handle, Position } from "@xyflow/react";
import { KIND_LABELS, recordText } from "../utils/labels";


const ICONS = { question: CircleHelp, source: BookOpen, direction: Compass, experiment: FlaskConical };
const POSITIONS = [["top", Position.Top], ["right", Position.Right], ["bottom", Position.Bottom], ["left", Position.Left]];


function Handles({ handleKind }) {
  return POSITIONS.map(([side, position]) => <Handle key={side} className="hidden-handle" id={`${handleKind}-${side}`} type={handleKind} position={position} isConnectable={false} />);
}


export function ResearchNode({ data, selected }) {
  const kind = data.kind;
  const Icon = ICONS[kind] || Compass;
  return <article className={`research-node kind-${kind} ${selected ? "selected" : ""}`}>
    <Handles handleKind="target" />
    <header><span className="node-kind-icon" role="img" aria-label={`${KIND_LABELS[kind] || kind}图标`}><Icon size={19} /></span>
      <div><span>{KIND_LABELS[kind] || kind}</span><h3>{recordText(data)}</h3></div></header>
    <footer><div className="node-meta"><span>{String(data.id || "").slice(0, 12)}</span></div></footer>
    <Handles handleKind="source" />
  </article>;
}
