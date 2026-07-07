# 0.1.0-beta.1 Decisions

This ledger captures release-time decisions as dated Y-statements. Historical
notes, ADRs, and design documents are evidence; the implemented system and this
release ledger are the decision-time record until the release closes into
`design-history/`.

## 2026-07-05 - Living design history replaces ADRs

Y: Memoria will retire `docs/adr/` as the live decision mechanism and use
release decision ledgers plus `design-history/` instead.

Because: alpha.1 through alpha.15 repeatedly reversed earlier architecture, so a
live ADR set makes older opinions look authoritative after implementation has
moved. Frozen release chapters preserve the facts, while `arcs.md` states the
current released line and pending unreleased work.

Pointers:
- Evidence: `scratch/design-history/memoria-design-history-alpha.1-to-alpha.15.md`
- Implementation target: `design-history/`
- Workflow target: `AGENTS.md`, `.agents/`

Status: accepted for the workflow-audit implementation.

## 2026-07-05 - Pinned pre-commit environments define third-party lint tools

Y: Memoria will pin ruff, ruff-format, yamllint, shellcheck, and gitleaks in
`.pre-commit-config.yaml`, and CI will run those same pre-commit hooks.

Because: the previous design pinned some tools in `requirements-dev.txt` while
CI used separate installers or Docker commands. That made local and CI behavior
depend on different installation paths. Pre-commit hook environments give one
versioned source for local commits and CI checks.

Pointers:
- Hook contract: `.pre-commit-config.yaml`
- CI callers: `.github/workflows/lint.yml`,
  `.github/workflows/lint-config.yml`, `.github/workflows/lint-installers.yml`,
  `.github/workflows/gitleaks.yml`
- Local setup: `scripts/dev/setup.sh`, `mise.toml`

## 2026-07-06 - Sandbox hardening rules from independent research (design §2.3)

Y: The code-execution sandbox's implementation will follow three specific
rules beyond what design §2.3 already specifies: (1) "approved-commands-only"
is enforced as an allowlist resolved to canonical resolved paths, never a
denylist or a string/pattern match against argv[0]; (2) any code that
constructs a `bwrap` invocation inserts the `--` argument delimiter before
the wrapped command, unconditionally; (3) adversarial validation of the
sandbox is an adaptive red-team process (attacks that adapt to the specific
defense), not a one-time static attack-list pass.

Because: independently-verified research found a real, named agent-sandbox
escape defeated by exactly a path-alias bypassing a denylist match; found
CVE-2024-32462 was caused by exactly the missing `--` delimiter in a
different bwrap-wrapping caller (Flatpak); and found peer-reviewed evidence
(NAACL 2025 Findings) that adaptive attacks defeat all eight tested static
defenses against indirect prompt injection, so static-only validation would
give false confidence.

Pointers:
- Evidence: `resources/0.1.0-beta.1-sandbox-backend-research.md` (Findings:
  the named path-alias escape; the CVE-2024-32462 root-cause finding; the
  adaptive-attacks finding)
- Implementation target: design.md §2.3 (the minimal sandbox), design §8 Q1
- Workflow target: none yet — implementation not started

Status: proposed, not yet ratified.

## 2026-07-06 - Coherent-slice policy confirmed with independent evidence (design §1.4)

Y: The existing whole-note-if-budget-else-section-expanded-anchor slice
policy (design §1.4) stands as specified, now with independent quantitative
support; SCAR's formalized continuity-aware expansion-decision threshold
(`S(c,n) > γ·cos(e_q,e_c)`) is named as a candidate refinement for a later
iteration, not adopted now.

Because: independently-verified research found a real, quantified precedent
(SCAR, arXiv:2606.16661, Table 3) showing whole-section retrieval winning on
accuracy but at far higher token cost than selective anchor-expansion —
directly confirming a budget-gated choice between the two, rather than a
blanket preference either way, is the evidence-backed shape.

Pointers:
- Evidence: `resources/0.1.0-beta.1-coherent-slice-research.md` (Findings 1-2)
- Implementation target: design.md §1.4
- Workflow target: none — no change to the shipped policy

Status: proposed, not yet ratified.

## 2026-07-06 - Exploration/diversity algorithm choice reconciled, not forked (design §4)

Y: The existing alpha.17 decision (`0.1.0-alpha.17/decisions.md`, 2026-07-06:
"MMR baseline, facility-location behind a fixture gate, DPP deferred") is
**confirmed**, not superseded, by independent beta.1-scoped research. No
competing beta.1 decision is created. One addition: the exploration
channel's *value* (whether users act on diversity-surfaced candidates at
all) is flagged as equally open as the algorithm choice, since no confirmed
evidence anywhere in the literature shows users prefer diversity-oriented
surfacing over pure relevance for exploration.

