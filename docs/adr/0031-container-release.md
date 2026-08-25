---
status: accepted
---
# Container Release
`v*` tag 发布三个 GHCR 镜像：`research-world` 的 runtime target 运行 control 与 worker，`research-world:<version>-runner` 运行 runner-controller，`research-world-runtime` 运行 Agent Runtime。`pre-alpha` 指向最新预发布版本。
发布 Compose 只引用镜像，不保留 build 配置；部署方以同一 `RW_VERSION` 拉取三个不可变标签。GitHub prerelease 记录对应的 pull 与启动命令。
