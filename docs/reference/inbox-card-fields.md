---
title: Inbox card fields
parent: Reference
---

# Inbox card fields

Schema fields for Inbox cards under `inbox/`. The source of truth is `src/.memoria/schemas/types/`; this page is the lookup view for the PI-facing card shapes. The daily **Needs me** view embeds only proposed `candidate`, `gap`, and `work-prompt` cards; `flag` and `alert` cards are still Inbox cards, but they are worked from Maintenance drift views unless they raise a work prompt.

## Shared card fields

| Field | Kind | Applies to | Meaning |
| --- | --- | --- | --- |
| `type` | `literal` | All cards | Pins the note to its schema. |
| `lifecycle` | `enum` | All cards | `proposed`, `current`, or `archived`. |
| `title` | `str` | All cards | Human-readable card title. |
| `raised_by` | `str` | Optional on all cards | Profile, operation, or process that raised the item. |
| `loudness` | `enum` | Optional on all cards | `quiet`, `notice`, `alert`, or `block`. `quiet`/`notice` stay pull-only; `alert`/`block` create a Telegram push record when written through the shared card writer; open `block` cards pause delegation and review-gated promotion until resolved. |
| `created` | `date` | Optional on all cards | Creation date. |

## Proposal cards

`candidate` and `gap` cards carry an argument, not a verdict.

| Field | Kind | Required | Meaning |
| --- | --- | --- | --- |
| `action` | `str` | Yes | What the PI would be accepting. |
| `argument_for` | `str` | Yes | The agent's case for the action. |
| `argument_against` | `str` | Yes | The agent's strongest honest self-rebuttal. |
| `what_tipped_it` | `str` | Yes | Why the item was raised anyway. |
| `certainty` | `enum` | Yes | `confident`, `likely`, or `unsure`. |
| `citekey` | `str` | Optional on `candidate` | Bibliographic item the card points at. |
| `url` | `str` | Optional on `candidate` | External source URL. |

## Verification cards

`flag` and `alert` cards lead with the finding because the verdict is not implied by the card existing.

| Field | Kind | Required | Meaning |
| --- | --- | --- | --- |
| `finding` | `str` | Yes | What the check found. |
| `agent_recommendation` | `enum` | Required on `flag`; optional on `alert` | `inconclusive`, `issues-found`, or `clean`. |
| `target` | `str` | Required-any on `flag`; optional on `alert` | Vault path or artifact the card points at. |
| `citekey` | `str` | Required-any on `flag` | Bibliographic item the card points at. |

## Work prompts

`work-prompt` cards tell the PI what completed, blocked, or needs attention. They carry no recommendation field. A useful prompt explains why it exists, what to do next, where to inspect the material, and how to keep or dismiss it.

| Field | Kind | Required | Meaning |
| --- | --- | --- | --- |
| `action` | `str` | Yes | What the PI should do. |
| `what_happened` | `str` | Yes | What finished or triggered the prompt. |
| `prompt_kind` | enum | Optional | `review`, `worklist`, `nudge`, or `blocked`; a quick hint for the surface that raised the prompt. |
| `target` | `str` | Required-any | Output path or artifact to review. |
| `task_id` | `str` | Required-any | Board card the prompt is about. |
| `lane` | `str` | Optional | Lane that completed the work. |

## Related

- The universal field grammar: [Frontmatter fields](frontmatter.md)
- The board state machine: [Kanban board reference](kanban-board.md)
- Why these shapes exist: [The honesty card](../explanation/kanban-board/card-schema.md)
