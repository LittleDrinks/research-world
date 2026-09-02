# 项目记忆
模型访问配置是部署级设置，Runtime 在其进程内解析部署提供的模型 id、baseurl 与 apikey；baseurl 与 apikey 只进入 Runtime，browser/control、公开 API、Trace 与日志不携带密钥，也不持久化或返回明文 apikey。
