# Chat Runtime 原型收敛

目标：继续修改 `/prototype/chat-runtime`，只做内存态 THROWAWAY UI，不改生产页面、后端、依赖与既有 `prototype/kimi/v02-atom-terminal/`。

## 参考结论

- DeepSeek Harness：session log 是模型可见上下文与恢复的事实源；轨迹按 `turn -> step -> message/tool call/tool result` 展示，durable session event 与 live agent event 分开。参考 `https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md`，不是照抄平面表格。
- Multica Agent：基础设置只有名称与 Runtime；Instructions、Skills、Model/Thinking 属于常用能力；访问、并发、环境变量、MCP 收进高级设置。参考 `https://multica.ai/docs/agents-create`。
- PlanWeave：左侧是一级模块、当前模块记录树、底部项目动作三段式；Agent 是列表选择后编辑，不是稀疏卡片首页。参考 `https://github.com/GaosCode/PlanWeave` 与本仓库 `research-world/web/src/prototype/MapAuthoringPrototype.jsx`。
- Danus：事实图是已验证事实及逻辑依赖的 DAG；失败尝试、计划和 agent 过程不混入事实图；错误事实可撤回并识别其依赖闭包。参考 `https://arxiv.org/html/2607.06447v2`。
- 现有产品代码：地图视觉与交互参考 `research-world/web/src/pages/MapPage.jsx`、`graph/GraphView.jsx`、`graph/Inspector.jsx`、`map.css`；项目选择参考 `pages/ProjectsPage.jsx` 与 `projects.css`；左下角参考 `components/AppShell.jsx` 的“退出项目”。
- ASCII 美学参考 `prototype/kimi/v02-atom-terminal/`，但只取等宽字、硬线、字符连线和克制动效，不复制它的 CLI 信息架构。

## A：收敛后的工作台

修改 `research-world/web/src/prototype/chat-runtime-kimi/` 的 A 方案。

1. 一级模块只有 `地图 / 对话 / 轨迹 / Agent`，保持单列。删除一级“科研日志”。地图主页面内用紧凑分段控件切换 `事实图谱 / 科研日志`；左侧下半记录树随子视图显示节点或日志日期。
2. 事实图谱必须像现有 MapPage：可见依赖连线、节点状态、选中态与右侧节点详情，不再是卡片索引。可复制现有结构与视觉，用当前原型 seed 做内存数据，不 fetch。图谱只放事实及依赖；科研日志仍是项目级时间线。
3. 对话保留 `@node_id` 引用、钉入节点、ResearchRun 与 execution 行整行下钻；prompt 和 skills 预览继续保留。
4. 轨迹改成完整页面。页头有明确“返回对话”，返回触发这次下钻的 thread。正文按 session 元信息、turn、step、assistant message、tool call/result 分层；工具输入输出可展开；左侧记录树可切 execution。不要继续用现在的平面 RuntimeInspector 表。
5. Agent 页面采用左列表 + 右编辑器。常用区只呈现名称、Runtime、Instructions、模型/推理强度、Skills；高级设置折叠，放权限、并发、环境变量、MCP。提供“从空白创建”和“AI 起草”两个入口，按钮可做内存态反馈。不要使用稀疏卡片首页。
6. 左下角改为现有 AppShell 的“退出项目”。点击进入同一原型内的项目选择页；项目页可点击回到工作台。

## 项目选择 Hero

项目选择不是营销落地页，而是实际入口。首屏以 `Research World` 为明确大标题，辅助文案只说明研究项目入口；同屏露出最近项目列表和新建按钮，不能只看见 Hero。沿用现有项目页的行式项目列表与真实密度。使用抽象但与事实图相关的 CSS/字符网络背景，不新增图片依赖，不做卡片套卡片。

## D：ASCII 动效美学变体

新增 `variant=D`，命名“ASCII 动效”。D 与 A 使用同一页面层级、交互和 seed，不能重新变成 CLI 产品。允许独立组件与 CSS，CSS class 完整隔离。

- 黑底、磷光绿、等宽字体、ASCII 边线/节点；颜色需保留成功、运行、警告、失败的区分。
- 动效只表达系统状态：运行 execution 的字符 spinner；新日志逐字/脉冲出现；图谱依赖边上有低频数据脉冲；项目 Hero 背景字符网络缓慢漂移；光标闪烁和轻扫描线。
- 禁止大幅位移、频繁闪烁、布局抖动。实现 `prefers-reduced-motion: reduce`，关闭所有非必要动画。
- A 方案保持现有 Research World 视觉，不应用 ASCII CSS。

## 边界与验收

- 不改 B/C 语义；只让切换器支持 A/B/C/D。
- 不装包，不 fetch，不做持久化，不改 `App.jsx`、生产 `MapPage`、`ProjectsPage`、`AppShell`。
- 所有按钮有真实内存态结果；不写解释设计的可见文案。
- 适配 1440x900 与 390x844，文本不重叠，固定工具条不遮内容。
- 函数尽量短，拆出明确组件；只写满足原型的实现。
- 完成后在 `research-world/web` 执行 `npm run build`，报告修改文件、验证结果与两个可访问 URL：`?variant=A`、`?variant=D`。