Because: independently-verified research confirms each leg of the existing
call — MMR's cheapness and its original authors' own explore-then-focus
workflow support it as baseline; facility-location's formal (1−1/e) coverage
guarantee supports keeping it as the next tier behind a fixture gate, since
the only evidence it beats MMR at surfacing overlooked material is one
unreplicated single-author preprint; DPP's real computational cost relative
to the other two remains unresolved in the literature itself, supporting
deferral. A 1998 MMR user-study claim of user preference for diversity
surfacing was explicitly refuted on adversarial review — no replacement
evidence for that claim was found.

Pointers:
- Evidence: `resources/0.1.0-beta.1-exploration-diversity-research.md`
  (Findings 1, 2, 5, 6; refuted claim #3)
- Implementation target: alpha.17 PR-F design; design.md §7 (exploration
  acted-on rate measurement)
- Workflow target: none yet — implementation not started

Status: proposed, not yet ratified.

## 2026-07-06 - Negation named as an explicit verification-check risk (design §4)

Y: Design §4's text-output verification checks will explicitly name negated
claims as a risk category requiring dedicated handling, and the free-form-
prose-plus-typed-evidence-set architecture (draft.md stays human-authored
prose; the evidence-set marker is the structured layer) is confirmed as the
right shape rather than an extraction-first pipeline.

Because: independently-verified research found negation is a specific,
repeated failure point for rigid/schema-driven methods across three
independent domains (formal semantic parsing, NLG factuality metrics,
clinical NLP) — the single most-replicated finding of this research round —
and found that AlignScore's own authors, from an unrelated domain,
independently recommend exactly Memoria's existing shape: structured/
extractive components as a post-hoc explanation layer, not the substrate for
composition or truth-judgment.

Pointers:
- Evidence: `resources/0.1.0-beta.1-extract-compose-boundary-research.md`
  (Findings 1, 5)
- Implementation target: design.md §4 (verification checks, not yet
  specified in detail)
- Workflow target: none yet — implementation not started

Status: proposed, not yet ratified.

## 2026-07-06 - Seed-corpus licensing mechanics settled; source list still open (design §7)

Y: Any seed-corpus source drawn from PMC will be filtered to the
"Commercial Use Allowed" license tier specifically (never PMC's own
`cc0[filter]`, which mixes in unrelated public-domain content, without a
per-article check); any source drawn from arXiv will be included only if the
author selected a redistribution-permissive license (CC BY or CC0)
specifically — arXiv hosting a paper is never itself sufficient permission.
The actual ~8 source list remains an open follow-up, not resolved by this
decision.

Because: independently-verified research confirmed these licensing
mechanics directly against PMC's and arXiv's own primary documentation, but
found no specific candidate papers, and found DOAJ and Semantic Scholar were
never reached (both dedicated search angles failed outright on rate limits)
— the mechanics are settled enough to constrain a future selection pass, but
the pass itself has not happened.

Pointers:
- Evidence: `resources/0.1.0-beta.1-seed-corpus-licensing-research.md`
- Implementation target: design.md §7 (the ~8-source corpus)
- Workflow target: a follow-up research pass naming specific candidates,
  not yet scheduled

Status: proposed, not yet ratified.

## 2026-07-06 - Retrieval-fusion decision deferred to a spike, not a literature verdict (requirements §6 Q5)

Y: Memoria will not decide dense/hybrid retrieval adoption from literature
review. A runnable spike protocol is committed instead, with a concrete,
pre-registered adoption bar to be fixed *before* the spike runs, not fit to
its results afterward. The dense-vs-BM25-only verdict itself is explicitly
deferred to that spike's outcome.

Because: independently-verified research found the literature contains no
verified, direct, quantified comparison of hybrid dense+sparse RRF fusion
against BM25-only — every claim attempting that specific comparison was
refuted on adversarial review — while confirming BM25 is independently a
strong, hard-to-beat zero-shot baseline. This question is empirical, not
resolvable by more research, matching the project's existing "each tier
must beat a declared cheap baseline or it is disabled" discipline.

Pointers:
- Evidence: `resources/0.1.0-beta.1-retrieval-fusion-research.md`;
  protocol: `resources/0.1.0-beta.1-retrieval-fusion-spike-protocol.md`
- Implementation target: `main/src/memoria_vault/runtime/retrieval_substrate.py`
  (`SELECTED_RETRIEVAL_SUBSTRATE`, `RETRIEVAL_SUBSTRATE_VERDICT`)
- Workflow target: the spike itself — not yet run

Status: proposed, not yet ratified.

Status: accepted for the workflow-audit implementation.
