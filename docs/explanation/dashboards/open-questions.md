---
topic: dashboards
---

# `open-questions` — design summary

**Runtime artifact.** Ships at `00-meta/01-dashboards/open-questions.md` in the [starter vault](https://github.com/eranroseman/memoria-vault) and runs in Obsidian via Dataview; the runtime queries live there. This page covers the design role.

## Mission

Turn the vault into a research agenda by collecting every note that contains an explicit `# Open questions` section. Open this when planning the next research direction — what questions has past synthesis raised that haven't been answered yet? The dashboard reads claim notes and paper notes (the two places open-questions sections accumulate naturally) and provides a single aggregated view across the corpus.

## What this dashboard is not

- **Not a synthesizer.** It collects existing open-questions sections; it doesn't propose new questions, cluster them, or rank them by importance. That's the human's job (or a future Mapper skill).
- **Not the only place questions live.** Inline `# Open questions` sections inside claim notes and paper notes are the *durable* questions — the ones worth re-finding months later. Ephemeral session questions live in fleeting-notes and find-pass output, not here.
- **Not auto-resolving.** When a question is answered, the human manually removes or restructures the section. The dashboard doesn't track which questions have been answered (no `resolved:` state) — that would require a richer schema than free-form section content.

## Design decisions

- **Free-form section, not structured frontmatter.** Questions live in markdown body content (`# Open questions` heading) rather than a frontmatter `open_questions: []` list. The reasoning: questions are *prose* (often paragraphs with context), and constraining them to flat YAML strings would lose the framing. The cost is that the dashboard can't filter/group by question metadata — it just lists the notes that have such sections.
- **Two source folders: `30-synthesis/01-claims/` and `20-sources/01-papers/`.** These are the two places where durable questions accumulate. Project pages might also have questions, but those are typically operational ("what should we do next") rather than research-direction ("what's still unknown").
- **Sort by `file.mtime` not by question count.** Recently-touched notes are likely the human's current focus; putting those first matters more than ranking by question density.
- **No dependency fallback.** Unlike most dashboards, this one works on day one — any note with `# Open questions` appears immediately.

## Related

- [vault/README.md](../vault/README.md) — claim-note structure (Open questions is a recommended section)
- [`weekly-review`](weekly-review.md) — the weekly ritual; open-questions is consulted as-needed for research-direction planning, not as a weekly step
- [Librarian design summary](../profiles/librarian.md) — the upstream discovery direction is informed by aggregated open questions
