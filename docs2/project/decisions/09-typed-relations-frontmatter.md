---
adr: 9
status: stub
---

# ADR-9: Typed relations in frontmatter

**Status:** Accepted

**Decision:** Adopt `supports:` and `contradicts:` as first-class frontmatter fields on `claim-note`. Each value is a list of wikilink targets. The Verifier uses these fields to trace that every cited source actually supports or contradicts the claim as labeled.

**Context:** Untyped wikilinks express connection but not relationship type. Typed relations make Verifier claim-tracing tractable and enable queries like "show me all contradicting evidence for this claim."

**Extended relations** (`similar`, `cross-domain`, `counter-intuitive`) deferred pending evidence of need — see [../roadmap/future-directions.md](../roadmap/future-directions.md).
