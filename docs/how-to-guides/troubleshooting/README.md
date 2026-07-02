---
title: Troubleshooting
parent: How-to guides
nav_order: 9
has_children: true
permalink: /how-to-guides/troubleshooting/
---

# Troubleshooting

Start from the symptom you're seeing. Each guide takes one failure mode from symptom → diagnosis → fix — find the row that matches what's wrong and follow it through.

| Symptom                                                           | Guide                                                            |
| ----------------------------------------------------------------- | ---------------------------------------------------------------- |
| Optional UI adapter is down and you still need to work            | [Safe mode](safe-mode.md)                                        |
| A card won't advance on the Kanban board                          | [Fix a stuck card](fix-stuck-card.md)                            |
| YAML parse error; a note is missing from Dataview queries         | [Fix broken frontmatter](fix-broken-frontmatter.md)              |
| An agent's write didn't land — denied, or never reached the gate  | [Diagnose a denied or blocked write](diagnose-a-denied-write.md) |
| Removed profile package reappeared                                | [Fix profile drift](fix-profile-drift.md)                        |
| Enrichment is empty after ingest; classification never applied    | Check provider config, then rerun source metadata checks |
| A filtered query returns nothing though the notes are valid       | [Fix missing query results](fix-missing-query-results.md)        |

## When several failures appear at once

Work highest-impact failures first:

1. Address `CRITICAL` issues before anything else: tamper detection and security failures can invalidate later diagnosis.
2. Address silent `HIGH` issues next: failures that look like "nothing to do" waste time and compound quietly.
3. Address visible `HIGH` breakage after silent failures.
4. Batch `MEDIUM` issues into the weekly review ritual.
5. Batch `LOW` issues monthly unless they block current work.

The severity definitions and full failure table live in [Failure modes](../../reference/failure-modes.md).
