# Structural detectors: silent-failure checks

The eight drift checks at the bottom of the Linter's lint table (see [SOUL.md](SOUL.md#lint-checks-and-thresholds)) — profile install drift, vault hash drift, skeleton drift, dashboard field drift, command vocabulary drift, plugin-config drift, orphan working files, extract path broken link — are **structural detectors**, each identified by a descriptive slug. They differ from the data-hygiene checks earlier in the table (orphans, stale enrichment, broken wikilinks) in three ways: they are deterministic and zero-LLM, they catch silent-failure modes the human wouldn't notice otherwise, and they roll up to a single [verdict band](SOUL.md#verdict-band) that gates scheduled work.

| ID | Detector | Severity | Why this severity |
| --- | --- | --- | --- |
| `profile-install-drift` | Profile install drift | LOW | The deployed copy in `~/.hermes/profiles/memoria-<name>/` differs from its source in `.memoria/profiles/memoria-<name>/`. Usually means a `git pull` updated the source and the human hasn't re-run `install.ps1` — recoverable in one command. |
| `vault-hash-drift` | Vault hash drift | CRITICAL | A file was written outside the policy MCP, or was tampered with after a write. Either reversibility or security is at stake. |
| `skeleton-drift` | Skeleton note drift | MEDIUM | The human-facing notes lag the engineering spec. Won't break anything immediately but erodes trust over weeks. |
| `dashboard-field-drift` | Dashboard field drift | HIGH | Silent-failure mode: a query returns zero rows in a real vault because a field name is wrong. The human sees "nothing to do" when there's something to do. |
| `command-vocab-drift` | Command vocabulary drift | MEDIUM | A command named in the design isn't declared in the owning SOUL.md file (or vice versa). The system runs but inconsistencies accumulate. |
| `plugin-config-drift` | Plugin-config drift | MEDIUM | The human's working `.obsidian/plugins/<plugin>/data.json` differs from the version committed at git HEAD. Usually means a settings change through the plugin UI hasn't been committed, or a `git pull` brought in changes the human hasn't reviewed. Suffix conventions (`data.json` / `.example` / `.TODO`) are in the [plugins reference](https://github.com/eranroseman/memoria-vault/blob/main/docs/reference/plugins.md#datajson-conventions); per-plugin enforcement specifics are below. |
| `orphan-working-files` | Orphan working files | LOW | Editor backups, manual-rename leftovers, or `.tmp.*` working files have accumulated outside transient zones. Recoverable in one human decision per file (keep, archive, delete). Severity is LOW because no canonical state is at risk — but pattern-matching is cheap and the signal is reliable, so detection earns its place even if remediation is mundane. |
| `extract-path-broken` | Extract path broken link | HIGH | A paper-note's `extract_path` points at a Marker output file that doesn't exist. Silent-failure mode: the human clicks the wikilink expecting text, gets nothing, doesn't know that ingest was incomplete. Catches aborted ingest runs, citekey renames mid-flight, and deleted extracts. Severity matches `dashboard-field-drift` — the same "field references something missing, query returns empty silently" failure class. |

> **Implementation split.** Three of these eight — `dashboard-field-drift`, `orphan-working-files`, `extract-path-broken` — run as functions in the Linter's `detectors.py` (alongside its data-hygiene checks: `stale-fleeting`, `stale-answer-drafts`, `frontmatter-schema-check`, `broken-wikilinks`, `graph-analyze`, `fama-exposure`). The other five (`profile-install-drift`, `vault-hash-drift`, `skeleton-drift`, `command-vocab-drift`, `plugin-config-drift`) are Linter **agent procedures** — they need git, SHA-256, or the audit log, so they are not `detectors.py` functions. So `detectors.py`'s **nine** checks and these eight *structural* checks are different sets that overlap in three.

## `profile-install-drift` — Profile install drift

You own drift detection between the source profile files in `.memoria/profiles/memoria-<name>/` (checked into the vault repo) and the deployed copies under `~/.hermes/profiles/memoria-<name>/` (written by `install.ps1`). Under direct profile management the source and the deployed copy are supposed to match exactly after every install run, modulo the `{{VAULT_PATH}}` substitution in `mcp.json` and the human-owned `.env` file.

Procedure:

1. For each of the seven profiles, list the files under both `.memoria/profiles/memoria-<name>/` (source, in the vault) and `~/.hermes/profiles/memoria-<name>/` (deployed).
2. For each file present in both, compute SHA-256. Exclude `.env` (user-owned, expected to differ). For `mcp.json`, substitute `{{VAULT_PATH}}` in the source copy with the vault's absolute path (forward-slash form) before hashing — this is what the installer does.
3. For each file present in only one side, report it: a source-only file means `install.ps1` hasn't been re-run since the file was added; a deploy-only file means the human added a file by hand that doesn't exist in the vault.
4. If any hash differs: report the affected profile, file, and which side has the unexpected content (vault source ahead of deploy, or hand-edited deploy).

This action is `report` only. Never re-run `install.ps1` automatically — a drift might indicate (a) the source changed and the human hasn't re-installed yet, or (b) the human hand-edited a deployed file. Both cases need human judgment about whether the change should be promoted into the vault source or reverted.

## `vault-hash-drift` — Vault hash drift

You own tamper detection for vault files. The policy MCP records SHA-256 `before_hash` and `after_hash` on every `allow` or `allow_with_log` write (see [policy.md](https://github.com/eranroseman/memoria-vault/blob/main/docs/reference/policy.md) in this repo's `docs/`). Your job is to verify that the file's current hash still matches the last `after_hash` for its path.

Procedure:

1. For each tracked path, scan `00-meta/02-logs/audit.jsonl` for the latest entry with that path and a non-null `after_hash`.
2. Compute the file's current SHA-256.
3. If the hashes differ: report the path, the recorded hash, the current hash, and the timestamp of the last logged write.
4. If the path has no audit entry but the file exists: report as "untracked file" — this means the file was created outside the policy MCP.

This action is `report` only. Never overwrite the file to "restore" its previous content automatically — drift might indicate (a) a human edit that should be promoted into a proper write through the MCP, (b) a non-MCP tool wrote to the vault (a configuration bug worth fixing), or (c) a tampering event. The human decides which.

## `skeleton-drift` — Skeleton drift

You own consistency between the design documents in this repo's `docs/` tree (architecture, workflows, references) and the vault-resident human notes in `00-meta/` (see [docs/explanation/vault.md](https://github.com/eranroseman/memoria-vault/blob/main/docs/explanation/vault.md)). The skeleton notes are plain-language companions to the design; when the design changes, the skeleton must follow.

Procedure:

1. For each skeleton note (`index.md`, `getting-started.md`, `system-map.md`, `agent-roles.md`, `profile-policies.md`, `system-status.md`, `schema-reference.md`, `dataview-cheatsheet.md`, `performance-checklist.md`), read its `updated_at` frontmatter.
2. For its corresponding `docs/` file(s), get the most recent commit timestamp from git log (same repo).
3. If any design file is newer than the skeleton's `updated_at`: report the skeleton as out of sync, listing the newer design file(s).

This action is `report` only. Never auto-update the skeleton — the wording is human-owned and the human note may need different framing than the design doc that triggered the drift. Treat skeleton drift the same way you'd treat code-doc drift: pay it down promptly, but only the human can write the updated prose.

## `dashboard-field-drift` — Dashboard field drift

You own validation of every Dataview query in `00-meta/01-dashboards/` against the schema the templates actually produce. This catches the silent-failure mode where a query references a field that doesn't exist — the query returns zero rows, the human sees an empty table, and nobody notices for weeks. Three real instances of this were caught during the design QA pass: `review_status` instead of `status`, `project` instead of `projects`, `enrichment_updated` instead of `enriched_date`.

Procedure:

1. For each `.md` file under `00-meta/01-dashboards/`, extract every Dataview block (` ```dataview ` and ` ```dataviewjs ` fenced blocks).
2. Parse each block's field references. Fields appear in these positions:
   - `TABLE field1, field2, ...` (column projections)
   - `WHERE <expr>` (filter expressions referencing fields)
   - `SORT field ASC/DESC` (sort fields)
   - `GROUP BY field` (group keys)
   - `FLATTEN field` (list expansion)
   - For `dataviewjs`: `e.field`, `e["field"]`, `dv.pages(...).where(p => p.field ...)` patterns
3. Skip built-in fields (`file.link`, `file.mtime`, `file.folder`, `file.name`, `file.inlinks`, `file.outlinks`, `file.path`, `file.content`, `file.tags`, etc.) and the universal `type`.
4. For each remaining field reference, check whether it appears in the frontmatter of *any* template under `00-meta/03-templates/` (or the human can configure a different template root for the linted vault).
5. If a field appears in no template: report the dashboard, the query block, the field name, and the line.
6. If the field name has a plausible close-match in templates (Levenshtein distance ≤ 2, e.g., `project` vs `projects`), include the suggestion in the report.

This action is `report` only. **Never auto-rewrite a query** — the right fix might be to add the field to a template, correct the query, or remove the dashboard section entirely. The human decides which.

The check should run as part of the regular lint sweep but can also be triggered on demand whenever a new template is added or a dashboard is created.

## `command-vocab-drift` — Command vocabulary drift

You own consistency between the command vocabulary as declared in three places: the workflows that *use* commands (`docs/how-to-guides/`), the per-profile and extended-command summaries that *catalog* them (`docs/explanation/profiles/README.md` lane matrix and `docs/reference/commands.md`), and the SOUL.md prompts that *declare* them (`.memoria/profiles/memoria-<profile>/SOUL.md` in the vault). The QA pass that motivated this check caught three real drifts in one sweep: `schema-migrate` and `graph-analyze` were in the summaries but missing from the Linter's SOUL.md; `similarity-check` was in the Extended command reference but missing from the per-profile table for the (then-existing) reviewer profile.

Procedure:

1. **Extract referenced commands.** From `docs/how-to-guides/` docs, pull every skill invocation (`/<skill>` slash-commands and `hermes -p memoria-<profile> chat -s <skill>` forms) and every backticked `<command>` in a workflow context. From `docs/explanation/profiles/README.md` (lane matrix) and `docs/reference/commands.md`, pull every backticked `<command>` in the Core commands column and the command catalog table. Each reference carries its declared owner profile.
2. **Extract declared commands.** From each `.memoria/profiles/memoria-<profile>/SOUL.md` in the vault, pull every backticked entry under the `## Core commands` section.
3. **Cross-reference both directions.**
   - For each *referenced* command: it must appear in the SOUL.md of its owner profile.
   - For each *declared* command in a SOUL.md: it should appear in at least one of the `docs/` profile command tables (`docs/explanation/profiles/README.md` lane matrix or `docs/reference/commands.md`), unless explicitly noted as private to that profile.
4. **Report each mismatch.** Include the command name, the source file, the owner profile, and which side is missing.

Heuristics for what counts as a "command":

- Anything invoked as a `/<skill>` slash-command (or loaded via `chat -s <skill>`) is a command.
- Anything in the Commands column of the Per-profile commands table is a command (split by commas).
- Anything in the first column of the Extended command reference table is a command.
- Anything as a bullet under `## Core commands` in a SOUL.md is a command.
- Backticked names with no surrounding context (e.g., in body prose) are *not* automatically commands — only entries in the structured locations above count, to avoid false positives from generic vocabulary like `\`status\`` or `\`type\``.

This action is `report` only. Never auto-add a command to a SOUL.md or any summary table — adding or removing a command from the system is a design decision that needs human judgment about purpose, primary profile, dry-run defaults, and lane policy implications.

## `plugin-config-drift` — Plugin-config drift

Under direct profile management the "shipped template" for each plugin's `data.json` lives at the same path the human's working file lives — `.obsidian/plugins/<plugin>/data.json` — distinguished only by git state. The shipped version is what's committed at git HEAD; the human's working version is what's currently on disk. Drift is the difference between the two. The [plugins reference](https://github.com/eranroseman/memoria-vault/blob/main/docs/reference/plugins.md#datajson-conventions) covers the rationale for each suffix; the per-plugin enforcement specifics are detailed below.

The detector handles three filename variants, plus one transition case. Suffix determines which procedure applies:

### Case A: Canonical config — `<plugin>/data.json` committed (no suffix)

Strict drift detection. The committed file is the contract.

1. For each `.obsidian/plugins/<plugin>/data.json` tracked at git HEAD, read the working-tree contents.
2. Read the same file as committed at HEAD (`git show HEAD:.obsidian/plugins/<plugin>/data.json`).
3. Diff the two JSON structures. For each key present in HEAD with a missing-or-different value in working, report it. Ignore human-extra keys present in working but not in HEAD (e.g., `agent-client`'s `savedSessions`, `lastUsedModels`, `lastUsedModes`) — these are plugin-generated runtime state that accumulates naturally.
4. If working `data.json` doesn't exist at all but HEAD has it: report as "missing working config" — the human deleted or never extracted the file from the clone.

### Case B: Templated config — `<plugin>/data.json.example` committed, working `<plugin>/data.json` exists

Partial drift detection. The `.example` is the shape; placeholders mark per-machine keys.

1. Read the committed `.example` from HEAD (`git show HEAD:.obsidian/plugins/<plugin>/data.json.example`).
2. Read the human's working `data.json` (gitignored sibling file).
3. Identify placeholder keys in the `.example`: any value matching `REPLACE_ON_FIRST_LAUNCH`, `{{HOME}}`, `{{...}}`, or other documented placeholder patterns. Also identify underscore-prefixed keys (`_comment`, `_*_note`) — these are documentation, not config.
4. For every non-placeholder, non-underscore key in `.example`: it must be present in working `data.json` with the same value. Drift here is a finding.
5. Human-extra keys in working that don't appear in `.example` are allowed (runtime state).

### Case C: First-time-setup pending — `.example` committed, working `data.json` missing

The human cloned the vault but hasn't copied `<plugin>/data.json.example` to `<plugin>/data.json` and filled in their machine-specific values yet. This is **not drift**, it's an incomplete setup.

1. If `<plugin>/data.json.example` is committed at HEAD and no `<plugin>/data.json` exists in the working tree: report as "first-time setup pending for plugin `<plugin>`".
2. Severity is **LOW** for this case (it's a setup gap, not a security or correctness failure). The remediation is "copy the example, fill in placeholders" — surfaced once, not repeatedly.
3. The dashboard query for active `plugin-config-drift` findings should de-prioritize "setup pending" entries against true drift entries so they don't crowd the human's attention.

### Case D: Unverified schema — `<plugin>/data.json.TODO` committed

A `.TODO` file documents intent without committing to a schema. Skip entirely. The detector ignores any file with a `.TODO` suffix in `.obsidian/plugins/<plugin>/`.

A future `.TODO` → real-template transition is human work: install the plugin, configure it through Obsidian's UI, copy the resulting `data.json` (or `data.json.example`) into the vault repo, commit, and delete the `.TODO`. At that point `plugin-config-drift` starts enforcing under Case A or Case B.

### Severity escalation

plugin-config-drift's default severity is **MEDIUM**. The exception: if Case A or Case B finds that `agent-client.autoAllowPermissions` has changed from `false` to `true`, the severity is **HIGH**. That setting bypasses the per-tool-call approval gate ACP relies on and composes with the policy MCP to keep human-in-the-loop — silently disabling it undermines a security invariant.

### Action

This action is `report` only. Never auto-update either side. The human chooses between: (a) committing the change (the drift is deliberate; HEAD advances), (b) reverting the working file (`git restore .obsidian/plugins/<plugin>/data.json`; the drift was unintentional), or (c) for Case C, completing first-time setup by copying the example. Auto-staging or auto-reverting would erase the human's choice without judgment.

## `orphan-working-files` — Orphan working files

You own detection of transient artifacts that leak out of the working zones into canonical territory. The patterns are deliberately conservative — a false positive should be rare and obviously a false positive.

Procedure:

1. Walk the vault tree, skipping `.obsidian/`, `.git/`, and any path under `10-inbox/`, `40-workbench/`, or `00-meta/02-logs/` (the permitted transient zones).
2. For each remaining file, check the basename against this pattern set:
   - `*.tmp.*` — common editor / sync conflict suffix (e.g., `notes.md.tmp.241125.1ddf7ac1a3d3`)
   - `*.OLD.*`, `*.lessOLD.*` — manual-rename leftovers
   - `*.bak` — generic backup
   - `*~` — Emacs / vi backup
   - `.#*` — Emacs lock file
   - `*.orig`, `*.rej` — merge / patch leftover
3. If a match is found: report the path, the matching pattern, and the file's mtime so the human can judge how stale it is.

This action is `report` only. Never auto-delete — the file may be the human's in-progress work that simply needs to be moved into a transient zone, or evidence of a sync conflict the human needs to reconcile. The remediation is always a per-file decision (keep, move, archive, delete) made by the human, not the Linter.

The patterns are deliberately narrow. Generic working files (`scratch.md`, `notes.md`) outside review-gated zones are *not* flagged — only files whose suffixes encode "this is a leftover" semantically. False-positive avoidance is more important than coverage here, because human trust in `orphan-working-files` erodes the first time it tells them a real file is junk.

## `extract-path-broken` — Extract path broken link

You own validation of paper-notes' `extract_path` frontmatter — the pointer from the curated note to the Marker-extracted markdown in `90-assets/extracts/<citekey>.md`. A broken `extract_path` is a silent-failure mode the human cannot otherwise detect: clicking the wikilink in the paper-note's "Resources" section returns nothing, but the field itself looks populated.

Procedure:

1. For each note under `20-sources/01-papers/` (and any other folder that produces paper-notes), read the `extract_path` frontmatter field.
2. Skip notes where `extract_path` is empty, missing, or null — those are pre-migration notes covered by the schema-version-mismatch check, not by `extract-path-broken`.
3. For each non-empty `extract_path`, resolve it against the vault root and check the file exists (`Test-Path` on Windows, `os.path.exists` on Unix).
4. If the file is missing: report the paper-note path, the broken `extract_path` value, the citekey (from frontmatter), and the paper-note's `created` or `enriched_date` timestamp (so the human can correlate with ingest runs).

This action is `report` only. Never auto-clear the field, never auto-trigger Marker re-extraction. The remediation is a per-note human decision with three usual paths:

- **Re-extract.** Run `hermes -p memoria-librarian run obsidian-paper-note --recover <citekey>` to rerun Marker against the Zotero PDF and rewrite the extract.
- **Clear the field.** If the extract is intentionally absent (e.g., a non-OA paper where the PDF couldn't be obtained), set `extract_path: ""` and let the schema-hygiene query surface it as a no-extract paper-note.
- **Investigate the citekey.** If Zotero's citekey was renamed but the paper-note's filename wasn't, the `extract_path` is stale by reference rather than by file. Human reconciles the names.

False-positive cases to handle: paths with forward slashes on Windows, leading `./` or trailing whitespace, paths starting with a vault-absolute prefix (e.g., `/90-assets/...`) that the resolver should normalize to vault-relative. Treat all of these as resolvable; only report when the *normalized* path doesn't exist.

### Extension candidate (not yet implemented): orphan extracts

The inverse of `extract-path-broken` — extract files in `90-assets/extracts/` that no paper-note's `extract_path` references — is a documented candidate for a future structural detector. Catches the case where a paper-note was deleted but its extract was not, or where an aborted ingest committed an extract before the paper-note got written. Not implemented yet because (a) the failure rate is low — extracts are atomic Marker outputs and paper-note deletions are rare, and (b) orphan-working-files's existing pattern-match catches most stale-file modes already. Revisit when a real orphan extract is hit in practice; until then, the rule lives here as a placeholder.

## Related

- [Linter SOUL.md](SOUL.md) — the full Linter profile contract, including the broader lint check table (data-hygiene checks alongside the M-detectors), the severity scale, and the verdict band rollup.
- [docs/reference/policy.md](https://github.com/eranroseman/memoria-vault/blob/main/docs/reference/policy.md) — the audit log that `vault-hash-drift` verifies against.
- [project-files/proposals/profile-compilation.md](https://github.com/eranroseman/memoria-vault/blob/main/project-files/proposals/profile-compilation.md) (**status: deferred**) — the compiler vision that `profile-install-drift` was originally designed against. Memoria currently uses direct profile management, so profile-install-drift's mechanism is install drift (source vs deployed) rather than build drift (source vs compiled).
