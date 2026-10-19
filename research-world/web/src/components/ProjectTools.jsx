import {useNavigate} from 'react-router-dom';
import {useWorld} from '../context/WorldContext';
import {recordUrl} from '../api';
import {LabelManager} from '../graph/Labels';
import {ProjectChanges} from '../graph/ProjectChanges';
import {ResultsPreview} from '../graph/ResultsPreview';

export function ProjectTools({close}){
  const {projectId}=useWorld(),navigate=useNavigate();
  if(!projectId)return null;
  return <section className="project-tools" aria-label="项目资料" onClick={close}><h2>项目资料</h2>
    <ResultsPreview/><ProjectChanges onSelect={id=>navigate(recordUrl(projectId,id))}/><LabelManager/>
  </section>;
}
