# Deployment options

The system spans a vault (knowledge layer) and an execution layer (Hermes profiles, MCPs). Where each lives — and how they sync — is a human decision with real tradeoffs. Four deployment patterns, ordered by setup complexity.

| Pattern | Sync mechanism | Always-on agent | Zotero API access | Ongoing cost | When to use |
| --- | --- | --- | --- | --- | --- |
| **`local-only`** | Git (manual pull / push) | ❌ Workstation must be on | ✅ Full localhost:23119 | $0 infra | Simplest start; single workstation; no discovery loop |
| **`local-mesh`** | Syncthing peer-to-peer (no VPS) | ⚠️ Primary device when on | ✅ Full localhost on primary | $0 infra | Desktop + laptop; want auto-sync without cloud subscription or VPS |
| **`obsidian-sync`** | Obsidian's cloud sync | ⚠️ Needs VPS for cron | ⚠️ `.bib` only on VPS | ~$10/mo | iOS access is needed; small team |
| **`always-on`** | Syncthing + VPS (P2P, peer = full filesystem) | ✅ VPS runs as a Syncthing peer | ⚠️ `.bib` only on VPS | ~$12–25/mo VPS | Multi-device with always-on agent; recommended for the [discovery loop](future-directions.md#the-discovery-loop) |

*(Legacy labels map: A → `local-only`, A+ → `local-mesh`, B → `obsidian-sync`, C → `always-on`. The named forms are authoritative; the letters are retained only where an existing anchor depends on them.)*

**Start with `local-only`; migrate to `local-mesh` when a second device enters the workflow; graduate to `always-on` when you need unattended automation.** Adding Syncthing to an existing vault is additive — it doesn't require restructuring anything. `local-mesh` is structurally `always-on` minus the VPS — same sync mechanism, same write-coordination concerns, just no rented machine carrying the always-on role.

## Common decisions across options

These apply regardless of which option you pick:

- **Git is the version history layer, not the sync layer.** All four options use Git for reversibility. Sync is a separate concern.
- **`library.bib` lives inside the vault** at `.memoria/library.bib`, exported by Better BibTeX. This makes the bib a first-class artifact that travels with the vault under whichever sync mechanism you choose.
- **Cheap-task routing is configured in Hermes, not in the deployment.** See [architecture/capability-stack.md](../../reference/architecture/capability-stack.md) for the model-routing pattern (synthesis to Claude, embed / classify / quick-summary to cheaper models via OpenRouter or similar).
- **Per-session log files, not a single `log.md`.** Each agent session writes a new file to `00-meta/02-logs/`. With one append-only file, distributed writes from VPS and desktop produce sync conflicts; one-file-per-session has nothing to conflict on.
- **Hermes data dir is `~/.hermes/` by default** (or `%USERPROFILE%\.hermes\` on Windows). Override with `HERMES_HOME=/path/to/dir` when you need isolation — most commonly on the local-mesh and always-on options, where any secondary device's Hermes should keep its own profiles, sessions, and audit log isolated from the primary's `~/.hermes/`.
- **One Hermes dispatcher per vault.** Under the local-mesh and always-on options, multiple machines have the vault but only *one* should run Hermes as a dispatcher (cron + `hermes gateway` + card claiming). The task registry lives in `~/.hermes/` per machine; two active dispatchers against the same synced vault race on card writes and produce conflicting audit logs. The convention: the *[primary device](../../reference/glossary.md#system-and-architecture)* (desktop on local-mesh, VPS on always-on) owns dispatch; secondary devices run vault-only or in restricted modes — see [Secondary-device patterns](#secondary-device-patterns-local-mesh-and-always-on) below.
- **Profile aliases are first-class.** The `install.ps1` script invokes `hermes profile install ./.memoria/profiles/memoria-<name> --alias memoria-<name>` for each profile, which gives you `memoria-librarian chat` as a shortcut for `hermes -p memoria-librarian chat`, which is what the workflows in [workflows/README.md](../../how-to/workflows/README.md) assume.
- **`.env` is per-machine, never committed.** Each profile ships a `.env.EXAMPLE` listing required and optional env vars with descriptions. The installer copies it to `.env` on first install if `.env` doesn't already exist; the human fills in keys. Hermes hard-excludes `.env` and `auth.json` from `hermes profile install` / `update` so credentials never travel between machines.
- **Profile memory can ride the vault.** `MEMORY.md` / `USER.md` are per-machine by default, but the [`memories/` junction](sync-and-coordination.md#syncing-profile-memory-across-machines-the-memories-junction) promotes them into the git-synced vault (`.memoria/profile-memory/memoria-<name>/`) so learned notes follow you across machines — the automatic, no-extra-channel way to share profile memory under non-concurrent local-only / local-mesh use. Session history (`state.db`) and secrets (`.env`) deliberately stay per-machine.

## Secondary-device patterns (local-mesh and always-on)

Under the local-mesh and always-on options, a "secondary device" is any machine other than the designated primary. (Under local-mesh, that's the laptop. Under always-on, that's the desktop — and any developer laptop alongside the VPS.) The primary owns dispatch; secondary devices range from "read-only consumers" to "ACP-capable interactive surfaces" depending on what's installed.

Four patterns, ordered by setup complexity:

| Pattern | What's installed on secondary | Read & edit vault | Dispatch cards | ACP plugin works |
| --- | --- | --- | --- | --- |
| **Vault-only** | Obsidian + vault folder + Git client | ✅ | ❌ | ❌ |
| **Telegram dispatch** | Telegram client (no vault on this device) | n/a | ✅ (via primary's bot) | ❌ |
| **HTTP API client** | Obsidian + QuickAdd / shell to POST to primary | ✅ | ✅ (via primary's API) | ❌ |
| **Hermes ACP-only** | Obsidian + full Hermes install (no cron, no `hermes gateway`) | ✅ | ✅ interactive only | ✅ |

### Vault-only (simplest)

The laptop has Obsidian + the vault folder + Git client, nothing else. Read notes, write notes (claim notes, fleeting captures, edits), search the vault, view dashboards, drop PDFs into `10-inbox/00-pdfs/` for the primary to ingest when sync delivers them. Covers ~80% of daily research work. No Hermes install, no agent-side conflicts possible.

### Telegram dispatch

The human runs Telegram on the secondary device (phone, tablet, or another laptop) and dispatches via the bot to the primary's Hermes. Lowest-friction extension of reach — no install on the secondary, no network coordination, works from any device with Telegram. Limited to the bot's command surface; can't run arbitrary Hermes commands or open ACP conversations.

### HTTP API client

The secondary's Obsidian sets up QuickAdd actions (or shell scripts) that POST to the primary's API server on `127.0.0.1:8642` (loopback) or a Tailscale-bridged address. The primary's Hermes does the work; the secondary just triggers it. Richer than Telegram (any API-callable command works) but doesn't enable ACP — the `agent-client` plugin spawns a local subprocess and doesn't talk over HTTP.

### Hermes ACP-only

The only pattern that **enables the `agent-client` (ACP) plugin on the secondary device.** The ACP plugin reads its `data.json` `command` field and spawns the Hermes binary as a local subprocess; without a local Hermes, no ACP. Install the Hermes binary, then choose which profiles to compile on this device — the choice matters for safety.

#### Install only the profiles you need (structural over behavioral enforcement)

The naive approach is to mirror the primary's full profile set on every device. That works under the convention *"don't enable cron, don't run `hermes gateway`, don't claim cards"* — but those are behavioral rules the human has to remember. A stronger guarantee is **structural enforcement**: only compile profiles whose behavior is architecturally safe on this device. `hermes -p memoria-librarian find` returns "profile not found" rather than running a duplicate discovery pass.

The recommended install tiers:

| Tier | Profiles | When to install |
| --- | --- | --- |
| **Always (baseline)** | `memoria-socratic` only | Every secondary device that uses ACP. Naturally safe — `policy.allow.write: []` lane policy and `routing.invocation: interactive_only` mean Socratic *cannot* write to the vault and *cannot* be queue-dispatched, regardless of human behavior. |
| **Add as needed** | `memoria-mapper`, `memoria-writer`, `memoria-verifier` | Each carries obligations the human must remember; install only when a specific recurring use case on this device justifies the risk. |
| **Never on a secondary device** | `memoria-librarian`, `memoria-coder`, `memoria-linter` | API costs, queue conflicts, heavy install footprint, or structurally background-only — see per-profile notes below. |

#### Per-profile risk on a secondary device

| Profile | Architectural safety on secondary | Verdict |
| --- | --- | --- |
| **Socratic** | Write-denied (`policy.allow.write: []`) and `routing.invocation: interactive_only`. Cannot write to the vault or claim cards by lane policy. The constraints below (no cron, no `serve`, no claim) are *vacuously satisfied* — there's nothing to disable. | **Always install.** |
| **Mapper** | Read-only across the vault except project-scratch (`40-workbench/<project>/01-map/corpus-map.md`, `*/01-map/gap-report.md`). Two Mapper instances writing the same project's scratch can collide. | **Borderline.** Install for read-only scope queries only; never run during active project work the primary is also handling. |
| **Verifier** | Read-only except `40-workbench/*/05-verification/`. Can spawn upstream gap cards. Two Verifier instances on the same draft is collision-prone. | **Borderline.** Install for ad-hoc `similarity-check` before filing a new claim; skip if the primary is running full `cite-check` against the same drafts. |
| **Writer** | Writes drafts to `10-inbox/02-answers/` and `40-workbench/*/04-drafts/`. Creates synthesis cards. Two-machine drafting on the same chapter is the most likely real-world collision. | **Borderline.** Install for `hermes -p memoria-writer chat` (interactive drafting Q&A); never use `run draft` on the secondary. |
| **Librarian** | Network-active — external APIs cost real money. Writes to `10-inbox/` and `20-sources/`. The primary's overnight discovery loop already covers this lane. A secondary Librarian run duplicates work, creates conflicting candidate cards, and double-charges the API budget. | **Don't install.** Use the primary via Telegram or API client when you need Librarian work from the laptop. |
| **Coder** | Writes to `40-workbench/*/06-code/`; spawns external coding agents (Claude Code, Codex, Aider, etc.) with their own heavy install footprints. Only relevant if the human codes on the secondary. | **Don't install** unless you actively code on the secondary. |
| **Linter** | Structurally background-only — designed to run scheduled, not interactively. The primary's Linter does the work; the secondary's would either be idle (no cron) or produce duplicate reports (if cron enabled — which it shouldn't be). | **Don't install.** Nothing to do with it on a secondary device. |

#### The constraint list, narrowed

With Socratic-only, the constraint list becomes much shorter because most of it is structurally enforced:

- **Cron irrelevant.** Socratic has no cron entries to enable.
- **`hermes gateway` irrelevant.** The dispatcher only matters if there are queue-dispatched profiles installed; Socratic is `interactive_only` and there are no others.
- **No card-claiming possible.** With no queue-dispatched profile installed, `hermes kanban claim` has nothing to claim from.

If you add Mapper / Writer / Verifier to the install set, the original constraints come back:

- **Do NOT schedule cron jobs** on the secondary. (`approvals.cron_mode` stays at its default `deny`, but that only blocks dangerous commands in cron context — the real safeguard is not creating cron jobs and not running the gateway.)
- **Do NOT run `hermes gateway`** on the secondary.
- **Use only interactive commands** (`chat`, `similarity-check` for Verifier). Never `run draft`, never full `cite-check` passes, never `scope-project` runs that touch project-scratch the primary also writes to.

Each added profile is an obligation the human is choosing to take on. Socratic-only requires none.

#### Recommended secondary-device workflow

Read a paper note on the laptop → open the ACP pane → run a `socratic-processing` conversation → write the resulting claim-note yourself (human's hands, not Socratic's) → sync carries the new note back to the primary, where the Librarian runs enrichment overnight. See the [Discuss workflow](../../how-to/workflows/upstream/discuss.md). Socratic's write-denial is what makes this *architecturally* safe — even with a buggy plugin or a misconfigured skill, the policy MCP returns `deny` before any bytes reach disk.

### SSH-spawned ACP (no local Hermes install)

The `agent-client` plugin's `command` field is just a shell command. Setting it to `ssh primary-host hermes-agent` makes the ACP plugin spawn the Hermes process on the primary over SSH, streaming stdio back. The secondary device has no Hermes installed; the primary's Hermes is the agent.

Requirements: SSH always reachable (Tailscale or local network), primary awake, tolerance for ~100–500ms latency per message. The pattern's attractiveness depends on whether the primary is reliably reachable — see "Pattern selection by option" below.

Under SSH-spawned ACP you can talk to *any* profile remotely, not just Socratic — the spawned Hermes is the authoritative one on the primary with the full profile suite. This matters because it removes the "what's installed locally?" question: nothing's installed locally, so the device can use whichever profile is appropriate for the moment.

Concrete `customAgents` configuration examples for both the SSH-spawn path and the local-install path are in [obsidian-plugins/required/agent-client.md — Configuring the laptop for non-Socratic ACP](../../reference/plugins/agent-client.md#configuring-the-laptop-for-non-socratic-acp). That section also has the deployment-option-specific recommendations table for which path to pick.

### Pattern selection by option

Which secondary-device pattern to use depends on the deployment option, because local-mesh and always-on have different reachability properties for the primary.

#### Under local-mesh (desktop + laptop)

The desktop is the primary, but desktops are often off. SSH-spawned ACP is therefore unreliable — it depends on the desktop being awake when the laptop wants ACP. The recommended path:

1. **Start vault-only.** Covers ~80% of laptop use.
2. **Add Telegram** for lightweight dispatch when the desktop is on.
3. **Promote to Hermes ACP-only** (Socratic-only baseline) when Socratic-on-the-train is a workflow you'd actually use. Local install gives an always-available interactive agent.
4. **SSH-spawned ACP** only if local-install is genuinely off-limits (corporate laptop, etc.) — and accept that ACP won't work when the desktop is asleep.

#### Under always-on (VPS + desktops + laptops)

The VPS is the primary, and a VPS is always on. SSH-spawned ACP becomes the *recommended* default for the laptop because the destination is always reachable and latency is bounded. The recommended path:

1. **Start vault-only** if you don't need ACP at all.
2. **SSH-spawned ACP** as the default ACP pattern. No local Hermes install on the laptop. The ACP plugin spawns the VPS's Hermes over Tailscale-bridged SSH. You can ACP with any profile because the VPS has the full suite. Zero install drift — the laptop always uses the primary's Hermes.
3. **Local Socratic-only install** as an *offline fallback* if you regularly work where SSH to the VPS is unreliable (planes, trains, weak hotel wifi). Configure the `agent-client` plugin with two `command` entries — primary SSH command and a fallback local command — and switch when offline.
4. **Local full install** only for a *developer* role (see [Phase 3 install discipline](timeline.md)), never for the principal investigator's laptop in human-as-reader mode. The dev install must use `HERMES_HOME` isolation and point at a *test vault*, never the production vault.

The architectural reason the recommendation differs: local-mesh's primary is unreliable (desktop sleeps), so the laptop needs a local agent for ACP to be usable; always-on's primary is reliable (VPS always on), so SSH-spawn removes the need for a local install entirely.

### Roles on secondary devices under always-on

Two distinct roles need different setups:

- **Human-as-reader (PI's laptop):** SSH-spawned ACP into the VPS is the primary pattern. Local install only as offline fallback (Socratic-only). The secondary is a reading and processing surface; the VPS does all the dispatching, scheduling, and writing.
- **Developer (building Memoria itself or its skills):** Full Hermes install on the dev machine is appropriate because testing changes requires running all profiles end-to-end. **Under always-on, `HERMES_HOME=/path/to/dev-hermes` isolation AND pointing at a *test vault* (clone, fixture, Docker volume) is mandatory, not optional.** Two Hermes dispatchers can coexist *only* if they're pointing at different vaults. A dev's Hermes pointed at the production vault while the VPS is also dispatching against it is the failure mode this rule exists to prevent — and under always-on it's the most likely real-world incident class because the dev's machine is on the same Tailscale as the VPS and can reach it.

The VPS remains the primary dispatcher in either case. Developers iterate against test vaults; the principal investigator's research vault is touched by exactly one Hermes (the VPS's).
