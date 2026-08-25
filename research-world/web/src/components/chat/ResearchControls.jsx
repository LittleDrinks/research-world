import { Workflow } from "lucide-react";
import { createSearchParams, Link, useLocation } from "react-router-dom";
import { useWorld } from "../../context/WorldContext";


export function ResearchControls({ thread, runs }) {
  const { projectId } = useWorld();
  const location = useLocation();
  const from = `${location.pathname}${location.search}`;
  const search = createSearchParams({ project_id: projectId, thread_id: thread.id, from }).toString();
  return <Link className="composer-tool" aria-label={`研究运行 ${runs.length}`}
    to={{ pathname: "/traces", search }}><Workflow size={15} /><span>研究运行 {runs.length}</span></Link>;
}
