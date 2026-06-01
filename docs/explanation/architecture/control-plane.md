# The control plane

The board defines what state a card is in. The policy MCP defines where a worker may write. The control plane is the third concern: how a human request reaches Hermes in the first place. It has three thin layers:

```
Obsidian (Command Palette / ACP pane)  ──►  Hermes API  ──►  MCP servers  ──►  Hermes
              (UI)                         (port 8642)    (policy + tasks)   (worker)
```

Each layer has exactly one job. None of them owns business logic except the MCP servers.

| Layer | What it does | What it does not do |
| --- | --- | --- |
| **Command Palette / ACP pane** | The two human entry points inside Obsidian. The Command Palette reads frontmatter from the active note and POSTs a JSON payload to the Hermes API. The ACP pane provides a conversational interface to Hermes alongside the active note. | No database access. No policy evaluation. No task state changes. |
| **Hermes API** | Receives the POST and dispatches the operation — add a card, run a task, query the audit log — into the MCP-gated worker. Upstream Hermes, not custom Memoria code. | No persistent state. No business rules. |
| **MCP servers** | `policy_mcp` checks permissions, writes the audit log. `tasks_mcp` updates the board, records handoffs, dispatches to Hermes. | No UI. No direct vault writes outside their declared tool surface. |
| **Hermes** | Runs the actual skill, writes the vault note, returns a structured result. | No board management — reports completion through the tasks MCP. |

---

## Why thin layers

**Each layer is trivially replaceable.** The Command Palette and the `hermes` CLI are interchangeable front-ends over the same Hermes API and MCP layer. Swapping one for the other touches nothing in the policy or task logic.

**Failure isolation.** If the Obsidian plugin breaks, the same operations run from the CLI. If the API server is down, Hermes can still execute via the CLI and its own MCP client. No single layer's failure takes down the whole system.

**One source of truth per concern.** Policy is in the policy MCP; task state is in the tasks MCP — never in the palette glue, which holds no state. The principle: never put business logic in the palette or QuickAdd wiring. That glue should be thin enough to rebuild in an afternoon; behavior lives in the MCP servers and Hermes.

---

## Why the API is fail-closed

The Hermes API is the dispatch entry point with the largest blast radius if misconfigured — anything that reaches it can dispatch tasks and trigger writes. The design responds to this with two complementary constraints.

First, the API defaults to binding on loopback only (`127.0.0.1`). The local-only, local-mesh, and obsidian-sync deployment configurations never need to go beyond this — the network surface is unexposed by default. Non-loopback binding is an explicit opt-in, and it requires the auth token to be set before binding takes effect.

Second, authentication is required for every deployment without exception, including the default loopback bind. The vault side mirrors this: the obsidian-local-rest-api plugin requires its own `apiKey` whenever it is reachable beyond loopback.

The reason there is no "add the token later" path is that misconfiguration here is invisible — the system functions without tokens, but unexpected entries begin appearing in the audit log. A silent security failure is worse than a startup failure. The fail-closed posture makes the misconfiguration immediately visible.

---

## Why MCP servers are registered per profile, not globally

MCP servers are registered per profile. Each profile carries an `mcp.json` listing the servers that profile may talk to. Memoria registers three servers across all profiles — `obsidian` for vault read/write, `policy` for permission checking and audit logging, and `tasks` for board state — but not every profile gets every tool from every server.

The reason for per-profile registration rather than a global server list is the same reason for separate profiles at all: `tools.include` filters let each profile's surface be narrowed to what it actually needs. The Socratic profile gets the `obsidian` server but only its read-side tools. This is the mechanism that makes "Socratic cannot write" enforceable at the API level, not just at the prompt level.

For the per-profile permission matrices, see [reference/profiles.md](../../reference/profiles.md).

---

## Related

- Policy MCP (what the rules are): [reference/policy-mcp.md](../../reference/policy-mcp.md)
- Board state machine (the cards being dispatched): [kanban-board/README.md](../kanban-board/README.md)
- Human channels (which access paths reach the API): [architecture/human-channels.md](human-channels.md)
