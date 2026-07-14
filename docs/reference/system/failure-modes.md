---
title: Failure modes
parent: System and infrastructure
nav_order: 5
grand_parent: Reference
---

# Failure modes

All known failure modes, sorted by severity. Each entry: symptom, severity, cause, and fix. For full symptom → diagnosis → fix recipes on the most common failures see [Troubleshooting](../../how-to-guides/troubleshooting/README.md).

**Severity scale.** These rows use the same `LOW`/`MEDIUM`/`HIGH`/`CRITICAL`
labels defined by [Linter: detectors and auto-fix](../analysis-and-surfaces/linter.md#the-detectors).
For linter findings, severity alone controls the verdict:

| Severity | Linter verdict |
| --- | --- |
| `CRITICAL` | `FAIL` |
| `HIGH` | `REVIEW` |
| `MEDIUM` | `REVIEW` |
| `LOW` | `PASS` when no higher-severity finding exists |

Attention loudness is independent metadata assigned by operations that create
attention cards; there is no automatic severity-to-loudness mapping. Open
`loudness: block` cards affect only the optional policy-hook path, and
alert/block cards attempt a Telegram push only when that adapter is configured.
The standalone CLI/worker path is not paused by loudness.

---

## All failure modes

Sorted by severity, then topic.

| Symptom | Severity | Cause | Fix |
| --- | --- | --- | --- |
| **Obsidian Linter corrupts frontmatter** | CRITICAL | The frontend Obsidian Linter plugin is installed — it can rewrite Memoria-owned frontmatter outside Memoria's controls | Uninstall it. It reorders/rewrites Memoria-owned Concept frontmatter; folder exclusion does not make it safe. `markdownlint` + the Memoria Linter cover its role. |
| **Memoria-owned frontmatter overwritten** | CRITICAL | A frontend formatter reordered or stripped schema-owned frontmatter on save | Exclude Memoria-owned folders from any frontend formatter; let the Memoria Linter own frontmatter. |
| DOI source stays unchecked after enrichment | HIGH | Provider config or required provider payloads are missing; required DOI providers block checked promotion when provider calls fail. | Check `<workspace>/.memoria/config/providers.yaml` and the provider replay/payload inputs, then rerun `memoria work enrich`. |
| Filtered views returning nothing | HIGH | A Work `research_area`/`methodology` value or note `topics` value does not match the controlled vocabulary exactly — looks like "nothing to do" | Check note `topics` with the schema/linter and inspect Work metadata with `memoria work export` or the read API. Compare both with [Vocabulary](../data-model/vocabulary.md); see [Fix missing query results](../../how-to-guides/troubleshooting/fix-missing-query-results.md). |
| Search index stale — `memoria ask` misses checked notes | HIGH | Index not rebuilt after notes changed (silent) | Rebuild the index: [Rebuild the search index](../../how-to-guides/operate/rebuild-the-search-index.md). |
| `audit.jsonl` growing without bound | LOW | Expected: the log is append-only forever, never rotated | The Linter's `audit-log-size` detector raises an advisory past 50 MB; archive a vault backup if disk pressure ever matters. |
| Broken frontmatter YAML | MEDIUM | YAML parse error: unclosed string, list indentation error, missing closing `---` | Fix raw YAML outside Obsidian; verify with the Linter. |
| Optional editor adapter can't connect | MEDIUM | The local HTTP server, token, read scope, or adapter configuration is stale | Use the standalone `memoria` CLI first, then repair the adapter configuration outside the core installer. |
| Classification attention not appearing | MEDIUM | The source was added but enrichment/classification did not run or did not produce a checked result | Run `memoria work enrich <id>` and inspect the request with `memoria request show`. |
| Schema mismatch in filtered views | MEDIUM | A hand-authored note or stale test-vault fixture does not match the current schema | Repair the specific note or reinitialize the test-vault from the current package seed, then validate with `./.memoria/.venv/bin/python -m memoria_vault.runtime.subsystems.integrity.linter.detectors --vault .` (on Windows, replace the interpreter path with `.\.memoria\.venv\Scripts\python.exe`). |
| Scheduled task did not run | MEDIUM | Host scheduler is disabled, asleep, or pointing at a stale workspace path | Run the same `memoria` command manually, then repair the operator-managed scheduler entry. |
| Same request fails after explicit retry | MEDIUM | Brittle prompt, broken input payload, or unavailable dependency | Inspect `memoria request show`. If the original arguments remain correct, fix the underlying error and retry the failed request. For changed non-scope arguments, create a successor with `request amend` and a fresh key; for a changed ID, reference, path, or target, submit a new original operation. Cancel only obsolete pending work; never retry a superseded request. |
| Request not progressing (`pending` / `running` / `failed`) | MEDIUM | Worker has not run, crashed mid-run, or recovery marked an interrupted run failed for explicit retry | See full recipe in [Fix a stuck request](../../how-to-guides/troubleshooting/fix-stuck-card.md). |
| `memoria doctor` reports unbacked blobs | MEDIUM | Blob files have no configured blob/general backup and no valid local stamp matching a present backup target | Run `memoria workspace backup <target>` outside the vault or configure blob-sync/general-backup coverage; SQLite-only replication is insufficient. See [Backup and recovery](backup-and-recovery.md). |
| Backup target is absent after interruption | HIGH | The process stopped during an identity-bound first publication or replacement | Run `memoria workspace recover`; it removes an unpublished first stage, restores a prior target when one existed, or retains a completed validated publication. |
| Restore refuses an older journal head | MEDIUM | The selected backup predates the journal head committed in the checked-out Git revision | Preserve the backup, check out the matching Git revision, then rerun `memoria workspace restore <source> --force`. |
| Restore reports that rollback also failed | HIGH | A filesystem error prevented one or more saved live components from returning to place | Stop writes. Run `memoria workspace recover`; it validates the live restore-transaction marker, restores its bound sibling rollback set, and verifies the recovered journal. |
| Citekey alias not found at ingest | LOW | Import payload or catalog row lacks the alias | Re-import the BibTeX/CSL file or capture the source by DOI/file path. |
| Pandoc + BBT DOCX corrupt | LOW | Known Pandoc/Better BibTeX issue with some citation styles | Rerun Pandoc; test on a single-citation document first. |

---

## Related

- The troubleshooting how-to guides: [Troubleshooting](../../how-to-guides/troubleshooting/README.md)
- Why the CRITICAL self-review failure can't happen: [Why the review gate is structural](../../explanation/rationale/boundaries/why-review-gate-is-structural.md)
