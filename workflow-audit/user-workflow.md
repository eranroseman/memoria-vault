# User workflow — agent, editor, Memoria plugin — 2026-07-09

The target day-to-day experience across the three components, under the
decided architecture (`roadmap.md` item 12 reactive substrate + Tier 3
surface strategy; `architecture-review.md` write topology). Division of
labor: **the editor is where judgment lives, the plugin is how the vault
looks back at you, the agent is the voice and hands.** Everything all
three do funnels through the same envelope and queue; the plugin and
agent never write files directly; direct PI edits are observed and
revalidated.

## Roles

| Component | Job | Never does |
|---|---|---|
| **Editor** (Obsidian first, VS Code probable second) | Reading, writing, thinking — notes, drafts, outlines, steering.md. The only surface the PI must touch | Gating, chatting |
| **Memoria plugin** | Ambient layer: status badges, inbox count, question/finding cards, one-click dispositions, context sharing, editor-event push | Conversation, inference, direct file writes |
| **Agent** (user's choice via MCP + shipped Memoria skill) | Fluent layer: converses from engine-authored payloads, runs operations, triages with the PI | Deciding anything — every disposition it files is the PI's, journaled with `actor=agent` |
| *Daemon (invisible fourth)* | Watches, validates, indexes, checks, re-promotes (Tier A/B/C chains) | Anything requiring judgment |

## Morning: triage

Overnight, Tier C ran gaps, tensions, digestion, and the integrity sweep.
The plugin badge shows the inbox count. Quick items are handled in the
plugin directly (one-click reject/defer on cards). Substantive items go to
the agent: "walk me through the inbox" — it reads `attention.list`, shows
a contradiction card's both claims with their evidence, the PI decides,
the agent files the disposition. The journal records the decision as the
PI's, filed by the agent.

## Capturing and reading a source

Paste a DOI into the agent chat → capture → enrichment; the plugin shows
the work land in the Library. The agent offers the interview — its
questions are engine-authored grounding interrogation generated for this
source, not improvisation. Answers become journaled interview turns,
sealed into digest compilation. The digest lands as a file in the editor,
badge already checked.

## Thinking (the core loop)

Write a claim note — raw, ungated. On save, the Tier-A chain: badge flips
to unchecked, template validates (a broken frontmatter field surfaces as
an inline card immediately, not on some later read), index updates, a
`[[supports::…]]` link becomes an edge candidate for confirmation. A
second later the badge is checked again; search and `ask` already reflect
the note. The vault keeps up with typing instead of discovering work when
something reads it.

## Writing (project → deliverable)

Edit the thesis in the project file. Ask the agent "where does the
argument stand?" — trace + gaps, spoken: stage, saturation, the
under-warranted claims, next actions; the plugin shows the same argument
health as a project-view panel. Slice → `outline.md` in the editor,
reordered by hand (the outline is the PI's). Compose → `draft.md`. Verify
findings arrive as evidence cards, each needing accept/reject (plugin or
agent). Export refuses until all are dispositioned — the vault holding the
PI's own standard.

## Two signature moments

- **Situated questioning:** select a paragraph, ask the agent "what
  contradicts this?" It calls `context.read`, knows which claim is on
  screen, queries the graph, answers with grounded items — files nothing
  unless told. CopilotKit's shared-state idea without an embedded copilot.
- **A claim falls:** one "decided wrong" disposition → the typed blast
  radius returns ("three notes lost their only grounds; the thesis
  regressed to developing; two warrants now unstated"); downstream badges
  flip in the editor; the agent walks through what to repair first. The
  central operation as a lived experience.

## What's real when

- **Today:** the agent workflow substantially works (MCP + `operation.run`
  + `requests.get` carry the whole loop); the plugin shows counts;
  statuses update on read.
- **After the reactive substrate (roadmap item 12):** live badges, on-save
  validation, the morning inbox actually populated overnight.
- **After Tier 3 (items 14–15):** question cards, the argument-health
  panel, situated context.

Every element above traces to a numbered roadmap item; this narrative is
the end state, not a new commitment. API gaps between here and there are
listed in roadmap item 12 (five additive surface-contract actions + one
SSE/long-poll events endpoint).
