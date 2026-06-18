---
title: alpha.7 docs audit handoff
---

# alpha.7 docs audit handoff

Status: carried-forward audit notes for alpha.8 planning. Generated after the alpha.7
QA/docs cleanup pass.

## Scope scanned

- alpha.7 implementation/docs alignment: installer model overlays, profile configs,
  gate dashboards, Homepage target, Portals/workspace model, release plans, and test
  plans.
- Release scratch under `docs/releasing/*/tmp/`.
- Diataxis audit of 179 files under `docs/explanation`, `docs/how-to-guides`,
  `docs/tutorials`, and `docs/reference`, split across four subagents.
- Fresh repo text scans for stale `Desk` / `Library workspace` / `Studio` workspace
  language and stale `home.md` status-strip language.

## Fixed in this pass

| Issue | Files changed | Reasoning |
| --- | --- | --- |
| Linux/WSL test profiles could not run against a local OpenAI-compatible Ollama model without hand edits. | `scripts/install.sh`, `scripts/install.ps1`, `src/.memoria/profiles/memoria-*/config.yaml`, `tests/test_profiles.py`, `tests/test_installer_skeleton.py`, `docs/reference/installer.md`, `docs/how-to-guides/setup/set-up-hermes.md`, `docs/how-to-guides/hermes-agent/configuration.md`, `docs/reference/hermes-cli.md`, `docs/reference/profiles.md`, `docs/testing/plans/hermes-cli-test-plan.md`, `docs/testing/plans/installer-test-plan.md` | Production keeps Kilo Code tier defaults; `MEMORIA_ENV=test` renders all profiles to local Ollama defaults with override env vars. The installer now refreshes deployed profile `config.yaml` after `hermes profile install`, because Hermes preserves user-owned config. |
| Current docs still described ADR-68 workspace switching as the active UI model. | `docs/reference/dashboards.md`, `docs/reference/on-disk-layout.md`, `docs/reference/obsidian-workspaces.md` already aligned and now used as source of truth; updated affected how-to, tutorial, explanation, reference, testing, and release-plan files. | ADR-81 makes `src/gates/{inbox,library,knowledge,project}.md` the primary navigation model. Workspaces now mean one reset layout named `Memoria`, not Desk/Library/Studio mode switching. |
| Shipped legacy dashboard notes contradicted ADR-81. | Removed `src/system/dashboards/desk.md`, `src/system/dashboards/library.md`, `src/system/dashboards/studio.md`. | These were old gate pages under `system/dashboards/`; the shipped gates now live under `src/gates/`. |
| Homepage docs described `home.md` as the launch surface with a status strip. | `docs/explanation/obsidian/home.md`, `docs/how-to-guides/using-obsidian/use-the-vault-homepage.md`, `docs/how-to-guides/setup/set-up-obsidian.md`, `docs/reference/dashboards.md`, `docs/reference/on-disk-layout.md`, `docs/reference/system-artifacts.md`, `docs/reference/obsidian-callouts.md`, `docs/adr/13-homepage-front-door.md`, dashboard explanation pages. | `src/.obsidian/plugins/homepage/data.json` opens `gates/inbox`; `src/home.md` is only a fallback link note. |
| Status-line docs described an unshipped widget as current behavior. | `docs/reference/obsidian-status-line.md`, `docs/explanation/obsidian/the-status-line.md`. | No status-line widget ships in alpha.7. The pages now mark it as a deferred ambient-indicator contract and name Inbox as the shipped glance. |
| Older release `tmp/` scratch remained after completed checkpoints. | Pruned alpha.4-alpha.7 `tmp/`; moved unresolved scratch to alpha.8 `tmp/`; updated release READMEs/plans. | Implemented scratch was captured in ADRs/current docs. Unimplemented detail belongs to the next checkpoint handoff, not closed release folders. |

## Remaining implementation documentation gaps

| Issue | Relevant files | Reasoning | Recommendation |
| --- | --- | --- | --- |
| Deferred how-to pages still live in the how-to tree. | `docs/how-to-guides/setup/set-up-vps.md`, `docs/how-to-guides/setup/set-up-messaging.md`, `docs/how-to-guides/setup/README.md`, `docs/how-to-guides/README.md` | `set-up-vps.md` is explicitly deferred/unvalidated but still reads like a procedure. `set-up-messaging.md` mixes shipped outbound alert setup with deferred inbound gateway behavior. This is not a current alpha.7 contradiction because both pages carry caveats, but it weakens how-to trust. | Split shipped procedures from deferred designs. Move unvalidated topology/inbound-gateway material to explanation or ADR/deferred release scratch; keep only runnable setup in how-to indexes. |
| The profile configuration guide is broader than a single task. | `docs/how-to-guides/hermes-agent/configuration.md`, `docs/reference/profiles.md`, `docs/reference/installer.md` | The guide now documents model overlay operations correctly, but it still mixes task steps, model routing reference, skills, API keys, and lane permissions. | Keep task procedures in how-to; move stable lookup tables to reference if the page grows further. |
| Controlled vocabulary reference is thin. | `docs/reference/vocabulary.md`, `src/system/vocabulary.md`, `src/.memoria/schemas/*.yaml` | The reference page points at the vocabulary but does not provide a complete reader-facing table of current allowed values. | Generate or maintain a concise allowed-values table from the shipped vocabulary/schema sources. |
| Status-line design is deferred but still present in current docs. | `docs/reference/obsidian-status-line.md`, `docs/explanation/obsidian/the-status-line.md`, `docs/adr/81-persistent-gate-dashboards.md` | The pages now state that the widget does not ship in alpha.7. Keeping them is useful as a contract, but readers may still expect a current feature because the pages sit under normal docs. | Either keep the explicit deferred banner or move the design into ADR/future-work docs if the site should describe only shipped surfaces. |

