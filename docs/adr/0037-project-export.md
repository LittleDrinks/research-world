---
status: accepted
sources:
  - id: issue-112
    title: Project export：可复现研究包下载
    url: https://github.com/LittleDrinks/research-world/issues/112
    accessed: 2026-08-26
---
# Project Export
Project export 是 Research Kernel 对单个 Project 当前状态生成的一次性只读研究包；不定义导入、同步或通用文件管理。
`GET /api/v1/projects/{project_id}/export` 不接受请求体，只委托 Kernel 读取投影并以 `application/zip` 下载。设置页只提供该链接。
ZIP 固定使用 UTF-8、词典序路径、固定 ZipInfo 时间与权限、无压缩写入；JSON 使用排序键和紧凑分隔符。同一 Kernel 状态得到字节相同的清单和包，不写临时文件，也不写入 Project。
`manifest.json` 固定描述格式版本、Project id 与排序后的 payload 文件；每项含相对路径、字节数和 SHA-256。`checksums.sha256` 按路径排序，校验全部 payload 与 `manifest.json`，不校验自身。
Payload 包含 `project.json` 的安全 Project facts、`pipeline-runs.json` 的运行与步骤事实、每个 Thread 的公开 Trace、每个 Project Artifact 的安全元数据与可导出内容、已发布报告以及 admitted source Artifact 生成的 `references.bib`。Artifact 先由 ArtifactStore 校验内容哈希；无效内容使导出失败，不产生部分包。
所有导出对象经过同一脱敏边界：凭据、授权、连接串、URL secret、绝对路径、工作区、Runtime continuation 和临时文件名均不进入任何路径、JSON、文本或 ZIP metadata。含敏感文本的可选 Artifact 内容不导出，其身份和受控 omission 状态仍留在清单中。
