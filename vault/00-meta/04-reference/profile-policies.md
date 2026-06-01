# Profile policies

Who can write where. Companion to the lane-override YAML files at `.memoria/lane-overrides/`.

## Folder × profile write access

| Folder | Ask (Socratic) | Map (Mapper) | Draft (Writer) | Check (Verifier) | Librarian | Coder | Linter |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `10-inbox/01-fleeting/` | — | — | — | — | ✓ | — | — |
| `10-inbox/02-answers/` | — | — | ✓ | — | — | — | — |
| `10-inbox/03-candidates/` | — | — | — | gap-candidate cards | ✓ | — | — |
| `20-sources/` | — | — | — | — | ✓ | — | — |
| `30-synthesis/01-claims/` | — | — | — | — | — | — | — |
| `30-synthesis/02-reference/` | — | — | dry-run | — | — | — | — |
| `30-synthesis/03-moc/` | — | — | — | — | — | — | — |
| `40-workbench/` | — | corpus-maps, gap-reports, comparative-briefs, cluster-maps | framing/ via counter-outline | verification/ | — | project notes | — |
| `40-workbench/*/04-drafts/` | — | — | ✓ | — | — | — | — |
| `40-workbench/*/06-code/` | — | — | — | — | — | ✓ | — |
| `40-workbench/*/03-canvas/` | — | — | argument mapping | — | — | — | — |
| `50-deliverables/` | — | — | export tasks | — | — | export tasks | — |
| `00-meta/02-logs/` | — | — | — | — | — | — | audit + session logs |

Legend: ✓ = full write; — = no write (denied by policy MCP); cell text = scoped write to specific subpaths.

## Key rules

- **Socratic is architecturally write-denied.** Lane policy `allow.write: []` — no writes anywhere, ever. Safe on any device.
- **Mapper is read-only across the vault.** Writes only to specific project-scratch paths (corpus-map, gap-report, comparative-briefs, cluster-maps).
- **Review-gated zones require human approval.** `30-synthesis/01-claims/`, `30-synthesis/02-reference/`, `30-synthesis/03-moc/`, and `50-deliverables/` are policy-MCP `dry_run` for every lane.
- **No lane writes canonical content directly.** Every promotion is synchronous with human attention.
- **Delete is universally human-only** and discouraged across the board. Prefer archive.

## How it's enforced

The **policy MCP** intercepts every vault write. Each lane has a YAML file at `.memoria/lane-overrides/<lane>.yaml` declaring `policy.allow`, `policy.deny`, and `policy.require`. The MCP returns one of four decisions per write: `allow`, `allow_with_log`, `deny`, or `dry_run`. Out-of-policy writes are blocked at the file-system level, not after the fact.

---

**For depth:** docs/reference/profiles.md#folder-permission-matrix — the authoritative matrix. docs/reference/policy.md — the runtime gate.
