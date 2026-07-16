# Surfaces bootstrap & installation — Design

Date: 2026-07-15. Status: **design (PI-approved in session), pre-plan**.
Owns the installation/bootstrap story for every Memoria surface; consumed by
the U3 (`2026-07-15-u3-obsidian-cards-design.md`) and U4
(`2026-07-15-u4-copi-agent-plugin-design.md`) specs. Partially baselines U1:
the contract points decided here (rendezvous, token, write-tool scoping,
the operation endpoint, and the status/views endpoints) bind until the U1
design gate (Plan 23 LOOP.9) honors or
explicitly supersedes them.

Derived from a first-principles rethink (four cited prior-art families:
editor/language-server lifecycles, repo-carried tooling, agent-integration
mechanics, local daemon pairing) plus PI rulings recorded in session. The
governing posture: **engine-first; everything else is generated into the
vault; the vault is the distribution channel.**

## 1. Decisions at a glance

| Item | Decision |
| --- | --- |
| Engine install | `pipx install memoria` (or `uv tool install memoria`) — the only thing ever installed outside a vault |
| Vault manifest | `.memoria/vault.json`: vault_id, schema_version, per-bundle versions + SHA-256 content hashes |
| Per-user state dir (never synced) | Linux/WSL2 `~/.local/state/memoria/vaults/<key>/`; macOS `~/Library/Application Support/Memoria/vaults/<key>/`; Windows `%LOCALAPPDATA%\Memoria\vaults\<key>\` — `<key>` = sha256(canonical vault path)[:16], computed only by the engine |
| Rendezvous | `<state>/runtime.json`, mode 0600, atomic write: `{schema, vault_path, vault_id, port, pid, boot_id, token, engine_version, started_at}`; deleted on clean exit |
| Server | `memoria serve`: foreground default port 8765 (walks 8765–8785); surface-spawned servers bind port 0 (ephemeral). Idle-exit 15 min, reset only by authenticated requests. One server per vault |
| Rendezvous verb | `memoria handshake --vault <path> [--spawn] --json` — connect-else-spawn-else-report; coordinates on stdout |
| Token | 256-bit urlsafe, minted fresh per server start; lives in server memory + the 0600 runtime.json only. Zero secrets in the vault |
| Secrets | `~/.config/memoria/secrets.env` (0600, user-scope) + process env; engine-loaded at every entry point; `memoria secrets set/list` |
| Agent bundle | perimeter + wiring owned here: `.claude/settings.json` (deny rules + hooks), `.claude/hooks/write_perimeter.py`, `.mcp.json`, `AGENTS.md` (via R1NG.4), `CLAUDE.md` (`@AGENTS.md` loader), `.codex/hooks.json`; method files owned by U4: `.claude/skills/memoria-copi/`, `.claude/hooks/session_status.py` |
| Obsidian bundle | `.obsidian/plugins/memoria/` seeded + enabled via `community-plugins.json`; **not marketplace-published this release** |
| Skew/repair verbs | `memoria doctor [--json]` (diagnose), `memoria upgrade` (regenerate all bundles) |
| Onboarding | `memoria onboard` (standalone, or `init`'s interactive tail) — see §7 |

## 2. Dependency graph and entry doors

Install-time chain (the only chain with a human at the wheel):

```text
user ──pipx/uv──▶ ENGINE ──memoria init──▶ VAULT
                                            ├─ content + .memoria/{vault.json,index.db}
                                            ├─ .obsidian/ (incl. plugins/memoria/)
                                            ├─ .claude/ + .mcp.json + CLAUDE.md
                                            ├─ .codex/hooks.json + AGENTS.md
                                            └─ Start here.md (tutorial front door, §7)
