---
name: draft-outline-argument
description: "Produce outline OPTIONS for an argument — two or three genuinely different structures over the same claim set, each with its strongest counter-argument stated, into project scratch. The counter-outline discipline: an outline that cannot name what would defeat it is not ready to draft. Use when a draft card asks for structure before prose."
version: 1.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Drafting, Outlining, Argumentation]
    related_skills: [qmd, obsidian]
  memoria:
    skill_id: "draft-outline-argument"
    profile: memoria-writer
    lane: draft
    mcp_tools:
      - obsidian.get_file_contents
      - obsidian.list_files
      - obsidian.search
      - obsidian.put_content
      - obsidian.append_content
      - policy.check_permission
      - policy.complete_write
    write_scope: ["projects/"]
    outputs: [source]
---

# draft-outline-argument

*(legacy name: `counter-outline`; load on disk as `draft-outline-argument`.)*

Structure before prose. Given a thesis (or a question) and a claim set, produce **two
or three genuinely different outline options** — not one outline with cosmetic
variants — each annotated with the strongest honest case *against* its structure. The
PI picks the spine; `draft-write-section` fills it.

## Inputs

| Input | Required | Meaning |
| --- | --- | --- |
| thesis / question | yes | What the piece argues or asks (from the handoff payload). |
| claim set | yes | The claim notes / citekeys available to carry the argument. |
| venue / length | no | Shapes section count and depth. |

## Procedure

1. **Read the claim set** (via the `obsidian` skill) and sort claims by role:
   load-bearing (the argument fails without them) vs supporting vs color. Note each
   load-bearing claim's `maturity` — a spine resting on `seedling` claims is a risk the
   PI must see.
2. **Build 2–3 distinct structures** (e.g. problem-first vs evidence-first vs
   tension-first). For each section node: the point it makes, the claims that carry it
   (`[@citekey]` / `[[claim links]]`), and any hole (a node no claim can carry —
   marked, never papered over).
3. **Counter-outline each option**: the strongest honest objection to *that structure*
   — the buried assumption, the claim ordering that begs the question, the section a
   hostile reviewer attacks first.
4. **Write — gated.** One file:
   `projects/<project>/outlines/<slug>-options.md`, frontmatter
   `drafted_by: memoria-writer`, `lifecycle: proposed`, `sources:` listing all citekeys
   used. Never write outside `projects/`.

## Output contract

One outline-options note: 2–3 labeled options, each with section nodes →
claim bindings → holes → its counter-outline paragraph; a closing comparison table
(option · load-bearing claims · weakest node). Scoring the options is
`draft-score-outline`'s job — present, don't rank, unless the handoff asks for both.

## Honesty rules

- Options must differ in structure, not phrasing — if you cannot find a second honest
  structure, deliver one option and say why, rather than inventing a strawman twin.
- Counter-arguments are genuine: name the objection a skeptical reader would actually
  raise, citing the contradicting claim note where one exists.
- A node without a carrying claim is a visible hole (`[!todo] no claim carries this`),
  feeding the gap workflow — never an improvised bridge sentence.
- No new claims, no edits outside project scratch, no self-scoring as "the best
  option" — the PI decides.
