import {registerWorkspaceTools} from './workspace-tools.mjs';
import { Type } from '@sinclair/typebox';
import {requestTool} from './bridge-request.mjs';

const text = Type.String();
const definitions = {
  graph: ['查询当前研究项目的图谱', Type.Object({query: Type.Optional(text)})],
  mmr: ['确定性选择候选：提供可追溯的相关性和成对相似度（同一尺度），返回选择顺序与重复性扣分。',Type.Object({
    candidates:Type.Array(Type.Object({id:text,relevance:Type.Number(),title:Type.Optional(text)}),{minItems:1,maxItems:100}),
    similarities:Type.Record(text,Type.Record(text,Type.Number())),count:Type.Integer({minimum:1,maximum:100}),diversity_weight:Type.Number({minimum:0,maximum:1}),
  })],
  record: ['保存研究对象，Source必须提供canonical_url。重复提醒返回候选id与revision；仍需新建时duplicate_resolution提供draft_hash、matches及差异reason。未验证方向必须注明不确定性。', Type.Object({
    type: Type.Union(['question','source','direction','experiment'].map(Type.Literal)),
    content: Type.Object({title: text, text,canonical_url:Type.Optional(text)}),
    duplicate_resolution:Type.Optional(Type.Object({reason:text,draft_hash:text,matches:Type.Record(text,Type.Integer({minimum:1}))})),
    artifact_ids: Type.Optional(Type.Array(text)),
  })],
  change: ['管理当前项目的研究记录：读取正文/固定版本、查看变更历史、评论/修订/贴标及管理标签定义。先read取得当前revision，submit使用base_revision防止覆盖他人修改。', Type.Union([
    Type.Object({operation:Type.Literal('preflight'),type:Type.Union(['question','source','direction','experiment'].map(Type.Literal)),content:Type.Object({title:text,text,canonical_url:Type.Optional(text)})}),
    Type.Object({operation:Type.Literal('read'),record_id:text,revision:Type.Optional(Type.Integer({minimum:1}))}),
    Type.Object({operation:Type.Literal('history'),record_id:Type.Optional(text)}),
    Type.Object({operation:Type.Literal('labels')}),
    Type.Object({operation:Type.Literal('label_create'),name:text,color:text,description:Type.Optional(text)}),
    Type.Object({operation:Type.Literal('label_update'),label_id:text,name:text,color:text,description:Type.Optional(text)}),
    Type.Object({operation:Type.Literal('label_delete'),label_id:text}),
    Type.Object({operation:Type.Literal('submit'),record_id:text,kind:Type.Union(['revise','comment','labels','status'].map(Type.Literal)),base_revision:Type.Integer({minimum:1}),reason:text,
      status:Type.Optional(Type.Union(['open','closed'].map(Type.Literal))),close_reason:Type.Optional(Type.Union(['completed','not_planned','duplicate'].map(Type.Literal))),duplicate_of:Type.Optional(text),
      title:Type.Optional(text),text:Type.Optional(text),comment:Type.Optional(text),reference_revision:Type.Optional(Type.Integer({minimum:1})),label_ids:Type.Optional(Type.Array(text))}),
  ])],
  artifact: ['读取或保存不可变产物。报告必须使用模板schema_id提交结构化JSON，禁止用自由Markdown替代；六维评分按模板逐分判据填写。原始文献用text/plain，代码与数据用实际格式。operation=read通过artifact_id读取项目内原文；templates获取报告模板与示例；结构化报告选择schema_id、record_id，content/path提供模板数据JSON；validate仅校验，capture校验后保存并关联对象。全文等已有UTF-8文件用path原样捕获。',
    Type.Object({operation:Type.Optional(Type.Union(['capture','validate','templates','read'].map(Type.Literal))),artifact_id:Type.Optional(text),
      content:Type.Optional(text),path:Type.Optional(text),media_type:Type.Optional(text),schema_id:Type.Optional(text),record_id:Type.Optional(text)})],
  connect: ['连接关系：supports/refutes必须由证据支持，Question不能作为supports/refutes的任一端点；方向依赖问题时用 source=Direction、target=Question、type=depends_on', Type.Object({source_id: text, target_id: text,
    type: Type.Union(['supports','refutes','depends_on'].map(Type.Literal))})],
  joint_condition: ['记录联合条件，必须说明各成员角色、目标陈述、联合理由与Artifact原文定位；不要用关系数量冒充进展或自动判真。', Type.Object({
    title:text, rule:Type.Union(['AND','OR','k-of-N'].map(Type.Literal)), k:Type.Optional(Type.Integer({minimum:1})),
    members:Type.Array(Type.Object({record_id:text,role:text}),{minItems:2,maxItems:12}),
    target_id:text, statement:text, rationale:text,
    evidence:Type.Array(Type.Object({artifact_id:text,locator:text}),{minItems:1,maxItems:12}),
  })],
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
