# Kimi Prototype — 契约

THROWAWAY PROTOTYPE：10 套 research-world 完整界面重构，路由 `/prototype/kimi?v=01..10`，底部切换条 + ←/→ 键切换。给用户 cherry-pick，不进入生产。

数据 `../seed.js`（内存态，禁止 fetch）：`kimiTasks`（33 节点：1 question + 20 direction + 5 experiment + 4 review，含 id/type/title/prompt/parent/scienceState/authoringState/executionState/agent/channel/group/position/goal/model/provider/workspace/permission/acceptance/tools）、`kimiProjects`（3 个项目）、`kimiActivity`（活动事件）、`kimiChat`（orchestrator 对话）、`PROTOTYPE_GROUPS`。

## 每个变体必须遵守

1. 自己的文件夹 `v<NN>-<name>/` 里两个文件：`index.jsx`（覆盖既有占位文件，**保持 default export**）和 `style.css`（在 index.jsx 里 `import "./style.css"`）。
2. 根元素 `<section className="vNN-root">`，占满 100%×100%，自带背景与 `color-scheme`，overflow 自控。
3. CSS 全部以 `.vNN-` 前缀 scoped，禁止污染全局、禁止改 `styles.css` / 他人文件夹 / BRIEF.md / seed.js / KimiPrototype.jsx / App.jsx。
4. 一套**完整 app 再想象**：四个 surface 都要可达——项目列表、研究图谱（question→direction→experiment/review 层级）、节点详情+对话、活动流——但**主次与导航模型按你的简报重新组织**（哪个是主 surface、怎么到达其他 surface，由你定）。
5. 可交互：点节点换详情、surface 间切换，全部 useState 内存态；欢迎做本地状态变更（如批准/改状态）。禁用路由跳转、禁用 fetch、禁用新 npm 包。可用 `lucide-react` 图标。**禁用 @xyflow/react**——图用 SVG/div 手绘，保持每套风格独立。
6. 某处展示当前选中项/派生计数（surface the state）。
7. UI 文案用中文（沿用种子里的状态词：待审查/待验证/已入图/已支持/已锁定、运行/排队/完成/失败/空闲）。
8. 密度要真：33 个节点该摆出来就摆出来，别只做 5 个的玩具。单文件 JSX 300–550 行是正常体量。
9. 不写测试、不写注释解释"这是原型"（文件头一行 THROWAWAY 注释即可）、不做错误处理。

## 运行 / 验证

```bash
cd research-world/web && npm run dev   # http://localhost:5173/prototype/kimi?v=01
```
不要启动 dev server（会和他人端口冲突）。写完用 `npx vite build` 验证编译；若因**他人**变体缺失报错可忽略，只修自己的错。

---

## 十套简报

### V01 深海玻璃 Deep-Sea Glass
视觉：黑蓝深海 `#020814`→`#0a1a3a` 纵深渐变，玻璃拟态面板（`backdrop-filter: blur(12px)`、1px 半透边、青色 `#00F0FF` 辉光描边），深层用更暗更模糊表现"下潜"。
使用逻辑：**图谱即桌面**。全屏节点海图，项目/详情/活动是悬浮玻璃舱；选中节点→右侧详情舱滑入；底部玻璃 dock 切 surface。节点按 group 分"海域"，连线发光。

### V02 ASCII 原子终端 Atom Terminal
视觉：纯等宽（Geist Mono），黑底磷光绿 `#33ff66`，扫描线/辉光，ASCII 原子像素装饰（节点用 `( o )`、电子轨道 `·`）。一切边框用 ASCII 字符或 1px 硬线。
使用逻辑：**键盘优先 CLI-in-GUI**。主区是 log 流（chat 与系统事件同流），底部命令行支持 `:open D-001`、`:map`、`:activity`、`:approve`；`:map` 把图谱渲染成 ASCII 布局（用种子 position 换算字符网格，parent 连线用 `─ │ ┌ └`）；右上角常驻快捷键表。