```

Run-time: Obsidian's native consent loads the embedded plugin, which runs
`memoria handshake --spawn` and talks HTTP+Bearer to the spawned server;
Claude Code's folder-trust activates the perimeter, its `.mcp.json` approval
spawns `memoria mcp` (stdio); Codex reads `AGENTS.md` and activates
`.codex/hooks.json` behind its project trust; vim/plain editors need nothing
running at all.

**Primary door: found the CLI.** Two commands (`pipx install memoria`,
`memoria init <path>`), then three host-native consent clicks. The other
doors converge on it:

- **Found the Obsidian plugin first** = opened a seeded vault without the
  engine: the plugin's spawn fails with ENOENT and renders the
  engine-missing panel — *"Engine missing — the Memoria CLI was not found
  (tried: `memoria`). Install it: `pipx install memoria`, then Retry. This
  vault remains fully readable and editable without it."* A settings field
  **Engine command** (default `memoria`) covers WSL2-hosted engines
  (`wsl memoria`) and nonstandard PATHs.
- **Agent first, engine-less machine**: folder-trust activates the perimeter
  before the first tool call (needs no engine); the `.mcp.json` spawn fails
  honestly; the SessionStart hook prints the install command into context.
  Between trust-accept and engine-install the agent cannot write: deny rules
  block the file tools and the only write tool does not exist yet.
- **Received a copied vault**: indistinguishable from a fresh seed — carries
  every surface and zero secrets. First handshake on the new machine creates
  a fresh state entry and token; original and copy can run side by side (the
  state key is the canonical path, not the vault_id).

Every write from every surface converges on the engine's single
trusted-writer path: CLI, MCP `operation_run`, and the HTTP server's
operation endpoint are three doors into the same code.

## 3. Server lifecycle

`memoria handshake` implements connect-else-spawn-else-report **inside the
engine** (written once, reviewed once): read `runtime.json` → if the pid is
alive AND `GET /v1/status` returns the recorded `boot_id`, return the
coordinates; else treat the file as stale, delete it, take `serve.lock`
(the loser of a race returns the winner's coordinates), spawn
`memoria serve --on-demand --ephemeral` detached, wait for the rendezvous
write (5 s timeout), return coordinates.

- Spawned servers bind port 0; the rendezvous file is the single source of
  truth (fixed well-known ports are the named anti-pattern). Foreground
  `memoria serve` defaults to 8765 and walks to 8785, recording the actual
  port.
- **Idle-exit 15 min**, reset only by *authenticated* requests.
  `GET /v1/status` is the sole unauthenticated endpoint — a liveness/identity
  probe (`boot_id`, `engine_version`) for handshake and failure triage — and
  it never resets the idle timer; authenticated data requests (the U3 pane's
  counts poll included) do, so an open pane deliberately keeps the server
  alive while a bare probe cannot. Explicit stop: authenticated
  `POST /v1/shutdown` (`memoria serve --stop --vault .` wraps it).
- Detached (not a child of the plugin) by design: two Obsidian windows share
  one server; an Obsidian crash cannot orphan a listener beyond the idle
  window.
- Client crash policy: bounded respawn — at most 3 spawn attempts in 3
  minutes, then the terminal honest state naming the log path
  (`<state>/serve.log`) and the manual command. Never a silent retry loop.
- Daemon-ready: the client contract is only "handshake returns coordinates
  of a live, authenticated server." A future daemon (or socket activation)
  pre-fills the same rendezvous; zero client changes.

## 4. Token and credentials

**In/beside split.** IN the vault (synced/copied/exported): markdown,
`.memoria/vault.json` (identity pointer, never a credential), the index DB,
and all surface bundles — zero secrets. BESIDE the vault (0600 state dir):
`runtime.json` (with the token), `serve.lock`, `serve.log`.

**Loopback token.** Minted per server start; 256-bit urlsafe; memory + the
0600 runtime.json only. Every request except `GET /v1/status` requires
`Authorization: Bearer <token>`. The server validates the Host header
(`127.0.0.1:<port>`/`localhost:<port>`) and rejects browser-origin requests
whose Origin is not `app://obsidian.md` — loopback position is not
authentication. Provisioning is engine→plugin stdout via handshake: the
plugin never locates the state file, never learns the key derivation, holds
the token in memory only, and explicitly never persists it into
`.obsidian/plugins/memoria/data.json` (which syncs with the vault).
Recovery ladder on 401: re-handshake once; if a live server still 401s,
render the token-invalid state with the restart instruction. When no server
runs, no valid secret exists at rest anywhere.

