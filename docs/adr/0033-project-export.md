---
status: accepted
---
# Project Export
## Decision
Project export is a read-only Kernel projection with `project.json`, `pipeline-runs.json`, `traces.json`, `artifacts.json`, `artifacts/<sha256>`, admitted-source `bibtex/<sha256>.bib`, and `manifest.json`.
The Artifact inventory combines admitted node payloads, Pipeline run/step/event payloads, Runtime Trace values, and every saved Artifact in the Project scope. A reference outside that scope fails export. Saved Artifacts remain under `artifacts/`; media type does not define a report.
Structured credential fields and credential or absolute-path values embedded in exported text are replaced. Textual Artifact entries contain sanitized export bytes while `artifacts.json` retains the immutable Artifact id, original SHA-256 and size, plus the exported SHA-256 and size. Binary Artifact bytes retain their original hash and size.
Free-text absolute paths are a boundary-delimited POSIX pathname with at least two components or a drive-qualified Windows pathname; URL spans remain intact.
Every referenced Trace requires a readable Runtime projection. Missing Runtime or failed inspection fails export before ZIP creation.
ZIP entries are lexically ordered and use fixed timestamp, Unix creator, permissions and deflate compression. The manifest checksums cover exported entries, excluding itself.
## Non-goals
Import, sync, file management, provider calls and report classification are outside Project export.
