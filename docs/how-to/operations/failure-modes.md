---
topic: operations
---

# Failure modes — Detect / Fix / Verify

Operational reference for failures that block core workflows. Each entry follows a **Detect / Fix / Verify** triplet: the symptom a human notices, the commands to recover, and the check that confirms the recovery actually worked. This is the authoritative companion to `00-meta/04-reference/safe-mode.md` (the vault-resident human note); use safe-mode for the *first response* and this doc for the *full recovery procedure*.

A recovery isn't complete until the verify step passes — symptoms alone don't confirm the fix held.

## Detailed recovery procedures

Full recipes for the failures most likely to block a core workflow. The [complete catalog](#all-failure-modes) — these plus everything else — is the table further down; the entries here just expand the most important rows.

### 1. Stale `.bib` — ingest can't find the citekey

**Detect.** In a `memoria-librarian` session, `/llm-wiki ingest --source {citekey}` returns "citekey not found" or "not in library.bib".

```bash
grep {citekey} .memoria/library.bib   # should return one entry
```

**Fix (human).** Export from Zotero (File → Export Library → Keep Updated), then push:

```bash
git add .memoria/library.bib
git commit -m "manual: bib update"
git push
git pull --ff-only   # on the agent node
```

**Verify.**

```bash
grep {citekey} .memoria/library.bib            # entry present
git log --oneline .memoria/library.bib | head -3   # recent commit
hermes -p memoria-librarian chat -s llm-wiki   # then: /llm-wiki ingest --source {citekey} --dry-run → no "not found" error
```

### 2. Missing `_proposed_classification` — classification can't proceed

**Detect.** Note exists in `20-sources/01-papers/` with `lifecycle: proposed` but no `_proposed_classification` comment block in the file body. The classification query in [weekly-review](../../explanation/dashboards/weekly-review.md) returns the note, but it has no classification proposal to review.

**Fix.**

```bash
hermes -p memoria-librarian chat -s classify   # then: /classify --source {citekey}
# Re-runs classify on a single note; re-proposes classification from the abstract
```

**Verify.** Open the note — `_proposed_classification` comment block now present with `study_design`, `methods`, `topic`, and `projects` fields populated. `lifecycle` remains `proposed` (correct — it only becomes `current` after the human promotes).

### 3. Broken frontmatter — note missing from Dataview queries

**Detect.** Obsidian Properties panel shows a YAML parse error. Note does not appear in Dataview queries that should include it.

```bash
hermes -p memoria-linter chat -s lint   # then: /lint --source {citekey} --dry-run — reports YAML structure issues
```

**Fix (human).** Open the raw file in an editor outside Obsidian (Obsidian masks the raw YAML). Common causes: unclosed string (`title: "Unterminated`), list indentation error, missing closing `---` delimiter. Fix manually, save.

**Verify.**

```bash
hermes -p memoria-linter chat -s lint   # then: /lint --source {citekey} --dry-run → no YAML errors reported
```

In Obsidian: Properties panel shows no error; note appears in a Dataview query (`FROM "20-sources/01-papers" WHERE file.name = "{citekey}"`).

### 4. Stale `qmd` index — vault search returns empty or outdated results

**Detect.** In a `memoria-writer` session, `/draft "known topic"` returns no vault results despite relevant notes existing.

```bash
qmd search "known term" --vault {vault-path}
# Returns empty or omits notes known to exist
```

**Fix.**

```bash
cd {vault-path}
qmd embed
# Full rebuild — 1–5 minutes for 500+ notes; 10–15 minutes for 2000+ notes
```

**Verify.**

```bash
qmd search "known term" --vault {vault-path}   # returns expected notes
hermes -p memoria-writer chat -s draft   # then: /draft "known topic" → returns vault results with citekeys
```

### 5. Profile install drift — deployed `SOUL.md` doesn't match vault source

**Detect.** The memoria-linter's `profile-install-drift` detector reports a SHA-256 mismatch between `.memoria/profiles/memoria-<name>/<file>` (vault source) and `~/.hermes/profiles/memoria-<name>/<file>` (deployed copy).

**Fix.** Either (a) the source changed in the vault and `install.ps1` hasn't been re-run — execute `./install.ps1` to redeploy all seven profiles; or (b) someone hand-edited the deployed copy — `diff` the two files, then either copy the change back into `.memoria/profiles/memoria-<name>/` and commit (promoting the edit) or just re-run `install.ps1` (discarding the edit).

**Verify.**

```bash
hermes -p memoria-linter chat -s health-report   # then: /health-report --detectors profile-install-drift — no drift reported
```

### 6. Stuck card — claimed but not progressing

**Detect.** A card sits in the same `status` on [board-state](../../explanation/dashboards/board-state.md) without advancing — most often `running` long after it was claimed, or `ready` that never gets dispatched. Because WIP is one `running` card per profile, a card wedged in `running` stalls its whole lane: nothing behind it gets claimed.

```bash
hermes kanban show <card-id>   # full state: status, retry count, blocker reason, handoff summary
hermes kanban list             # the lane's queue — is it backing up behind one card?
```

**Fix.** Depends on where it's wedged:

- **`running` (worker crashed or hung).** The claim is stale — no `done`, no return to `ready`. The dispatcher reclaims stale claims automatically on its next tick and returns the card to `ready` (recorded as `outcome: reclaimed`) — there is no manual `retry` verb. If it re-wedges at once on the re-dispatch, the tool or prompt is broken rather than transient — treat it as the `blocked` case.
- **`blocked` (a human decision is owed — e.g. escalated past `max_retries`).** It needs a fix, not a re-run. Address the cause (revise the handoff `metadata`, fix the tool, rewrite the prompt), then `hermes kanban unblock` → `ready`; re-dispatch resets the retry count. If it can't be made to work, `hermes kanban archive` it with `reason: "infeasible"`. See the [retry pattern](../../explanation/kanban-board/README.md#retry-pattern).
- **`ready` but never dispatched.** Usually an unresolved `assignee` — the dispatcher emits `skipped_nonspawnable` and leaves the card in `ready`. Check the `assignee` names a real lane (see [worker lanes](../../explanation/kanban-board/states.md#worker-lanes-and-the-exit-contract)).

**Verify.**

```bash
hermes kanban show <card-id>   # status has advanced, or the card is archived with an explicit reason
```

No card silently sitting: it has either moved off the stuck state or been archived with a `reason`.

## All failure modes

Sorted by severity (most urgent first), then by topic. The **Severity** column uses the four bands from the [memoria-linter severity scale](../../explanation/profiles/linter.md#severity-scale), read as operational urgency: **CRITICAL** (vault integrity or security at risk) → **HIGH** (silent or active breakage — the system may look healthy while losing or degrading data) → **MEDIUM** (real drift; works now, will bite later) → **LOW** (cosmetic, or recoverable in one command).

| Symptom | Severity | Cause | Fix |
| --- | --- | --- | --- |
| **Obsidian Linter corrupts frontmatter** | CRITICAL | The Obsidian Linter running on agent-maintained folders | Exclude `10-inbox/`, `20-sources/`, `30-synthesis/02-reference/` in the Obsidian Linter's `foldersToIgnore` — see [obsidian-plugins/README.md](../../reference/plugins/README.md). |
| **`_proposed_classification` or `_enrichment` deleted** | CRITICAL | An Obsidian Linter rule or plugin upgrade introduced an HTML-comment stripper that ran on save | **Never enable any rule that strips HTML comments.** Currently no such rule exists in Obsidian Linter v1.31.2, but the precaution is forward-looking — diff the rule registry before accepting any plugin upgrade. See [obsidian-plugins/README.md](../../reference/plugins/README.md). |
| Enrichment block empty after ingest | HIGH | Polite-pool email not set (`OPENALEX_EMAIL` missing in `.env`) (silent — ingest "succeeded" but with degraded data) | `echo $OPENALEX_EMAIL`; check per-profile `.env` |
| Dataview queries returning nothing | HIGH | `study_design` or `topic` vocabulary inconsistency — query returns empty table that looks like "nothing to do" | Check values in notes match the schema vocabulary exactly (see [frontmatter-schema.md](../../reference/frontmatter-schema.md)). |
| `qmd` search index stale — `draft` finds no notes | HIGH | Index not rebuilt after notes changed (silent — search returns nothing, looks like no matches) | See the **Stale `qmd` index** recipe (#4) above. |
| `audit.jsonl` growing without bound | HIGH | memoria-linter log rotation not running (silent until disk fills) | Check [memoria-linter log rotation](../../explanation/profiles/linter.md#log-rotation); it rotates weekly. |
| Broken frontmatter YAML | MEDIUM | YAML parse errors cause downstream enrichment to fail | See the **Broken frontmatter** recipe (#3) above. |
| Obsidian-agent-client can't connect | MEDIUM | ACP server not running or tunnel down | `systemctl --user status hermes-acp` and `hermes-tunnel` |
| `_proposed_classification` not appearing | MEDIUM | `classify` skill not installed or not in lane's allow list | `hermes skills install classify`; check `.memoria/lane-overrides/librarian.yaml` |
| Syncthing + `.bib` race condition | MEDIUM | VPS reads `.bib` while Syncthing is mid-transfer | Use Git pull for `.bib` distribution on the `always-on` option, not Syncthing — see [sync-and-coordination.md](../../project/roadmap/sync-and-coordination.md#bib-watcher-always-on-only). |
| VPS tunnel drops on WSL2 restart | MEDIUM | systemd user service not auto-starting | `systemctl --user enable hermes-tunnel`. |
| Schema version mismatch in Dataview | MEDIUM | Notes on old schema version | `/schema-migrate --dry-run` (in a `memoria-linter` session) → review proposed field additions → run without `--dry-run` on a single folder first. |
| Cron job didn't fire overnight | MEDIUM | Sleep-prone host or stale `.env` | `always-on` option only (VPS); check `journalctl --user -u hermes-overnight` and the [discovery loop section](../../project/roadmap/future-directions.md#the-discovery-loop). |
| Retry count climbing on same card | MEDIUM | Brittle prompt or broken tool | After `max_retries` (default 3) recoverable failures the card auto-escalates to `blocked` — see [kanban-board/README.md retry pattern](../../explanation/kanban-board/README.md#retry-pattern). The human decides whether to revise the payload or archive as infeasible. |
| Card not progressing (`running` / `ready` / `blocked`) | MEDIUM | Worker crashed mid-claim, unresolved `assignee`, or a human decision owed on a `blocked` card | See the **Stuck card** recipe (#6) above. |
| Citekey not found at ingest | LOW | `.bib` not updated or not pulled | See the **Stale `.bib`** recipe (#1) above. |
| `_enrichment` fields not queryable | LOW | `_enrichment` is a YAML comment block, not real frontmatter (design constraint, not a defect) | Use note modification date (`file.mtime`) as a proxy, or promote specific fields (e.g., `enriched_date`) to main frontmatter. |
| Pandoc + BBT DOCX corrupt | LOW | Known Pandoc/Better BibTeX issue with some citation styles | Rerun Pandoc; test on a single-citation document first to isolate. |
| High Scite contrast flag | LOW | Paper is actively disputed (a curation signal, not a system failure) | Open paper in Zotero → check what Scite classifies as contrasting → decide whether to include as primary or supporting evidence only. |
| Profile install drift after edit | LOW | Vault source changed but `install.ps1` not re-run | See the **Profile install drift** recipe (#5) above. |
| Bitwarden bootstrap token rejected | LOW | Wrong region or revoked token | Re-run `hermes secrets bitwarden setup` and pick the correct region (US Cloud / EU Cloud / self-hosted) — see [roadmap/secret-management.md](../../project/roadmap/secret-management.md). |

## When this doc is wrong

If a failure recurs and the Fix here doesn't work, treat that as a design issue. Either the symptom mapping is incomplete (the doc points at the wrong cause) or the fix is brittle (works sometimes but not always). In both cases the right response is to update this doc, not to memorize a workaround — the next human who hits it should find a recipe that actually works.

The rule: never let a stale fix sit in this doc. If a command changed (e.g., a renamed flag) or a service was replaced (e.g., Bitwarden → 1Password), update or remove the entry the same session the drift is noticed.
