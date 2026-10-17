---
status: accepted
issue: 344
sources:
  - https://caddyserver.com/docs/caddyfile/directives/forward_auth
  - https://caddyserver.com/docs/caddyfile/directives/reverse_proxy
  - https://jupyter-server.readthedocs.io/en/stable/other/full-config.html
---
# 服务器工作区入口
服务器Compose叠加Caddy网关，只有网关公开；控制面、Runtime与工作区端口均绑定宿主loopback。网关使用宿主网络连接这些端口，不向工作区挂Docker socket，不把工作区接入控制面网络。
服务器模式设置RW_WORKSPACE_PROXY=1。每个Project的Jupyter使用/labs/<Project标识主体>/为base_url，页面、静态资源、Terminal和Notebook WebSocket共用该前缀。Runtime返回同站点相对URL，本机模式保持直接端口URL。
网关从URL提取Project标识，请求Runtime解析已运行且归属正确的容器端口；请求方不能指定上游URL或端口。解析仅返回loopback上游，不返回Jupyter凭证。客户端同名路由头先清除，代理时也不向工作区转发；不存在或未就绪工作区返回错误。
Jupyter继续验证自己的令牌与cookie，网关不绕过认证；令牌不进入访问日志。Caddy处理HTTP、SSE与WebSocket转发，不在应用内重写代理协议。部署文件为compose.server.yaml，服务器将其作为Compose override使用。
浏览器消息标识使用已有Nano ID依赖生成，不依赖仅安全上下文提供的crypto.randomUUID；HTTP服务器入口与localhost使用相同消息协议。
