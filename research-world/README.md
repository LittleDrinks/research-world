# Research World

## 评测者入口

- **125 题全量结果站点**：<https://littledrinks.github.io/research-world/>（随仓库维护更新；终态与缺口全量保留）
- **五深度案例证据链**：`evidence/contest-2026/`（q049/q089/q021/q112/q098 的 V1→独立评审→final 版本链、运行账本与哈希）
- **本地复现**：仓库根配置 `.env`（小写 `apikey`/`baseurl`，凭证不入库）后执行 `cd research-world && docker compose up --build -d`，前端 <http://localhost:8095>
- **技术方案报告**：`evidence/contest-2026/report/`（官方模板 P1–P20 填充版）
- 提交时点存档 tag：`contest-2026-submission`
单问题研究控制面：SQLite 图谱是唯一真源，artifact 按 SHA-256 寻址；节点上的对话经 orchestrator 决策为 workflow，双审准入。
## Start
```bash
docker compose up --build -d
```
控制面 `http://127.0.0.1:8095`（projects 卡片页）。服务：control(8095)、worker、runtime(8098)、runner-controller(8096)。启动不创建 workflow，不调用模型。
## Pre-alpha
```bash
docker pull ghcr.io/littledrinks/research-world:pre-alpha
docker pull ghcr.io/littledrinks/research-world:pre-alpha-runner
docker pull ghcr.io/littledrinks/research-world-runtime:pre-alpha
docker compose -f compose.release.yaml up -d
```
固定版本以 GitHub prerelease 中的 `v*` 标签替换 `pre-alpha`。
## Doctor
```bash
docker compose exec control rw doctor --embedding
```
## CLI
```bash
docker compose exec control rw project create --file /projects/q049/project.json
docker compose exec control rw project list
docker compose exec control rw graph show --project q049
```
## Verify
```bash
uv run pytest
cd ../harness && uv run pytest
cd web && npm test
docker compose config -q
```
