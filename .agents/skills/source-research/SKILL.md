---
name: source-research
description: Search primary scientific literature and return verified metadata, relevance, conflicting evidence, and access limits.
---
1. Query `literature` using applicable Crossref, OpenAlex, arXiv or PubMed sources; retain the database and query alongside results.
2. Compare title, authors, year and DOI or stable identifier across available results. Flag disagreement and unavailable metadata.
3. Treat abstracts and search metadata as background. Do not invent full-text quotations, page locations, licenses, experimental results or claims unavailable in returned records.
4. Return relevant sources, their support or challenge to the research direction, and unresolved questions. A Child Agent returns candidates to the main Agent; it does not write the research graph.
