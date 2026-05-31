---
topic: roadmap
---

# Design tensions to watch

These are tensions that won't resolve cleanly. Decisions on them shape Memoria's character.

- **Autonomy vs. control.** More automation makes the system faster but harder to trust. The default leans heavily toward control (review gate, no auto-promotion). The temptation will be to relax this; resist for the first six months.
- **Schema strictness vs. flexibility.** Strict schemas catch errors but slow capture. Loose schemas are fast but accumulate inconsistency. The compromise is *strict at the gate, flexible inside the lane*: classification promotes proposed fields to canonical, but the proposed fields themselves can be loose.
- **Specialization vs. simplicity.** Seven profiles is more setup than one agent. The payoff is reliability and architectural separation; the cost is configuration overhead. The full seven are the Memoria v0.1 baseline — if v0.2 wiring is not yet shipped, mode-based is a temporary fallback (see [profiles/README.md](../../explanation/profiles/README.md)), but it carries weaker safety properties and should be migrated away from as soon as the wiring lands.
- **Vault stability vs. graph richness.** A rich knowledge graph is the goal, but every link is also a maintenance burden. The linking patterns in [vault/README.md](../../explanation/vault/README.md) bias toward fewer, stronger links.
- **Single-user vs. team.** Memoria is designed for one human. If multiple humans share the vault, the `review_owner` field becomes load-bearing in ways the current design doesn't fully address.
