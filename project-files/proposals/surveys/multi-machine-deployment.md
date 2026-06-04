---
topic: proposals
title: Multi-machine deployment (topologies and secondary-device patterns)
status: deferred
created: 2026-06-01
---

# Multi-machine deployment

The v0.1 default is `local-only` — one workstation, Git for history, Zotero on localhost ([deployment options](../../../docs/explanation/deployment/deployment-options.md)). This proposal covers everything past that default: the multi-machine sync topologies and the patterns by which a *secondary* device safely reads, edits, and (sometimes) dispatches against a shared vault. It is deferred because v0.1 ships single-device; the topologies are additive and cost nothing to defer.

Adjacent: [multi-vault-and-multi-machine.md](multi-vault-and-multi-machine.md) covers cross-machine *capabilities* (cross-vault retrieval, session-history sync, a shared memory server). This file covers the *deployment substrate* those capabilities run on. The two are designed to move together.

## What

Three sync topologies beyond `local-only`, plus a set of operating patterns for any device that isn't the designated primary.

| Pattern | Sync mechanism | Always-on agent | Zotero API access | Ongoing cost | When to use |
| --- | --- | --- | --- | --- | --- |
| `local-mesh` | Syncthing peer-to-peer (no VPS) | ⚠️ Primary device when on | ✅ Full localhost on primary | $0 infra | Desktop + laptop; auto-sync without cloud subscription or VPS |
| `obsidian-sync` | Obsidian's cloud sync | ⚠️ Needs VPS for cron | ⚠️ `.bib` only on VPS | ~$10/mo | iOS access is needed; small team |
| `always-on` | Syncthing + VPS (P2P, peer = full filesystem) | ✅ VPS runs as a Syncthing peer | ⚠️ `.bib` only on VPS | ~$12–25/mo VPS | Multi-device with always-on agent; recommended for the [discovery loop](discovery-loop.md) |

**Migration path.** Start `local-only`; migrate to `local-mesh` when a second device enters the workflow; graduate to `always-on` when you need unattended automation. `local-mesh` is structurally `always-on` minus the VPS — same sync mechanism, same write-coordination concerns, just no rented machine carrying the always-on role. The conventions common to every pattern (Git as history layer, `memoria.bib` in-vault, per-session logs, **one Hermes dispatcher per vault**, `.env` per-machine) are documented as adopted design in [deployment options](../../../docs/explanation/deployment/deployment-options.md) and are what make these patterns safe.

## Why

`local-only` requires the workstation to be on and offers no auto-sync and no unattended automation. Two felt needs push past it: working the vault from a second device (laptop, phone, tablet), and running discovery/ingest overnight without a human kickoff. Both require a sync topology *and* a safe answer to "what may a non-primary device do against a vault the primary is also dispatching against?" — without one, two machines race on card writes and corrupt the audit log.

## Trade-offs

- **Write coordination is the core risk.** Two active Hermes dispatchers against one synced vault race on card writes and produce conflicting audit logs. The whole secondary-device design exists to make that structurally impossible, not merely discouraged.
- **`always-on` adds standing cost and ops surface** — a rented VPS (~$12–25/mo), a Syncthing mesh to keep healthy, and a cron whose silent failure is the dominant operational risk.
- **`obsidian-sync` degrades Zotero access** to `.bib`-only on the VPS (no live localhost API), constraining Librarian discovery on that node.
- **SSH-spawned ACP trades install simplicity for a reachability dependency** — it removes local install drift but only works while the primary is awake and reachable, with ~100–500ms latency per message.
- **Install drift across devices** is a standing maintenance cost once more than one machine compiles profiles.

## Adoption trigger

Per topology, a concrete signal — not "might be useful":
- **`local-mesh`:** a *second device* genuinely enters daily use and manual Git pull/push between them is the felt friction.
- **`always-on`:** unattended overnight work is wanted — most concretely, the [discovery loop](discovery-loop.md) — and a sleep-prone workstation keeps missing the cron.
- **`obsidian-sync`:** iOS/mobile vault access is required and Syncthing-on-mobile isn't viable.

