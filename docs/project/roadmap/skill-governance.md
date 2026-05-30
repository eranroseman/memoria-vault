---
topic: roadmap
---

# Skill governance and lifecycle

> **Status: deferred — maybe later if needed.** This entire feature (state machine, per-skill governance notes in `00-meta/07-skills/`, the `skill-lifecycle` dashboard, the 7-step onboarding checklist) is not part of the active design. Adding a skill today means editing the relevant lane-override file's `policy.allow.skills` list and dropping the SKILL.md into the right profile's `skills/` folder — that's the runtime mechanism, and it works without the governance overlay. The design notes below are preserved for the case where the system accumulates enough skills and passthrough-graduations that the lifecycle overlay becomes worth standing up. See [future-directions.md §"Skill governance"](future-directions.md#skill-governance) for the deferral context.

The expansion-threshold rule for *skills* is its own practice. Skills are first-class objects with their own state machine, parallel to the card lifecycle on the board. Adding a skill — whether a K-Dense wrapper, a `<service>-fetch` skill graduating from `rest-passthrough`, or a new in-vault skill — passes through these states before it can claim work.

## Skill states

```text
intake ──► proposed ──► scaffolded ──► testing ──► needs-review ──► approved ──► active ──► archived
```

| State | Meaning |
| --- | --- |
| `intake` | A skill has been requested. No folder, no code, no contract. |
| `proposed` | A purpose, lane, and rough contract are written down. |
| `scaffolded` | The skill folder exists with `SKILL.md` and a runnable stub. |
| `testing` | Validated against a minimal example and a failure case. |
| `needs-review` | Permission mapping is drafted; awaiting human approval. |
| `approved` | Lane-override files updated; the policy MCP recognizes it. |
| `active` | In use. Tracked in the skill registry; included in audit log decisions. |
| `archived` | Retired; removed from lane-override `allow` lists but folder retained for history. |

## Skill registry

One markdown note per active skill, kept in `00-meta/07-skills/`. The note carries the authoritative metadata that the [`skill-lifecycle` dashboard](../../explanation/dashboards/skill-lifecycle.md) queries.

```yaml
---
type: skill-note
skill_name: paper-lookup
lane: library
stage: active
networked: true
owner: memoria-librarian
created_at: 2026-01-15T10:00:00Z
updated_at: 2026-05-25T14:00:00Z
next_action: ""
tags: [hermes, skill, k-dense]
---
```

`skill-note` is not in the 15 note types listed in [vault/README.md](../../explanation/vault/README.md) — it's a meta-note in `00-meta/`, the same family as registry and config notes. Don't link skill notes from the synthesis graph.

## Skill onboarding checklist

Promoting a skill from `intake` to `active` follows this 7-step checklist. Each step gates the next state.

1. **Define** (`intake → proposed`). One-sentence purpose. Primary lane. Networked vs. local. Decide whether it could be served by `rest-passthrough` first.
2. **Scaffold** (`proposed → scaffolded`). Create `~/.hermes/skills/<skill-name>/` with the standard subfolder set: `SKILL.md` (required), `scripts/` (executables), `references/` (contracts and docs the skill depends on), `templates/` (example payloads and prompts), `assets/` (static files and test fixtures). Subfolders may be empty initially but the structure is uniform across all skills.
3. **Write `SKILL.md`**. YAML frontmatter, when-to-use, inputs, procedure, output contract, pitfalls, references.
4. **Validate** (`scaffolded → testing`). Run a minimal happy-path example. Run a failure case. Confirm timeouts and that secrets are read from env vars, not hardcoded.
5. **Register permissions** (`testing → needs-review`). Add to the appropriate lane-override file's `policy.allow.skills` list. Add to the lane permissions matrix in [profiles/README.md](../../reference/profile-matrices.md#lane-permissions-matrix).
6. **Document** (`needs-review → approved`). Create the skill-note in `00-meta/07-skills/`. Add an example invocation. Note any endpoint or schema references.
7. **Activate** (`approved → active`). Run once for real; set the skill-note's `stage: active`. Schedule a 4-week review checkpoint.

Retirement (`active → archived`) follows the reverse: remove from `policy.allow.skills`, set `stage: archived`, but keep the skill-note and the folder for history.

## Passthrough-to-dedicated-skill graduation

A skill earns promotion from `rest-passthrough` to its own dedicated skill when:

- The same endpoint has been called > 5 times across distinct tasks, **or**
- The endpoint has a non-trivial auth flow (OAuth, signed requests) that adds friction every call, **or**
- The endpoint's response shape needs normalization that the passthrough's generic output can't carry cleanly.

Below those thresholds, stay on the passthrough.

## Why this lives in the roadmap

Skill governance is operational bookkeeping that matters most once the system is past MVS and accumulating tooling. A fresh install has a fixed set of K-Dense skills and the generic passthrough — no governance needed. The state machine and registry become load-bearing only when passthrough-graduations, retirements, and lane-permission changes start happening regularly. Treat the governance system as something to stand up around Phase 6, not Phase 1.
