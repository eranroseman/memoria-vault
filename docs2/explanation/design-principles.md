# Design principles

Ten principles that settle ambiguous decisions. When a tool choice, workflow step, or architectural question is unclear, these are the tiebreakers.

---

**1. The vault is the artifact.**

Not the chat log, not the PDF folder, not the Zotero library. The Obsidian vault is what you are building. Everything else — Zotero, Hermes, the Kanban board — serves the vault. A useful output that lives only in a chat transcript hasn't been captured.

**2. Compound, don't just collect.**

Every source ingested should make the whole corpus more useful. A new paper note that connects to existing claim notes, adds to an MOC, and updates a comparative-brief is compounding. An isolated file that sits unlinked is just collection. The design distinguishes them: synthesis structures (claim notes, MOCs, reference notes) exist precisely to force compounding.

**3. Separate capture from synthesis.**

Raw annotations are not synthesis. A paper note is not a claim note. A fleeting thought is not an answer note. The architecture preserves this distinction with folder structure, lifecycle fields, and separate templates. Blurring it produces a vault where everything is "sort of processed" and nothing is reliably citable.

**4. The agent writes narrowly.**

Agents read broadly but write to controlled areas. Humans review every promotion to canonical zones. This is not a limitation — it is what keeps the vault trustworthy. A vault where agents write freely is a vault where the human doesn't know what they actually believe.

**5. Provenance everywhere.**

Every claim traces back to a citekey. Every agent action traces back to an audit log entry. Untraceable content is not knowledge — it is a liability that will fail when cited. The policy MCP, the SHA-256 audit chain, and the `sources:` field on claim notes all enforce this.

**6. Prefer incremental over full rewrites.**

The agent updates notes, not replaces them. History matters. Dry-run before auto-fix. A note that exists and is imperfect is almost always better than a note that was deleted and recreated. The `superseded_by` field exists precisely so claims can be updated without destroying provenance.

**7. Lint or decay.**

A knowledge base that is never linted slowly becomes unusable. The Linter is not optional maintenance — it is the mechanism that keeps the vault structurally trustworthy. Schema drift, broken links, stale enrichment, and orphaned notes compound silently; the Linter makes them visible.

**8. Code is a research output.**

Code artifacts belong in the vault and are traceable to the literature that motivated them. The false boundary between "notes" and "code" is an organizational failure mode. A figure-generation script with no provenance link to the claim it illustrates is as untrustworthy as an uncited claim.

**9. Simplest stack that solves the real bottleneck.**

Every tool in the stack addresses a specific friction point. Tools that don't address real friction are liabilities — they add maintenance overhead, failure modes, and cognitive load. The design is deliberately narrow: Zotero for references, Obsidian for the vault, Hermes for the agent layer. Extensions earn their place by removing friction, not adding features.

**10. The agent lives in the editor.**

Research, writing, and coding all access the same agent from within their respective editors via ACP. Context-switching to a separate chat window is a UX failure mode — the agent should be present where the work is happening, with the active note as implicit context. This is why the agent-client plugin, the command palette, and the VS Code workspace pattern exist.

---

## Related

- Why these principles led to a human-gated system: [architecture/why-human-gate.md](architecture/why-human-gate.md)
- Why specialist profiles rather than one generalist: [architecture/why-specialist-profiles.md](architecture/why-specialist-profiles.md)
- Why not autonomous: [architecture/why-not-autonomous.md](architecture/why-not-autonomous.md)
