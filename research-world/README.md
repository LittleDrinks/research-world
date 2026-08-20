# Research World
单问题研究控制面：SQLite 图谱是唯一真源，artifact 按 SHA-256 寻址；节点上的对话经 orchestrator 决策为 workflow，双审准入。
## Start
```bash
docker compose up --build -d
```
控制面 `http://127.0.0.1:8095`（projects 卡片页）。服务：control(8095)、worker、harness(8098)、runner-controller(8096)。启动不创建 workflow，不调用模型。
## Doctor
```bash
docker compose exec control rw doctor --embedding
```
## CLI
```bash
docker compose exec control rw project create --file /projects/orbits-49/project.json
docker compose exec control rw project list
docker compose exec control rw graph show --project orbits-49
```
## Verify
```bash
uv run pytest
cd ../harness && uv run pytest
cd web && npm test
docker compose config -q
```
