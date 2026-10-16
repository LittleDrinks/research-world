# v15-time-window · 时间窗

- 类型：局部组件
- 设计问题：审查五问如何在一个时间窗口内有界可答
- 挑战对象：/projects 与 /activity 全量列表
- 主要交互：窗口切换（6h–720h）、五问卡、柱状下钻、影响流
- 数据规模：960 条事件流
- 取舍/待验证：五问文案是 mock 模板；真实需从 Fact Graph 与 Trajectory 确定性派生
- 状态：THROWAWAY 原型；答案与弃项见 v24 选型矩阵。
