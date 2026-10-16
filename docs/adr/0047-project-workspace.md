---
status: accepted
issue: 338
sources:
  - https://jupyterlab.readthedocs.io/en/stable/user/terminal.html
  - https://docker-py.readthedocs.io/en/stable/containers.html
  - https://github.com/earendil-works/pi/blob/4dd2b149d155d7369de16ea4dc77c84e9f5ffb24/packages/coding-agent/src/core/tools/edit.ts
---
# 项目实验工作区
一个Project按需使用一个Docker容器；Pi与JupyterLab位于同一容器，共用/workspace和Python环境。项目文件、Pi配置及原生会话分别保存在独立持久卷；容器停止或重建不删除卷。
Runtime管理容器生命周期，控制面验证Project并提供启动/停止入口。Jupyter端口仅映射宿主loopback，使用随机认证令牌；当前本机工作台直接打开新标签页。远端网页的统一代理入口不在本次交付范围。
工作区镜像复用既有Pi版本，安装JupyterLab与基础计算依赖，以普通用户启动。只挂当前Project卷，不挂全部项目目录、宿主Pi目录或Docker socket；所选模型的凭证由Runtime复制到工作区私有目录，不返回给产品API。
用户直接编辑文件，Pi使用原生edit的目标文本匹配及文件变更队列；不引入人工接管或强制暂停流程。该队列不宣称对外部编辑器提供跨进程原子冲突保护。科学执行结果由用户或后续科研操作发布为不可变Artifact，工作文件可修改。
本轮原生Pi入口为Jupyter终端，默认模型取研究助手配置；现有产品对话Runtime不在本轮替换。工作区停止会终止其中进程，保留文件；项目永久删除时清理所属容器和卷，正在运行的工作区须先停止。

生命周期请求即使收到取消，也持有项目锁等待已派发Docker操作完成；停止和启动不得交错。新建容器配置失败时回收容器，持久卷保留供重试；等待就绪超时返回实际启动状态。删除先验证运行状态及全部资源归属，再清理工作区，最后删除Runtime记录；清理失败保留记录，允许重试。
