---
status: accepted
---
# Project Export
## Decision
Project export is a read-only Kernel projection with `project.json`, `pipeline-runs.json`, `traces.json`, `artifacts.json`, `artifacts/<sha256>`, BibTeX metadata `bibtex/<sha256>.bib`, and `manifest.json`.
The Artifact inventory combines admitted node payloads, Pipeline run/step/event payloads, Runtime Trace values, and every saved Artifact in the Project scope. A reference outside that scope fails export. Saved Artifacts remain under `artifacts/`; media type does not define a report.
Credential labels normalize case and arbitrary non-alphanumeric separators; their complete line-delimited value is redacted in strings. Absolute POSIX and drive-qualified Windows paths redact regardless of wording, component spelling, separator or spaces; URL spans remain intact. Recursive fact transformation admits only finite JSON scalars, string-key maps and lists; binary values, non-string keys, cycles, unknown values and raw secret fields become deterministic parseable redaction markers.
Every Artifact retains identity, original SHA-256, media type, size and creation time in `artifacts.json`. Each `artifacts/<sha256>` member is a deterministic JSON metadata-only omission record, including textual and unknown media; raw artifact bodies never enter the ZIP. BibTeX media additionally receive a deterministic parseable `@comment` metadata record containing only immutable Artifact metadata. This export is a reproducible manifest, not a raw file transfer.
Every referenced Trace requires a readable Runtime projection. Missing Runtime or failed inspection fails export before ZIP creation.
ZIP entries are lexically ordered and use fixed timestamp, Unix creator, permissions and deflate compression. The manifest checksums cover exported entries, excluding itself.
## Non-goals
Import, sync, file management, provider calls and report classification are outside Project export.
