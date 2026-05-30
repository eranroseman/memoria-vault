---
topic: general
---

# Design-summary page template

`dashboards/*.md` and `profiles/*.md` are **design summaries**: one page per dashboard or profile, describing the *design role* of a thing whose *runtime* lives elsewhere — a Dataview query in the starter vault, or a `SOUL.md` contract. The ~19 pages share one skeleton. This file is that skeleton, so the set stays consistent and a new page is quick to write.

It is the same template-vs-instance split the rest of the repo uses ([vault/note-types.md](../note-types.md) vs `00-meta/03-templates/`; [obsidian-ui/design-system.md](design-system.md) vs the vault copy): the summary holds the *why*; the runtime artifact holds the *what*.

## The skeleton

```md
---
mode: reference            # reference for spec-like pages; explanation for conceptual ones
audience: operator
topic: dashboards          # or: profiles
---

# `<name>` — design summary

**Runtime artifact.** Ships at `00-meta/01-dashboards/<name>.md` in the starter vault and
runs via Dataview; the runtime queries live there. This page covers the design role.

## Mission

What the thing is for, in 2–4 sentences: when the human opens or invokes it, and the one
decision it serves.

## What this dashboard is not

Bulleted contrasts with the siblings it's most often confused with — each bullet names the
sibling and the distinguishing axis. This section carries most of the design clarity; it is
usually worth more than the Mission.

## Design decisions

The non-obvious choices and their rationale: thresholds, deliberate exclusions, the
deterministic-vs-LLM split, graceful-degradation behavior, research/ADR provenance. This is
the design memory — the part that cannot be reconstructed from the runtime artifact.

## Related

Siblings, the workflow / profile / ADR it connects to, and the glossary terms it leans on.
```

## Where profiles differ

Profile pages use the same skeleton with two changes:

- **Runtime pointer:** `**Runtime contract.** Full prompt and operational detail live at `.memoria/profiles/memoria-<name>/SOUL.md`.` instead of the Dataview-query pointer.
- **Extra section:** a **`## Permissions and commands`** pointer (to the lane-permission matrix in [profiles/README.md](../../explanation/profiles/README.md) and the SOUL.md) sits between *Design decisions* and *Related*.

## Why a summary instead of just the runtime

The runtime artifact says *what* the thing does mechanically; the design summary says *why it is shaped that way* and *what it deliberately is not* — the rationale a reader needs to change it safely. A reviewer skimming the folder should be able to read one summary and know whether a proposed change is sound, without opening the Dataview query or the SOUL.md. If a page has nothing under *Design decisions* and *What this is not* that the runtime artifact doesn't already make obvious, it is a candidate to collapse into the folder index instead — but in practice the rationale is exactly what these pages exist to preserve.
