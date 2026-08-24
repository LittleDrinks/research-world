# dpskv4p — Research World 前端挑战 24 套

THROWAWAY UI PROTOTYPE。对现有 /projects /map /chat /activity 的审美与交互做 24 套结构性挑战。双击任意 `vNN-*/index.html` 或从 `index.html` 总览进入；无构建、无后端、无持久化，全部内存态。

## 第一性原理

- 系统本质：一个集群推进一个科学问题；图谱是唯一持久研究状态（CONTEXT/PROBLEM）。
- 核心约束：研究者审查带宽不能随轨迹长度线性增长；先看增量，再按需下钻。
- 五问标尺（PROBLEM 成功条件）：① 本周期新增了什么 ② 失败在哪 ③ 下一步做什么 ④ 上游错误影响了谁 ⑤ 证据是否可复现。
- 审美约束：demo 系统实用克制；视觉语言服务于审查带宽，不是装饰。

## 目录

| 区间 | 类型 | 方案 |
|------|------|------|
| v01–v06, v09–v11, v24 | 完整系统（10 套） | 舰队总览 / 证据制图台 / 审计台账 / 双审庭审台 / 谱系铁路 / 能力装配甲板 / 证据矩阵 / 预算闸门 / 人工裁决收件箱 / 设计选型矩阵 |
| v12–v20 | 局部组件（9 套） | 节点解剖台 / 幽灵档案室 / 影响半径计算器 / 时间窗 / 命令面板 / 复现凭据卡 / 密度压力表 / 高光报错台 / 引用检查清样 |
| v07, v08, v21–v23 | 125 命题完整展示（5 套） | Q112 环保塑料（湿实验）/ Q49 行星轨道（JPL）/ Q21 抗生素（SciFact）/ Q89 能量转换（Matbench）/ Q98 睡眠（Sleep-EDF+手表） |

每套的 `notes.md` 记录设计问题、挑战对象、交互、数据规模、取舍；`DESIGN.md` 是完整的第一性原理推导与折叠顺序。

## 共享框架

- `shared/questions.js`：docs/questions.json 转换的真实 125 题（构建脚本生成，勿手改）。
- `shared/seed.js`：mulberry32(20260905) 确定性 mock 世界；每页同数据、可复现，附生成耗时。
- `shared/ui.js` + `rw-ui.css`：底部切换条（←/→ 与键盘切换）、Prototype state 面板、总览返回；遵循 .agents/skills/prototype/UI.md 的 switcher 规范，但按用户要求扩到 24 变体（超出 skill 默认 3–5 的上限）。
- 页面脚本顺序固定：questions.js → seed.js → ui.js → 页面脚本。

## 运行与验证

```bash
python3 -m http.server 8099 -d prototype/dpskv4p   # 或直接双击 index.html
node shots.mjs                                     # Playwright 全量截图（用 research-world/web/node_modules）
python3 check.py                                   # 语法/引用/结构校验
```

## 交付边界

- 全部 mock：不接后端，但数据规模真实（125 题全量、5000 节点压力场、960 事件账本）。
- 未做：真实 API 接线、持久化、测试、迁移；这些都是后续把胜出方案折叠进 research-world/web 时的事。
- 选型结论入口：v24 选型矩阵；答案格式是“A 的头部 + B 的图谱 + C 的收件箱”，不是单选。
