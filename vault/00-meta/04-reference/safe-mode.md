# Safe mode

The three core workflows (ingest, review, export) with minimal commands and fallbacks when something is broken. Open this when Hermes, the ACP connection, or the watcher is down.

## Symptoms → diagnosis

| Symptom | Likely cause | First check |
| --- | --- | --- |
| ACP pane doesn't open or shows error | Hermes process not reachable | `hermes profile list` from terminal |
| Cards don't move forward | Tasks MCP not running | Check `policy_mcp.py` and `tasks_mcp.py` processes |
| New captures don't appear in inbox | Watcher / QuickAdd not firing | Check QuickAdd config in Obsidian Settings |
| Linter findings stale | Cron not running | Check cron status in [[../01-dashboards/index|Daily Health dashboard]] |
| Dashboards show errors | Dataview not loaded | Reload plugins in Obsidian Settings |
| Wikilinks broken across many notes | File or folder was renamed without updating refs | `git diff` to find the rename |

## Three workflows in safe mode

### Ingest (when Librarian is down)

1. In Zotero, export the paper to BibTeX (Better BibTeX → Quick Copy)
2. Manually create a paper-note at `20-sources/01-papers/<citekey>.md` from the [[../03-templates/paper-note|paper-note template]]
3. Fill in `citekey`, `title`, `lifecycle: proposed`
4. When Librarian is back up, it picks up the partial note for enrichment

### Review (when policy MCP is down)

1. The runtime gate is bypassed. **Treat every write as if it could land somewhere it shouldn't.**
2. Make changes carefully; commit frequently with `git commit`
3. When the MCP is back, replay the audit log to verify no out-of-policy writes happened

### Export (when Verifier or Writer is down)

1. Verify citations manually — every citekey in the draft must resolve to a `20-sources/01-papers/` file
2. Run Pandoc directly:
   ```bash
   pandoc draft.md \
     --bibliography .memoria/library.bib \
     --csl .memoria/csl/apa.csl \
     -o output.docx
   ```
3. Skip cite-check, similarity-check; rely on human review only

## Recovery checklist

- [ ] Restart Obsidian
- [ ] Restart Hermes (`hermes profile list` should respond)
- [ ] Restart MCP servers (`policy_mcp.py`, `tasks_mcp.py`)
- [ ] Check `.memoria/` is intact (`profiles/`, `mcp/`, `lane-overrides/`)
- [ ] Check `00-meta/02-logs/` for recent error entries
- [ ] `git status` — has anything unexpectedly changed?
- [ ] If still broken: see [Failure modes](https://eranroseman.github.io/memoria-vault/reference/failure-modes/)

## Last-resort: re-install

```bash
cd <vault-root>
git stash                  # save any in-flight uncommitted changes
./scripts/install.ps1              # re-run the installer
git stash pop              # restore
```

The installer is idempotent and always-overwrite — it rewrites author-owned files from the vault source, preserves human-owned `.env` secrets.

---

**For depth:** [Failure modes](https://eranroseman.github.io/memoria-vault/reference/failure-modes/) — Detect / Fix / Verify recipes for every documented failure mode.
