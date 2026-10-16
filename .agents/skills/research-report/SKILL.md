---
name: research-report
description: Compose a scientific report from the current Project research graph, preserve uncertainty, and save an immutable report Artifact.
---
1. Query `graph` for the current Project's sources, directions, experiments and evidence relations.
2. Separate supported claims, proposed explanations, completed operations and unexecuted plans. Every claim cites its available source or experiment; disclose missing evidence.
3. Compose Research question, Conclusions, Evidence and methods, Limitations and gaps. Request an independent review through `delegate` when available; revise claims that exceed evidence.
4. Save the report through `artifact` using `text/markdown`, then return its download URL. Saving a report does not validate its claims.
