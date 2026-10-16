import {registerWorkspaceTools} from './workspace-tools.mjs';
import { Type } from '@sinclair/typebox';

const text = Type.String();
const definitions = {
  graph: ['查询当前研究项目的图谱', Type.Object({query: Type.Optional(text)})],
  record: ['保存研究对象。未验证方向必须注明不确定性。', Type.Object({
    type: Type.Union(['question','source','direction','experiment'].map(Type.Literal)),
    content: Type.Object({title: text, text}),
    artifact_ids: Type.Optional(Type.Array(text)),
  })],
  artifact: ['保存不可变文本产物，返回可下载的 Artifact', Type.Object({content:text,media_type:Type.Optional(text)})],
  connect: ['连接关系：supports/refutes必须由证据支持，Question不能作为supports/refutes的任一端点；方向依赖问题时用 source=Direction、target=Question、type=depends_on', Type.Object({source_id: text, target_id: text,
    type: Type.Union(['supports','refutes','depends_on'].map(Type.Literal))})],
  literature: ['检索一手文献元数据，保留来源与不确定性', Type.Object({
    source: Type.Union(['crossref','openalex','arxiv','pubmed'].map(Type.Literal)), query: text})],
  delegate: ['委派独立上下文的研究或审查 Agent，等待并返回结果；子 Agent 不能写图',
    Type.Object({instructions: text, task: text})],
};

export default function(pi) {
  for (const name of JSON.parse(process.env.RW_SELECTED_TOOLS || '[]')) {
    if(name==='workspace'){registerWorkspaceTools(pi);continue;}
    const [description, parameters] = definitions[name];
    pi.registerTool({name, label: name, description, parameters,
      async execute(_id, args, signal) {
        const response = await fetch('http://127.0.0.1:8098/internal/tools', {
          method: 'POST', signal,
          headers: {'Content-Type': 'application/json', 'X-Tool-Token': process.env.RW_TOOL_TOKEN},
          body: JSON.stringify({tool:name, arguments:args}),
        });
        if (!response.ok) throw new Error(`Tool failed (${response.status})`);
        const data = await response.json();
        return {content:[{type:'text',text:JSON.stringify(data)}],details:{}};
      },
    });
  }
}
