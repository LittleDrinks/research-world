---
status: accepted
---
# Report Publication
Research Kernel owns admitted Claim, Source and Artifact projection, final delivery validation and deterministic HTML rendering. Runtime exposes `publish_report` only to invoke that controlled Kernel operation; Runtime Trace remains audit-only and never supplies report facts.
A generated preview is temporary and has no named Project Artifact reference. Saving creates one immutable named report reference to the published HTML Artifact. Reading that reference always returns the original bytes.
Chat Report cards are the report entry point. No Reports navigation is restored. Preview is sandboxed; downloads are `text/html`.
