---
project: contest-2026
issue: "LittleDrinks/research-world#297"
deliverable: ".scratch/demo-video.mp4（1920×1080，30fps，无声，约 7 分钟）"
structure: 方法链约 70%＋产品演示收尾约 30%，中文黑底白字字幕卡叙述，无配音
evidence: "evidence/contest-2026/（q049/run.md、submission-evidence.md P14-P20、deep-cases.md、all/index.md）"
redlines: 凭证零出现；只用 evidence/ 与真实录屏；数字与 run.md 一致
---
# 演示视频分镜清单（issue #297 粗剪）
## 生成方式
- 字幕卡/表格卡：`make_cards.mjs` 用 Playwright 渲染 HTML → 1920×1080 PNG（黑底白字，Noto Sans SC）。
- 屏幕录制：`record_site.mjs`（125 结果站筛选演示）与 `record_product.mjs`（Compose 产品的发问→流式→刷新→图谱），Playwright `recordVideo`，1920×1080 webm。
- 合成：`compose.sh` 用 ffmpeg 把每张卡转成定长片段、录制裁剪提速并叠加字幕条，concat 成 `.scratch/demo-video.mp4`。
- 125 站点本地预览：`uv run python scripts/build-results-site.py` 后 `python -m http.server 8099 -d dist/results-site`。
- 产品栈：`docker compose -p rw297 up --build -d`（独立项目名，避免与主树历史容器冲突）。
## 分镜
| # | 内容 | 素材 | 秒 |
|---|---|---|---:|
| 01 | 标题卡：Research World · 125 个科学问题的 AI 研究工作流 | 卡 | 12 |
| 02 | 一句话卡：每题一个独立作者 Session（三方向→研究计划→候选结论），独立评审按固定六维 rubric 打分，修订留痕，审计回执存哈希 | 卡 | 16 |
| 03 | 125 题总看板截图：125/125 有候选结论，8 completed / 117 partial / 0 failed | 截图卡 | 16 |
| 04 | 章节卡：方法链 · 旗舰案例 q049 | 卡 | 6 |
| 05 | q049 问题卡：行星轨道为何不衰减坠日＋错误前提＋约束（一手来源、planned/executed 边界） | 卡 | 18 |
| 06 | V1 三方向表（D1 混沌失稳 / D2 微弱耗散 / D3 太阳演化）与各自处理 | 卡 | 28 |
| 07 | V1 结果卡：9/12；来源 2/5；引力波功率错约 22 个数量级（10⁻²⁰ W，实际约 200 W） | 卡 | 18 |
| 08 | 独立评审发现表：5 个 finding（DOI 错配、arXiv 号错、反向转述、22 个数量级、无效判据）→ 修订结果 | 卡 | 38 |
| 09 | 修订链卡：V1→review→…→V8，每轮 review 与被拒原因保留；V8 12/12、来源 6/6、reviewer 判 deliverable | 卡 | 22 |
| 10 | Peters 计算卡：P=196.291 W，t=3.374×10³⁰ s≈1.069×10²³ yr，退出码 0，输出 SHA-256 留痕，reviewer 独立复算一致 | 卡 | 24 |
| 11 | 六维 rubric 卡：问题理解/文献证据/Direction/科学推理/研究计划/表达与追溯；直答对照 4/12 与 6/12，V1 9/12，final 12/12 | 卡 | 22 |
| 12 | 代价对照表卡：attempt 2 实算近似 / attempt 6 长度近似 / Workflow V1（字符、calls、token、rubric、来源） | 卡 | 30 |
| 13 | 五深度案例卡：q049/q089/q021/q112/q098 V1→final、来源门、终态；合计 3144 次调用 | 卡 | 20 |
| 14 | 章节卡：125 全量 · 结果站点 | 卡 | 6 |
| 15 | 站点演示录屏：总看板滚动→领域筛选→终态筛选→打开 q049 详情 | 录屏 | 48 |
| 16 | 章节卡：产品演示 · Compose 实栈 | 卡 | 6 |
| 17 | 起栈卡：docker compose up --build -d；control/runtime/runner-controller/worker 四容器 healthy | 卡 | 14 |
| 18 | 产品录屏 A：/projects 新建项目→/chat 新建对话→发问「行星轨道为什么不衰减坠入太阳？」→流式回答 | 录屏 | 40 |
| 19 | 产品录屏 B：刷新页面→同一问与同一答仍在 | 录屏 | 18 |
| 20 | 产品录屏 C：/map 图谱一眼 | 录屏 | 14 |
| 21 | 结尾卡：仓库、结果站点、证据目录；12/12 是评审结论而非永久事实 | 卡 | 16 |
| 合计 | | | ≈432s（7:12） |
## 剪辑规则
- 硬切、无转场、无配乐（粗剪标准）；录屏片段截去等待头尾，必要时 1.5–2× 提速，字幕条全程叠加在录屏底部。
- 卡片停留时间即阅读时间；表格卡字号 ≥28px（1080p 下可读）。
- 凭证零出现：录屏不打开 settings/.env 相关页面；合成后抽查帧。
