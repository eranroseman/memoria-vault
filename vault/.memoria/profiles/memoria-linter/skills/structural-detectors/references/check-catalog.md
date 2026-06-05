# Check catalog

Every check the Linter runs, with thresholds. Each is a **report** by default; auto-fix is
gated by the auto-fix class policy in `SOUL.md`. Severity levels (CRITICAL/HIGH/MEDIUM/LOW/INFO)
and the verdict-band rollup are defined in `SOUL.md`.

## Which substrate runs each check

- **Engine** — a function in `scripts/detectors.py` (pure-stdlib, zero-LLM, needs only the
  vault tree). Run by every sweep: `orphan-working-files`, `stale-fleeting`,
  `stale-answer-drafts`, `extract-path-broken`, `frontmatter-schema-check`, `broken-wikilinks`,
  `dashboard-field-drift`, `graph-analyze` (orphan-synthesis-note detection), `fama-exposure`.
- **Agent procedure** — needs `git`, SHA-256, or the audit log, so it can't live in the script.
  Run on the full (weekly) sweep only: `profile-install-drift`, `vault-hash-drift`,
  `skeleton-drift`, `command-vocab-drift`, `plugin-config-drift`. Full procedures are in
  `structural-detectors.md`.
- **Dashboard signal** — surfaced passively by a Dataview query under `00-meta/01-dashboards/`,
  not executed by the Linter. The rows below marked "surface in … dashboard" are these; the
  Linter reports them only when a sweep is explicitly asked to.

## Threshold table

