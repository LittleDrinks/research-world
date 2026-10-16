---
name: source-research
description: Retrieve primary scientific sources, verify bibliographic metadata, preserve available full text as Project Artifacts, and disclose evidence limits.
version: 1
updated: 2026-08-24T00:00:00Z
---
# Source Research
1. Search at least two applicable scholarly databases and preserve every query, database, and verification time in the SourceCandidate.
2. Verify title, authors, year, venue, DOI or stable URL, source type, license, and access status against Crossref, OpenAlex, arXiv, PubMed, or the primary publisher record.
3. Retrieve the complete text from an official archive when available. Store it with `project_files`; copy its Artifact id, media type, and SHA-256 into the SourceCandidate.
4. Record relevance to the current Direction as supports, refutes, or background, with exact quotations and section, page, paragraph, table, or figure locations.
5. Never use an abstract as a full-text location or as support for a claim.
6. When complete text cannot be retrieved, set access status to `full_text_unavailable`, state the reason and unresolved questions, use the source only as background, return no Artifact, and return no claims.
7. Return candidates only. Never submit nodes, decide Admission, invent metadata, or treat a successful Tool call as admitted evidence.