## Guard

Do not stand up a VPS or a Syncthing mesh as a preparatory measure. `local-only` is the correct posture until a second device or unattended automation is real; adding Syncthing later is additive and restructures nothing, so there is no first-mover cost to pay early. The one invariant that must never be relaxed when you do adopt these: **exactly one Hermes dispatcher per vault** — every secondary-device pattern below is a way of honouring that.

## Proposed mechanism — secondary-device patterns

Under any multi-machine topology, a "secondary device" is any machine other than the designated primary. (Under `local-mesh`, that's the laptop. Under `always-on`, that's the desktop — and any developer laptop alongside the VPS.) The primary owns dispatch; secondary devices range from read-only consumers to ACP-capable interactive surfaces depending on what's installed.

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
| **Verifier** | Read-only except `40-workbench/*/05-verification/`. Can spawn Compile-flow gap cards. Two Verifier instances on the same draft is collision-prone. | **Borderline.** Install for ad-hoc `similarity-check` before filing a new claim; skip if the primary is running full `cite-check` against the same drafts. |
| **Writer** | Writes drafts to `10-inbox/02-answers/` and `40-workbench/*/04-drafts/`. Creates synthesis cards. Two-machine drafting on the same chapter is the most likely real-world collision. | **Borderline.** Install for `hermes -p memoria-writer chat` (interactive drafting Q&A); never use `run draft` on the secondary. |
| **Librarian** | Network-active — external APIs cost real money. Writes to `10-inbox/` and `20-sources/`. The primary's overnight discovery loop already covers this lane. A secondary Librarian run duplicates work, creates conflicting candidate cards, and double-charges the API budget. | **Don't install.** Use the primary via Telegram or API client when you need Librarian work from the laptop. |
| **Coder** | Writes to `40-workbench/*/06-code/`; spawns external coding agents (Codex, Claude Code; Kilo Code and Aider planned) with their own heavy install footprints. Only relevant if the human codes on the secondary. | **Don't install** unless you actively code on the secondary. |
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

Read a paper note on the laptop → open the ACP pane → run a `socratic-processing` conversation → write the resulting claim-note yourself (human's hands, not Socratic's) → sync carries the new note back to the primary, where the Librarian runs enrichment overnight. See the [Discuss workflow](../../../docs/how-to-guides/compile/discuss-a-paper.md). Socratic's write-denial is what makes this *architecturally* safe — even with a buggy plugin or a misconfigured skill, the policy MCP returns `deny` before any bytes reach disk.

### SSH-spawned ACP (no local Hermes install)

The `agent-client` plugin's `command` field is just a shell command. Setting it to `ssh primary-host hermes-agent` makes the ACP plugin spawn the Hermes process on the primary over SSH, streaming stdio back. The secondary device has no Hermes installed; the primary's Hermes is the agent.

Requirements: SSH always reachable (Tailscale or local network), primary awake, tolerance for ~100–500ms latency per message. The pattern's attractiveness depends on whether the primary is reliably reachable — see "Pattern selection by topology" below.

Under SSH-spawned ACP you can talk to *any* profile remotely, not just Socratic — the spawned Hermes is the authoritative one on the primary with the full profile suite. This matters because it removes the "what's installed locally?" question: nothing's installed locally, so the device can use whichever profile is appropriate for the moment.

The `customAgents` keys are agent-client plugin settings. Which path to pick — SSH-spawn or local-install — depends on the topology; see *Pattern selection by topology* below.

### Pattern selection by topology

Which secondary-device pattern to use depends on the topology, because `local-mesh` and `always-on` have different reachability properties for the primary.

#### Under `local-mesh` (desktop + laptop)

The desktop is the primary, but desktops are often off. SSH-spawned ACP is therefore unreliable — it depends on the desktop being awake when the laptop wants ACP. The recommended path:

