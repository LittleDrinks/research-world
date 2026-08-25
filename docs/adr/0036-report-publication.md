---
status: accepted
---
# Report Publication
Research Kernel owns admitted Claim, Source and Artifact projection, validation and deterministic HTML rendering. `publish_report` accepts only a title and derives every finding, citation and evidence section from that projection. Runtime invokes that command without adding report input; Trace remains audit-only.
Projection source views contain only id, title, source level, check time and evidence anchor. Artifact views contain only id, media type, size and claim/source linkage. Fields that can reveal credentials, transport, configuration, paths or raw payload are excluded. Artifacts appear only when an admitted claim cites their admitted source or experiment evidence.
Validation rejects a projection whose fact text, claim, source or linked artifact cannot be verified. It returns structured `code`, `path` and `value`; rejection creates neither a published preview nor a saved reference. Rendering uses validated findings and anchored citations, and states the validated absence of code, formulas or charts instead of inventing content.
A preview is a temporary publication handle scoped to one Project and Thread. Saving creates an immutable named report reference to its exact HTML bytes. Names are unique within a Project and duplicate names return `report_name_taken`. Identical HTML may be published independently by different Projects. History queries and reads are Project-scoped.
Chat Report cards are the report entry point and render the controlled Runtime publication result. No Reports navigation is restored. Preview is sandboxed; downloads are `text/html`.
