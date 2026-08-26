---
name: research-report
description: Generate a scientific research report or run its pre-delivery citation check from a Research Kernel projection.
---
# Research Report
1. Call `report_projection`. Read `projection` only from a `ready` envelope; return a `blocked` envelope's controlled gaps without composing facts, citations, HTML or links. Its input budget is 2,048 approximate tokens.
2. The delivered structure is `Research question`, `Conclusions`, `Evidence and methods`, `Limitations and gaps`. Research Kernel owns headings, citations and typed evidence rendering.
3. Call `publish_report` with only a human-readable title. Return the controlled publication result; on failure return its structured gaps and no preview, download or save.