1. **Start vault-only.** Covers ~80% of laptop use.
2. **Add Telegram** for lightweight dispatch when the desktop is on.
3. **Promote to Hermes ACP-only** (Socratic-only baseline) when Socratic-on-the-train is a workflow you'd actually use. Local install gives an always-available interactive agent.
4. **SSH-spawned ACP** only if local-install is genuinely off-limits (corporate laptop, etc.) — and accept that ACP won't work when the desktop is asleep.

#### Under `always-on` (VPS + desktops + laptops)

The VPS is the primary, and a VPS is always on. SSH-spawned ACP becomes the *recommended* default for the laptop because the destination is always reachable and latency is bounded. The recommended path:

1. **Start vault-only** if you don't need ACP at all.
2. **SSH-spawned ACP** as the default ACP pattern. No local Hermes install on the laptop. The ACP plugin spawns the VPS's Hermes over Tailscale-bridged SSH. You can ACP with any profile because the VPS has the full suite. Zero install drift — the laptop always uses the primary's Hermes.
3. **Local Socratic-only install** as an *offline fallback* if you regularly work where SSH to the VPS is unreliable (planes, trains, weak hotel wifi). Configure the `agent-client` plugin with two `command` entries — primary SSH command and a fallback local command — and switch when offline.
4. **Local full install** only for a *developer* role (see [Phase 4 install discipline](../../releases/v0.1/release-plan-v0.1-spillover.md)), never for the principal investigator's laptop in human-as-reader mode. The dev install must use `HERMES_HOME` isolation and point at a *test vault*, never the production vault.

The architectural reason the recommendation differs: `local-mesh`'s primary is unreliable (desktop sleeps), so the laptop needs a local agent for ACP to be usable; `always-on`'s primary is reliable (VPS always on), so SSH-spawn removes the need for a local install entirely.

### Roles on secondary devices under `always-on`

Two distinct roles need different setups:

- **Human-as-reader (PI's laptop):** SSH-spawned ACP into the VPS is the primary pattern. Local install only as offline fallback (Socratic-only). The secondary is a reading and processing surface; the VPS does all the dispatching, scheduling, and writing.
- **Developer (building Memoria itself or its skills):** Full Hermes install on the dev machine is appropriate because testing changes requires running all profiles end-to-end. **Under `always-on`, `HERMES_HOME=/path/to/dev-hermes` isolation AND pointing at a *test vault* (clone, fixture, Docker volume) is mandatory, not optional.** Two Hermes dispatchers can coexist *only* if they're pointing at different vaults. A dev's Hermes pointed at the production vault while the VPS is also dispatching against it is the failure mode this rule exists to prevent — and under `always-on` it's the most likely real-world incident class because the dev's machine is on the same Tailscale as the VPS and can reach it.

The VPS remains the primary dispatcher in either case. Developers iterate against test vaults; the principal investigator's research vault is touched by exactly one Hermes (the VPS's).

## Dependencies

- Syncthing (for `local-mesh` / `always-on`) and a rented VPS (for `always-on`); Tailscale for SSH-spawn reachability.
- The adopted common conventions in [deployment options](../../../docs/explanation/deployment/deployment-options.md) — especially **one dispatcher per vault** — which these patterns presuppose.
- [discovery-loop.md](discovery-loop.md) is the main thing that *motivates* `always-on`; adopting `always-on` before the discovery loop (or a real second device) is premature.

## Related

- **Adopted baseline:** [deployment options](../../../docs/explanation/deployment/deployment-options.md) (the `local-only` default and the common conventions).
- **Cross-machine capabilities:** [multi-vault-and-multi-machine.md](multi-vault-and-multi-machine.md) (cross-vault retrieval, session-history sync, shared memory server) — the capabilities that ride this substrate.
- **Install discipline:** [release-plan-v0.1-spillover.md](../../releases/v0.1/release-plan-v0.1-spillover.md) (Phase 4 dev-install rules).
- **Glossary:** [primary device](../../../docs/reference/glossary.md#system).
