---
topic: roadmap
---

# Success metrics

After six months of running Memoria, the system should be measurable on:

- **Time from capture to claim.** How long does a source spend between Zotero capture and producing at least one claim note?
- **Promotion rate.** What fraction of claim notes reach evergreen maturity within a year?
- **Review backlog.** How many cards are awaiting review (`review_status: requested`) at any time? Trend over time.
- **Orphan rate.** What fraction of notes have zero inlinks? Trend over time.
- **Reuse rate.** When drafting a chapter, what fraction of cited claims come from existing claim notes vs. fresh synthesis?
- **Suggestion disposition.** Per profile, the accept : edit : reject ratio of proposals (from each card's `review_status` outcome). The clearest read on whether the human-AI loop is paying off — distinct from the review *backlog* above. Log from day one; it cannot be backfilled.
- **Cost per run.** Tokens / $ per card-run, rolled up to cost-per-promoted-claim and the nightly discovery-loop trend — capability gains can cost 10× (ScienceAgentBench), and unattended loops compound.
- **Claim-staleness / FAMA exposure.** Current claims carrying `superseded_by`, and — the real signal — drafts or answers that cite a superseded claim (see [ADR-22](../decisions/22-claim-supersession.md)). A correctness signal with no dashboard home: drift-watch is structural and the contradictions dashboard (ADR-16) tracks disagreement, not staleness.
- **Coverage@k (loose ends).** Qualifying notes not yet linked or found, beyond the orphan count above.

These are not contract metrics; they are diagnostic. If reuse rate is high, the vault is paying off. If review backlog grows unboundedly, the workflow is mis-tuned. The disposition, cost, FAMA-exposure, and coverage metrics come from the benchmark review ([roadmap/evaluation.md](evaluation.md), Observability) and all aggregate from the extended audit-log substrate ([architecture/memory-tiers.md](../../explanation/architecture/memory-tiers.md)).
