import {ExternalLink,FlaskConical} from 'lucide-react';
import {useWorkspace} from '../context/WorkspaceContext';
import {useWorld} from '../context/WorldContext';
import '../workspace.css';

export function WorkspacePage(){
  const {projectId,data}=useWorld();
  const project=data.projects.find(p=>p.id===projectId);
  return project?<Workspace key={projectId} project={project} />:<p>请选择项目。</p>;
}

function Workspace({project}){
  const {state}=useWorkspace();
  return <section className="workspace-page"><header><FlaskConical/><div><h1>实验工作区</h1><p>{project.name} · 对话中的 Agent 与你共享文件和 Python 环境</p></div></header>
    <div className="workspace-card"><div className="workspace-status"><strong>工作区已就绪</strong><span>随项目自动启停</span></div>
      <a className="button primary" href={state.url} target="_blank" rel="noreferrer"><ExternalLink size={16}/>打开 JupyterLab</a>
      <p className="muted">关闭最后一个项目页面后，工作区中的程序会停止，已保存的文件会保留。单独打开的 JupyterLab 页面不会保持工作区运行。</p></div>
    <WorkspaceGuide/>
  </section>;
}

function WorkspaceGuide(){
  return <div className="workspace-card"><h2>人和 Agent 使用同一份文件</h2><ol>
    <li>打开 JupyterLab，在文件列表创建或上传脚本、数据和 Notebook。</li>
    <li>回到「对话」，让研究助手读取、编辑或运行这些文件。</li>
    <li>你也可以直接编辑文件，在 JupyterLab 的 Terminal 执行 <code>python hello.py</code>，或选择 Notebook 的 Python (Research World) 内核。</li>
    </ol><p>工作目录：<code>/workspace</code>。文件、终端和 Notebook 使用同一套 Python；对话中的 Agent 使用同一工作目录。</p>
    <p className="muted">所有项目 Agent 默认可访问工作区，无需额外配置。工作文件可修改，重要结果请另存为研究产物。</p></div>;
}