## Remaining consistency notes

| Issue | Relevant files | Reasoning | Recommendation |
| --- | --- | --- | --- |
| Historical release docs and superseded ADRs still contain Desk/Library/Studio language. | `docs/adr/68-workspaces-desk-library-studio.md`, `docs/adr/70-navigation-gates-dashboards.md`, `docs/releasing/0.1.0-alpha.6/release-plan-0.1.0-alpha.6.md`, `docs/releasing/0.1.0-alpha.7/validation-log.md` | These are historical records, not current-system docs. The active source of truth is ADR-81 plus reference/how-to pages. | Leave historical wording intact unless adding status notes; do not rewrite old release evidence as if it originally used the new model. |
| Alpha.8 carried-forward scratch contains old UI vocabulary by design. | `docs/releasing/0.1.0-alpha.8/tmp/ui-architecture-design-history-alpha7.md`, `docs/releasing/0.1.0-alpha.8/tmp/test-env-design-alpha5.md` | These are preserved design-history inputs, not docs-site pages. | When promoting any carried-forward idea, rewrite it against ADR-81 and current implementation before it becomes durable docs. |

## Diataxis summary

The audited docs are broadly in the right quadrants. The main fixed defect was stale
UI terminology, not quadrant placement. Remaining per-file recommendations:

| File | Expected type | Recommendation |
| --- | --- | --- |
| `docs/explanation/README.md` | README index | Consider trimming long reading paths; keep routing and section summaries. |
| `docs/explanation/architecture/README.md` | README index | Shorten architecture explanation or move detailed layer prose to a child page. |
| `docs/explanation/workflows/verify-on-commit.md` | Explanation | Add more "why commit time" rationale or move to reference/how-to if it stays mechanism-only. |
| `docs/explanation/profiles/README.md` | README index | Remove stale release-status narrative when next editing; keep it as a profile index. |
| `docs/explanation/dashboards/operational-health/skill-lifecycle.md` | Explanation | Consider renaming if "lifecycle" reads like a state machine rather than skill governance. |
| `docs/how-to-guides/README.md` | README index | Still long for an index; consider tightening to a category map. |
| `docs/how-to-guides/hermes-agent/configuration.md` | How-to | Split stable reference tables from task steps if the page continues to grow. |
| `docs/how-to-guides/setup/set-up-messaging.md` | How-to | Split shipped outbound alerts from deferred inbound messaging gateway. |
| `docs/how-to-guides/setup/set-up-vps.md` | How-to | Move deferred/unvalidated topology to explanation/ADR or keep excluded from setup index until validated. |
| `docs/how-to-guides/curate/build-a-moc.md` | How-to | Consider renaming the file to match the current "hub" title, with redirect if supported. |
| `docs/how-to-guides/operate/run-a-schema-migration.md` | How-to | Replace broad git examples such as `git add -A` with explicit-path staging. |
| `docs/how-to-guides/troubleshooting/safe-mode.md` | Troubleshooting how-to | Optionally split by failure mode if the page becomes hard to scan. |
| `docs/reference/computational-toolbox.md` | Reference | Move deeper method rationale to explanation if the page gets longer. |
| `docs/reference/linking.md` | Reference | Keep tables; shorten opening rationale if strict reference shape is desired. |
| `docs/reference/obsidian-plugins.md` | Reference | Recheck the Obsidian Git push-behavior table against exact plugin keys. |
| `docs/reference/vocabulary.md` | Reference | Add complete current allowed values or explicitly point to generated source. |
| `docs/tutorials/02-your-first-note.md` | Tutorial | Use `YYYY-MM-DD` or "today's date" in examples; make beginner archive/fold-in choice explicit. |
| `docs/tutorials/05-synthesize-toward-a-writing-project.md` | Tutorial | Add one concrete step for finding map results in the Inbox gate; consider MOC/hub link text cleanup. |
| `docs/tutorials/06-verify-and-address-gaps.md` | Tutorial | Optional: say "Open the Inbox gate" before reading flags/gaps for navigation consistency. |
| `docs/tutorials/07-find-new-sources.md` | Tutorial | Sequence now uses current gate language; next edit can clarify whether it depends on Tutorial 06 or can run after Tutorial 04. |

## Scan notes

Remaining `Desk/Library/Studio` hits after cleanup are expected in one of four buckets:
retired-command assertions, tests that ensure workspace commands are absent, superseded
ADR/historical release evidence, or alpha.8 scratch. They should not be treated as
current-system contradictions without first checking the file's role.
