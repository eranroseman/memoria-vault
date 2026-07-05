---
created: 2026-06-02
updated: 2026-07-01
---

# Troubleshooting

The one help note kept in-vault for offline recovery. Full recipes live in the
[troubleshooting how-tos](https://eranroseman.github.io/memoria-vault/how-to-guides/troubleshooting/);
the complete failure catalog is [failure modes](https://eranroseman.github.io/memoria-vault/reference/failure-modes).

## Verify the Runtime

Run from a terminal:

| Check | Command | Healthy when |
| --- | --- | --- |
| CLI package | `.memoria/.venv/bin/memoria --help` | prints `memoria` help |
| Bundle | `.memoria/.venv/bin/memoria doctor bundle --workspace .` | reports `ok: true` or actionable failed checks |
| Search | `.memoria/.venv/bin/memoria workspace rebuild --workspace . --search` | rebuild completes and writes the search manifest |
| Integrity | `.memoria/.venv/bin/python -m memoria_vault.runtime.subsystems.integrity.linter.detectors --vault .` | final verdict is `PASS` or gives concrete findings |
| Git | `git status --short` | only expected local edits appear |

Alpha.15 does not require Hermes, Obsidian, Zotero, or installed profiles. If an
optional adapter is broken, keep working through the `memoria` CLI and repair the
adapter separately.

## Symptoms To Check First

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Command fails before running | venv missing or package not installed | `.memoria/.venv/bin/memoria --help` |
| New captures do not become checked | enrichment/full-text/provider data missing | `memoria request list` and `.memoria/config/providers.yaml` |
| Search returns stale results | search checked-only index needs rebuild | `memoria workspace rebuild --search` |
| Linter findings stale | scheduled task not running | run the same `memoria` command manually |
| Attention views look stale | projections or search need rebuild | `memoria workspace rebuild --search` |
| Wikilinks broken across many notes | File/folder renamed without updating refs | `git diff` to find the rename |

## Safe Mode

Use the CLI and Git directly:

```bash
.memoria/.venv/bin/memoria doctor bundle --workspace .
.memoria/.venv/bin/memoria request list --workspace .
git status --short
```

If provider-backed work is blocked, capture source metadata and full text as
unchecked work, commit the checkpoint, and rerun enrichment when provider inputs
are available.

## Recover

- [ ] Run `memoria doctor bundle`.
- [ ] Check `.memoria/` has `schemas/`, `config/`, `index/`, `staging/`, and `state/`.
- [ ] Check `system/logs/` for recent error entries.
- [ ] Run `git status --short`.
- [ ] Rebuild search with `memoria workspace rebuild --search`.

Last resort: create a fresh workspace with the bootstrap installer and copy only
user-authored content across intentionally. Alpha.15 has no profile-only
redeploy mode.
