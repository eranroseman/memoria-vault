---
topic: decisions
id: 61
title: Nightly discovery loop, code-experiment loop, and Writer-proposed claims
status: superseded
date_proposed: 2026-06-11
date_resolved: 2026-06-19
assumes: [48, 21]
supersedes: []
superseded_by: [95, 96, 97]
---

# ADR-61: Nightly discovery loop, code-experiment loop, and Writer-proposed claims

## Superseded

This proposal bundle is split into one ADR per lane-bounded automation expansion:

- [ADR-95](95-nightly-proactive-discovery-loop.md): Nightly proactive discovery loop.
- [ADR-96](96-code-lane-keep-revert-experiment-loop.md): Code-lane keep/revert experiment loop.
- [ADR-97](97-writer-proposed-candidate-claim-notes.md): Writer-proposed candidate claim notes.

## Related

- **Related decisions / Depends on:** [ADR-48 Co-PI and agent consolidation](48-copi-and-agent-consolidation.md) (the Librarian `find` capability the nightly loop drives); [ADR-21 L3 autonomy ceiling](21-l3-autonomy-ceiling.md) (the boundary all three respect); [ADR-51](51-inbox-category-and-honesty-card.md) (candidate and gap proposals land as Inbox cards).
- **Original tracking issue:** [#411](https://github.com/eranroseman/memoria-vault/issues/411).
