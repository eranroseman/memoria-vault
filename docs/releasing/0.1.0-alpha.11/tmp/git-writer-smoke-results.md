# Git-backed trusted-writer smoke results

Date: 2026-06-28

Sandbox: `/home/eranr/Memoria-test/.memoria/tmp/alpha11-git-writer-smoke`

Verdict: **PASS**.

| Check | Status | Evidence |
| --- | --- | --- |
| trusted write commit couples file and journal | pass | commit=d0fbf38; files=['.memoria/journal/events.jsonl', 'knowledge/digest-alpha.md'] |
| failed write is quarantined and hidden | pass | commit=062f58e; visible=[] |
| PI edit is backfilled as traced commit | pass | commit=507d106; files=['.memoria/journal/events.jsonl', 'knowledge/note-human-alpha.md'] |
| foreign untraced commit is quarantined by scan | pass | foreign_commit=63fd5d8; quarantine_commit=afce1c5 |
| cascade rollback is inverse traced commit | pass | commit=77db914; rollback={'rolled_back': ['knowledge/digest-alpha', 'knowledge/note-machine-alpha'], 'flagged': ['knowledge/note-human-alpha']}; statuses={digest:rolled_back, machine:rolled_back, human:flagged} |
| smoke repo ends clean | pass | commits=8; initial=932de35; machine_commit=9ebece0 |

## Notes

This is a disposable smoke in `~/Memoria-test`; it is not production alpha.11
code. It proves the core writer contract can be represented as real git history:
trusted writes commit file + journal together, failed writes quarantine, foreign
commits are detected and quarantined, and rollback is an inverse traced commit.
