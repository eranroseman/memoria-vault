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

## Fail-closed startup

The Hermes API is the dispatch entry point with the largest blast radius if misconfigured — anything that reaches it can dispatch tasks and trigger writes. Two startup rules:

**Default to loopback only.** The API binds to `127.0.0.1` unless explicitly configured otherwise. The local-only, local-mesh, and obsidian-sync deployment options never need anything else. The always-on option may extend to a network interface — but only with the API's auth token set.

**Always authenticate.** Hermes requires `API_SERVER_KEY` for every deployment, including the default loopback bind. A non-loopback bind additionally requires `API_SERVER_HOST` to be set explicitly. The vault side mirrors this: the obsidian-local-rest-api plugin requires its own `apiKey` whenever it is reachable beyond loopback.

The rule is binary: every HTTP surface runs authenticated, and non-loopback binding is opt-in. There is no "I'll add the token later" — a misconfiguration here is invisible until unexpected entries appear in the audit log.

---

## MCP server registration

MCP servers are registered per profile. Each profile carries an `mcp.json` at `~/.hermes/profiles/memoria-<name>/mcp.json` listing the servers that profile may talk to. Memoria registers three servers across all profiles:

- **`obsidian`** — vault read/write via the Obsidian Local REST API
- **`policy`** — the Memoria policy MCP, reading lane-overrides from `.memoria/lane-overrides/`
- **`tasks`** — the task registry MCP fronting the Hermes Kanban

Not every profile gets every tool from every server — `tools.include` filters narrow the surface per profile. The Socratic profile gets the `obsidian` server but only its read-side tools, for example.

---

## Related

- Policy MCP (what the rules are): [reference/architecture/policy-mcp.md](../../reference/architecture/policy-mcp.md)
- Board state machine (the cards being dispatched): [kanban-board/README.md](../kanban-board/README.md)
- Human channels (which access paths reach the API): [architecture/human-channels.md](human-channels.md)
