---
topic: profiles
---

# Linter — design summary

**Runtime contract.** Full prompt, lint check table, and the M-detector specifications live at `.memoria/profiles/memoria-linter/SOUL.md` and `.memoria/profiles/memoria-linter/M-detectors.md` in the starter vault.

## Mission

Linter is Memoria's deterministic conscience. It validates structure (frontmatter shape, link health, schema versions), catches silent-failure modes the human wouldn't notice (the eight M-detectors), and owns audit-log rotation and per-session log writing. The defining trait is **zero-LLM throughout**: every check Linter runs is regex, AST walk, SHA-256 hash, file existence, or set arithmetic. The same vault state produces the same report on every run, in every environment — which is what makes Linter the only Memoria profile that can sit inside CI gating.

## What this profile is not

- **Not a content checker.** Linter doesn't grade quality, judge whether a claim is well-supported, or assess whether a draft reads well. Those are Verifier's (provenance) and the human's (quality) domains. Linter checks *structure*: does the frontmatter parse, does the wikilink resolve, does the schema version match the authoritative reference.
- **Not Verifier.** Both run mechanical checks; Verifier is content-aware, Linter is content-agnostic (see [Profile boundaries](README.md#profile-boundaries)). Linter's questions are structural: is the schema valid, does `extract_path` resolve, is `data.json` consistent with the committed template?
- **Not an LLM.** This is non-negotiable. Memoria's design treats Linter's determinism as load-bearing — if the verdict-band rollup ever depended on LLM judgment, it would no longer be reproducible across runs, which would defeat its role as a CI gate. Any check that needs LLM judgment is by definition not a Linter check.
- **Not a fixer by default.** Dry-run is the default. Auto-fix is allowed only for the `safe-and-unambiguous` and `authorized-targeted` classes; schema changes, content edits, and review-gated-zone edits are always report-only. The policy MCP enforces the class gate at the tool layer — Linter cannot bypass it even if it tried.

## Design decisions

- **Zero-LLM and deterministic — the design parallel to the trust score.** Linter's verdict band (PASS / REVIEW / FAIL) is the structural rollup; the fleet-health dashboard's trust score is the operational rollup. Both are headline single numbers; both are reproducibly computed from logs and findings; neither involves LLM judgment in the rollup. This parallelism is intentional — operational health and structural health get separate headline metrics with the same epistemic discipline.
- **Owns `00-meta/02-logs/`.** Linter writes per-session log summaries, rotates the policy MCP audit log weekly (`audit.jsonl` → `00-meta/02-logs/archive/audit-YYYY-WW.jsonl`), and writes lint findings. This is the only path where Linter writes routinely (the rotation mechanics and its `authorized-targeted` classification are detailed in [Log rotation](#log-rotation) below).
- **M-detectors are the silent-failure layer.** The eight M-detectors catch failure modes the human wouldn't notice by reading content: a Dataview query that references a field no template emits (`dashboard-field-drift`), a `data.json` that drifted from the committed version (`plugin-config-drift`), an `extract_path` pointing at a missing file (`extract-path-broken`). The defining property is "silent" — the failure mode looks like "nothing to do" when there's actually something to do. The full detector specs live in `M-detectors.md` alongside the runtime SOUL.md.
- **Auto-fix is class-gated by the policy MCP.** When `profile = "memoria-linter"` and `action = "auto_fix"`, the MCP requires `flags.class ∈ {"safe-and-unambiguous", "authorized-targeted"}`. Schema/content changes and review-gated-zone edits are always `deny` regardless of who requests them. Class gating is the runtime enforcement of the auto-fix policy — not just a design rule, an enforced one.

## The eight M-detectors

The structural detectors, each a deterministic zero-LLM check identified by a descriptive slug. The full procedures (hashing, field-parsing, the four `plugin-config-drift` cases) live in `.memoria/profiles/memoria-linter/M-detectors.md` in the starter vault; this is the at-a-glance index.

| ID | Severity | Catches |
| --- | --- | --- |
| `profile-install-drift` | LOW | The deployed copy under `~/.hermes/profiles/memoria-<name>/` differs from its vault source (usually a `git pull` without re-running `install.ps1`). |
| `vault-hash-drift` | CRITICAL | A file was written outside the policy MCP, or tampered with after a write — the audit-log SHA-256 chain no longer matches. |
| `skeleton-drift` | MEDIUM | The human-facing `00-meta/04-reference/` skeleton notes lag the design spec they mirror. |
| `dashboard-field-drift` | HIGH | A Dataview query references a field no template emits → the query returns zero rows and the human sees "nothing to do" when there is. |
| `command-vocab-drift` | MEDIUM | A command named in the design isn't declared in its owner profile's SOUL.md (or vice versa). |
| `plugin-config-drift` | MEDIUM | A working `.obsidian/plugins/<plugin>/data.json` differs from the version committed at git HEAD (HIGH if `agent-client.autoAllowPermissions` flips to `true`). |
| `orphan-working-files` | LOW | Editor backups / `.tmp.*` / `.bak` leftovers accumulated outside the transient zones. |
| `extract-path-broken` | HIGH | A paper-note's `extract_path` points at a Marker extract file that doesn't exist. |

The defining property is **silent**: each catches a failure that looks like "nothing to do" while something is actually wrong. They roll up into the verdict band (below).

## Auto-fix policy

Linter classifies every proposed fix into one of four classes. The class determines whether the fix can apply automatically or requires explicit human action; the policy MCP enforces the class gate at the tool layer — Linter cannot bypass it.

| Class | Examples | Default |
| --- | --- | --- |
| `safe-and-unambiguous` | Trailing whitespace, missing `created` timestamp on a new note, missing required template field with one obvious value | **Auto-fix** (delegated to Templater — see [§"Implementing safe-and-unambiguous fixes via Templater"](#implementing-safe-and-unambiguous-fixes-via-templater)) |
| `authorized-targeted` | Audit-log rotation, lint-findings file truncation, dashboard `last_updated` refresh | **Auto-fix** (Linter's own logs/dashboards only) |
| `schema-content` | Frontmatter field rename, value-set change, deprecated field removal | **Dry-run** (always — needs `schema-migrate`) |
| `review-gated-edit` | Any write to `30-synthesis/01-claims/`, `30-synthesis/02-reference/`, `30-synthesis/03-moc/`, `50-deliverables/` | **Deny** (the policy MCP forces `dry_run` regardless of class) |

The gate is `policy.allow.auto_fix.classes: ["safe-and-unambiguous", "authorized-targeted"]` in `lane-overrides/linter.yaml`; anything else is `deny`. See [architecture/policy-mcp.md](../../reference/architecture/policy-mcp.md) for the request/response contract and audit-log shape.

## Severity scale

Every Linter finding carries a severity. The scale drives dashboard surfacing, notification routing, and the verdict-band rollup:

| Severity | Meaning | Examples |
| --- | --- | --- |
| `LOW` | Cosmetic or eventually-fixable. Doesn't block; aggregated weekly. | Trailing whitespace, missing optional field, slightly stale `enriched_date`. |
| `MEDIUM` | Real drift that hasn't yet caused breakage. Surfaced in [`weekly-review`](../dashboards/weekly-review.md); reviewed during the Friday ritual. | `data.json` plugin config diverged from committed version (`plugin-config-drift`), unused MOC entry, broken non-canonical link. |
| `HIGH` | Active breakage or imminent breakage. Surfaced in [Daily Health](../dashboards/daily-health.md) and [`drift-watch`](../dashboards/drift-watch.md); pushed to Telegram. | Broken `extract_path` (`extract-path-broken`), schema version mismatch on a recently-edited note, audit-log SHA-chain break (`vault-hash-drift`). |
| `CRITICAL` | System integrity at risk. Always pushes to Telegram, blocks dispatch until acknowledged. | Audit-log tamper detection failure, policy MCP startup failure, lane-override file invalid. |

The verdict band rolls up by counting findings: `PASS` if no HIGH/CRITICAL; `REVIEW` if any MEDIUM but no HIGH; `FAIL` if any HIGH or CRITICAL.

## Log rotation

Linter owns `00-meta/02-logs/` and rotates the policy MCP audit log on a weekly schedule:

- **Source.** `00-meta/02-logs/audit.jsonl` (append-only by the policy MCP throughout the week).
- **Rotation trigger.** Sunday 00:00 local, or when the active file exceeds 50 MB, whichever comes first.
- **Archive.** Moved to `00-meta/02-logs/archive/audit-YYYY-WW.jsonl` (ISO week-numbered). The active file is recreated empty and the policy MCP resumes appending.
- **Retention.** Archive files are kept indefinitely by default. The human can configure quarterly deletion in `.memoria/log-retention.yaml`; Linter checks this file on each rotation pass.
- **Hash chain.** Each archive's first entry's `before_hash` matches the previous archive's last `after_hash`. `vault-hash-drift` (audit-log SHA-chain break) fires if the link fails — the chain stays auditable across rotations.

Rotation is classed as `authorized-targeted` in the [auto-fix table](#auto-fix-policy), so the policy MCP allows it without escalation. Session logs (`00-meta/02-logs/sessions/YYYY-MM-DD-HHMM.jsonl`) are written one per Hermes session and not rotated; they accumulate, but human pruning is rare since each is small.

## Implementing safe-and-unambiguous fixes via Templater

Linter delegates `safe-and-unambiguous` auto-fixes to [Templater](../../reference/plugins/templater-obsidian.md) rather than writing them directly. Templater already handles frontmatter parsing, atomic file updates, and Obsidian's open-buffer reconciliation — all of which Linter would otherwise have to re-implement carefully and risk getting wrong.

The pattern:

1. Linter detects a fixable finding (e.g., missing `created` on a fleeting note with `_creation_marker:` present).
2. Linter invokes a Templater script by triggering it through Templater's documented plugin API (e.g., `app.plugins.plugins['templater-obsidian'].templater.append_template_to_file`), passing the file path and fix parameters. *(Status: design intent — specific invocation API TBD; Templater does not expose a headless API independent of the Obsidian runtime.)*
3. Templater performs the edit using its existing safe-edit primitives (preserves cursor position, reconciles with open buffers, atomic write).
4. Linter records the fix in the audit log; the policy MCP audits the Templater call as Linter's own write.

This keeps Linter's fix surface small (one delegation pattern) and uses a battle-tested library for the dangerous parts (concurrent edits, atomic writes). Anything outside Templater's safe-edit surface — multi-file refactors, content-level rewrites, schema migrations — falls back to dry-run regardless of class.

## Permissions and commands

Folder permission matrix lives in [profiles/README.md](../../reference/profile-matrices.md#folder-permission-matrix); the runtime contract (lint check table, full M-detector specs, threshold values) lives in the SOUL.md and M-detectors.md alongside it. The command catalog is in [profiles/profile-commands.md](../../reference/profile-commands.md).

## Related

- Workflows: [lint](../../how-to/workflows/maintenance/lint.md)
- Reference: [architecture/policy-mcp.md](../../reference/architecture/policy-mcp.md) — the auto-fix class gate is enforced here; the audit log Linter rotates is owned here.
- Reference: [roadmap/profile-compilation.md](../../project/roadmap/profile-compilation.md) — **deferred design.** `profile-install-drift` was originally specified against this compiler; under direct profile management `profile-install-drift` is the install-drift check (vault source vs deployed copy), not build drift.
- Method class: [architecture/why-computational-methods.md](../architecture/why-computational-methods.md) — Linter is the definitive example of a fully deterministic profile.
- ADRs: [9 typed relations](../../project/decisions/09-typed-relations-frontmatter.md) — the Linter validates `relations:` keys against the controlled vocabulary (a `schema-check` concern). [16 contradictions dashboard](../../project/decisions/16-contradictions-dashboard.md) — adjacent concept; the Linter is structural, the contradictions surface is content.
