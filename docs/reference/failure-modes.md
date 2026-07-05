---
title: Failure modes
parent: System and infrastructure
grand_parent: Reference
---

# Failure modes

All known failure modes, sorted by severity. Each entry: symptom, severity, cause, and fix. For full symptom → diagnosis → fix recipes on the most common failures see [Troubleshooting](../how-to-guides/troubleshooting).

**Severity scale.** These rows use the same `LOW`/`MEDIUM`/`HIGH`/`CRITICAL` scale defined by [Linter: detectors and auto-fix](linter.md#the-detectors); what this page adds is where each level escalates:

| Severity | Escalates to |
| --- | --- |
| `CRITICAL` | Raises `loudness: block`: blocks new delegation or worker promotion until acknowledged, surfaces in the rail's **Now**, and records a Telegram push attempt when the bot environment is configured ([Inbox card fields](inbox-card-fields.md)). |
| `HIGH` | Surfaced in the rail's **Now** and in Maintenance's Drift watch. |
| `MEDIUM` | Surfaced in Maintenance during the weekly review. |
| `LOW` | Aggregated weekly. |

---

## All failure modes

Sorted by severity, then topic.

| Symptom | Severity | Cause | Fix |
| --- | --- | --- | --- |
| **Obsidian Linter corrupts frontmatter** | CRITICAL | The frontend Obsidian Linter plugin is installed — it is incompatible with Memoria ([ADR-130](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)) | Uninstall it. It reorders/rewrites Memoria-owned Concept frontmatter; folder exclusion does not make it safe. `markdownlint` + the Memoria Linter cover its role. |
| **Memoria-owned frontmatter overwritten** | CRITICAL | A frontend formatter reordered or stripped schema-owned frontmatter on save | Exclude Memoria-owned folders from any frontend formatter; let the Memoria Linter own frontmatter. |
| DOI source stays unchecked after enrichment | HIGH | Provider config or required provider payloads are missing; required DOI providers block checked promotion when provider calls fail. | Check `<workspace>/.memoria/config/providers.yaml` and the provider replay/payload inputs, then rerun `memoria work enrich`. |
| Dataview queries returning nothing | HIGH | `methodology` or `topics` field value doesn't match the controlled vocabulary exactly — looks like "nothing to do" | Check values in notes match [Vocabulary](vocabulary.md) exactly — full recipe: [Fix missing query results](../how-to-guides/troubleshooting/fix-missing-query-results.md). |
| `search` search index stale — `draft` finds no notes | HIGH | Index not rebuilt after notes changed (silent) | Rebuild the index: [Rebuild the search index](../how-to-guides/operate/rebuild-the-search-index.md). |
| `audit.jsonl` growing without bound | LOW | Expected: the log is append-only forever, never rotated ([ADR-127](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)) | The Linter's `audit-log-size` detector raises an advisory past 50 MB; archive a vault backup if disk pressure ever matters. |
| Broken frontmatter YAML | MEDIUM | YAML parse error: unclosed string, list indentation error, missing closing `---` | Fix raw YAML outside Obsidian; verify with the Linter. |
| Future editor adapter can't connect | MEDIUM | An external adapter added outside the alpha.15 baseline has a stale command path or local app configuration | Use the standalone `memoria` CLI first, then repair the adapter configuration outside the core installer. |
| Classification attention not appearing | MEDIUM | The source was added but enrichment/classification did not run or did not produce a checked result | Run `memoria work enrich <id>` and inspect the request with `memoria request show`. |
| Unsupported sync topology reading partial projections | MEDIUM | A deferred second-device or VPS setup reads files while sync is mid-transfer | Return to the supported local install; any future sync topology needs its own validation before support. |
| Deferred always-on bridge unreachable | MEDIUM | Unsupported `always-on` topology drifted or the single dispatcher is offline | Return to the supported local install, or follow the deferred topology notes in [Always-on VPS design](../design/always-on-vps-design.md). |
| Schema mismatch in Dataview | MEDIUM | A hand-authored note or stale sandbox fixture does not match the current schema | Repair the specific note or reinitialize the sandbox from the current template, then validate with `python3 -m memoria_vault.runtime.subsystems.integrity.linter.detectors --vault .`. |
| Scheduled task did not run | MEDIUM | Host scheduler is disabled, asleep, or pointing at a stale workspace path | Run the same `memoria` command manually, then repair the operator-managed scheduler entry. |
| Retry count climbing on same request | MEDIUM | Brittle prompt or broken tool | After `max_retries` (default 3) the request moves to `blocked`. Revise the request payload or archive as infeasible. |
| Request not progressing (`running` / `ready` / `blocked`) | MEDIUM | Worker crashed mid-run or human decision is owed on a blocked request | See full recipe in [Fix a stuck card](../how-to-guides/troubleshooting/fix-stuck-card.md). |
| Citekey alias not found at ingest | LOW | Import payload or catalog row lacks the alias | Re-import the BibTeX/CSL file or capture the source by DOI/file path. |
| Pandoc + BBT DOCX corrupt | LOW | Known Pandoc/Better BibTeX issue with some citation styles | Rerun Pandoc; test on a single-citation document first. |
| Removed profile directory appears | LOW | A pre-alpha.14 profile package or lane override was copied into the template/workspace | Delete the profile/lane package and run `python scripts/checks/alpha14_negative_gate.py`. |

---

## Related

- The troubleshooting how-to guides: [Troubleshooting](../how-to-guides/troubleshooting/README.md)
- Why the CRITICAL self-review failure can't happen: [Why the review gate is structural](../design/why-review-gate-is-structural.md)
