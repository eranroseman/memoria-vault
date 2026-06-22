---
title: Failure modes
parent: Reference
---

# Failure modes

All known failure modes, sorted by severity. Each entry: symptom, severity, cause, and fix. For full symptom → diagnosis → fix recipes on the most common failures see [Troubleshooting](../how-to-guides/troubleshooting).

**Severity scale.** These rows use the same `LOW`/`MEDIUM`/`HIGH`/`CRITICAL` scale defined by [Linter: detectors and auto-fix](linter.md#the-detectors); what this page adds is where each level escalates:

| Severity | Escalates to |
| --- | --- |
| `CRITICAL` | Raises `loudness: block`: blocks new delegation and review-gated promotion until acknowledged, surfaces on Home, and records a Telegram push attempt when the bot environment is configured ([Inbox card fields](inbox-card-fields.md)). |
| `HIGH` | Surfaced on Home and in `drift-watch`. |
| `MEDIUM` | Surfaced in `weekly-review`. |
| `LOW` | Aggregated weekly. |

---

## All failure modes

Sorted by severity, then topic.

| Symptom | Severity | Cause | Fix |
| --- | --- | --- | --- |
| **Obsidian Linter corrupts frontmatter** | CRITICAL | The frontend Obsidian Linter plugin is installed — it is incompatible with Memoria ([ADR-12](../adr/12-obsidian-linter-reference-only.md)) | Uninstall it. It reorders/rewrites the agent-owned `_proposed_classification` / `_enrichment` frontmatter; folder exclusion does not make it safe. `markdownlint` + the Memoria Linter cover its role. |
| **`_proposed_classification` or `_enrichment` overwritten** | CRITICAL | A frontend formatter reordered or stripped agent-owned frontmatter namespaces on save | Exclude agent-maintained folders from any frontend formatter; let the Memoria Linter own frontmatter. |
| Enrichment block empty after ingest | HIGH | `OPENALEX_API_KEY` missing in per-profile `.env` (silent — ingest "succeeded" with degraded data; OpenAlex requires a key since 2026-02) | Check `echo $OPENALEX_API_KEY`; populate the per-profile `.env`, then re-ingest — full recipe: [Fix empty enrichment](../how-to-guides/troubleshooting/fix-empty-enrichment.md). |
| Dataview queries returning nothing | HIGH | `methodology` or `topics` field value doesn't match the controlled vocabulary exactly — looks like "nothing to do" | Check values in notes match [Vocabulary](vocabulary.md) exactly — full recipe: [Fix missing query results](../how-to-guides/troubleshooting/fix-missing-query-results.md). |
| `qmd` search index stale — `draft` finds no notes | HIGH | Index not rebuilt after notes changed (silent) | `cd {vault-path} && qmd embed` — full rebuild (1–5 min for 500+ notes, 10–15 min for 2000+). |
| `audit.jsonl` growing without bound | LOW | Expected: the log is append-only forever, never rotated ([ADR-25](../adr/25-session-logging-two-logs.md)) | The Linter's `audit-log-size` detector raises an advisory past 50 MB; archive a vault backup if disk pressure ever matters. |
| Broken frontmatter YAML | MEDIUM | YAML parse error: unclosed string, list indentation error, missing closing `---` | Open in an editor outside Obsidian (Obsidian masks raw YAML). Fix manually. Verify with `python3 .memoria/operations/integrity/linter/detectors.py --vault .` (the Linter is an operation, not an agent — there is no `memoria-linter` profile). |
| Obsidian agent-client can't connect | MEDIUM | `hermes -p memoria-copi acp` cannot start or the plugin command path is stale | Run `hermes -p memoria-copi acp` in a terminal, then check the bundled agent-client settings and profile `.env`. |
| `_proposed_classification` not appearing | MEDIUM | The Librarian's `catalog-classify-source` skill did not run or the capture never reached the catalog lane | Check the source card and `memoria-librarian` bundled skills, then rerun the catalog/classify task. |
| Syncthing + `.bib` race condition | MEDIUM | VPS reads `.bib` while Syncthing is mid-transfer | Use Git pull for `.bib` distribution on `always-on` deployment — not Syncthing. |
| Deferred always-on bridge unreachable | MEDIUM | Unsupported `always-on` topology drifted or the single dispatcher is offline | Return to the supported local install, or follow the deferred topology notes in [Always-on VPS design](../explanation/deployment/always-on-vps-design.md). |
| Schema mismatch in Dataview | MEDIUM | Notes do not match the current schema | Run a manual, git-disciplined migration — there is no automated migrate command. Follow [Run a schema migration](../how-to-guides/operate/run-a-schema-migration.md) and validate with `python3 .memoria/operations/integrity/linter/detectors.py --vault .`. |
| Cron job didn't fire overnight | MEDIUM | Sleep-prone host, stale `.env`, or missing Hermes cron registration | Check `hermes cron list`, the latest board/metrics outputs under `system/`, and rerun the installer profiles-only path if wrappers are missing. |
| Retry count climbing on same card | MEDIUM | Brittle prompt or broken tool | After `max_retries` (default 3) the card auto-moves to `blocked`. Revise the handoff `metadata` or archive as infeasible. |
| Card not progressing (`running` / `ready` / `blocked`) | MEDIUM | Worker crashed mid-claim, unresolved `assignee`, or human decision owed on `blocked` card | See full recipe in [Fix a stuck card](../how-to-guides/troubleshooting/fix-stuck-card.md). |
| Citekey not found at ingest | LOW | `.bib` not updated or not pulled | Export from Zotero (File → Export Library → Keep Updated); `git add .memoria/memoria.bib && git commit && git push`. |
| `_enrichment` fields not queryable | LOW | `_enrichment` is a nested frontmatter namespace; Dataview can't query nested keys directly | Promote specific fields (e.g., `enriched_date`) to main frontmatter, or query the parent key. |
| Pandoc + BBT DOCX corrupt | LOW | Known Pandoc/Better BibTeX issue with some citation styles | Rerun Pandoc; test on a single-citation document first. |
| Profile install drift after edit | LOW | Vault source changed but profiles not re-deployed | Re-run `bash scripts/install.sh --profiles-only` (`.\scripts/install.ps1 -ProfilesOnly` on Windows). |
| Bitwarden bootstrap token rejected | LOW | Wrong region or revoked token | Re-run `hermes secrets bitwarden setup` and pick the correct region. |

---

## Related

- The troubleshooting how-to guides: [Troubleshooting](../how-to-guides/troubleshooting/README.md)
- Why the CRITICAL self-review failure can't happen: [Why the review gate is structural](../explanation/rationale/why-human-gate.md)
