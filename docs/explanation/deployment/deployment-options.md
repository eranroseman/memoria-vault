---
title: Deployment options
parent: Deployment
nav_order: 3
---

# Deployment options

The system spans a **vault** (knowledge layer) and an **execution layer** (Hermes profiles, MCPs). Where each lives — and how they sync — is a human decision with real trade-offs. The supported install path is **`local-only`**. The multi-machine topologies (`local-mesh`, `obsidian-sync`, `always-on`) and the secondary-device operating patterns are a forward-looking capability, specified in [multi-machine deployment](../../adr/63-multi-machine-deployment.md).

| Pattern | Sync mechanism | Always-on agent | Zotero API access | Ongoing cost | When to use |
| --- | --- | --- | --- | --- | --- |
| **`local-only`** (default) | Git (manual pull / push) | ❌ Workstation must be on | ✅ Full localhost:23119 | $0 infra | Simplest start; single workstation; no discovery loop |
| `local-mesh` | Syncthing peer-to-peer (no VPS) | ⚠️ Primary device when on | ✅ Full localhost on primary | $0 infra | Desktop + laptop; auto-sync without cloud or VPS — see the [multi-machine proposal](../../adr/63-multi-machine-deployment.md) |
| `obsidian-sync` | Obsidian's cloud sync | ⚠️ Needs VPS for cron | ⚠️ `.bib` only on VPS | ~$10/mo | iOS access; small team — see the [multi-machine proposal](../../adr/63-multi-machine-deployment.md) |
| `always-on` | Syncthing + VPS (P2P, peer = full filesystem) | ✅ VPS runs as a Syncthing peer | ⚠️ `.bib` only on VPS | ~$12–25/mo VPS | Multi-device with always-on agent — see the [multi-machine proposal](../../adr/63-multi-machine-deployment.md) |

**Start with `local-only`.** It is the adopted posture: a single workstation, Git for history, Zotero on localhost. Adding Syncthing or a VPS later is additive — it doesn't require restructuring the vault — so deferring the multi-machine patterns costs nothing. When a second device or unattended automation enters the picture, see the [multi-machine deployment proposal](../../adr/63-multi-machine-deployment.md).

## Common decisions across options

These conventions are adopted design; they hold regardless of which pattern you run, and they are what make the multi-machine patterns safe when you do adopt them. The rationale is the point here; for the exact paths, env-var names, and what the installer writes where, see [Installer (bootstrap)](../../reference/installer.md).

- **Git is the version history layer, not the sync layer.** Every pattern uses Git for reversibility. Sync is a separate concern.
- **`memoria.bib` lives inside the vault** at `.memoria/memoria.bib`, exported by Better BibTeX. This makes the bib a first-class artifact that travels with the vault under whichever sync mechanism you choose.
- **Cheap-task routing is configured in Hermes, not in the deployment.** See the model-routing pattern (synthesis to Claude, embed / classify / quick-summary to cheaper models via OpenRouter or similar).
- **Per-session log files, not a single `log.md`.** The Linter's per-session digests write one file per session to `system/logs/sessions/` ([ADR-25](../../adr/25-session-logging-two-logs.md)). With one append-only file, distributed writes from VPS and desktop produce sync conflicts; one-file-per-session has nothing to conflict on. *(The audit log `audit.jsonl` is a single append-only file, so cross-machine sync of the audit log waits on the multi-machine patterns below.)*
- **Hermes data dir is `~/.hermes/` by default** (or `%USERPROFILE%\.hermes\` on Windows). Override with `HERMES_HOME=/path/to/dir` when you need isolation — most commonly under multi-machine patterns, where a secondary device's Hermes should keep its own profiles, sessions, and audit log isolated from the primary's `~/.hermes/`.
- **One Hermes dispatcher per vault.** Under any multi-machine pattern, multiple machines have the vault but only *one* should run Hermes as a dispatcher (cron + `hermes gateway` + card claiming). The task registry lives in `~/.hermes/` per machine; two active dispatchers against the same synced vault race on card writes and produce conflicting audit logs. The convention: the *[primary device](../../reference/glossary.md#system)* owns dispatch; secondary devices run vault-only or in restricted modes — see the secondary-device patterns in the [multi-machine proposal](../../adr/63-multi-machine-deployment.md).
- **Profile aliases are first-class.** The installer's profile-install step registers each profile under a `memoria-<name>` alias, so `memoria-librarian chat` is a shortcut for `hermes -p memoria-librarian chat` — what the workflows in [Workflows](../workflows/README.md) assume. The exact command and seed semantics are owned by [Installer (bootstrap)](../../reference/installer.md).
- **`.env` is per-machine, never committed.** Each profile ships a `.env.EXAMPLE` listing required and optional env vars with descriptions. The installer copies it to `.env` on first install if `.env` doesn't already exist; the human fills in keys. Hermes hard-excludes `.env` and `auth.json` from `hermes profile install` / `update` so credentials never travel between machines.
- **Agent memory can ride the vault.** Because the Co-PI is the sole memory carrier ([The Co-PI](../profiles/co-pi.md)), its `MEMORY.md` / `USER.md` (`~/.hermes/profiles/memoria-copi/memories/`) are the only agent memory to share. Per-machine by default, but the [`memories/` junction](../../adr/60-cross-vault-knowledge-sharing.md) promotes them into the git-synced vault so the Co-PI's learned notes follow you across machines — the automatic, no-extra-channel way to share agent memory under non-concurrent local-only / local-mesh use. Session history (`state.db`) and secrets (`.env`) deliberately stay per-machine.

## Related

- **Multi-machine deployment** (the deferred topologies and secondary-device patterns): [Multi-machine deployment (topologies and secondary-device patterns)](../../adr/63-multi-machine-deployment.md).
- **Setup steps:** [Setup how-to guides](../../how-to-guides/setup).
- **What gets installed where:** [Installer (bootstrap)](../../reference/installer.md).
