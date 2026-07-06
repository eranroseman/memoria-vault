---
title: Engine read API
parent: Agents and control
grand_parent: Reference
nav_order: 22
---

# Engine read API

`memoria_vault.engine.api` is the host-neutral read/write boundary used by the
CLI and future transports. It returns verdict-tagged payloads with
`api_version: engine-read-api.v1` and view data in `view-spec.v1`.

Alpha.17 adds project WRITE reads and wrappers:

| Function | Contract |
| --- | --- |
| `read_slice(workspace, project_path)` | Reads `outline.md`, checked members, and computed in-slice links. |
| `read_outline(workspace, project_path)` | Alias for `read_slice`. |
| `read_draft(workspace, project_path)` | Reads `draft.md`, evidence markers, and derived evidence rows. |
| `compose_draft(...)` | Queues `compose-project-draft`. |
| `verify_draft(...)` | Queues `verify-project-draft`. |
| `promote_draft_passage(...)` | Queues `promote-draft-passage`. |
| `read_exploration(...)` | Reads the relevance-independent exploration channel. |

Adapters should call this API instead of opening SQLite or files directly.
