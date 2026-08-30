# Domain docs
[CONTEXT.md](../../CONTEXT.md) is the single glossary for Research Kernel, Runtime, Session, Run, Turn, Trace, Adapter and graph terms.
[ADR-0033](../adr/0033-runtime-adapters-and-event-delivery.md) and [ADR-0034](../adr/0034-direct-kernel-fact-recording.md) are the accepted Runtime/Kernel decisions for ownership, execution, event delivery and direct fact recording.
Their `supersedes` entries mark historical scopes that no longer provide current implementation instructions; other ADR details remain historical unless they conflict with those scopes.
Read the glossary and applicable ADR before changing a domain concept. Use defined terms and their exclusions in issue titles, code, tests and docs; surface conflicts before implementation.
Run `bash docs/agents/governance-check.sh` to verify the tracked governance files and current-contract assertions.
