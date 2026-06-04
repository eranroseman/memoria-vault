---
title: "Linter: detectors and auto-fix"
parent: Reference
---

# Linter: detectors and auto-fix

Structural detectors, auto-fix classes, and severity scale for the Memoria Linter profile. For design rationale see [The Linter](../explanation/profiles/linter.md). For profile identity, permissions, and invocation level see [Profile capabilities](profiles.md).

---

## The eight structural detectors

Eight deterministic, zero-LLM checks. Full per-detector procedures live in [Structural detectors: silent-failure checks](../../vault/.memoria/profiles/memoria-linter/structural-detectors.md).

**Implementation:** three detectors are functions in `detectors.py` (pure Python stdlib); five run as live-Linter agent procedures that need runtime context the script lacks (git diff, SHA-256 audit-log pass, commit timestamps). `detectors.py` itself defines nine functions in total — these three structural detectors plus six housekeeping checks (broken-wikilink, fama-exposure, graph-analyze, orphan-working-files, schema-check, stale-answer-drafts, stale-fleeting) — so the "nine functions vs. eight structural detectors" counts measure different things and do not contradict.

| Slug | Severity | Implementation | Catches |
| --- | --- | --- | --- |
| `profile-install-drift` | LOW | agent procedure (git diff) | Deployed copy under `~/.hermes/profiles/memoria-<name>/` differs from its vault source (usually a `git pull` without re-running `scripts/install.sh --profiles-only`). |
| `vault-hash-drift` | CRITICAL | agent procedure (SHA-256 vs audit log) | File written outside the policy MCP, or tampered with — the audit-log SHA-256 chain no longer matches. |
| `skeleton-drift` | MEDIUM | agent procedure (git timestamps) | Human-facing `00-meta/` skeleton notes lag the design spec they mirror. |
| `dashboard-field-drift` | HIGH | `detectors.py` (stdlib) | A Dataview query references a field no template emits → query returns zero rows and human sees "nothing to do" when there is work. |
| `command-vocab-drift` | MEDIUM | agent procedure (SOUL.md scan) | A command named in the design isn't declared in its owner profile's SOUL.md (or vice versa). |
| `plugin-config-drift` | MEDIUM | agent procedure (git HEAD diff) | Working `.obsidian/plugins/<plugin>/data.json` differs from the version committed at git HEAD. HIGH if `agent-client.autoAllowPermissions` flips to `true`. |
| `orphan-working-files` | LOW | `detectors.py` (stdlib) | Editor backups / `.tmp.*` / `.bak` leftovers accumulated outside transient zones. |
| `extract-path-broken` | HIGH | `detectors.py` (stdlib) | A paper-note's `extract_path` points at a Marker extract file that doesn't exist. |

The defining property of all eight: **silent** — each failure looks like "nothing to do" while something is actually wrong.

---

## Auto-fix classes

Every proposed fix carries a class, hard-coded by the detector. The class determines whether the fix applies automatically or requires human action; the policy MCP enforces the gate at the tool layer.

| Class | Examples | Default behavior |
| --- | --- | --- |
| `safe-and-unambiguous` | Trailing whitespace, missing `created` timestamp, missing required template field with one obvious value | **Auto-fix** (granted; delegated to Templater) |
| `authorized-targeted` | Audit-log rotation, lint-findings file truncation, dashboard `last_updated` refresh | **Auto-fix** (granted; Linter's own logs/dashboards only) |
| `schema-content` | Frontmatter field rename, value-set change, deprecated field removal | **Dry-run always** (not granted; requires `schema-migrate`) |
| `review-gated-edit` | Any write to `30-synthesis/01-claims/`, `30-synthesis/02-reference/`, `30-synthesis/03-moc/`, `50-deliverables/` | **Deny** |

Policy gate: `policy.allow.auto_fix.classes: ["safe-and-unambiguous", "authorized-targeted"]` in `lane-overrides/linter.yaml` — the two granted classes; the other two appear under `deny.auto_fix.classes`. The `review-gated-edit` *class* is denied outright (`AUTO_FIX_DENY_CLASSES`). Separately, a mutating write to a review-gated *zone* (a different mechanism) degrades to `dry_run` — see [Policy MCP](policy-mcp.md#auto-fix-policy).

---

## Severity scale

| Severity | Meaning | Dashboard surfacing |
| --- | --- | --- |
| `LOW` | Cosmetic or eventually-fixable. Does not block. | Aggregated weekly in `weekly-review`. |
| `MEDIUM` | Real drift that hasn't yet caused breakage. | Surfaced in `weekly-review`; reviewed in the Friday ritual. |
| `HIGH` | Active or imminent breakage. | Surfaced in Daily Health and `drift-watch`; pushed to Telegram. |
| `CRITICAL` | System integrity at risk. Blocks dispatch until acknowledged. | Always pushed to Telegram. |

**Verdict band rollup:** `PASS` if only LOW/INFO findings (or none). `REVIEW` if any HIGH or MEDIUM and no CRITICAL. `FAIL` only if any CRITICAL. A HIGH-only run is `REVIEW`, never `FAIL`.

---

## Schedule

The Linter is the first lane cleared for scheduled dispatch (read-mostly, low blast radius). Its jobs are defined in the profile's `cron/scheduled.yaml`:

| Cron | Card | Cadence |
| --- | --- | --- |
| `0 2 * * *` | `nightly-hygiene` | Nightly 02:00 |
| `0 5 * * *` | `fleeting-staleness-report` | Nightly 05:00 |
| `0 4 * * MON` | `weekly-drift-report` | Weekly, Monday 04:00 |

Dispatch stays **disabled** until the lane has produced stable dry-run reports (`approvals.cron_mode` defaults to `deny`); it is enabled deliberately, not on install. The Linter also runs on demand and after each ingest batch.

---

## Related

- Profile identity, permissions, and invocation level: [Profile capabilities](profiles.md)
- Design rationale: [The Linter](../explanation/profiles/linter.md)
- Workflow: [run the Linter](../how-to-guides/maintain/run-the-linter.md)
- Recovery: [fix broken frontmatter](../how-to-guides/recovery/fix-broken-frontmatter.md), [fix profile drift](../how-to-guides/recovery/fix-profile-drift.md)
