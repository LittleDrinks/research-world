# Research World
单问题研究控制面：SQLite Fact Graph 保存当前研究状态，Artifact 按 SHA-256 寻址；主 Agent 动态编排 Workflow，Graph CLI 写入或删除图谱，Trajectory 记录工作过程。
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