**Agents need no token**: MCP is stdio spawned by the host as the same OS
user; the CLI is direct invocation. Secret provisioning scopes to exactly
one client — the Obsidian plugin.

### 4b. Credentials registry (LLM + service keys)

The vault stores **pointers only** (`providers.yaml` `key_env:` names —
already true at rest). Resolution, uniform for all credentials: process env
first, then `~/.config/memoria/secrets.env` (0600, user-scope — outside the
vault *and* outside the per-vault state dir, since keys are user-scoped
across vaults), **loaded by the engine at every entry point** (`serve`,
`mcp`, CLI). Engine-side loading closes the GUI-launch hole: a server
spawned from desktop-launched Obsidian no longer depends on shell-profile
exports — for model calls *and* server-side enrichment alike.

Two failure classes:

| Credential | Class | When unset |
| --- | --- | --- |
| any live-model `key_env` (e.g. `KILOCODE_API_KEY`) | required-for-operation | the call **refuses before the network** with the named remediation (`memoria secrets set <NAME>`); the current silent fallback chain (`MEMORIA_MODEL_API_KEY` → `OPENAI_API_KEY` → `KILOCODE_API_KEY`, `operations.py:958-962`) is **removed** — explicit `key_env` or nothing |
| `OPENALEX_API_KEY` | enhancing | keyless polite-pool mode (lower rate limits) |
| `SEMANTIC_SCHOLAR_API_KEY` | enhancing | adapter off / keyless-throttled — the existing `default_on_when_keyed` pattern, generalized to the class |
| `PUBMED_API_KEY` | enhancing | NCBI keyless tier when the PubMed adapter lands |
| `GITHUB_TOKEN` | enhancing | when the GitHub capture adapter lands (not yet wired): anonymous rate limits; private repos refuse honestly |
| `NCBI_EMAIL` | identity (not secret) | polite-pool identity (`mailto`/`email` query params) omitted; same file, same mechanism |

