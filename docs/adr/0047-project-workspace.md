---
status: accepted
issue: 340
sources:
  - https://jupyterlab.readthedocs.io/en/stable/user/terminal.html
  - https://docker-py.readthedocs.io/en/stable/containers.html
  - https://github.com/earendil-works/pi/blob/4dd2b149d155d7369de16ea4dc77c84e9f5ffb24/packages/coding-agent/src/core/tools/edit.ts
---
# 项目实验工作区
一个Project按需使用一个Docker容器；产品对话中的Pi留在Runtime，原生read/write/edit/bash通过operations接口在项目容器内执行，与JupyterLab共用/workspace和Python环境。项目文件和终端配置保存在独立持久卷；容器停止或重建不删除卷。
Runtime管理容器生命周期，控制面验证Project并提供启动/停止入口。Jupyter端口仅映射宿主loopback，使用随机认证令牌；当前本机工作台直接打开新标签页。远端网页的统一代理入口不在本次交付范围。
工作区镜像复用既有Pi版本，安装JupyterLab与基础计算依赖，以普通用户启动。只挂当前Project卷，不挂全部项目目录、宿主Pi目录或Docker socket；所选模型的凭证由Runtime复制到工作区私有目录，不返回给产品API。
用户直接编辑文件，Pi使用原生edit的目标文本匹配及文件变更队列；不引入人工接管或强制暂停流程。该队列不宣称对外部编辑器提供跨进程原子冲突保护。科学执行结果由用户或后续科研操作发布为不可变Artifact，工作文件可修改。
AgentSpec选择workspace能力后展开四个原生工具；服务端按冻结的Project绑定容器，不接受模型传入Project或容器标识。首次操作自动启动工作区，同一Turn后续操作不得自动重启被用户停止的容器。Child Agent沿用只读研究能力，不继承workspace。工作区停止会终止其中进程，保留文件；项目永久删除时清理所属容器和卷，正在运行的工作区须先停止。

生命周期请求即使收到取消，也持有项目锁等待已派发Docker操作完成；停止和启动不得交错。新建容器配置失败时回收容器，持久卷保留供重试；等待就绪超时返回实际启动状态。删除先验证运行状态及全部资源归属，再清理工作区，最后删除Runtime记录；清理失败保留记录，允许重试。

产品对话是默认Agent入口，无需在Jupyter终端另开Pi。文件工具复用Pi的匹配、截断与结果格式，只替换底层I/O；命令在容器普通用户下执行，取消或超时清理该调用的进程组后才结束Turn。写工作文件不等于发布Artifact，发布仍需显式调用artifact。
对话按Trajectory顺序显示连续文本段与工具卡片；工具开始时出现，后续事件原位更新输入、输出与终态。持久化delta与实时事件按seq合并去重，刷新、重连不改变顺序，不再在末尾汇总工具或重复最终文本。
