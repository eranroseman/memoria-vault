---
title: The Linter
parent: Profiles
---


# The Linter

The Linter is Memoria's deterministic conscience. It validates structure (frontmatter shape, link health, schema versions), catches silent-failure modes the human wouldn't notice from reading content, and owns audit-log rotation and per-session log writing. Its defining trait is **zero-LLM throughout**: every check the Linter runs is regex, AST walk, SHA-256 hash, file existence, or set arithmetic. The same vault state produces the same report on every run, in every environment.

---

## Why it's designed this way

**Zero-LLM is load-bearing, not a limitation.** Memoria treats Linter's determinism as the condition for CI use. If the Linter's verdict ever depended on LLM judgment, it would no longer be reproducible across runs — which would defeat its purpose as a structural gating mechanism. Any check that genuinely needs LLM judgment is, by definition, not a Linter check. That's not a gap; it's the design.

**The eight structural detectors catch what reading can't.** The structural detectors are designed for one property: they catch failures that look like "nothing to do" when something is actually wrong. A Dataview query that references a field no template emits returns zero rows — the human sees an empty dashboard and assumes there's nothing to review. A paper note whose `extract_path` points at a missing file appears normal. These failures are invisible without a structural sweep. The Linter's job is to make them visible before they compound.

**Owns `00-meta/02-logs/`.** The Linter writes per-session log summaries and rotates the audit log weekly. This ownership is narrow by design — the Linter is the only profile that routinely writes to logs, keeping the audit trail predictable. Audit log rotation is classified as `authorized-targeted` auto-fix, the only class where the Linter writes without explicit human approval.

**A structural parallel to the trust score.** The Linter's verdict band (PASS / REVIEW / FAIL) is the structural health rollup; the fleet-health dashboard's trust score is the operational health rollup. Both are headline numbers, both are computed reproducibly from logs and findings, and neither involves LLM judgment. The parallelism is intentional — structural health and operational health deserve the same epistemic discipline.

---

## What the Linter is not

**Not a content checker.** The Linter doesn't grade quality, judge whether a claim is well-supported, or assess whether a draft reads well. Those are Verifier's domain (provenance) and the human's domain (quality). The Linter checks *structure*: does the frontmatter parse, does the wikilink resolve, does the schema version match the canonical reference?

**Not Verifier.** Both run mechanical checks, but the Linter is content-agnostic and Verifier is content-aware. The Linter asks: is the schema valid, does `extract_path` point to an existing file, is `data.json` consistent with the committed template? Verifier asks: does this claim trace to a real source, is this citekey retracted? Same mechanical approach, different questions.

**Not a fixer by default.** Dry-run is the default. Auto-fix is allowed only for two classes of findings: cosmetically safe changes (trailing whitespace, missing timestamps) and authorized log-maintenance operations. Schema changes, content edits, and writes to review-gated zones are always report-only. The policy MCP enforces this at the tool layer — the Linter cannot bypass it even if asked.

---

## Related

**Explanation**

- Structural counterpart in content: [Verifier](verifier.md)
- The weekly ritual Linter findings feed into: [weekly review](../dashboards/structural-health/weekly-review.md)
- Why the Linter runs zero LLM: [why-computational-methods.md](../rationale/why-computational-methods.md)

**How-to**

- Workflow: [run the Linter](../../how-to-guides/maintenance/run-the-linter.md)
- Recovery: [fix broken frontmatter](../../how-to-guides/recovery/fix-broken-frontmatter.md), [fix profile drift](../../how-to-guides/recovery/fix-profile-drift.md)

**Reference**

- Structural detectors, auto-fix classes, severity scale: [linter.md](../../reference/linter.md)
- Profile identity, permissions, invocation level: [profiles.md](../../reference/profiles.md)