| Check | Threshold | Action |
| --- | --- | --- |
| Orphan claim / reference notes | `length(file.inlinks) = 0` and `type != "moc"` | Report — surface in weekly dashboard. |
| Stale enrichment (literature) | `enriched_date` older than the per-type threshold in [Enrichment staleness by type](#enrichment-staleness-by-type) (Article 180d; Preprint / Repository / Package 30d; Person 90d; Organization 365d) | Report — flag for `enrich` re-run. |
| Classification debt per project | > 30% of notes with `lifecycle: proposed` | Report — surface in weekly dashboard. |
| Broken wikilinks | Any `[[name]]` that doesn't resolve | Report. Auto-fix only if explicitly authorized for a scoped folder. |
| FAMA exposure (obsolete-memory reuse) | A downstream note (`draft` / `answer-note` / `reference-note` / …) wikilinks a claim that is `lifecycle: archived` or carries `superseded_by` | Report the citing note + the superseded claim; the human re-points or drops the citation. Never auto-edit. The `fama_exposure` function in `detectors.py`; claim supersession (ADR-10) makes it measurable — a publication-grade signal. |
| Author entity gaps | A paper note's author exists but has no `person-note` note | Report — proposal to create. |
| `pub_status` anomalies | Zotero retraction alert disagrees with vault `pub_status` | Report — never silently update. |
| Scite contrast | `> 15%` contrasting citations on a paper | Report — surface for human attention. |
| Schema version mismatch | `schema_version` differs from current schema | Report — propose `schema-migrate --dry-run`. |
| Promote-to-reference queue | `maturity: evergreen` notes still in `30-synthesis/01-claims/` | Report — surface in promotion backlog. |
| MOC threshold crossed | A `topic` has ≥ 15 notes (papers + claim notes combined) and no `moc` covering it | Report — surface "consider a MOC for topic X" in the weekly dashboard. **Report-only (Tier 1)**; never auto-create or draft a MOC (curation is human-owned). |
| Stale inbox | `answer-note` with `lifecycle: proposed` older than 7 days | Report — surface in weekly dashboard. |
| Answer-draft retention | `answer-note` in `10-inbox/02-answers/` older than 90 days (mtime) — the `stale-answer-drafts` detector | Report — flag for keep / promote / discard; **never auto-archive**. Surface in weekly dashboard. |
| Stale items | Item note's `last_checked` older than 90 days | Report. |
| Stale literature | Paper note with `file.mtime` older than 180 days and `lifecycle: current` | Report. |
| Profile install drift | A deployed `~/.hermes/profiles/memoria-<name>/` file (SOUL.md, config.yaml, mcp.json, anything under skills/ or cron/) has a different SHA-256 than its source at `.memoria/profiles/memoria-<name>/` (mcp.json compared after `{{VAULT_PATH}}` substitution) | Report — surface the affected profile and file; the human must either re-run `scripts/install.ps1` to refresh the deployed copy or revert the hand-edit. Never auto-install. |
| Vault hash drift | A vault file's current SHA-256 doesn't match the last `after_hash` recorded for that path in `audit.jsonl` | Report — file was modified outside the policy MCP. Surface in the audit-log dashboard. |
| Skeleton note drift | A vault-skeleton human note in `00-meta/` (e.g., `agent-roles.md`, `profile-policies.md`) has `updated` older than the corresponding file's last commit in this repo's `docs/` | Report — surface as a "skeleton out of sync" item. Never auto-update; the human note's wording is human-owned. |
| Dashboard field drift | A field referenced in a Dataview query under `00-meta/01-dashboards/` does not appear in any template's frontmatter | Report — surface the dashboard, the query, and the missing field. The query is silently broken (returns zero rows in a real vault) until either the field is added to the relevant template or the query is corrected. Never auto-rewrite the query. |
| Command vocabulary drift | A command name in `docs/how-to-guides/` or `docs/reference/obsidian-command-palette.md` does not appear in the Core commands section of its owner profile's `.memoria/profiles/memoria-<profile>/SOUL.md` (or vice versa) | Report — surface the command name, the source file, and the owner-profile's SOUL.md. Never auto-add commands to SOUL.md files; command surface changes are a design decision. |
| Plugin-config drift | The human's working `.obsidian/plugins/<plugin>/data.json` differs from the version committed at git HEAD for the same path. Human-extra keys (e.g., `agent-client`'s `savedSessions`) are ignored. Variant files with `.example` or `.TODO` suffixes (e.g., `data.json.example`, `data.json.TODO`) follow modified rules — see the `data.json` conventions in `docs/reference/obsidian-plugins.md`. | Report — surface the plugin, the key, and the expected vs actual value. Never auto-update either side; either the human's choice is deliberate (commit the change) or it's drift (revert the working file to git HEAD). |
| Orphan working files | A file matches a transient-artifact pattern (`*.tmp.*`, `*.OLD.*`, `*.bak`, `*.lessOLD.*`, `*~`, `.#*`) and resides outside the permitted transient zones (`10-inbox/`, `40-workbench/`, `99-system/logs/`). Most often: an editor backup or a half-renamed scratch file that the human left behind after a manual rename. | Report — surface the path and the matching pattern. Never auto-delete; the file may be the human's in-progress work. |
| Extract path broken link | A paper-note's `extract_path` frontmatter field is set (non-empty) but the referenced file does not exist on disk. The path was populated during ingest but the extract is missing — either Marker silently failed, an aborted ingest left orphaned state, the human renamed a citekey without renaming the extract, or the extract was deleted. | Report — surface the paper-note path, the broken `extract_path` value, and the citekey. Severity HIGH (silent-failure mode). Never auto-rewrite the field; the human decides whether to re-run Marker, clear the field, or remove the paper-note. |

The eight checks at the bottom (`profile-install-drift` through `extract-path-broken`) are the
**structural detectors** — deterministic, zero-LLM, catching silent-failure modes that look
like "nothing to do" while something is wrong. Three (`dashboard-field-drift`,
`orphan-working-files`, `extract-path-broken`) run in the engine; the other five are agent
procedures (`structural-detectors.md`).

## Enrichment staleness by type

Different note types decay at different rates. Use these cadences for re-enrichment scheduling:

| Type | Re-enrichment cadence | What changes |
| --- | --- | --- |
| Article | 180 days | Citation count, related papers |
| Preprint | 30 days | May have been published; check for journal version |
| Person | 90 days | New papers, affiliation changes |
| Organization | 365 days | Rarely changes |
| Repository | 30 days | Stars, issues, releases, maintenance status |
| Package | 30 days | New versions, deprecation |

Surface stale notes in the weekly dashboard. The agent never re-enriches without a trigger —
either scheduled or explicitly invoked.
