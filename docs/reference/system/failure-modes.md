---
title: Failure modes
parent: System and infrastructure
nav_order: 5
grand_parent: Reference
---

# Failure modes

All known failure modes, sorted by severity. Each entry: symptom, severity, cause, and fix. For full symptom → diagnosis → fix recipes on the most common failures see [Troubleshooting](../../how-to-guides/troubleshooting/README.md).

**Severity scale.** These rows use the same `LOW`/`MEDIUM`/`HIGH`/`CRITICAL` scale defined by [Linter: detectors and auto-fix](../analysis-and-surfaces/linter.md#the-detectors); what this page adds is where each level escalates:

| Severity | Escalates to |
| --- | --- |
| `CRITICAL` | Raises `loudness: block`: blocks new delegation or worker promotion until acknowledged, surfaces in the rail's **Now**, and records a Telegram push attempt when the bot environment is configured ([Control plane](../control-and-policy/control-plane.md)). |
| `HIGH` | Surfaced in the rail's **Now** and in Maintenance's Drift watch. |
| `MEDIUM` | Surfaced in Maintenance during the weekly review. |
| `LOW` | Aggregated weekly. |

---

## All failure modes

Sorted by severity, then topic.

| Symptom | Severity | Cause | Fix |
| --- | --- | --- | --- |
| **Obsidian Linter corrupts frontmatter** | CRITICAL | The frontend Obsidian Linter plugin is installed — it is incompatible with Memoria ([thin read-API surfaces over one engine, PI direct access preserved](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)) | Uninstall it. It reorders/rewrites Memoria-owned Concept frontmatter; folder exclusion does not make it safe. `markdownlint` + the Memoria Linter cover its role. |
| **Memoria-owned frontmatter overwritten** | CRITICAL | A frontend formatter reordered or stripped schema-owned frontmatter on save | Exclude Memoria-owned folders from any frontend formatter; let the Memoria Linter own frontmatter. |
| DOI source stays unchecked after enrichment | HIGH | Provider config or required provider payloads are missing; required DOI providers block checked promotion when provider calls fail. | Check `<workspace>/.memoria/config/providers.yaml` and the provider replay/payload inputs, then rerun `memoria work enrich`. |
| Dataview queries returning nothing | HIGH | `methodology` or `topics` field value doesn't match the controlled vocabulary exactly — looks like "nothing to do" | Check values in notes match [Vocabulary](../data-model/vocabulary.md) exactly — full recipe: [Fix missing query results](../../how-to-guides/troubleshooting/fix-missing-query-results.md). |
| `search` search index stale — `draft` finds no notes | HIGH | Index not rebuilt after notes changed (silent) | Rebuild the index: [Rebuild the search index](../../how-to-guides/operate/rebuild-the-search-index.md). |
| `audit.jsonl` growing without bound | LOW | Expected: the log is append-only forever, never rotated ([quarantine-and-verify with durable, audit-logged crash recovery](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)) | The Linter's `audit-log-size` detector raises an advisory past 50 MB; archive a vault backup if disk pressure ever matters. |
| Broken frontmatter YAML | MEDIUM | YAML parse error: unclosed string, list indentation error, missing closing `---` | Fix raw YAML outside Obsidian; verify with the Linter. |
| Optional editor adapter can't connect | MEDIUM | The local HTTP server, token, read scope, or adapter configuration is stale | Use the standalone `memoria` CLI first, then repair the adapter configuration outside the core installer. |
| Classification attention not appearing | MEDIUM | The source was added but enrichment/classification did not run or did not produce a checked result | Run `memoria work enrich <id>` and inspect the request with `memoria request show`. |
| Schema mismatch in Dataview | MEDIUM | A hand-authored note or stale sandbox fixture does not match the current schema | Repair the specific note or reinitialize the sandbox from the current package seed, then validate with `python3 -m memoria_vault.runtime.subsystems.integrity.linter.detectors --vault .`. |
| Scheduled task did not run | MEDIUM | Host scheduler is disabled, asleep, or pointing at a stale workspace path | Run the same `memoria` command manually, then repair the operator-managed scheduler entry. |
| Same request fails after explicit retry | MEDIUM | Brittle prompt, broken input payload, or unavailable dependency | Inspect `memoria request show`, amend or cancel the request, then retry only after the underlying error is fixed. |
| Request not progressing (`pending` / `running` / `failed`) | MEDIUM | Worker has not run, crashed mid-run, or recovery marked an interrupted run failed for explicit retry | See full recipe in [Fix a stuck card](../../how-to-guides/troubleshooting/fix-stuck-card.md). |
| Citekey alias not found at ingest | LOW | Import payload or catalog row lacks the alias | Re-import the BibTeX/CSL file or capture the source by DOI/file path. |
| Pandoc + BBT DOCX corrupt | LOW | Known Pandoc/Better BibTeX issue with some citation styles | Rerun Pandoc; test on a single-citation document first. |

---

## Related

- The troubleshooting how-to guides: [Troubleshooting](../../how-to-guides/troubleshooting/README.md)
- Why the CRITICAL self-review failure can't happen: [Why the review gate is structural](../../explanation/rationale/boundaries/why-review-gate-is-structural.md)
