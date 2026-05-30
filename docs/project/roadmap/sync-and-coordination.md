---
topic: roadmap
---

# Sync and write coordination

Under multi-machine [deployment options](deployment-options.md), agent writes and human writes need coordination. This file covers the three coordination mechanisms: the sync window mental model, the `.agent-lock` file, and the bib watcher (the always-on option only). It also covers syncing profile memory across machines via the [`memories/` junction](#syncing-profile-memory-across-machines-the-memories-junction).

## Sync window: the 5–15 second mental model

When the agent runs on a VPS and the human is reading the same vault locally in Obsidian, writes propagate through Syncthing in roughly 5–15 seconds: ~1–2s for filesystem watcher detection, ~2–8s for network transfer, ~1–3s for Obsidian to reload. The full chain:

```text
Hermes writes file (VPS)
  → Syncthing detects change:   ~1–2s
  → Network transfer to desktop: ~2–8s
  → Obsidian detects new file:  ~1–3s
─────────────────────────────────────
Total:                          ~5–15s typical
```

What this means operationally:

| Scenario | What you see | How to handle |
| --- | --- | --- |
| Both sides idle for >30 seconds | Both nodes converged; identical view. | Normal case for chat-style queries. |
| You just edited a note in Obsidian | Hermes won't see it for 5–15s. | Wait a moment before asking Hermes about it. |
| Hermes just finished a batch | New files appear in Obsidian over 10–40s. | Visually obvious; watch the file explorer. |
| Hermes is mid-batch ingest | Mixed state — some files updated, some not. | Don't chat during active ingest; it confuses the conversation. |

Syncthing uses atomic file replacement on delivery, so Obsidian never reads a half-written file. The 5–15 second window is *clean lag*, not torn-write lag. The system doesn't need explicit coordination rituals for normal use.

## Agent write coordination (`.agent-lock`)

Under [the always-on option](deployment-options.md), the race between agent and human writes is **frequent, not rare** — the VPS is always-on and runs cron tasks, discovery loops, scheduled enrichment, and the bib watcher continuously. The human on the desktop or laptop reads (and occasionally writes) the same vault while the VPS is mid-batch. Syncthing produces a recoverable conflict copy rather than silently overwriting, but conflicts compound over weeks. **`.agent-lock` is required discipline under `always-on`, not an optional habit.**

Under [the local-mesh option](deployment-options.md), the race is rare-but-real — the primary desktop only writes when the human is actively using it, and the desktop typically has long idle periods. `.agent-lock` is still recommended but the failure mode is much less frequent.

The mechanism: a `00-meta/.agent-lock` file. Hermes creates it before starting a batch write and removes it when finished. The human's Obsidian-side workflow (a Templater script, a [`board-state` dashboard](../../explanation/dashboards/board-state.md) glance, or a manual habit) checks for the file before triggering its own writes.

```text
00-meta/
└── .agent-lock          # presence means "agent is mid-batch; defer your writes"
```

The required care tightens with deployment option:

| Pattern | When to check `.agent-lock` | Why |
| --- | --- | --- |
| **`local-only`** (single machine) | Never — only one machine writes | No race possible |
| **`local-mesh`** (desktop + laptop) | Before editing hot zones (`10-inbox/`, `40-workbench/<active>/`) on the laptop while the desktop is on | Race exists but only when both machines are active |
| **`obsidian-sync`** | Same as `local-mesh` if you have a VPS for cron; otherwise no | Depends on whether anything else is writing concurrently |
| **`always-on`** (VPS + desktops + laptops) | Before any edit in zones the VPS is actively touching — `10-inbox/`, project-scratch for active projects, the current verify-cycle draft | VPS writes continuously; assume an edit collision is the default state unless you've checked |

Not airtight — a determined Writer can ignore the lock — but adequate for a single-user workflow where the human's main risk is *forgetting* the agent is running, not *deliberately* colliding with it. Under `always-on` specifically, the human should treat checking the lock the same way they treat checking the dispatcher status before any edit in active zones.

## Bib watcher (always-on only)

When Zotero runs on the desktop and Hermes runs on the VPS, the VPS needs a current `library.bib` to ingest sources. Better BibTeX auto-exports the bib to `.memoria/library.bib` on every Zotero change; Syncthing delivers the file to the VPS within the standard sync window.

If Syncthing isn't between Zotero and the VPS (e.g., the local-only option migrating to a VPS without adopting Syncthing), use a small file watcher on the desktop that commits the bib to Git on change:

```bash
# .memoria/watch-and-push-bib.sh
#!/usr/bin/env bash
set -euo pipefail
inotifywait -m -e modify "$VAULT/.memoria/library.bib" |
while read; do
  cd "$VAULT"
  git add .memoria/library.bib
  git commit -m "bib: auto-export" || true
  git push
done
```

The VPS pulls before every ingest. This is the lowest-cost way to get a fresh bib to the VPS without committing to Syncthing — useful as a bridge between the local-only option and the always-on option.

## Syncing profile memory across machines (the `memories/` junction)

By default, [profile memory](../../explanation/architecture/memory-tiers.md#the-substrates) (`MEMORY.md` + `USER.md`) is per-machine local runtime state — `install.ps1` rebuilds the profile directory on each device and the learned notes start empty. Under [the local-only or local-mesh options](deployment-options.md) with **non-concurrent** use (one machine at a time), you usually want those learned notes to follow you between machines. They are the one piece of `~/.hermes/` worth promoting into the git-synced vault: small (~800 + ~500 tokens), plain-markdown, and merge-friendly — unlike the session database (`state.db`, binary) or `.env` ([never synced](deployment-options.md)).

**Mechanism.** The real files live *in the vault* at `.memoria/profile-memory/memoria-<name>/`; a directory junction makes Hermes read and write them through its normal `memories/` path. Git tracks the vault copy, so the existing vault sync carries learned memory between machines with no extra channel.

```text
.memoria/profile-memory/memoria-<name>/        # git-tracked, lives in the vault
        ▲ junction
~/.hermes/profiles/memoria-<name>/memories/    # where Hermes reads and writes
```

**Setup (`link-memory.ps1` at the vault root — run once per machine, and again after every `install.ps1`).** (not yet authored; create manually or wait for the v0.2 install script — see implementation-status.md) Directory junctions need no admin on Windows and are transparent to Hermes:

```powershell
$Vault    = $PSScriptRoot                              # vault root (the git repo)
$Profiles = "$env:USERPROFILE\.hermes\profiles"
$Store    = Join-Path $Vault ".memoria\profile-memory"
$names = 'memoria-librarian','memoria-mapper','memoria-socratic',
         'memoria-writer','memoria-verifier','memoria-coder','memoria-linter'

foreach ($n in $names) {
    $live = Join-Path $Profiles "$n\memories"          # Hermes's path
    $dest = Join-Path $Store $n                         # git-tracked home in the vault
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    # First run only: migrate any existing notes into the vault store
    if ((Test-Path $live) -and -not ((Get-Item $live).LinkType)) {
        Copy-Item "$live\*" $dest -Recurse -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path $live) { Remove-Item $live -Recurse -Force }
    New-Item -ItemType Junction -Path $live -Target $dest | Out-Null
}
```

**Why re-run after `install.ps1`.** `hermes profile install --force` recreates `~/.hermes/profiles/memoria-<name>/` from vault source on every run (see [on-disk-layout.md](../../explanation/architecture/on-disk-layout.md#version-control)), replacing the junction with an empty real folder. The data is safe — it lives in the vault — so re-running `link-memory.ps1` restores the link. That robustness is the point: the vault, not `~/.hermes/`, is the source of truth for learned memory. The cleanest wiring is to call `link-memory.ps1` as a final step of `install.ps1`.

**Daily flow.** Nothing beyond the vault handoff you already do: `git pull` when you sit down, `git commit && git push` when you leave. The memory files *are* vault files now.

**What this carries — and what it deliberately doesn't.**

| Carried | Not carried |
| --- | --- |
| `MEMORY.md`, `USER.md` — learned conventions and the user profile | `state.db` session search (binary SQLite — corrupts under raw file-sync and conflicts on merge; use `hermes profile export`/`import` if you need chat-history recall to travel) |
| | `.env` / `auth.json` — per-machine secrets, [never synced](deployment-options.md) |
| | The compiled profile (`SOUL.md`, `config.yaml`, `skills/`) — rebuilt per machine by `install.ps1` |

**Concurrency note.** Under non-concurrent use there is no contention. Under [the always-on option](deployment-options.md) (or local-mesh with both machines active), two devices writing learned notes can produce a git merge conflict on `MEMORY.md` — recoverable because it is plain text, but a reason this pattern is aimed at the non-concurrent case. For real-time cross-machine memory under genuine concurrency, a cloud [Hermes memory provider](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers) is the better tool — see [Hermes memory server](future-directions.md#hermes-memory-server-shared-memory-provider) on the roadmap. Carrying `state.db` chat history (which the junction omits) between machines is the [scripted session-history sync](future-directions.md#scripted-session-history-sync) roadmap item.
