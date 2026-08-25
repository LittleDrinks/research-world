---
name: research-report
description: Generate a scientific research report or run its pre-delivery citation check from a Research Kernel projection.
---
# Research Report
1. Call `report_projection` to inspect the admitted claim, source and linked Artifact views. Do not compose report facts, citations, HTML or artifact links.
2. Call `publish_report` with only a human-readable title. Research Kernel derives the validated report from its projection.
3. Return the controlled publication result. When it fails, return every structured gap and do not offer a preview, download or save.
