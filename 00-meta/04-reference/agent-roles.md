# Agent roles

What each Hermes profile does. Companion to the per-profile contracts at `.memoria/profiles/memoria-<name>/SOUL.md`.

## The seven profiles

| Profile | In picker? | What it does |
| --- | --- | --- |
| **Socratic** | Yes (default) | Think a source through in conversation before you distill it. Write-denied across the vault. |
| **Mapper** | Yes | Map a project's corpus — what's ready, thin, missing — before writing. Read-only across vault. |
| **Writer** | Yes | Distill sources into claim notes; turn framings into drafts. |
| **Verifier** | Yes | Trace a draft's claims back to their sources; flag the gaps. Verification reports only. |
| **Librarian** | No — Kanban cards | Find and ingest sources. Network-active; runs from cards. |
| **Coder** | No — external delegation | Scaffolds code-note handoffs; substantive work goes to Claude Code / Codex / Aider. |
| **Linter** | No — background/cron | Validates structure, metadata, schema, link health. Default dry-run. |

## How they're invoked

- **Socratic** — persistent ACP pane (the default agent). `Cmd-P → Memoria: ask about this note`.
- **Mapper / Writer / Verifier** — transient ACP via palette commands (`Memoria: find related notes`, `Memoria: counter-outline this section`, `Memoria: similarity-check this claim`), or via the mode-switching hotkeys in an open chat (`Ctrl+Shift+2/3/4`).
- **Librarian** — runs on cards from the Kanban; not in the ACP picker.
- **Coder** — scaffolds handoffs; the actual editing happens in an external coding agent.
- **Linter** — scheduled background runs; produces reports, never acts on canonical content.

## Architectural protection

Each profile has **narrow permissions**, enforced by the policy MCP at every vault write. Socratic can't write at all. Mapper is read-only outside project scratch. Verifier writes only verification reports. Writer can't write to review-gated zones. See [[profile-policies]] for the full matrix.

## Why the split

The seven-profile design exists because **specialists are safer than generalists**. A profile with narrow permissions cannot accidentally do work outside its lane — even if a malformed task or a hallucinated path would push it there. The review gate (review-gated zones require human approval) and the lane-overrides (machine-enforced YAML) compose so that the worst case is a logged `deny`, not a silent review-gated-zone write.

---

**For depth:** profiles/README.md — the authoritative per-profile contracts and the seven-profile design rationale.
