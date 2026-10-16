---
status: accepted
sources:
  - https://github.com/LittleDrinks/ai4sci/issues/74
  - https://github.com/allenai/scifact/tree/68b98a56d93e0f9da0d2aab4e6c3294699a0f72e
  - https://github.com/allenai/scifact-evaluator/tree/66feffc5b2cc9e28e3ce3b8c9e824c3c642981eb
---
# SciFact 完整性门
任何 SciFact 检索运行先校验官方数据包 SHA-256、train/dev/test/corpus 计数、gold 文档和句索引、source/evaluator revision，以及官方 `--k 3` 检索预算。任一项失败时不创建运行、不计分、不报告子集结果。
预检工具只读本地数据与固定仓库，不连接 Runtime 或模型端点。运行时 API 连通性另行预检；失败时完整 dev 保持 `0/300`。
