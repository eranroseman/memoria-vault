---
topic: architecture
---

# Control plane: how a human request reaches Hermes

The board defines *what state* a card is in. The policy MCP defines *where* a worker may write. But the system also needs a daily-use surface for the human to *trigger* discrete actions — queue a task, run an active card, audit a write, push registry state into a note. The control plane has three thin layers between the human and Hermes:

```text
Obsidian (Command Palette / Agent Client pane)  ──►  Hermes API  ──►  MCP servers  ──►  Hermes
                    (UI)                            (hermes gateway)  (policy + tasks)   (worker)
```

Each layer has exactly one job. None of them owns business logic except the MCP servers.

| Layer | What it does | What it doesn't do |
| --- | --- | --- |
| **Command Palette / Agent Client pane** (Obsidian) | The two human entry points inside Obsidian. The Command Palette reads frontmatter from the active note and POSTs a small JSON payload to the Hermes API. The **Agent Client pane (ACP)** — the editor-level agent interaction surface — provides a conversational interface to Hermes alongside the active note. Both show a status notice on completion. | No database access. No policy evaluation. No task state changes. |
| **Hermes API** | Hermes's built-in HTTP API (`hermes gateway`, `127.0.0.1:8642` — command and default port are per upstream Hermes docs; verify current values at hermes-agent.nousresearch.com/docs); receives the POST and triggers the operation — add a card, run a task, query the audit log — dispatching into the MCP-gated worker. Upstream Hermes, not custom Memoria code. | No persistent state. No business rules. |
| **MCP servers** | `policy_mcp` checks permissions, writes the audit log. `tasks_mcp` updates the board, records handoffs, dispatches to Hermes. | No UI. No direct vault writes outside their declared tool surface. |
| **Hermes** | Runs the actual skill, writes the vault note, returns a structured result. | No board management — reports completion through the task MCP. |

## Why thin layers

- **Each layer is trivially replaceable.** The Command Palette and the `hermes` CLI are interchangeable front-ends over the same Hermes API and MCP layer; swapping one for the other doesn't touch the policy or task logic.
- **Failure isolation.** If the plugin breaks, the same operations run from the CLI. If the API server is down, Hermes can still execute via the CLI and its own MCP client.
- **One source of truth per concern.** Policy is in the policy MCP; task state is in the tasks MCP — never in the palette glue, which holds no state.

The principle that makes this work: **never put business logic in the palette / QuickAdd glue.** That glue should be thin enough to rebuild in an afternoon; behavior lives in the MCP servers and Hermes, not the UI.

## Fail-closed startup

The Hermes API is the dispatch entry point — and the one with the largest blast radius if misconfigured, since anything that can reach it can dispatch tasks and trigger writes. Two rules at startup:

- **Default to loopback only.** Bind to `127.0.0.1` unless explicitly configured otherwise. The vast majority of deployments (the local-only, local-mesh, and obsidian-sync options; see [roadmap/deployment-options.md](../../project/roadmap/deployment-options.md)) never need anything else. Under the always-on option and the micro-always-on variant of local-mesh (where the laptop reaches the desktop's Hermes via Tailscale-bridged SSH or API), the binding may need to extend to a network interface — but only with the API's auth token set.
- **Always authenticate; never expose a non-loopback bind unprotected.** Hermes requires `API_SERVER_KEY` for **every** deployment, including the default loopback bind — so the auth token is always set, not just when going off-host. Binding to a non-loopback interface additionally requires explicitly setting `API_SERVER_HOST`; do that only with the key in place. Failing closed at startup is what makes the always-on option (VPS-side API reachable from the desktop) viable without a long-running unauthenticated endpoint. The vault side mirrors this: the obsidian-local-rest-api plugin requires its own `apiKey` whenever it is reachable beyond loopback.

The rule is binary: every HTTP surface runs authenticated, and a non-loopback bind is opt-in. There is no "I'll add the token later" — a misconfiguration here is invisible until someone notices traffic in the audit log they didn't expect.

## MCP server registration

MCP servers are registered **per profile**, following the standard Hermes pattern. Each profile carries an `mcp.json` at `~/.hermes/profiles/memoria-<name>/mcp.json` listing the servers that profile may talk to. The same information can also live in `config.yaml` under `mcp_servers:` — the two shapes are interchangeable and Hermes reads both. Under direct profile management, both files are hand-authored in `.memoria/profiles/memoria-<name>/` and copied verbatim by the installer (with `{{VAULT_PATH}}` substituted in `mcp.json`).

The shape, per server: `command` or `url`, `env`, `enabled`, `timeout`, and `tools.include` / `tools.exclude` filters. Memoria registers three servers across the relevant profiles:

- **`obsidian`** — vault read/write via the Obsidian Local REST API. All profiles.
- **`policy`** — the Memoria policy MCP (described above), reading lane-overrides from `.memoria/lane-overrides/`. All profiles.
- **`tasks`** — the task registry MCP that fronts the Hermes Kanban. All profiles.

Not every profile gets every tool from every server — `tools.include` filters narrow the surface per profile (e.g., the Socratic profile gets the `obsidian` server but only the read-side tools). The exact config file shape follows the [official Hermes MCP config reference](https://hermes-agent.nousresearch.com/docs/reference/mcp-config-reference) — we don't redefine it here.

## Related

- Policy MCP (the rules being enforced): [architecture/policy-mcp.md](../../reference/architecture/policy-mcp.md)
- Board state machine (the cards being dispatched): [kanban-board/README.md](../kanban-board/README.md)
- Deployment options (when non-loopback binding becomes relevant): [roadmap/deployment-options.md](../../project/roadmap/deployment-options.md)