`memoria secrets set <NAME>` / `memoria secrets list` (names and set/unset
only — never values). `memoria doctor` reports name, class, status, source
(env|file), and the concrete effect when unset ("refuses" / "keyless
3 req/s" / "adapter off"). Class-2 degradation is stated in the operation's
own output (search-honesty applied to enrichment), never silent. Keyless
modes stay first-class: deterministic-fixture and local Ollama need no
credentials, so CI and offline use are untouched.

## 5. Write-perimeter ordering

The perimeter is written by the same act that creates the vault — there is
never a Memoria vault on disk without `.claude/settings.json` — and it
travels with every copy, so the per-clone-activation hole of hook managers
is structurally impossible. Activation is the host's own trust dialog,
which fires before the session's first tool call. Three layers, each
fail-closed without the engine:

1. **Declarative deny rules** (`.claude/settings.json`): `Edit`, `Write`,
   `NotebookEdit` denied on `**/*.md`, `.memoria/**`, and — so the perimeter
   cannot be edited away by the thing it constrains — `.claude/**`,
   `.mcp.json`, `.obsidian/**`, `.codex/**`. Host deny rules also cover
   recognized bash file commands (`cat >`, `sed -i`, …) per Claude Code's
   documented behavior; arbitrary subprocess writes remain detect-only
   (layer 3). Zero runtime dependencies.
2. **PreToolUse hook** (`.claude/hooks/write_perimeter.py`, stdlib-only):
   denies writes into protected paths **unconditionally** — it never needs
   the engine to say no. Message: *"Memoria write perimeter: vault notes are
   engine-mediated — a direct edit would be recorded as the human's work by
   the provenance layer. Use the MCP tool `operation_run` or the `memoria`
   CLI."*
3. **Provenance watcher** (existing `observe-pi-edits`): the audit backstop
   for the documented gap that arbitrary subprocesses can bypass tool-level
   rules — non-engine writes are *detected* even where not prevented.

Codex mirror: the write rule as ungated `AGENTS.md` prose plus
`.codex/hooks.json` behind Codex's project trust. Skew never weakens the
perimeter: deny globs are static and the hook is unconditional — drift
affects reporting, never enforcement. A copied vault on an engine-less
machine is agent-read-only (no write doors exist) while remaining fully
human-usable. Residual holes, named: hand-deleting `.claude/` (every engine
touchpoint then warns loudly — absence is loud, never a silent no-op) and
headless sessions that skip trust dialogs (either project settings load and
the perimeter enforces, or they don't load and the project write tool is
not approved either; the watcher audits Bash-level writes regardless).

## 6. Upgrade and skew

Surfaces never self-update and are never patched in place. `pipx upgrade
memoria` → the next command in a vault compares `vault.json` bundle stamps
and warns → `memoria upgrade` regenerates every bundle, rewrites the
manifest (versions + SHA-256 hashes), and backs up any file whose on-disk
hash mismatches its manifest hash (someone hand-edited a seeded file) to
`.memoria/backup/<timestamp>/`, listing it in the output. Regeneration and
tampering are visible events.

Detection at every contact point, each surface reporting its own truth: the
CLI warns on every command; the plugin compares its `manifest.json` version
to the handshake's `engine_version` and shows the skew banner; the
SessionStart hook runs `memoria doctor --json --quick` and injects a
context line; rendezvous entries with a mismatched `engine_version` or dead
pid are treated as stale and respawned. Both directions are handled: vault
newer than engine → "upgrade the engine: `pipx upgrade memoria`"; engine
newer than vault → `memoria upgrade`. No update phone-home (no-telemetry
posture); skew banners are the compensating control.

## 7. Onboarding runway

`memoria onboard` (standalone, or the interactive tail of `init`) walks the
researcher from "engine installed" to "sitting in Obsidian with the
tutorial open":

1. **Obsidian detection** — platform-specific presence check. If missing:
   offer the native package manager with explicit consent — the command is
   shown and run only on yes, from a **frozen allowlist**
   (`brew install --cask obsidian`, `winget install Obsidian.Obsidian`,
   flatpak `md.obsidian.Obsidian`); anything else falls back to
   detect-and-direct (print/open the download URL). The engine never
   downloads binaries itself.
2. **Open the vault** via the `obsidian://` URI scheme
   (`xdg-open`/`open`/`start`), triggering Obsidian's own trust-and-enable
   prompt and, through the §2 chain, plugin → handshake → server.
   *Implementation check:* first-time registration of a brand-new folder
   may not be reachable via URI; if the URI bounces, print the manual
   fallback verbatim ("Open Obsidian → Open folder as vault → <path>").
3. **Tutorial start** — `init` seeds `Start here.md` at the vault root (the
   vault's own front door) linking the tutorial sequence and the co-PI
   variant; `onboard` ends by deep-linking to it. The CLI/plain-editor
   tutorial path remains first-class.
4. **Zotero (conditional)** — probe the Zotero connector API on
   `127.0.0.1:23119`; only if a running Zotero is detected, offer the
   integration step inline; otherwise the tutorial's import chapter covers
   it later. Zotero stays an optional adapter, never a gate.
5. **Credentials notice** — non-blocking: one line naming
   `memoria secrets set <NAME>` if live-model operations are wanted (§4b).

**Boundary:** this runway is machine wiring + entry choreography. The O1
design gate (Plan 23 LOOP.5) keeps what needs its own session — seed corpus
+ licensing decision, `steering.md` authoring, the co-PI interview, and the
time-to-first-answer instrumentation that measures this whole path — and
consumes this runway as its substrate.

## 8. Rejected alternatives (with flip conditions)

- **Obsidian marketplace channel now** — an unpaired second distribution
  channel reintroduces version skew. Flip: post-beta, publish a
  paired-version plugin that refuses vaults seeded by other versions.
- **Plugin-supervised child server** — an Obsidian crash orphans or kills
  the listener; two windows fight over it. Detached + idle-exit instead.
- **Fixed well-known port** — collides across vaults and with other apps;
  rendezvous file + port 0 instead.
- **Token in plugin settings** (`.obsidian/…/data.json`) — travels with
  every vault sync/export; the named failure of the closest prior art.
- **Silent env fallback chain for model keys** — violates fail-closed and
  honest failure; removed in §4b.
- **Engine downloads Obsidian** — installer-surface posture forbids it;
  consented package-manager delegation only.
- **User-global agent skill install** — breaks vault-scoping and goes stale
  against engine upgrades; the bundle is vault-embedded and regenerated.

## 9. Implementation slices (feeds the plan)

1. Engine: `handshake` verb, state-dir rendezvous, per-boot token,
   `--idle-exit`, Host/Origin validation, `POST /v1/shutdown`.
2. Engine: secrets file loading at all entry points, `secrets set/list`,
   class-aware fail-closed/degrade behavior, fallback-chain removal,
   doctor credential report.
3. `init`/`upgrade`: agent-bundle perimeter + wiring seeding
   (`.claude/settings.json`, `write_perimeter.py`, `.mcp.json`, `CLAUDE.md`,
   `.codex/hooks.json`), `vault.json` bundle manifest (versions + hashes),
   hand-edit backup on regenerate. Method files (`memoria-copi/SKILL.md`,
   `session_status.py`) are seeded by the same verbs but their content is
   the U4 spec's; `AGENTS.md` lands via Plan 23 R1NG.4.
4. `doctor`: skew + credential + bundle-integrity report.
5. `onboard`: Obsidian detect/offer/open, `Start here.md` seed, Zotero
   probe, credentials notice.
6. Plugin: replace the hardcoded `serverUrl` with handshake spawn (engine
   command setting; bounded respawn; honest states — rendered per the U3
   spec's UI section).
7. Docs: installation how-to rewrite; failure-states reference; secrets
   how-to.

## 10. Out of scope

Obsidian marketplace publication (flip condition in §8); the O1 wizard
content (seed corpus, licensing, steering.md, co-PI interview — LOOP.5,
consuming §7); the reactive daemon (beta.2; §3 stays daemon-ready);
multi-device/sync topologies (beta.2 register); any surface beyond the
three bundles named here.

## 11. Acceptance criteria

`memoria init` on a clean machine yields a vault where: the perimeter files
exist before any agent session can start (probe: fresh init → immediate
agent session → file-tool writes denied); handshake returns working
coordinates with a token that never appears inside the vault tree (probe:
grep the vault for the token after a full session); the server exits within
the idle window when all clients close and an unauthenticated status probe
does not prevent it; a copied vault on an engine-less machine is
agent-read-only and fully human-editable; a missing class-1 credential
refuses with the named remediation and a missing class-2 credential
degrades with an in-output notice; `memoria upgrade` regenerates all
bundles and backs up hand-edited seeded files; `memoria onboard` reaches
"tutorial open in Obsidian" on a machine with a supported package manager
in ≤5 minutes of user time.

## Appendix: session artifacts

Blinded clean-slate design + 4 cited prior-art digests (editor/langserver,
repo-carried tooling, agent integration, local pairing) produced 2026-07-15;
conclusions folded here. PI rulings in session: engine-first (primary door),
no marketplace this release, package-manager consent install (option B),
Zotero conditional-detect, secrets file mechanism, credentials two-class
registry.
