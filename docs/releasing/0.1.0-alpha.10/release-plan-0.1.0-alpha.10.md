---
release: v0.1.0-alpha.10
status: complete     # draft | candidate | complete | released
released: false      # machine cut-flag; true ONLY for a formal tagged release
title: Release plan -- v0.1.0-alpha.10
parent: Releasing
nav_order: 2
---

# Release plan -- v0.1.0-alpha.10

**Current status: complete internal checkpoint record.** This plan covers the full
post-alpha.9 change set, from the alpha.9 close commit
`3ba5081f` / [#858](https://github.com/eranroseman/memoria-vault/pull/858)
through `main` at `e56aba40` /
[#928](https://github.com/eranroseman/memoria-vault/pull/928), plus the release
execution fixes and evidence recorded in
[v0.1.0-alpha.10 validation log](validation-log.md). It replaces the earlier narrow
Hermes-only alpha.10 framing. alpha.10 remains an internal checkpoint: no
release-please PR, tag, or GitHub Release was cut.

## 1. Scope -- what this release is

alpha.10 is the post-alpha.9 consolidation checkpoint. It gathers the runtime,
onboarding, Obsidian surface, schema, and release-process work that landed after
alpha.9 into one validation boundary.

| Area | Merged changes after alpha.9 | Outcome |
| --- | --- | --- |
| Hermes/runtime governance | [#862](https://github.com/eranroseman/memoria-vault/pull/862), [#865](https://github.com/eranroseman/memoria-vault/pull/865)-[#873](https://github.com/eranroseman/memoria-vault/pull/873), [#874](https://github.com/eranroseman/memoria-vault/pull/874), [#882](https://github.com/eranroseman/memoria-vault/pull/882), [#883](https://github.com/eranroseman/memoria-vault/pull/883), [#886](https://github.com/eranroseman/memoria-vault/pull/886), [#904](https://github.com/eranroseman/memoria-vault/pull/904), [#905](https://github.com/eranroseman/memoria-vault/pull/905) | Hermes 0.17 was evaluated against on-box evidence; profiles now align to the 0.17 tool-policy shape; configuration, profile, and redeploy drift are documented; direct history tools were hardened. |
| Onboarding, tutorials, and sample vault | [#884](https://github.com/eranroseman/memoria-vault/pull/884), [#887](https://github.com/eranroseman/memoria-vault/pull/887)-[#901](https://github.com/eranroseman/memoria-vault/pull/901), [#925](https://github.com/eranroseman/memoria-vault/pull/925), [#927](https://github.com/eranroseman/memoria-vault/pull/927) | The tutorial path was rebuilt around a destination-first arc, sample-vault support moved into the installer scaffold and reference docs, setup docs were simplified, and the sample retraction/supersession fixture was corrected. |
| Obsidian surfaces and navigation | [#903](https://github.com/eranroseman/memoria-vault/pull/903), [#907](https://github.com/eranroseman/memoria-vault/pull/907)-[#914](https://github.com/eranroseman/memoria-vault/pull/914) | The left-pane rail became the primary navigation surface; Inbox became the queue; dashboard duplicates collapsed to Bases embeds; ADR-116 established View/Collection/Rail vocabulary and the Queue/Maintenance split. |
| Type, dashboard, and form contracts | [#915](https://github.com/eranroseman/memoria-vault/pull/915)-[#924](https://github.com/eranroseman/memoria-vault/pull/924) | ADR-117/118/119 landed the document-type naming scheme, dashboard consolidation, schema-owned forms, and a complete declarative type/schema contract. |
| Agent and release-process hygiene | [#860](https://github.com/eranroseman/memoria-vault/pull/860), [#861](https://github.com/eranroseman/memoria-vault/pull/861), [#864](https://github.com/eranroseman/memoria-vault/pull/864), [#885](https://github.com/eranroseman/memoria-vault/pull/885), [#893](https://github.com/eranroseman/memoria-vault/pull/893), [#906](https://github.com/eranroseman/memoria-vault/pull/906), [#910](https://github.com/eranroseman/memoria-vault/pull/910), [#926](https://github.com/eranroseman/memoria-vault/pull/926) | Worktree, PR, agent-guidance, audit, and verification-process drift were tightened; `scripts/verify` now defines the Source/Package/Runtime/Product/Release gate vocabulary. |

The checkpoint boundary is validation and documentation, not new feature work.
It should prove that the post-alpha.9 repo, shipped vault tree, and test runtime
are coherent after the navigation, schema, tutorial, and Hermes changes.

## 2. Definition of done -- gates

v0.1.0-alpha.10 is complete when every gate below is closed in the release parent
[#875](https://github.com/eranroseman/memoria-vault/issues/875) or its successor
release issue, with evidence attached there. This file defines the gates; issue
state is the source of truth.

| Gate | Proves | Verified by |
| --- | --- | --- |
| Source | The repository is internally coherent after #860-#927: formatting, lint, docs, ADR/code drift, agent guidance, links, spelling, schema, and changed-code tests are green. | `scripts/verify pr` on current `main`; CI checks green. |
| Package | The shipped vault tree assembles cleanly and the model-free workflow replay still works after sample-vault, schema, dashboard, and surface changes. | `scripts/verify package`; installer/sample-vault assertions; fresh-vault integrity. |
| Runtime | Hermes 0.17 policy/profile expectations, Local REST API/MCP wiring, and direct-tool deny paths still hold in `~/Memoria-test`. | `scripts/verify runtime` when local prerequisites are available; contract/cost doctors; live deny and Obsidian MCP smoke. |
| Product | The user-facing experience is coherent: tutorials, sample vault, left rail, Inbox queue, Maintenance collection, Bases/dashboard embeds, schema-owned forms, and page-name/title expectations render and match docs. | Attended Obsidian pass plus targeted tutorial/sample-vault walkthrough. |
| Release | alpha.10 can close as an internal checkpoint with no hidden state: blockers triaged, docs current, release scratch disposed, issue/milestone state updated, and no formal tag expected. | Release issue evidence, docs sweep, close-out sweep. |

## 3. Validation -- stages

The automated release-candidate prefix is:

```bash
scripts/verify rc
```

`scripts/verify rc` covers Source, Package, and the opt-in Runtime smoke. If the
local runtime cannot bind sockets or Hermes/Obsidian prerequisites are absent,
record the skip reason and run the Runtime Gate manually on the test host.

| Stage | Proves |
| --- | --- |
| Source | `scripts/verify pr` passes on the final candidate commit. |
| Package | `scripts/verify package` passes; the disposable vault builds, hooks work, plugin bundle is present, and the workflow replay reaches the expected artifacts. |
| Runtime | Hermes profile redeploy, contract/cost doctors, direct-tool deny, and Obsidian MCP smoke are recorded against `~/Memoria-test`, not production. |
| Product | Manual Obsidian checks cover the rail, Inbox queue, Maintenance collection, dashboard/Bases embeds, schema-owned forms, and the sample-vault tutorial path. |
| Release | Gate evidence is linked from the release issue; no High-priority blocker remains; this plan and the release README are current. |

## 4. Blockers

Not enumerated here. By definition the blockers are any open gate/stage issue
under the alpha.10 release parent, any open issue assigned to the
`0.1.0-alpha.10` milestone, plus any open High-priority blocker in the
[Memoria Issue Tracker](https://github.com/users/eranroseman/projects/1).

## 5. Out of scope (later)

- A formal public release, tag, release-please PR, signed artifact, or packaged
  installer distribution.
- New memory machinery: NLI/MaxSAT contradiction automation, model-free warrant
  checking, external memory providers, or cross-vault sharing.
- ADR-116 Phase 3 / Portals-as-primary-rail work, which was explicitly retired.
- Production-vault migration. alpha.10 validation runs in `~/Memoria-test` or
  disposable vaults.
- Any new Hermes feature beyond the policy/config/profile changes already landed
  and verified against the installed runtime.

## 6. Known limitations

- Limitation: alpha.10 is an internal checkpoint, not a tagged release. Impact:
  there is no GitHub Release or release-please changelog entry. Workaround: use
  this plan, merged PRs, and the release issue trail as the checkpoint record.
- Limitation: Runtime acceptance still depends on a local Hermes/Obsidian test
  host. Impact: CI can prove Source and Package Gates, but GUI and live MCP
  behavior require attended evidence. Workaround: record the manual Runtime and
  Product Gate checks in the release issue.
- Limitation: The alpha.10 Obsidian GUI follow-up has workspace/plugin evidence,
  not screenshot evidence. Impact: the Linux app opened the WSL test vault,
  Markdown surfaces, Bases views, and live Local REST API, but the WSL image had
  no screenshot/window-capture tool for pixel evidence. Workaround: keep the
  rendering requirement in the release-candidate runbook for hosts with capture
  tooling.
- Limitation: The sample vault is tutorial/test scaffolding, not user data
  migration. Impact: sample-vault correctness does not prove production-vault
  upgrade safety. Workaround: keep production validation separate and disposable.

## 7. Documentation integrity

Before alpha.10 closes, complete a fresh docs sweep over changed behavior:

1. **Coverage:** Hermes/profile policy, configuration surfaces, tutorials,
   sample vault, left rail, Inbox/Maintenance split, dashboard/Bases embeds,
   document types, schema-owned forms, and release verification gates have current
   how-to/reference/explanation coverage.
2. **Single source of truth:** ADR-116/117/118/119 own the architectural
   decisions; docs describe current behavior without duplicating machine-readable
   schema contracts unless a doctor covers the mirror.
3. **Navigation/indexing:** tutorial, reference, explanation, releasing, and
   testing indexes point to the new or renamed pages.
4. **Terminology:** use View, Collection, Rail, Inbox queue, Maintenance
   collection, document type, schema-owned form, Source Gate, Package Gate,
   Runtime Gate, Product Gate, and Release Gate consistently.
5. **Freshness:** Hermes claims are on-box verified; Obsidian claims match the
   installed plugins and shipped vault tree; sample-vault instructions match the
   installer scaffold.

Required checker summary: `scripts/verify pr`, `python scripts/docs_doctor.py
docs`, `python scripts/status_doctor.py`, `python scripts/check_test_refs.py`,
and cspell.

## 8. Runtime readiness

Runtime evidence is required because alpha.10 changed profiles, Hermes policy
shape, Obsidian navigation surfaces, Bases/dashboard embeds, forms, and sample
vault behavior.

Record:

1. `scripts/verify runtime` result or the exact skip reason plus manual
   replacement evidence.
2. Hermes version, profile redeploy status, and contract/cost doctor results.
3. At least one live allowed Obsidian MCP write and one direct-tool deny through
   the deployed policy gate.
4. Obsidian rendering of the left rail, Inbox queue, Maintenance collection,
   dashboard/Bases embeds, and schema-owned form surfaces.
5. Sample-vault tutorial path opened from a clean scaffold.

No runtime check may mutate the production vault.

## 9. Release close-out sweep

Before closing the checkpoint:

1. Review `docs/releasing/0.1.0-alpha.10/tmp/` if it exists; fold durable content
   into ADRs/docs/issues, move unfinished work forward, then delete completed
   scratch.
2. Confirm all post-alpha.9 PRs listed in the scope table are represented in the
   docs, ADRs, tests, or known limitations.
3. Close or roll forward alpha.10 issues and milestone items.
4. Leave the main checkout clean and fast-forwarded after merge.

## 10. Cut procedure

This checkpoint follows the untagged internal path:

1. Required CI is green on `main`; `scripts/verify rc` evidence is recorded or
   Runtime Gate skip/manual replacement evidence is attached.
2. Product Gate attended checks are complete for Obsidian, sample vault, and
   tutorial changes.
3. Documentation integrity, runtime readiness, and close-out sweeps are complete.
4. Do not cut a tag or GitHub Release. Set this plan to `status: complete`,
   `released: false` after the release parent issue is closed.
5. Close the milestone, rolling unfinished issues to the next checkpoint.

## 11. Roadmap after this release

| Phase | When | Goal |
| --- | --- | --- |
| alpha.11 or next checkpoint | After alpha.10 close | Pick the next scope from observed Runtime/Product Gate gaps, not from speculative architecture. |
| Runtime automation | When a stable self-hosted runner exists | Move more Runtime Gate checks from attended evidence into repeatable CI. |
| Product quality eval | When gold tasks are ready | Add the Product Gate quality layer for classification, citation, and draft quality. |
