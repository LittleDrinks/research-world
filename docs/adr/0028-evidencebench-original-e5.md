---
status: accepted
sources:
  - https://github.com/EvidenceBench/EvidenceBench/tree/bf1d9633c694381c7b016fd56ee9f95f48593cc3
  - https://huggingface.co/intfloat/e5-large-v2/tree/f169b11e22de13617baa190a028a32f3493550b6
---
# EvidenceBench Original E5
EvidenceBench 固定 commit `bf1d9633c694381c7b016fd56ee9f95f48593cc3`；E5 Large V2 固定 revision `f169b11e22de13617baa190a028a32f3493550b6`。源码 archive、Git tree、Original 数据和模型 snapshot 分别通过逐文件完整性门后才允许评测。
官方 preprocessor 将 JSON object 载入 mapping 后直接迭代键，却把迭代值按记录访问；官方 scorer 与 evaluator 同时要求 mapping。运行副本只将 `for point in dataset` 改为 `for point in dataset.values()`。Git 不保留 pipeline 假定存在的空输出目录，preprocessor、embedder 与 scorer 又从两个相对根定位这些目录；运行布局建立缺失目录并以符号链接统一到 `Evaluation/embedding`。clean source、pipeline shell、512 token 截断、模型、scorer、evaluator 与评价预算不变，补丁、链接及两侧 hash 随产物保存。
Original test 完整运行 ER@optimal 与 ER@10；oracle、两组 293 条 prediction、预算、Average Coverage、环境 lock、输入与模型 checksum 共同构成完成门。
