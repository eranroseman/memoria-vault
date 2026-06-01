# Linter reference

Structural detectors, auto-fix classes, and severity scale for the Memoria Linter profile. For design rationale see [explanation/profiles/linter.md](../explanation/profiles/linter.md). For profile identity, permissions, and invocation level see [profiles.md](profiles.md).

---

## The eight structural detectors

Eight deterministic, zero-LLM checks. Full per-detector procedures live in [structural-detectors.md](../../vault/.memoria/profiles/memoria-linter/structural-detectors.md).

**Implementation:** three detectors are functions in `detectors.py` (pure Python stdlib); five run as live-Linter agent procedures that need runtime context the script lacks (git diff, SHA-256 audit-log pass, commit timestamps).

| Slug | Severity | Implementation | Catches |
| --- | --- | --- | --- |
| `profile-install-drift` | LOW | agent procedure (git diff) | Deployed copy under `~/.hermes/profiles/memoria-<name>/` differs from its vault source (usually a `git pull` without re-running `install.sh --profiles-only`). |
| `vault-hash-drift` | CRITICAL | agent procedure (SHA-256 vs audit log) | File written outside the policy MCP, or tampered with — the audit-log SHA-256 chain no longer matches. |
| `skeleton-drift` | MEDIUM | agent procedure (git timestamps) | Human-facing `00-meta/04-reference/` skeleton notes lag the design spec they mirror. |
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
| `review-gated-edit` | Any write to `30-synthesis/01-claims/`, `30-synthesis/02-reference/`, `30-synthesis/03-moc/`, `50-deliverables/` | **Deny** (policy MCP forces `dry_run` regardless of class) |

Policy gate: `policy.allow.auto_fix.classes: ["safe-and-unambiguous", "authorized-targeted"]` in `lane-overrides/linter.yaml` — the two granted classes; the other two appear under `deny.auto_fix.classes`.

---

## Severity scale

| Severity | Meaning | Dashboard surfacing |
| --- | --- | --- |
| `LOW` | Cosmetic or eventually-fixable. Does not block. | Aggregated weekly in `weekly-review`. |
| `MEDIUM` | Real drift that hasn't yet caused breakage. | Surfaced in `weekly-review`; reviewed in the Friday ritual. |
| `HIGH` | Active or imminent breakage. | Surfaced in Daily Health and `drift-watch`; pushed to Telegram. |
| `CRITICAL` | System integrity at risk. Blocks dispatch until acknowledged. | Always pushed to Telegram. |

**Verdict band rollup:** `PASS` if no HIGH or CRITICAL findings. `REVIEW` if any MEDIUM but no HIGH. `FAIL` if any HIGH or CRITICAL.

---

## Related

- Profile identity, permissions, and invocation level: [profiles.md](profiles.md)
- Design rationale: [explanation/profiles/linter.md](../explanation/profiles/linter.md)
- Workflow: [run the Linter](../how-to-guides/maintenance/run-the-linter.md)
- Recovery: [fix broken frontmatter](../how-to-guides/recovery/fix-broken-frontmatter.md), [fix profile drift](../how-to-guides/recovery/fix-profile-drift.md)
