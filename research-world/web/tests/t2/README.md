# T2 验收套件
前置：`research-world/` 下 `docker compose up --build -d`，四容器 healthy；`npm run dev` 不参与，直连 8095。
运行：`cd research-world/web && npm run test:t2`。
用例：01 流式收尾；02 刷新恢复；03 无内部标识泄露；04 无工具纯文本轮；05 凭证失败可见（以无效 API key 临时重建 runtime，结束自动恢复并复验回答）。
产物：`web/test-results/t2/`（report.json、html 报告、每用例 trace 与截图）。目录已 gitignore，作为 PR 附件归档。
凭证红线：`.env` 的 apikey/baseurl 与运行时生成的无效 key 只存在于进程内存；失败输出经 `helpers/env.js` 脱敏。
