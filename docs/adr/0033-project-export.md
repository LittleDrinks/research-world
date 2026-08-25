---
status: accepted
---
# Project Export
## Decision
Project export is a read-only Kernel projection with `project.json`, `pipeline-runs.json`, `traces.json`, `artifacts.json`, `artifacts/<sha256>`, BibTeX metadata `bibtex/<sha256>.bib`, and `manifest.json`.
The Artifact inventory combines admitted node payloads, Pipeline run/step/event payloads, Runtime Trace values, and every saved Artifact in the Project scope. A reference outside that scope fails export. Saved Artifacts remain under `artifacts/`; media type does not define a report.
The export boundary allowlists JSON scalars, `dict`, `list`, and `tuple`; every other value is `[REDACTED]`. Credential-labelled fields, all absolute or temporary paths, every URI userinfo, and credential-bearing URI query value are redacted in values, keys, member names and decoded serialized JSON. URI handling accepts every scheme. Serialized JSON is rejected as `[REDACTED]` before decoding when it exceeds the byte or item limit. Traversal consumes mappings and sequences incrementally under the same item and depth limits; it never materializes arbitrary iterators.
Every Artifact identity is exactly `artifact:<64 lowercase SHA-256 hex>` and must agree with `sha256`; malformed Artifact records become an `invalid_artifact_identity` inventory record and receive no member or fabricated digest. Valid Artifacts retain identity, original SHA-256, media type, size and creation time in `artifacts.json`. Each `artifacts/<sha256>` member is a deterministic JSON metadata-only omission record, including textual and unknown media; raw artifact bodies never enter the ZIP. BibTeX media additionally receive a deterministic parseable `@comment` metadata record containing only immutable Artifact metadata. This export is a reproducible manifest, not a raw file transfer.
Report archive membership is projected only from durable publication and named-report records owned by the Kernel. Until that model is available, no report archive member is emitted; report projections, source HTML, Markdown, and arbitrary Artifacts are not reports.
Every referenced Trace requires a readable Runtime projection whose `session.workspace` resolves to the exported Project workspace. Missing, unreadable, foreign or malformed sessions fail export before ZIP creation.
ZIP entries are lexically ordered and use fixed timestamp, Unix creator, permissions and deflate compression. The manifest checksums cover exported entries, excluding itself.
## Non-goals
Import, sync, file management, provider calls and report classification are outside Project export.
