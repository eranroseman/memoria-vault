# The agent-client picker

The agent-client plugin implements ACP inside Obsidian. Its `customAgents` array drives a picker — a list of profiles the human can switch the active chat between. This document explains why the picker is shaped the way it is: why Memoria labels its profiles by identity rather than by action, and what each label is meant to communicate.

For the `data.json` keys, load-bearing settings, hotkeys, and per-device install discipline, see [reference/plugins.md](../../reference/plugins.md).

---

## Profiles, not modes

The picker is a **profile switcher**, not a mode selector. Each entry is a distinct specialist with a fixed permission contract. Memoria labels its profiles by identity — Socratic, Mapper, Writer, Verifier — because they are different agents, not different modes of one agent.

An earlier design borrowed verb-label conventions (Ask / Map / Draft / Check) that name actions inside one assistant. Memoria's entries are separate agents — closer to role-named specialists like Architect and Orchestrator. The label names the contract-holder; the description carries the "what happens next."

---

## The four ACP-suitable profiles

| Picker label | Profile | Invocation pattern | Why |
| --- | --- | --- | --- |
| **Socratic** — Think a source through in conversation before distilling it | `memoria-socratic` | Persistent pane (default) | Long conversations during processing. Architecturally write-denied — safe on any device. The standard ACP use case: open the pane in the Reading & Processing workspace, talk through a paper note via questioning. |
| **Mapper** — Map a project's corpus: what's ready, thin, missing | `memoria-mapper` | Transient session | Quick corpus-retrieval queries via command palette. Session opens, returns results, closes. Not for persistent chat. |
| **Writer** — Distill sources into claim notes; turn framings into drafts | `memoria-writer` | Transient session | Quick drafting assistance via command palette ("counter-outline this section"). Useful with discipline — interactive `chat` mode only. Session closes after response. |
| **Verifier** — Trace a draft's claims back to their sources; flag the gaps | `memoria-verifier` | Transient session | Pre-filing similarity check ("show top-3 similar notes to this claim"). Returns ranked list, session closes. |

Socratic is the **persistent** default because reading sessions demand sustained conversation. The other three are transient — they answer one question and close, which keeps context discipline and prevents the human from accidentally running drafting operations in a persistent Mapper session.

---

## Why three profiles are absent from the picker

**Librarian** — network-active; every `find`-style chat costs external API calls. Better dispatched via cards (queued, audited, retryable). Add only if the human specifically wants interactive discovery and accepts the cost.

**Coder** — delegates substantive coding to an external coding agent. The Hermes-side Coder profile doesn't fit ACP chat — its work happens in the external agent's session, not in a conversational pane.

**Linter** — background-only by design. No interactive use case.

---

## Related

- Socratic profile: [explanation/profiles/socratic.md](../profiles/socratic.md)
- Reading & Processing workspace (where the persistent ACP pane lives): [reference/obsidian/workspaces.md](../../reference/obsidian/workspaces.md)
- Plugin settings: [reference/plugins.md](../../reference/plugins.md)
