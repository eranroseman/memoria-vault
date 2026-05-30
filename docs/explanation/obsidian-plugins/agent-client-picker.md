---
topic: plugins
---

# The agent-client picker — profiles labelled by identity

The [agent-client plugin](../../reference/plugins/agent-client.md) implements ACP inside Obsidian, and its `customAgents` array drives a *picker*: a list of agents the human can switch the active chat between. This document is about *why* that picker is shaped the way it is — why Memoria labels its profiles by identity rather than by action, and what each label and description is meant to communicate. For the `data.json` keys, the load-bearing settings, the hotkeys, and the per-device install detail, see [the configuration reference](../../reference/plugins/agent-client.md).

## A profile switcher, not a single-profile binding

The agent-client plugin is a *profile switcher*. Each entry in `customAgents` is one profile available in the picker; `defaultAgentId` is the one the human falls into by default. Memoria's four ACP-suitable profiles are labelled by **identity** — Socratic, Mapper, Writer, Verifier — because they are distinct specialists with fixed permission contracts, not interchangeable modes of one agent. (An earlier design borrowed Kilocode's verb-label scheme — Ask / Map / Draft / Check — but those name *actions* to switch between inside one assistant; Memoria's entries are separate agents, closer to Roo Code's role-named specialists like Architect and Orchestrator. The label names the contract-holder; the description carries the "what happens next.")

The profile IDs (`memoria-socratic`, etc.) and SOUL.md contracts are unchanged — the picker `displayName` is the profile's own name plus a one-line description. Architectural docs everywhere else refer to profiles by these same names.

## Picker labels and descriptions

| Picker label (`displayName`) | Profile ID | Pattern | Why |
| --- | --- | --- | --- |
| **Socratic** — Think a source through in conversation before distilling it. | `memoria-socratic` | **Persistent pane (default)** | Long conversations during processing. Architecturally write-denied (`policy.allow.write: []`); safe on any device. The standard ACP use case — open the pane in the Reading & Processing workspace, talk through a paper note via questioning. |
| **Mapper** — Map a project's corpus — what's ready, thin, missing — before writing. | `memoria-mapper` | **Transient session** | Quick corpus-retrieval queries via command palette ("find related notes," "what does my corpus say about X"). Session opens, returns results, closes. Not for persistent chat. |
| **Writer** — Distill sources into claim notes; turn framings into drafts. | `memoria-writer` | **Transient session** | Quick drafting chat via command palette ("counter-outline this section," "rephrase this paragraph"). Useful with discipline — interactive `chat` mode only, never auto-`run draft`. Session closes after response. |
| **Verifier** — Trace a draft's claims back to their sources; flag the gaps. | `memoria-verifier` | **Transient session** | Pre-filing similarity check via command palette ("show top-3 similar notes to this claim"). Returns ranked list, session closes. |

## Why these are skipped from the picker

Three of the seven profiles are deliberately *not* offered in the picker — the reasoning is part of the same identity-based design:

- **Librarian** — network-active; every `find`-style chat costs external API calls. Better dispatched via cards (queued, audited, retryable). Add only if the human specifically wants interactive discovery and accepts the cost characteristics.
- **Coder** — delegates substantive coding to an external coding agent (Claude Code, Codex, Aider). The Hermes-side Coder profile doesn't fit ACP chat.
- **Linter** — background-only by design ([profiles/linter.md](../profiles/linter.md)). No interactive use case.

## Related

- [Plugin configuration reference: agent-client](../../reference/plugins/agent-client.md) — the load-bearing `data.json` settings, hotkeys, and per-device install discipline.
