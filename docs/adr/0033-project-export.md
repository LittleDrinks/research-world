---
status: accepted
---
# Project Export
## Decision
Project export is a read-only Kernel projection with `project.json`, `pipeline-runs.json`, `traces.json`, `artifacts.json`, `artifacts/<sha256>`, admitted-source `bibtex/<sha256>.bib`, and `manifest.json`.
The Artifact inventory combines admitted node payloads, Pipeline run/step/event payloads, Runtime Trace values, and every saved Artifact in the Project scope. A reference outside that scope fails export. Saved Artifacts remain under `artifacts/`; media type does not define a report.
Structured credential fields (`api_key`, `client_secret`, tokens, credentials and passwords) and credential or absolute-path values embedded in exported text are replaced. Textual Artifact entries contain sanitized export bytes while `artifacts.json` retains the immutable Artifact id, original SHA-256 and size, plus the exported SHA-256 and size. Binary Artifact bytes retain their original hash and size.
Textual media types are `text/*`, `*+json`, `*+xml`, and `application/json`, `application/x-bibtex`, `application/xml`, `application/javascript`, `application/yaml` or `application/x-yaml`; this includes SVG through `image/svg+xml` and excludes every other binary type. JSON, XML and YAML entries are parsed and re-encoded after structural redaction; BibTeX and JavaScript retain valid source syntax through token replacement.
An absolute POSIX path has two or more non-empty components after `/`; components may begin with digits, hyphens or non-ASCII characters. A Windows path is drive-qualified. A complete structured scalar, quoted or bracketed value may contain spaces. In free prose, an unquoted path has no spaces and ends only at end-of-value or `,`, `;`, `)`, `}`, `]`, a quote, or `<`; whitespace does not delimit it. URL spans remain intact. This preserves ambiguous prose such as `The ratio /alpha/beta is dimensionless.` while removing objectively bounded paths.
Every referenced Trace requires a readable Runtime projection. Missing Runtime or failed inspection fails export before ZIP creation.
ZIP entries are lexically ordered and use fixed timestamp, Unix creator, permissions and deflate compression. The manifest checksums cover exported entries, excluding itself.
## Non-goals
Import, sync, file management, provider calls and report classification are outside Project export.
