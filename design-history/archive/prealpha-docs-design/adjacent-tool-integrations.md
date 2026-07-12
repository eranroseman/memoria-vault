---
topic: explorations
title: Integrations and adjacent surfaces
status: deferred
folded_into: memoria-design-update  # partial - pattern library (D11) + Catalog (#220 biblib)
created: 2026-05-31
parent: Design notes
grand_parent: Explanation
nav_order: 10
nav_exclude: true
---

# Integrations and adjacent surfaces

Capabilities that connect Memoria to external tools or add new interaction surfaces.

---

## 1. Memoria Inspector Obsidian plugin

**What.** A read-only sidebar pane that exposes admin views without requiring the Linter to be invoked: board card counts by status, per-lane WIP depth, recent audit log entries, Linter verdict band. Pure read; no writes. Reduces the need to open a Hermes session for a health check.

**Adoption trigger.** The human regularly opens a Hermes session just to check board or Linter state — not to do work.

---

## 2. Hermes → Todoist gap-card integration

**What.** When the Verifier creates a gap card in `10-inbox/03-candidates/` (a failed claim-trace that Librarian needs to fill), mirror it as a Todoist task so it appears in the human's existing task-management surface. Gap cards that sit unactioned in the vault are invisible to the human's daily workflow; a Todoist task bridges the gap.

**Trade-offs.** Adds an external dependency. Requires Todoist API credentials in `.env`. If Todoist items are not worked down, the vault's gap cards also stagnate — mirroring doesn't fix a review-capacity problem.

**Adoption trigger.** The human uses Todoist as their primary task surface *and* gap cards regularly sit unactioned for > 2 weeks.

---

## 3. Open-design integration for polished deliverables

**What.** An external rendering agent ([open-design](https://github.com/nexu-io/open-design) pattern) takes a Pandoc-exported Markdown deliverable and applies the vault's design system (`.memoria/design-system.md`) to produce visually polished output (slide decks, formatted PDFs, web pages). The Coder profile scaffolds the handoff; the rendering agent produces the artifact; the human reviews the result.

**Adoption trigger.** The human needs a deliverable format (presentation, designed PDF) that plain Pandoc doesn't produce and is willing to maintain a design-system file.

---

## 4. Static HTML admin reports

**What.** Snapshot reports — board state, Linter verdict summary, metrics — rendered to static HTML by the Linter on a weekly schedule and stored in `50-deliverables/04-releases/`. Useful for retrospective review or sharing a vault health snapshot without requiring the recipient to open Obsidian.

**Adoption trigger.** The human wants to share or archive periodic health snapshots, or finds the Dataview dashboards too slow for a quick weekly review.

---

## 5. Literate code-note (weave + tangle)

**What.** A `code-note` that interleaves prose and executable code in a single file (the "literate programming" pattern). The Linter checks that the executable code and the prose description haven't drifted. Enables a research notebook where the implementation and its explanation live together and are drift-detected.

**Adoption trigger.** The human is writing code-notes for computational methods where the code and the prose description of the method regularly diverge, and finds the divergence costly to catch manually.