### V03 任务控制 Mission Control
视觉：NASA 遥测，近黑 `#0b0e14` + 琥珀/青双色告警，密集小面板、大号数字、等宽数据字体、细网格分隔。
使用逻辑：**监控优先**。主屏=遥测仪表盘网格：状态计数大数字板、各 agent/runtime 健康表、执行队列、活动 ticker（横向滚动）、缩略图谱只是其中一格。点任意节点→全屏下钻 modal（含详情+对话）。顶部大时钟/MISSION ELAPSED。

### V04 活手稿 Living Manuscript
视觉：奶白纸面 `#faf8f2`，serif 标题（Georgia/宋体系），章节编号，红笔批注，页边注，脚注引用 `[1]`，双栏排版。
使用逻辑：**阅读写作优先**。研究=一部在写的手稿：左栏目录（章=group，节=direction），正文每节是叙述段落+内嵌"实验卡片"；右页边注=该节节点状态/审查意见，待审节点以红笔批注样式出现；项目选择是封皮页；活动流="修订记录"附录页。

### V05 看板分流 Kanban Triage
视觉：Linear 风浅色，白底、灰细分隔、状态彩色小圆点、紧凑行高、⌘K 命令面板。
使用逻辑：**分诊优先**。主屏=看板，列=科学状态（待审查/待验证/已支持/已锁定），卡片=节点（含 agent/执行态 chips），可拖拽或按钮改列（本地 state）；顶栏 list/board 切换 + ⌘K 面板（搜节点、跳 surface）；详情=右侧 drawer（详情+迷你对话）；活动=一条 inbox 视图。

### V06 对话编排 Chat Orchestrator
视觉：现代 AI chat（浅色+单蓝色强调），气泡+卡片混排，宽阅读列居中。
使用逻辑：**会话优先**。home=与 Orchestrator 的长对话：节点以可展开卡片在对话流中"物化"，可回复"展开 D-001 的实验"插入新卡片；右侧"已钉入上下文"栏；图谱收缩为左上"按编号索引"抽屉；活动=对话中的系统消息。输入框常驻底部，支持 `@节点编号` 引用。

### V07 蓝图 CAD Blueprint
视觉：蓝图纸 `#123a6b` 底 + 白/浅蓝线，点阵网格背景，技术标注框带引线，尺寸标注 `|←——→|`，右下角图签栏（图号/比例/日期/审批），剖面符号。
使用逻辑：**图优先 + 精密 inspector**。全屏蓝图：节点=仪器框（带编号引出线），parent 连线=装配线；选中→右侧"剖面详图"把 prompt/验收标准/工具/环境逐层展开；顶部图层开关（按 type/group 过滤）；项目=图纸目录（drawing index）；活动=修订表（rev table）。

### V08 星图天文台 Observatory
视觉：深空黑 + 星云径向渐变，恒星发光点（box-shadow 光晕），星座折线，黄道环刻度，底部"目镜"读数栏等宽字体。
使用逻辑：**缩放导航**。三层抽象：L1 问题（单颗亮星）→ L2 方向（星座，20 颗）→ L3 实验/审查（星团）；点击/滚轮下钻，Esc 上升；目镜栏实时显示选中星体的全部字段；项目=选观测目标；活动=观测日志侧栏。连线闪烁=运行中。

### V09 积木桌面 Bento Desktop
视觉：浅色 bento 网格，圆角 18px 磁贴、柔和投影、每格一种淡色（薄荷/杏/薰衣草/天蓝），大字标题+小字数据。
使用逻辑：**可组合桌面**。主屏=磁贴桌面：项目卡、mini 图谱、执行队列、活动流、对话窗、指标计数各占一格（大小不一）；每格有"展开"钮进入 focus 全屏模式（格内 surface 变主视图，含详情+对话）；支持点节点在图谱格与详情格联动。

### V10 实验日志 Lab Journal
视觉：暖纸质感 `#f6f1e7`，手写风标题可选，便利贴黄 `#fff3a3` 点缀，日期大标题，"APPROVED" 红色印章，竖排时间线。
使用逻辑：**时间优先**。主列=按天的日志流（近一周），条目=当天节点事件（状态变更/实验结果/审查意见），内嵌节点卡；左栏=月历+日期跳转；右栏=待办与队列便签；详情=点开条目展开；对话=日志条目下的"批注"线程；项目=日志封面。
