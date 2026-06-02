---
created: 2026-06-02
updated: 2026-06-02
---

# Troubleshooting

The one help note kept in-vault — for when you're offline or something's broken. Verify the system is up, fall back to manual workflows, recover. Full Detect/Fix/Verify recipes: [failure modes](https://eranroseman.github.io/memoria-vault/reference/failure-modes/).

## Verify the plumbing

Quick checks that the system itself is up (run from a terminal):

| Check | Command | Healthy when |
| --- | --- | --- |
| Hermes + profiles | `hermes profile list` | all 7 `memoria-*` profiles respond |
| Gateway / API | `hermes gateway status` | running on `:8642` |
| Policy + obsidian MCP | trigger a write, watch `00-meta/02-logs/audit.jsonl` | new `allow_with_log` rows appear |
| Cron scheduler | [[daily-health]] § Cron status | the four standard tasks show recent runs |
| Zotero local API | open a citekey link / re-ingest | resolves (port 23119) |

Profiles: `memoria-{librarian, mapper, socratic, writer, verifier, coder, linter}`.

## Symptoms → diagnosis

| Symptom | Likely cause | First check |
| --- | --- | --- |
| ACP pane doesn't open or shows error | Hermes process not reachable | `hermes profile list` from terminal |
| Cards don't move forward | Hermes not processing the board | `hermes profile list`; check [[board-state]] |
| New captures don't appear in inbox | Watcher / QuickAdd not firing | Check QuickAdd config in Obsidian Settings |
| Linter findings stale | Cron not running | Cron status in [[daily-health|Daily Health]] |
| Dashboards show errors | Dataview not loaded | Reload plugins in Obsidian Settings |
| Wikilinks broken across many notes | File/folder renamed without updating refs | `git diff` to find the rename |

## Working in safe mode

**Ingest (Librarian down):** Quick-Copy BibTeX from Zotero → create `20-sources/01-papers/<citekey>.md` from the [[paper-note|paper-note template]] with `citekey`, `title`, `lifecycle: proposed`. Librarian enriches it when back up.

**Review (policy MCP down):** the runtime gate is bypassed — **treat every write as if it could land somewhere it shouldn't.** Edit carefully, `git commit` often; replay the audit log when the MCP returns.

**Export (Verifier/Writer down):** verify citekeys resolve manually, then run Pandoc directly — skip cite-check / similarity-check, rely on human review:

```bash
pandoc draft.md --bibliography .memoria/memoria.bib --csl .memoria/csl/apa.csl -o output.docx
```

## Recover

- [ ] Restart Obsidian
- [ ] Restart Hermes (`hermes profile list` should respond)
- [ ] Restart the policy MCP (`policy_mcp.py`)
- [ ] Check `.memoria/` is intact (`profiles/`, `mcp/`, `lane-overrides/`)
- [ ] Check `00-meta/02-logs/` for recent error entries
- [ ] `git status` — has anything unexpectedly changed?

**Last resort — re-install** (idempotent; rewrites author-owned files, preserves your `.env` secrets):

```bash
cd <vault-root>
git stash          # save in-flight changes
./scripts/install.ps1
git stash pop
```

Still broken? → [failure modes](https://eranroseman.github.io/memoria-vault/reference/failure-modes/) (Detect / Fix / Verify per mode).
