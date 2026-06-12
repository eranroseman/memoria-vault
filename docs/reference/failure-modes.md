---
title: Failure modes
parent: Reference
---

# Failure modes

All known failure modes, sorted by severity. Each entry: symptom, severity, cause, and fix. For full symptom → diagnosis → fix recipes on the most common failures see [Troubleshooting](../how-to-guides/troubleshooting).

**Severity scale** (matches the [Linter severity scale](linter.md#the-detectors)):

| Severity | Meaning |
| --- | --- |
| `CRITICAL` | Vault integrity or security at risk. Blocks dispatch until acknowledged. Always pushes to Telegram. |
| `HIGH` | Silent or active breakage — the system may look healthy while losing or degrading data. Surfaced on Home and in `drift-watch`. |
| `MEDIUM` | Real drift; works now, will bite later. Surfaced in `weekly-review`. |
| `LOW` | Cosmetic or recoverable in one command. Aggregated weekly. |

---

## All failure modes

Sorted by severity, then topic.

| Symptom | Severity | Cause | Fix |
| --- | --- | --- | --- |
| **Obsidian Linter corrupts frontmatter** | CRITICAL | The frontend Obsidian Linter plugin is installed — it is incompatible with Memoria (ADR-12) | Uninstall it. It reorders/rewrites the agent-owned `_proposed_classification` / `_enrichment` frontmatter; folder exclusion does not make it safe. `markdownlint` + the Memoria Linter cover its role. |
| **`_proposed_classification` or `_enrichment` overwritten** | CRITICAL | A frontend formatter reordered or stripped agent-owned frontmatter namespaces on save | Exclude agent-maintained folders from any frontend formatter; let the Memoria Linter own frontmatter. |
| Enrichment block empty after ingest | HIGH | `OPENALEX_API_KEY` missing in per-profile `.env` (silent — ingest "succeeded" with degraded data; OpenAlex requires a key since 2026-02) | Check `echo $OPENALEX_API_KEY`; populate the per-profile `.env`. |
| Dataview queries returning nothing | HIGH | `methodology` or `topics` field value doesn't match the schema vocabulary exactly — looks like "nothing to do" | Check values in notes match [Frontmatter fields](frontmatter.md) vocabulary exactly. |
| `qmd` search index stale — `draft` finds no notes | HIGH | Index not rebuilt after notes changed (silent) | `cd {vault-path} && qmd embed` — full rebuild (1–5 min for 500+ notes, 10–15 min for 2000+). |
| `audit.jsonl` growing without bound | HIGH | Linter log rotation not running (silent until disk fills) | Verify Linter's `cron/scheduled.yaml` rotation task is active. |
| Broken frontmatter YAML | MEDIUM | YAML parse error: unclosed string, list indentation error, missing closing `---` | Open in an editor outside Obsidian (Obsidian masks raw YAML). Fix manually. Run `hermes -p memoria-linter chat -s lint` to verify. |
| Obsidian agent-client can't connect | MEDIUM | ACP server not running or tunnel down | `systemctl --user status hermes-acp` and `hermes-tunnel`. |
| `_proposed_classification` not appearing | MEDIUM | `classify` skill not installed or not in Librarian lane's allow list | `hermes skills install classify`; check `.memoria/lane-overrides/librarian.yaml`. |
| Syncthing + `.bib` race condition | MEDIUM | VPS reads `.bib` while Syncthing is mid-transfer | Use Git pull for `.bib` distribution on `always-on` deployment — not Syncthing. |
| VPS tunnel drops on WSL2 restart | MEDIUM | systemd user service not auto-starting | `systemctl --user enable hermes-tunnel`. |
| Schema version mismatch in Dataview | MEDIUM | Notes on old schema version | `hermes -p memoria-linter chat -s schema-migrate` → `--dry-run` first, review diff, then run on a single folder first. |
| Cron job didn't fire overnight | MEDIUM | Sleep-prone host or stale `.env` (`always-on` only) | Check `journalctl --user -u hermes-overnight`. |
| Retry count climbing on same card | MEDIUM | Brittle prompt or broken tool | After `max_retries` (default 3) the card auto-moves to `blocked`. Revise the handoff `metadata` or archive as infeasible. |
| Card not progressing (`running` / `ready` / `blocked`) | MEDIUM | Worker crashed mid-claim, unresolved `assignee`, or human decision owed on `blocked` card | See full recipe in [Fix a stuck card](../how-to-guides/troubleshooting/fix-stuck-card.md). |
| Citekey not found at ingest | LOW | `.bib` not updated or not pulled | Export from Zotero (File → Export Library → Keep Updated); `git add .memoria/memoria.bib && git commit && git push`. |
| `_enrichment` fields not queryable | LOW | `_enrichment` is a nested frontmatter namespace; Dataview can't query nested keys directly | Promote specific fields (e.g., `enriched_date`) to main frontmatter, or query the parent key. |
| Pandoc + BBT DOCX corrupt | LOW | Known Pandoc/Better BibTeX issue with some citation styles | Rerun Pandoc; test on a single-citation document first. |
| Profile install drift after edit | LOW | Vault source changed but profiles not re-deployed | Re-run `bash scripts/install.sh --profiles-only` (`.\scripts/install.ps1 -ProfilesOnly` on Windows). |
| Bitwarden bootstrap token rejected | LOW | Wrong region or revoked token | Re-run `hermes secrets bitwarden setup` and pick the correct region. |

---

## Recover checklist order

When multiple failures occur simultaneously:

1. CRITICAL first — address tamper detection and security before anything else.
2. HIGH that's silent — failures that "look like nothing to do" burn time and can compound.
3. HIGH that's visible — active breakage with obvious symptoms.
4. MEDIUM — address during the weekly review ritual.
5. LOW — batch and address monthly.

---

## Related

- The troubleshooting how-to guides: [Troubleshooting](../how-to-guides/troubleshooting/README.md)
- Why the CRITICAL self-review failure can't happen: [Why the review gate is structural](../explanation/rationale/why-human-gate.md)
