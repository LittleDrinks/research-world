---
status: accepted
---
# Project Export
## Decision
Project export is a read-only Kernel projection with `project.json`, `pipeline-runs.json`, `traces.json`, `artifacts.json`, `artifacts/<sha256>`, admitted-source `bibtex/<sha256>.bib`, and `manifest.json`.
The Artifact inventory combines admitted node payloads, Pipeline run/step/event payloads, Runtime Trace values, and every saved Artifact in the Project scope. A reference outside that scope fails export. Saved Artifacts remain under `artifacts/`; media type does not define a report.
Credential keys normalize case and separators; `api-key`, `client-secret`, `token`/`tokens`, credentials and passwords redact across structured values and text. Credential or absolute-path values embedded in exported text are replaced. `artifacts.json` retains immutable Artifact identity, original SHA-256 and size, plus exported SHA-256 and size.
Textual media types are `text/*`, `*+json`, `*+xml`, and `application/json`, `application/x-bibtex`, `application/xml`, `application/javascript`, `application/yaml` or `application/x-yaml`; this includes SVG through `image/svg+xml`. Valid JSON, XML, YAML and BibTeX are parsed and deterministically re-encoded after structural redaction. XML retains element-tree comments and processing instructions; CDATA lexical form normalizes to equivalent text. A declared structured Artifact that does not parse becomes a deterministic, parseable redaction record. Every opaque binary Artifact remains in the inventory and archive under `artifacts/<sha256>`, but its member is a deterministic metadata-only omission record, never its raw bytes.
An absolute POSIX path has two or more non-empty components after `/`; components may begin with digits, hyphens or non-ASCII characters. A Windows path is drive-qualified with either slash. A complete structured scalar, quoted or bracketed value may contain spaces. In free prose, an unquoted path has no spaces and ends only at end-of-value or `,`, `;`, `)`, `}`, `]`, a quote, or `<`; whitespace does not delimit it. URL spans remain intact. This preserves ambiguous prose such as `The ratio /alpha/beta is dimensionless.` while removing objectively bounded paths.
Every referenced Trace requires a readable Runtime projection. Missing Runtime or failed inspection fails export before ZIP creation.
ZIP entries are lexically ordered and use fixed timestamp, Unix creator, permissions and deflate compression. The manifest checksums cover exported entries, excluding itself.
## Non-goals
Import, sync, file management, provider calls and report classification are outside Project export.
