---
topic: decisions
id: 105
title: Content-light diagnostic plane — out of the vault, ephemeral, opt-in detail
status: accepted
date_proposed: 2026-06-19
date_resolved: 2026-06-19
assumes: [24, 46, 104]
supersedes: []
superseded_by: []
---

# ADR-105: Content-light diagnostic plane — out of the vault, ephemeral, opt-in detail

## Context

The three-plane model ([ADR-104](104-telemetry-three-planes.md)) introduces a diagnostic plane to close a real gap: Memoria's own deterministic code (MCP servers, ingest, crons) currently fails with nothing but stderr, so an already-happened or intermittent failure cannot be diagnosed. But this plane is the **first place vault-derived content could land in a log** — failed-request payloads, malformed note lines, provider error bodies — and Memoria's posture is otherwise content-free ([Telemetry & logs](../reference/telemetry.md)) and local-first. Done naively it would convert a content-never-logged system into one where a forgotten debug flag plus a routine `git push` exfiltrates unpublished research. The norm across comparable local tools (Obsidian plugins, VS Code, local AI runtimes) is also unambiguous: ship diagnostics, default them quiet, keep content behind a distinct opt-in, and never auto-exfiltrate. This decision fixes the plane's privacy and lifecycle contract so the benefit is captured without the leak.

## Decision

Memoria's diagnostic plane is **content-light, local, and disposable**, governed by these rules:

- **Scope: Memoria's own Python MCP servers and Operations only.** Agent reasoning, prompts, retries, and tool selection live inside the external unmodified Hermes runtime ([ADR-22](22-build-on-hermes-runtime.md)) and the MCP-only sandbox ([ADR-46](46-seven-layer-architecture.md)) and are not reachable; the plane does not pretend to cover them.
- **Outside the vault, outside Git.** Diagnostic files live under an OS state directory (`$XDG_STATE_HOME/memoria/diagnostics/`, falling back to `~/.local/state/memoria/diagnostics/` on Linux/WSL), **never** under `system/logs/` or anywhere in the Git-tracked, sync-tracked vault tree. A `.gitignore` entry is a belt-and-suspenders backstop, not the primary control. Each machine keeps its own; diagnostics are not shared state.
- **Content-light by default, deny-by-default for raw payloads.** Default capture is errors and warnings as **typed error codes plus a SHA-256 + length of any payload** — never the payload itself, never free-text that embeds content. Paths and note titles are treated as content (hashed or basename-stripped) in anything shareable. Raw payloads are available only through an **ephemeral, self-disarming capture**: a single run/session that reverts to content-light on restart, with a visible banner while active. There is no persistent "log content = on" configuration key.
- **Leveled and bounded.** Levels are error/warn/info/debug/trace, default errors-and-warnings, raised per-component via an environment variable. Files rotate by size with an explicit backup cap (bounded total footprint, tens of MB), compressed; diagnostics are troubleshooting aids, not a record.
- **No remote telemetry.** Nothing is sent anywhere automatically. Sharing is a single **user-triggered redacted bundle** that is **human-reviewable before it leaves the machine** and is covered by a redaction self-test (a golden corpus of known-sensitive strings asserted absent). The bundle defaults to codes-and-hashes; including any raw content is a separate, per-bundle, explicit opt-in.

## Consequences

- The operability gap is closed for the parts Memoria controls, which are the parts that actually break, without adding a content-exfiltration surface.
- Diagnostics from one machine are invisible on another — acceptable, because they are local troubleshooting, not shared record.
- "Content-light by default" means the *most useful* debugging detail (the exact bad payload) needs the deliberate ephemeral capture step. This is a real friction, accepted as the price of the privacy guarantee.
- A small dependency (a structured-logging library) and a first-party redaction step enter the codebase; redaction logic and its golden-corpus test stay first-party and unit-tested rather than delegated to a transitive dependency.
- The shared envelope ([ADR-104](104-telemetry-three-planes.md)) must keep the diagnostic plane's rotation/disposal rules from ever touching the audit plane's append-only-forever rule, and vice versa — the planes share an envelope, not a retention policy.

## When this matters

The plane earns its place the first time an unattended `always-on` run ([ADR-63](63-multi-machine-deployment.md)) or a cron fails and the cause is unrecoverable from stderr. The ephemeral content-capture path matters only when a typed error code plus payload hash is genuinely insufficient to reproduce a parse/enrichment failure — build the content-light core first and add the capture path on first real need.

## Alternatives considered

**Full structured logging with content, redacted by an allow-list at emission, stored in `system/logs/`.** Rejected: an allow-list cannot sanitize free-text error bodies, malformed lines (whose payload *is* the content), or tracebacks, and `system/logs/` is Git-tracked and pushed — one forgotten toggle plus `git push` leaks unpublished notes. The "off OneDrive" protection does not cover the Git channel.

**Opt-in-only, no standing diagnostic file (bundle-on-demand only).** Rejected as the sole model: it cannot diagnose intermittent or already-happened failures, because nothing was recording when the bug occurred. Kept as the *sharing* model, layered over a content-light standing log.

**Persistent content-logging toggle.** Rejected: for the single non-expert user ([ADR-24](24-single-researcher-scope.md)) a left-on flag is the classic forgotten-leak, and a verbosity/content config surface fights the opinionated-not-configurable posture. Ephemeral self-disarming capture gives the capability without the standing risk.

## Related

- **Related decisions / Depends on:** [ADR-104 (telemetry three planes)](104-telemetry-three-planes.md) (the plane this details); [ADR-22 (build on the Hermes runtime)](22-build-on-hermes-runtime.md) and [ADR-46 (seven-layer architecture)](46-seven-layer-architecture.md) (why agent cognition is out of scope); [ADR-24 (single-researcher scope)](24-single-researcher-scope.md) (the one-user foot-gun argument).
- **Tracking issue:** [#736](https://github.com/eranroseman/memoria-vault/issues/736) — implementation-readiness tracker; closed after `memoria/runtime/diagnostics.py` and its unit tests shipped.
- **Design rationale:** [Telemetry architecture](../explanation/architecture/telemetry-architecture.md).
- **Reference:** [Telemetry & logs](../reference/telemetry.md) (the content-free posture this plane is the sole exception to).
