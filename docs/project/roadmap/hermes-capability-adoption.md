---
topic: roadmap
---

# Hermes capability adoption

Hermes ships far more than Memoria uses. Two design reviews walked the upstream Hermes Agent
feature surface (~29 capabilities — cron, delegation, hooks, skills, memory, toolsets,
checkpoints, context refs, code execution, the provider/reliability spine, MCP, plugins, ACP,
the API server, personality, skins, vision, image-gen, TTS, voice, browser, batch, external
memory providers) and asked one question of each: **adopt now, defer to a trigger, or
consciously reject.** This page is the disposition — the decision record so the question isn't
re-litigated.

The governing constraint: **Memoria is pre-runtime.** So "adopt now" means *structural*
(can't define the system correctly without it) or *free / set-and-forget*, **not** anything
that can only be tuned against live traffic. Capabilities that pay off only at corpus scale or
under load are deferred with an explicit trigger. Most adopt-now items are **already in the
design** — this page links them rather than restating them.

## Adopt now

Either already designed (linked), or a cheap, set-and-forget default worth fixing before standup.

| Capability | Disposition | Where it lives / what to set |
| --- | --- | --- |
| **Toolsets per profile** | Already designed | Per-profile toolsets are the permission mechanism — [profile-matrices.md](../../reference/profile-matrices.md) + the lane-override files ([profiles/README.md](../../explanation/profiles/README.md#lane-override-files)). |
| **MCP as integration backbone** | Already designed | Policy MCP, Zotero, OpenAlex, etc. plug in here — [policy-mcp.md](../../reference/architecture/policy-mcp.md); per-profile base MCPs in the lane-overrides. |
| **Delegation (orchestrator→specialist)** | Already designed, with boundary | The [delegation ladder](../../explanation/profiles/README.md#delegation-ladder) + the rule "delegate narrow, temporary subtasks; never the defining judgment." Durable state lives on the board, never in an ephemeral child. |
| **`SOUL.md` per profile (voice/identity)** | Already designed | Seven runtime contracts shipped in the starter vault — [profiles/README.md per-profile contracts](../../explanation/profiles/README.md#per-profile-contracts). |
| **Nested `AGENTS.md` / context files** | Already in use | Folder-boundary conventions; keep each concise. |
| **Cron — the lane decision** | Already designed | Which lanes are scheduled vs human-triggered — [standard-cron-tasks.md](standard-cron-tasks.md); the proactive case is the [discovery loop](future-directions.md#the-discovery-loop). |
| **Model routing (synthesis vs cheap)** | Already designed | Per-profile model + cheap-model routing — [capability-stack.md](../../reference/architecture/capability-stack.md#model-routing-synthesis-on-claude-cheap-tasks-elsewhere). |
| **Memory boundary rule** | Already designed | Operational facts in Hermes memory; research knowledge in the vault — [memory-tiers.md](../../explanation/architecture/memory-tiers.md). |
| **Prompt caching** | Set-and-forget | On by default for supported providers; the only discipline is keeping each profile's prefix (`SOUL.md` + `AGENTS.md` + pinned skills) **stable within a run** so the cache hits. No config. |
| **Provider routing — `data_collection: deny`** | Set-and-forget (privacy) | A research-privacy requirement, not an optimization: ingested literature and synthesis must not be trained on. Ship the deny flag on by default where OpenRouter is the gateway. Pairs with [secret-management.md](secret-management.md). |
| **Checkpoints / rollback** | One-line enable | Enable the shadow-git checkpoint store so a bad agent edit to a note has a turn-level undo before the first real edit; tune `max_file_size_mb` so Markdown is captured and PDFs/datasets aren't. Independent of the vault's own git history. |
| **Context references (`@file`, `@diff`)** | Document | Operator ergonomics at the review gate; **CLI-only** (not on the gateway/Obsidian/mobile). Worth a one-line operator note, no design weight. |

## Future direction (deferred to a trigger)

Real value, but only realizable once the loop runs, at corpus scale, or under load — and most
can only be *tuned* against real traffic.

| Capability | Trigger to revisit |
| --- | --- |
| **Credential pools** | When parallel/overnight ingest hits single-key rate limits. |
| **Fallback providers** | When provider outages start dropping cards to `retry-needed`; tune the ladder against real failures. |
| **Per-lane routing (`sort` / `order`)** | When per-lane cost data exists to tune price-vs-quality routing. |
| **Vision (`vision_analyze`)** | Highest-value multimodal pick — add to the Librarian's ingest toolset once ingest runs and the aux-vision fallback is configured (figures/tables/charts in PDFs). |
| **API server (`hermes gateway`)** | When mobile/remote review is wanted — the OpenAI-compatible `:8642` endpoint is the phone path. Bind fail-closed (see [glossary: fail-closed startup](../../reference/glossary.md)). |
| **ACP cockpit** | The diff-and-approve review UX (Obsidian [agent-client](../../reference/plugins/agent-client.md) + VS Code). Adopt once reviewing is a daily activity; verify the plugin renders diffs/approvals first. |
| **Hooks (defense-in-depth)** | Only if a fast *local* check (e.g. auto-lint on write) proves needed once the loop runs. The [policy MCP](../../reference/architecture/policy-mcp.md) stays authoritative — do **not** run two write-scope enforcement layers to keep in sync. |
| **First-party `memoria` plugin** | Bundles review-gate hooks + a `/promote` command + a board CLI — depends on the hooks decision above. |
| **Skills catalog (workflows → `SKILL.md`)** | A packaging project that pays off once the workflows run; governance is deferred in [skill-governance.md](skill-governance.md). |
| **`execute_code` for enrichment** | A token optimization for the multi-API enrichment loop once that loop runs (available on WSL2/Linux). |
| **Browser (discover fallback)** | When a needed source has no API; API-first, browser as last resort, local backend for private URLs. |
| **Batch runner** | One-time pilot-corpus run only (implementation-plan step), never steady state — results still funnel into `review-required`. |
| **Reference tooling: Docling, Inciteful, identifier reconciliation** | Catalogued in [computational-toolbox.md](../../reference/architecture/computational-toolbox.md#citation-format-parsers) as evaluated-not-adopted; reach for them when the corpus is table/figure-heavy or citation-network discovery / bulk entity reconciliation becomes a felt need. |

## Consciously rejected

Recorded so they aren't reopened. Each would harm an invariant or duplicate something Memoria
already does better.

| Capability | Why rejected |
| --- | --- |
| **External memory providers** (Mem0, Honcho, …) | The clearest reject: an auto-extracting, auto-injecting "memory" store is a second, *un-gated* knowledge layer competing with the vault — exactly the unreviewed accumulation Memoria exists to replace. The vault is the knowledge store; built-in `MEMORY.md` holds operational facts only. |
| **Image generation** | Generated images are the opposite of sourced evidence; they would pollute the vault's "everything is traceable" invariant. If ever needed for a deliverable, the asset lives outside the canonical layers. |
| **Voice mode** | Conflicts with the deliberate, auditable, review-gated model — voice is for fast conversational loops, not a slow path through explicit states. |
| **TTS** | Marginal — at most an optional audio digest on top of the cron `--deliver` path; not a capability. |
| **Skins** | Pure CLI chrome, zero design weight. |
| **Batch (steady state)** | A training-data / eval tool; running thousands of unattended ingests is the over-automated black box the architecture refuses. (One-time pilot use is in the future table above.) |

## Related

- **Source analysis:** two internal Hermes-feature design reviews (kept in the working notes, not the published docs).
- **Where adopt-now items are specified:** [profiles/README.md](../../explanation/profiles/README.md), [profile-matrices.md](../../reference/profile-matrices.md), [policy-mcp.md](../../reference/architecture/policy-mcp.md), [capability-stack.md](../../reference/architecture/capability-stack.md), [standard-cron-tasks.md](standard-cron-tasks.md).
- **Deferred-feature catalog:** [future-directions.md](future-directions.md) (Memoria-internal futures; this page is the *upstream-Hermes-capability* axis).
