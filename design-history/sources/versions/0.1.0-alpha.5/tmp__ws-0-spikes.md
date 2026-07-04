# WS-0 spike verdicts — alpha.5 Project gate

Date: 2026-06-16

Issue: [#576](https://github.com/eranroseman/memoria-vault/issues/576)

## Verdicts

| Spike | Verdict | Consequence |
| --- | --- | --- |
| §D3 `registerBasesView` | **Usable.** The published `obsidian@1.13.1` TypeScript API exposes `Plugin#registerBasesView(viewId, registration): boolean`, plus `BasesView`, `BasesViewRegistration`, `BasesViewFactory`, `BasesQueryResult`, and `QueryController`. | WS-E can build the project dashboard as a custom Bases view. Pin the plugin build/test surface to `obsidian@1.13.1` or newer and keep a compile check around the custom view. |
| §13.1 maturity threshold | **Conservative default:** load-bearing project signals require a connected thesis-rooted argument component with at least **5 addressed relations**, including at least **1 `supports`** and **1 `contradicts`** edge. Below that, impact/gap/saturation output remains advisory and visibly low-confidence. | WS-A records this in the Project-gate ADR; WS-C/WS-D implement the threshold as the default. Raising confidence by lowering this threshold is a safety change. |
| §13.4 materialization shape | **Single generated index-note by default.** Because §D3 is usable, pay the custom-view cost once and avoid per-note write amplification. Use per-note stamps only as a fallback if the custom Bases view is cut. | WS-C writes one generated Project gate index note with `computed_at`, `stale`, and per-note derived values; WS-E reads it through the custom Bases view. |

## Evidence

Commands run in the WS-0 worktree:

```bash
npm view obsidian version dist-tags.latest
npm view obsidian@1.13.1 dist.tarball
npm pack obsidian@1.13.1
tar -xOf obsidian-1.13.1.tgz package/obsidian.d.ts | rg -n "registerBasesView|BasesView|BasesViewRegistration|BasesQueryResult|QueryController"
```

Observed package/version:

```text
version = '1.13.1'
dist-tags.latest = '1.13.1'
```

Observed API declarations in `obsidian.d.ts`:

```text
BasesView
BasesViewRegistration
BasesViewFactory
BasesQueryResult
QueryController
Plugin#registerBasesView(viewId: string, registration: BasesViewRegistration): boolean
```

The downloaded tarball was removed after inspection and is not part of the repo.

## Notes for downstream workstreams

- WS-E should create the custom view as a small, version-pinned pilot first: render a trivial `BasesView` from `BasesQueryResult` before adding graph-specific UI.
- WS-C should not stamp derived values onto every claim/thesis note unless WS-E drops the custom view. The default cache is a generated index note.
- The dashboard must show `computed_at` and stale/low-confidence state; Bases does not make graph computations live.
