---
topic: profiles
---

# Coder profile and the external coding agent

The Memoria Coder profile and external coding agents (Kilocode, Aider, Claude Code, Codex) operate as **parallel agents with a shared filesystem**. Hermes owns research and reference; the coding agent owns code. The `code-note` is the human-readable handoff between them.

This reference is the authoritative how-to. The summary in [profiles/README.md](../../explanation/profiles/README.md#coder--external-coding-agent) is the architectural framing; this document specifies the workspace patterns.

## The two-agent boundary

- The Coder profile scaffolds the `code-note` with vault context (motivating sources, project links, purpose).
- The external coding agent reads the vault as a second workspace folder (read-only via `external_directory`); it edits code in `40-workbench/*/06-code/`.
- The human reviews `code-note` updates and commits as a review gate.

No orchestration infrastructure required — the two agents coordinate through the markdown handoff, not through subprocess dispatch. This keeps the Coder profile narrow (scaffold + document) and lets the specialized coding tool do what it does best.

## Where to open the project in VS Code

The split between "code lives in the vault" and "code lives in its own repo" depends on the project's lifecycle.

### Small scripts and analysis code

Open the vault root in VS Code. The coding agent gets direct access to the paper notes and reference pages that motivated the code. Put the agent's instruction file (`CLAUDE.md`, `.kilocode/rules/`, `.cursorrules`, depending on tool) in `40-workbench/<project>/06-code/` so the agent's context starts there rather than at the vault root.

### Real projects with their own lifecycle

Give the project its own Git repo outside the vault, then open the project repo as the primary workspace folder and add the vault as a *read-only* second folder. The standard `.code-workspace` pattern:

```json
{
  "folders": [
    { "path": ".",                       "name": "scoping-pipeline" },
    { "path": "../../<your-vault>",      "name": "vault (context only)" }
  ],
  "settings": {
    "files.readonlyInclude": {
      "../../<your-vault>/**/*": true
    }
  }
}
```

The first folder is the project repo (where the agent reads and writes); the second is the vault (which the agent reads for context but should never modify). Replace `<your-vault>` with the actual folder name the human cloned the starter vault into. The `files.readonlyInclude` rule enforces the boundary at the editor level — even if the agent has write tools enabled, VS Code refuses the write.

### Rule of thumb

If the project has `requirements.txt`, `pyproject.toml`, `package.json`, or another dependency manifest, it gets its own repo. Single scripts or notebooks live inside the vault at `40-workbench/<project>/06-code/` and open with the vault root.

## The `code-note` always lives in the vault

The `code-note` markdown file lives in the vault at `40-workbench/<project>/06-code/<project>.md` regardless of where the actual code lives. When code is in an external repo, the code-note carries a `repo:` frontmatter field pointing at the repo path. This keeps provenance traceable from the vault even when the executable artifact is elsewhere.

See `00-meta/03-templates/code-note.md` (in the starter vault) for the frontmatter shape.

## The pattern generalizes: external rendering agents

The "Hermes-side scaffold + external agent execution + human review gate" pattern is not specific to code. The same shape works for visual artifacts (slide decks, posters, infographics) — Memoria treats the rendering tool as a *peer of the external coding agent*, not as a new orchestration layer.

The standard external rendering agent is **[open-design](https://github.com/nexu-io/open-design)** — self-hosted, agent-driven, MCP-integrated, supports Hermes as one of its 16 built-in agent CLIs. Open-design slots into the same architectural role as Claude Code, Codex, Aider, or Kilocode — but for visual artifacts instead of code.

### What changes vs the Coder ↔ coding-agent pattern

| Dimension | External coding agent | External rendering agent (open-design) |
| --- | --- | --- |
| Artifact type | Code (scripts, modules, repos) | Visual deliverables (decks, posters, infographics, web pages) |
| Hermes-side profile | Coder | Writer (renders from drafts) or Coder (renders from code-note specs) |
| Vault destination | `40-workbench/*/06-code/` for code-notes; external repos for real projects | `50-deliverables/<project>/` for finished artifacts |
| Shared filesystem read | Vault read-only via `external_directory` (existing pattern) | Same — open-design reads the vault for paper-notes, claim-notes, design-system.md |
| Shared filesystem write | `40-workbench/*/06-code/` only | `50-deliverables/<project>/` only |
| Handoff artifact | `code-note` markdown with `repo:` frontmatter | `deliverable` note with `export_path:`, `design_system:`, and `render_command:` frontmatter (see `00-meta/03-templates/deliverable.md` (in the starter vault)) |
| Design source | (none — code is its own spec) | [`00-meta/04-reference/design-system.md`](../../reference/templates/design-system.md) — the portable DESIGN.md that defines palette, typography, spacing, layout, etc. |
| Review gate | Human reviews `code-note` updates and commits | Human reviews the rendered artifact (HTML preview, PDF) and accepts |

### Why the boundary stays clean

The same architectural reason that keeps Memoria's Coder narrow applies here: open-design is good at rendering; Memoria is good at curating content. Mixing the two — having Memoria's Writer profile try to also do layout/typography/color, or having open-design try to also manage research provenance — produces a worse version of each. The split is:

- **Memoria owns content.** Drafts, claim notes, paper notes, verification reports, design-system.md.
- **Open-design owns rendering.** Reads Memoria's content + design-system.md as input, produces the polished artifact.
- **The human owns the gate.** Reviews the rendered artifact; accepts to `50-deliverables/` or rejects (with the standard [post-rejection paths](../../explanation/kanban-board/README.md#post-rejection-paths) — spawn a revision render with a different design system, or discard).

### Workspace pattern

Same shape as the coding-agent workspace. If open-design runs as a daemon on the same machine, give it read access to the vault and write access to `50-deliverables/<project>/`:

```json
{
  "folders": [
    { "path": "../../open-design",       "name": "open-design (daemon)" },
    { "path": "../../<your-vault>",      "name": "vault (context only)" }
  ],
  "settings": {
    "files.readonlyInclude": {
      "../../<your-vault>/**/*": true
    },
    "files.readonlyExclude": {
      "../../<your-vault>/50-deliverables/**/*": true
    }
  }
}
```

Replace `<your-vault>` with the actual folder name the human cloned the starter vault into (per [on-disk-layout.md](../../explanation/architecture/on-disk-layout.md#starter-vault-versioned-distributable), the vault root folder name is human-defined).

The vault is read-only by default; the `50-deliverables/` folder is the explicit write exception (the `readonlyExclude` flag overrides the broader `readonlyInclude`).

### The `deliverable` note as handoff artifact

Just as `code-note` is the human-readable handoff between Memoria and the coding agent, the `deliverable` note (`00-meta/03-templates/deliverable.md` (in the starter vault)) is the handoff between Memoria and open-design. The note carries:

- `export_path:` — vault-relative path to the rendered artifact (e.g., `50-deliverables/jitai-thesis/chapter-3-deck.pptx`)
- `related_draft:` — wikilink to the primary source draft
- `sources:` — additional wikilinks (claim notes, code notes) the deliverable derived from
- `design_system:` — which design system was used (e.g., `lab-jitai-2026`), referencing the design-system file at `00-meta/04-reference/`
- `render_command:` — the exact open-design command that produced the artifact (for reproducibility)

This keeps the deliverable traceable back into the vault even after it's been exported — a paper PDF in `50-deliverables/` can be traced to the claim notes whose content it presents, the paper notes those claims cite, and the design-system that styled it.

For deliverables built via Pandoc or manual export, `design_system:` and `render_command:` remain blank — they're open-design-specific fields. The other fields apply to any deliverable regardless of build pipeline.

### When NOT to use open-design

Memoria's existing **Pandoc export pipeline** ([workflows/README.md](../workflows/README.md)) handles body-text exports (Word, PDF, HTML) for journal submissions, manuscripts, and other text-first deliverables. The boundary is:

- **Pandoc**: body-text-dominant outputs. Long-form prose with citations. Bibliography-driven.
- **Open-design**: visually-dominant outputs. Slide decks, posters, infographics, landing pages. Design-system-driven.

A journal manuscript goes through Pandoc; a conference poster goes through open-design. A draft might use Pandoc for the body PDF and open-design for an accompanying slide deck. Both can coexist; what they shouldn't do is overlap on the same artifact type.

### AI image generation: gate it explicitly

Open-design's image generation capabilities (gpt-image-2, Seedance, HyperFrames) are powerful but raise reproducibility concerns for research outputs. **Default to disabled in Memoria contexts.** A research deliverable should use the design system's deterministic side (typography, layout, color, spacing) but render real figures, real diagrams, real photos. AI-generated illustrations belong only in contexts where the human has explicitly opted in (e.g., a popular-science blog post, a teaching slide). The design-system template's anti-patterns section names this explicitly — see [obsidian-ui/design-system.md](../../reference/templates/design-system.md).
