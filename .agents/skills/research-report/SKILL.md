---
name: research-report
description: Generate a scientific research report or run its pre-delivery citation check from a Research Kernel projection.
---
# Research Report
1. Call `report_projection` to read admitted claims, sources, Artifacts, source levels, and check times. Build candidate facts with exact projected claim and source ids. Do not infer a link.
2. Call `report_validate` with the candidate facts before drafting. Return its structured gaps when `valid` is false.
3. Draft only from `accepted_facts`. Use this order: research question; conclusions; evidence and methods; limitations and gaps. Put claim and source ids beside each factual sentence. Put a projected Artifact id in every chart caption.
4. Call `export_bibtex` with a projected source Artifact id. Include only the returned validated content. Never synthesize, repair, or complete a `.bib` record.
5. Call `report_validate` again with the delivered fact set. Deliver only while `valid` remains true.
