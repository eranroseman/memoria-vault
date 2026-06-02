---
created: 2026-06-02
updated: 2026-06-02
---

# Troubleshooting

The one help note kept in-vault — for when you're offline or something's broken. Verify the system is up, fall back to manual workflows, recover. Step-by-step recipes for the common failures: [recovery how-tos](https://eranroseman.github.io/memoria-vault/how-to-guides/recovery/). The full catalog of every known failure (symptom · severity · cause · fix): [failure modes](https://eranroseman.github.io/memoria-vault/reference/failure-modes/).

## Verify the plumbing

Quick checks that the system itself is up (run from a terminal):

| Check | Command | Healthy when |
| --- | --- | --- |
| Hermes + profiles | `hermes profile list` | all 7 `memoria-*` profiles respond |
| Gateway / API | `hermes gateway status` | running on `:8642` |
| Policy + obsidian MCP | trigger a write, watch `99-system/logs/audit.jsonl` | new `allow_with_log` rows appear |
| Cron scheduler | [[daily-health|Daily Health]] § Cron status | the four standard tasks show recent runs |
| Zotero local API | open a citekey link / re-ingest | resolves (port 23119) |

Profiles: `memoria-{librarian, mapper, socratic, writer, verifier, coder, linter}`.

Command details: [Hermes CLI reference](https://eranroseman.github.io/memoria-vault/reference/hermes-cli/). After a reboot or a break, run the fuller [return-to-work checklist](https://eranroseman.github.io/memoria-vault/how-to-guides/maintenance/return-to-work/).

## Symptoms → diagnosis

A quick lookup; the complete catalog (symptom · severity · cause · fix) is [failure modes](https://eranroseman.github.io/memoria-vault/reference/failure-modes/).

| Symptom | Likely cause | First check |
| --- | --- | --- |
| ACP pane doesn't open or shows error | Hermes process not reachable | `hermes profile list` from terminal |
| Cards don't move forward | Hermes not processing the board | `hermes profile list`; check [[board-state|Board State]] |
| New captures don't appear in inbox | Watcher / QuickAdd not firing | Check QuickAdd config in Obsidian Settings |
| Linter findings stale | Cron not running | Cron status in [[daily-health\|Daily Health]] |
| Dashboards show errors | Dataview not loaded | Reload plugins in Obsidian Settings |
| Wikilinks broken across many notes | File/folder renamed without updating refs | `git diff` to find the rename |

Step-by-step recipes for the common ones: [stuck card](https://eranroseman.github.io/memoria-vault/how-to-guides/recovery/fix-stuck-card/) · [broken frontmatter](https://eranroseman.github.io/memoria-vault/how-to-guides/recovery/fix-broken-frontmatter/) · [profile drift](https://eranroseman.github.io/memoria-vault/how-to-guides/recovery/fix-profile-drift/) · [stale `.bib`](https://eranroseman.github.io/memoria-vault/how-to-guides/recovery/fix-stale-bib/) · [denied write](https://eranroseman.github.io/memoria-vault/how-to-guides/recovery/diagnose-a-denied-write/).

## Working in safe mode

The full walkthrough is the [safe-mode how-to](https://eranroseman.github.io/memoria-vault/how-to-guides/recovery/safe-mode/); the essentials:

**Ingest (Librarian down):** Quick-Copy BibTeX from Zotero → create `20-sources/01-papers/<citekey>.md` from the [[paper-note|paper-note template]] with `citekey`, `title`, `lifecycle: proposed`. Librarian enriches it when back up. (Normal path: [capture & ingest](https://eranroseman.github.io/memoria-vault/how-to-guides/sources/capture-and-ingest/).)

**Review ([policy MCP](https://eranroseman.github.io/memoria-vault/reference/policy-mcp/) down):** the runtime gate is bypassed — **treat every write as if it could land somewhere it shouldn't.** Edit carefully, `git commit` often; replay the audit log when the MCP returns.

**Export (Verifier/Writer down):** verify citekeys resolve manually, then run Pandoc directly — skip cite-check / similarity-check, rely on human review (Pandoc/CSL details: [export reference](https://eranroseman.github.io/memoria-vault/reference/export/)):

```bash
pandoc draft.md --bibliography .memoria/memoria.bib --csl .memoria/csl/apa.csl -o output.docx
```

## Recover

- [ ] Restart Obsidian
- [ ] Restart Hermes (`hermes profile list` should respond)
- [ ] Restart the policy MCP (`policy_mcp.py`)
- [ ] Check `.memoria/` is intact (`profiles/`, `mcp/`, `lane-overrides/`)
- [ ] Check `99-system/logs/` for recent error entries
- [ ] `git status` — has anything unexpectedly changed?

**Last resort — [re-install](https://eranroseman.github.io/memoria-vault/reference/installer/)** (idempotent; rewrites author-owned files, preserves your `.env` secrets):

```bash
cd <vault-root>
git stash          # save in-flight changes
./scripts/install.ps1
git stash pop
```

Still broken? → the [recovery how-tos](https://eranroseman.github.io/memoria-vault/how-to-guides/recovery/) (Detect / Fix / Verify per failure), or the full [failure-modes catalog](https://eranroseman.github.io/memoria-vault/reference/failure-modes/).
