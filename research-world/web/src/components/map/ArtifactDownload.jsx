import { Download, Eye } from "lucide-react";
import { artifactUrl } from "../../api";


export function ArtifactDownload({ artifact }) {
  if (!artifact) return null;
  const viewUrl = artifactUrl(artifact.project_id, artifact.id);
  const downloadUrl = artifactUrl(artifact.project_id, artifact.id, true);
  return <div className="form-actions artifact-download">
    <a className="button secondary" href={viewUrl} target="_blank" rel="noreferrer" aria-label={`查看 Artifact ${artifact.id}`} title="查看 Artifact"><Eye size={14} />查看</a>
    <a className="button secondary" href={downloadUrl} download aria-label={`下载 Artifact ${artifact.id}`} title="下载 Artifact"><Download size={14} />下载</a>
  </div>;
}
