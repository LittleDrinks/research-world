import {registerWorkspaceTools} from './workspace-tools.mjs';
import { Type } from '@sinclair/typebox';
import {requestTool} from './bridge-request.mjs';

const text = Type.String();
const definitions = {
  graph: ['查询当前研究项目的图谱', Type.Object({query: Type.Optional(text)})],
  record: ['保存研究对象。未验证方向必须注明不确定性。', Type.Object({
    type: Type.Union(['question','source','direction','experiment'].map(Type.Literal)),
    content: Type.Object({title: text, text}),
    artifact_ids: Type.Optional(Type.Array(text)),
  })],
  artifact: ['保存不可变文本产物；全文等已有UTF-8文件用path直接捕获，避免重写内容。返回可下载的Artifact。',
    Type.Union([Type.Object({content:text,media_type:Type.Optional(text)}),
      Type.Object({path:text,media_type:Type.Optional(text)})])],
  connect: ['连接关系：supports/refutes必须由证据支持，Question不能作为supports/refutes的任一端点；方向依赖问题时用 source=Direction、target=Question、type=depends_on', Type.Object({source_id: text, target_id: text,
    type: Type.Union(['supports','refutes','depends_on'].map(Type.Literal))})],
  literature: ['检索一手文献元数据，保留来源与不确定性', Type.Object({
    source: Type.Union(['crossref','openalex','arxiv','pubmed'].map(Type.Literal)), query: text})],
  delegate: ['并行委派独立上下文的研究或审查 Agent，按输入顺序返回结果；逐任务指定推理深度，子 Agent 不能写图',
    Type.Object({tasks: Type.Array(Type.Object({instructions: text, task: text,
      thinking: Type.Union(['low','medium','high'].map(Type.Literal))}), {minItems: 1, maxItems: 8})})],
};

export default function(pi) {
  for (const name of JSON.parse(process.env.RW_SELECTED_TOOLS || '[]')) {
    if(name==='workspace'){registerWorkspaceTools(pi);continue;}
    const [description, parameters] = definitions[name];
    pi.registerTool({name, label: name, description, parameters,
      async execute(_id, args, signal) {
        const data = await requestTool(name, args, signal);
        return {content:[{type:'text',text:JSON.stringify(data)}],details:{}};
      },
    });
  }
}
