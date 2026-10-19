---
name: research-report
description: Review a Project's research evidence against its published rubric and save a structured audit Artifact.
---
1. Query `graph` and read the target record's fixed version and referenced artifacts. Separate supported claims, explanations, completed operations and plans.
2. Call `artifact` with `operation=templates`. Read the selected schema, every dimension's score anchors, applicability rules, evidence requirements and character budgets.
3. Check each applicable dimension against the fixed inputs. Use `check` with a score only after checking evidence; use `unverified` without a score when access or execution is missing. Use `skip` only for an inapplicable dimension and explain why. Low scores require an actionable correction.
4. Record execution evidence separately: a complete plan is not an executed experiment. Cite artifact IDs and precise locations for each scored dimension. An inaccessible full text cannot support a claim of full-text verification.
5. Save code, source text and raw results as evidence files with their actual media types. Save the audit as JSON through `artifact` with `schema_id`, `record_id` and the fixed `target_artifact_id`. Correct reported field errors until validation succeeds; do not substitute a Markdown attachment.
6. Return the saved report's reading URL and the unresolved corrections. A schema-valid report does not establish scientific correctness.
