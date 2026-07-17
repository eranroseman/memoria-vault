# O1 Onboarding + Seed Corpus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the O1 spec — the license-floored seed-corpus manifest and `memoria seed install`, derived steering with the thin watch/mute override, `onboarding-step` telemetry for the ≤30-minute bar, the diary template, and the tutorial/doc restructure onto the doc-arc wizard.

**Architecture:** A shipped manifest (eight verified CC BY/CC0 sources) feeds a per-method fetch/resolve layer into the existing PDF capture seam through a new PI-only `seed-install` operation; steering inverts from an authored file to a derived token union (`runtime/steering.py`) with `steering.md` reseeded as a two-section override; five `onboarding-step` emit points ride I1's telemetry substrate through one guarded helper; the tutorial arc restructures so project framing precedes capture. Spec of record: `docs/superpowers/specs/2026-07-16-o1-onboarding-seed-design.md` (main @ `07bedc74`).

**Tech Stack:** Python 3 / SQLite / pytest; plain-markdown docs; no new dependencies (PyYAML already shipped).

## Global Constraints

- Correctness gate: `python scripts/verify`; `main` needs a PR + `verify`/`gitleaks`; squash merge; explicit-path staging only (never `git add -A`); disposable vaults only (`tmp_path`).
- **License floor (spec §1, the recorded freeze blocker):** every manifest row's license ∈ {CC BY, CC BY 4.0, CC0} with an https evidence URL and pinned identifier — `tests/test_seed_manifest.py::test_license_impl_start_check` IS the impl-start check; a failing row is replaced, never waived.
- **No network in tests**: every fetcher takes an injectable `opener`; tests inject fakes (canned XML/PDF/tar.gz bytes).
- Keyless end-to-end: no task may make credentials a requirement of onboarding.
- All line refs verified at origin/main `07bedc74` (post-PR-#1502); re-anchor by symbol if drifted.
- The spec's §1 ledger Y-statement and the #902 re-deferral comment already shipped with the spec PR — not re-planned here.

## Cross-section contracts (BINDING — the manifests' seam resolutions)

1. **Manifest** (M.1 produces): `src/memoria_vault/product/seed_corpus/manifest.yaml`, rows `{id, title, identifier, license, license_evidence, fetch{method,url}, role, repo?}`; `load_seed_manifest() -> list[dict]` / `parse_seed_manifest(text) -> list[dict]` in `memoria_vault.product.seed_corpus`; the eight pinned work_ids: `chen-2018-undesirable-difficulty, moreira-2019-retrieval-practice, settles-2016-spaced-repetition, morrison-2020-offloading, ose-askvik-2020-handwriting, schmidt-2018-luhmann-card-index, mirzababaei-2021-toulmin-agent, asai-2024-openscholar`.
2. **Seed install** (M.3 produces): engine `seed_install(vault, rows=None, *, opener=None, context) -> {admitted, skipped, failed, notices, telemetry}` (ValueError iff admitted+skipped both empty); worker operation id `seed-install` (PI-only); CLI `memoria seed install --workspace <path>` — the exact backticked path the D-section docs cite (doc-claims gate: M.3 merges before D).
3. **Steering module** (S produces): `memoria_vault.runtime.steering` — `relevance_tokens`, `steering_overrides(vault) -> (watch, mute)`, `effective_steering_tokens(vault) -> set[str]`, `effective_steering_provenance(vault) -> [{token, sources}]`; source labels `project:<rel> | hub:<rel> | question:<rel> | watch`; the reseeded two-section `steering.md` (`## Watch for` / `## Muted`).
4. **Onboarding-step helper** (T produces, M.3 consumes via guarded import): `memoria_vault.runtime.onboarding_steps` — `emit_onboarding_step(vault, step) -> str | None` (never raises into callers), `emit_onboarding_step_once`, `has_onboarding_step`, `emit_first_answer_if_seed_grounded(vault, answer, *, manifest_loader=None)`; `ONBOARDING_STEPS = {init-done, onboard-done, project-framed, seed-installed, first-answer}`; `NATIVE_EVENT_FIELDS['onboarding-step'] = {'step'}` added to the I1-owned table.
5. **Cross-plan order tolerance:** I1's `runtime/telemetry.py` + v19 table are a **hard block for T.1 only** (grep-first stop-note); every other telemetry touch is a guarded no-op recorded as `skipped-helper-not-landed`. The surfaces plan's BOOT-D owns `memoria onboard` — T's onboard-done and D.4's `Start here.md` repoint carry both-branch steps (edit if landed, amend the surfaces plan text if not).
6. **Execution order:** M.1 → M.2 → M.3 → {S.1 → S.2 → S.3} → {T.1 → T.2 → T.3} → D.1 → D.2 → D.3 → D.4. S is independent of M/T; D runs last (docs cite CLI surfaces the code tasks create). T.1 blocks on the I1 plan's slices 1–2 being merged.
7. **TEST_LEVELS registrations** (`tests/conftest.py:18`): `test_seed_manifest.py: "contract"`, `test_seed_install.py: "contract"`, `test_steering_tokens.py: "contract"`, `test_onboarding_steps.py: "contract"`; extended files (`test_knowledge.py`, `test_cli.py`, `test_capture.py`, seed/floor tests) are already registered.

---
# M — Seed manifest + `memoria seed install`

Implements spec §1 (licensing decision, license floor, fetch rule, impl-start check) and §2 (the eight-source corpus, the manifest artifact, the per-method fetch/resolve layer, idempotency and per-row honesty, the frame-first notice) — slices 1–2 of §9. Spec: `docs/superpowers/specs/2026-07-16-o1-onboarding-seed-design.md`. The §1 dated Y-statement ledger entry and the #902 re-deferral comment shipped with the spec PR — not re-planned here.

**Cross-plan order tolerance (binding).** Section T of this plan owns `emit_onboarding_step(vault: Path, step: str) -> None` (the `onboarding-step` native telemetry type, built on I1's `record_telemetry_event(vault, event_type, payload) -> str` in `src/memoria_vault/runtime/telemetry.py` — see `docs/superpowers/plans/2026-07-16-i1-full-wiring.md` interface 1). Section M never imports `record_telemetry_event` directly; M.3's emit is a guarded import of section T's emit_onboarding_step (module memoria_vault.runtime.onboarding_steps) that no-ops with a recorded gap when the helper has not landed. Grep-first rule: before writing M.3's emit wrapper, run `grep -rn "def emit_onboarding_step" src/memoria_vault/` — re-anchor the import module if T placed the helper elsewhere; if the grep is empty, keep the guarded import exactly as written. The surfaces plan's `memoria onboard` (BOOT-D) is not consumed by M at all — the onboard-done emit point belongs to section T.

**Why a new worker operation, not a bare engine call.** All vault writes go through `enqueue_operation → run_request → _run_operation_job` (worker.py:303-315), which loads a packaged capability manifest per operation id (`load_operation_policy`, operations.py:103-108). Three shipped gates force the co-changes M.3 makes: `test_worker_operations_are_cataloged_and_policy_shaped` (tests/test_capabilities.py:61-79) requires worker-dispatch ids ≡ manifest catalog ids both ways; `test_every_operation_has_a_floor_entry` (tests/test_floor_coverage.py:37-42) requires an `OPERATION_REGISTRY` entry in tests/floor_lib.py; `test_cli_command_surface_is_exact` (tests/test_cli.py:73-146) pins the exact CLI command set. `seed-install` is registered PI-only in `PROTECTED_OPERATION_ACTORS` (worker.py:53-66) — onboarding is a PI action, agent surfaces cannot trigger network fetches, and the offline floor sweep (which enqueues as `actor="agent"`, tests/test_floor_sweep_operations.py:73-78) refuses deterministically with no network, the same shape as `curate-note-link` (tests/floor_lib.py:481-489).

**SPEC GAPS (each resolved inline; all are repo-convention resolutions, none change spec mechanisms):**

1. **Row ids.** The spec's §2 table has no id column but §2 names `id` first in the manifest schema and fixes `id` = catalog `work_id`. Resolution: kebab-case `author-year-topic` slugs (listed in M.1), each provably stable under the catalog's `_work_id` normalization (`safe_filename(value).strip("._-")`, capture.py:660-664 / state.py:3452-3458) — pinned by `test_ids_survive_catalog_work_id_normalization`.
2. **License-evidence URLs.** §2 requires `license_evidence` per row but pins only row 8's ("the abs page"). Resolution: each source's canonical publisher landing page (the page carrying the CC statement), DOI-derived; row 8 uses the spec-pinned `https://arxiv.org/abs/2411.14199v1`. The §1 impl-start check re-verifies against exactly these URLs.
3. **Elided titles.** The spec table abridges rows 4, 5, and 7 with "…". Resolution: the manifest ships the full published titles; the implementer confirms them on the evidence-URL visit that the impl-start check already requires (M.1 commit step). Tests pin ids/licenses/methods/URLs/repos — not title prose — so a title correction never breaks a gate.
4. **"Archived" detection for the frame-first notice.** The task sketch says `archived != True`; the repo convention for concept files is `lifecycle: archived` (`_is_current_frontmatter`, knowledge.py:3056-3057; spec §4.1 says "non-archived `type: project`"). Resolution: a project is active iff frontmatter `type == "project"` and `lifecycle not in {"retracted", "archived"}`, walked with `iter_markdown` (vaultio.py:217-226) over `projects/` (covers both `projects/<slug>.md` and `projects/<slug>/project.md`, knowledge.py:3074-3079).
5. **Section T helper's module home.** The signature is fixed (`emit_onboarding_step(vault, step)`) but its module is T's to choose. Resolution: guarded import from `memoria_vault.runtime.onboarding_steps` (section T's module), with the grep-first re-anchor rule above; absence is a recorded no-op (`"telemetry": "skipped-helper-not-landed"` in the result payload), never a crash.

---

### Task M.1: The seed-corpus manifest + loader + license impl-start check

**Files:**

- Create `src/memoria_vault/product/seed_corpus/__init__.py` (loader `load_seed_manifest` / `parse_seed_manifest`)
- Create `src/memoria_vault/product/seed_corpus/manifest.yaml` (the eight spec-§2 rows)
- Create `tests/test_seed_manifest.py`
- Modify `pyproject.toml` — package-data block at pyproject.toml:29-31 (add the seed_corpus yaml glob so installed wheels carry the manifest; the sibling precedent is `"memoria_vault.product.capabilities.operations" = ["*.md"]` at :31)
- Modify `tests/conftest.py` — `TEST_LEVELS` dict at tests/conftest.py:18 (new test file registration; this is the "new file ⇒ register" case)

**Interfaces:**

- Consumes: `yaml.safe_load` (PyYAML is a runtime dependency, pyproject.toml:15); `importlib.resources.files` (repo precedent: `_capability_resource`, runtime/capabilities.py:107-119); `safe_filename(value: str) -> str` (runtime/paths.py:15-17, in the test).
- Produces: `load_seed_manifest() -> list[dict[str, Any]]`; `parse_seed_manifest(text: str) -> list[dict[str, Any]]`; `SEED_LICENSE_FLOOR = frozenset({"CC BY", "CC BY 4.0", "CC0"})`; `SEED_FETCH_METHODS = frozenset({"pmc-oa", "pdf-url", "arxiv-pdf"})`; the manifest row schema `{id, title, identifier, license, license_evidence, fetch{method,url}, role, repo?}` with the eight pinned work_ids that M.2/M.3 and the tutorial sections rely on.

- [ ] **Step 1: Write the failing test** — create `tests/test_seed_manifest.py`:

```python
"""Contract tests for the shipped seed-corpus manifest (O1 spec sections 1-2).

test_license_impl_start_check IS the impl-start check the beta.1 decisions
ledger names: it re-asserts, on every run, that each row clears the license
floor, carries an https evidence URL, and pins its identifier. A row that
fails is replaced, never waived (spec section 1).
"""

from __future__ import annotations

import re

from memoria_vault.product.seed_corpus import (
    SEED_FETCH_METHODS,
    SEED_LICENSE_FLOOR,
    load_seed_manifest,
    parse_seed_manifest,
)
from memoria_vault.runtime.paths import safe_filename

EXPECTED_IDS = [
    "chen-2018-undesirable-difficulty",
    "moreira-2019-retrieval-practice",
    "settles-2016-spaced-repetition",
    "morrison-2020-offloading",
    "ose-askvik-2020-handwriting",
    "schmidt-2018-luhmann-card-index",
    "mirzababaei-2021-toulmin-agent",
    "asai-2024-openscholar",
]

_BAD_ROW_TEMPLATE = """
- id: bad-row
  title: "Bad fixture row"
  identifier: "doi:10.1234/bad"
  license: {license}
  license_evidence: "https://example.test/license"
  fetch:
    method: {method}
    url: "{url}"
  role: "fixture"
"""


def _bad_row(
    license_value: str = "CC BY 4.0",
    method: str = "pdf-url",
    url: str = "https://example.test/bad.pdf",
) -> str:
    return _BAD_ROW_TEMPLATE.format(license=license_value, method=method, url=url)


def test_manifest_ships_all_eight_rows_in_spec_order() -> None:
    rows = load_seed_manifest()

    assert [row["id"] for row in rows] == EXPECTED_IDS


def test_license_impl_start_check() -> None:
    assert SEED_LICENSE_FLOOR == {"CC BY", "CC BY 4.0", "CC0"}
    for row in load_seed_manifest():
        assert row["license"] in {"CC BY", "CC BY 4.0", "CC0"}, row["id"]
        assert str(row["license_evidence"]).startswith("https://"), row["id"]
        identifier = str(row["identifier"])
        assert identifier.startswith(("doi:", "arxiv:")), row["id"]
        if identifier.startswith("arxiv:"):
            assert re.search(r"v\d+$", identifier), (
                f"{row['id']}: arXiv identifier must pin a version"
            )


def test_fetch_methods_match_spec_table() -> None:
    assert SEED_FETCH_METHODS == {"pmc-oa", "pdf-url", "arxiv-pdf"}
    rows = load_seed_manifest()
    methods = {row["id"]: row["fetch"]["method"] for row in rows}

    assert methods == {
        "chen-2018-undesirable-difficulty": "pmc-oa",
        "moreira-2019-retrieval-practice": "pdf-url",
        "settles-2016-spaced-repetition": "pdf-url",
        "morrison-2020-offloading": "pmc-oa",
        "ose-askvik-2020-handwriting": "pmc-oa",
        "schmidt-2018-luhmann-card-index": "pdf-url",
        "mirzababaei-2021-toulmin-agent": "pmc-oa",
        "asai-2024-openscholar": "arxiv-pdf",
    }
    urls = {row["id"]: row["fetch"]["url"] for row in rows}
    assert urls["asai-2024-openscholar"] == "https://export.arxiv.org/pdf/2411.14199v1"
    for row_id in (
        "chen-2018-undesirable-difficulty",
        "morrison-2020-offloading",
        "ose-askvik-2020-handwriting",
        "mirzababaei-2021-toulmin-agent",
    ):
        assert urls[row_id].startswith(
            "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC"
        ), row_id


def test_paper_repo_affordance_pairs() -> None:
    rows = {row["id"]: row for row in load_seed_manifest()}

    assert rows["asai-2024-openscholar"]["repo"] == "https://github.com/AkariAsai/OpenScholar"
    assert rows["asai-2024-openscholar"]["identifier"] == "arxiv:2411.14199v1"
    assert rows["settles-2016-spaced-repetition"]["repo"] == (
        "https://github.com/duolingo/halflife-regression"
    )


def test_ids_survive_catalog_work_id_normalization() -> None:
    # state._work_id / capture._work_id normalize via safe_filename().strip("._-");
    # the pre-check in seed_install only holds if manifest ids are fixed points.
    for row in load_seed_manifest():
        assert safe_filename(row["id"]).strip("._-") == row["id"]


def test_parse_rejects_license_floor_violation() -> None:
    try:
        parse_seed_manifest(_bad_row(license_value="CC BY-SA 4.0"))
    except ValueError as exc:
        assert "license floor" in str(exc)
    else:
        raise AssertionError("CC BY-SA must fail the license floor")


def test_parse_rejects_unknown_fetch_method() -> None:
    try:
        parse_seed_manifest(_bad_row(method="scrape"))
    except ValueError as exc:
        assert "fetch.method" in str(exc)
    else:
        raise AssertionError("unknown fetch methods must be rejected")


def test_parse_rejects_non_https_fetch_url() -> None:
    try:
        parse_seed_manifest(_bad_row(url="http://example.test/bad.pdf"))
    except ValueError as exc:
        assert "https" in str(exc)
    else:
        raise AssertionError("non-https fetch URLs must be rejected")
```

- [ ] **Step 2: Run and watch it fail** — `python -m pytest tests/test_seed_manifest.py -v` → collection error: `ModuleNotFoundError: No module named 'memoria_vault.product.seed_corpus'`.

- [ ] **Step 3: Minimal implementation.** Create `src/memoria_vault/product/seed_corpus/__init__.py`:

```python
"""Shipped seed-corpus manifest: pinned identifiers, licenses, fetch methods.

Fetch-on-onboard, manifest-only (O1 spec section 1): the product ships this
manifest, never third-party content. Every row must clear the license floor;
tests/test_seed_manifest.py carries the impl-start check that re-asserts it.
"""

from __future__ import annotations

import re
from importlib.resources import files
from typing import Any

import yaml

SEED_LICENSE_FLOOR = frozenset({"CC BY", "CC BY 4.0", "CC0"})
SEED_FETCH_METHODS = frozenset({"pmc-oa", "pdf-url", "arxiv-pdf"})
_REQUIRED_ROW_FIELDS = (
    "id",
    "title",
    "identifier",
    "license",
    "license_evidence",
    "fetch",
    "role",
)


def load_seed_manifest() -> list[dict[str, Any]]:
    """Load and validate the packaged seed-corpus manifest."""
    text = files(__package__).joinpath("manifest.yaml").read_text(encoding="utf-8")
    return parse_seed_manifest(text)


def parse_seed_manifest(text: str) -> list[dict[str, Any]]:
    """Parse manifest YAML and enforce the row schema plus the license floor."""
    rows = yaml.safe_load(text)
    if not isinstance(rows, list) or not rows:
        raise ValueError("seed manifest must be a non-empty YAML list of rows")
    for row in rows:
        _validate_row(row)
    ids = [str(row["id"]) for row in rows]
    duplicates = sorted({work_id for work_id in ids if ids.count(work_id) > 1})
    if duplicates:
        raise ValueError(f"seed manifest ids must be unique: {', '.join(duplicates)}")
    return rows


def _validate_row(row: Any) -> None:
    if not isinstance(row, dict):
        raise ValueError("seed manifest rows must be maps")
    label = str(row.get("id") or "<missing id>")
    missing = [field for field in _REQUIRED_ROW_FIELDS if not row.get(field)]
    if missing:
        raise ValueError(f"seed manifest row {label} missing fields: {', '.join(missing)}")
    if row["license"] not in SEED_LICENSE_FLOOR:
        raise ValueError(
            f"seed manifest row {label} license {row['license']!r} fails the license floor"
        )
    if not str(row["license_evidence"]).startswith("https://"):
        raise ValueError(f"seed manifest row {label} license_evidence must be an https URL")
    identifier = str(row["identifier"])
    if not identifier.startswith(("doi:", "arxiv:")):
        raise ValueError(f"seed manifest row {label} identifier must be doi:... or arxiv:...")
    if identifier.startswith("arxiv:") and not re.search(r"v\d+$", identifier):
        raise ValueError(f"seed manifest row {label} arXiv identifier must pin a version")
    fetch = row["fetch"]
    if not isinstance(fetch, dict):
        raise ValueError(f"seed manifest row {label} fetch must be a map")
    if fetch.get("method") not in SEED_FETCH_METHODS:
        raise ValueError(
            f"seed manifest row {label} fetch.method must be one of "
            f"{', '.join(sorted(SEED_FETCH_METHODS))}"
        )
    if not str(fetch.get("url") or "").startswith("https://"):
        raise ValueError(f"seed manifest row {label} fetch.url must be an https URL")
```

Create `src/memoria_vault/product/seed_corpus/manifest.yaml` (all eight spec-§2 rows; comment-header style mirrors `workspace_seed/.memoria/schemas/folders.yaml`; yamllint is `relaxed` with line-length disabled, `.yamllint:13-19`):

```yaml
# Seed-corpus manifest - the shipped artifact of
# docs/superpowers/specs/2026-07-16-o1-onboarding-seed-design.md (section 2).
# Fetch-on-onboard, manifest-only (section 1): pinned identifier + license +
# evidence URL + fetch method ship here; no third-party content enters the
# repo or the package. Every fetch is https and needs no credentials.
# tests/test_seed_manifest.py carries the license impl-start check.

- id: chen-2018-undesirable-difficulty
  title: "Undesirable Difficulty Effects in the Learning of High-Element Interactivity Materials"
  identifier: "doi:10.3389/fpsyg.2018.01483"
  license: CC BY 4.0
  license_evidence: "https://www.frontiersin.org/articles/10.3389/fpsyg.2018.01483/full"
  fetch:
    method: pmc-oa
    url: "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC6099118"
  role: "Tension pair A: desirable difficulty effects shrink or reverse for high-element-interactivity material"

- id: moreira-2019-retrieval-practice
  title: "Retrieval Practice in Classroom Settings: A Review of Applied Research"
  identifier: "doi:10.3389/feduc.2019.00005"
  license: CC BY
  license_evidence: "https://www.frontiersin.org/articles/10.3389/feduc.2019.00005/full"
  fetch:
    method: pdf-url
    url: "https://www.frontiersin.org/articles/10.3389/feduc.2019.00005/pdf"
  role: "Tension pair B: retrieval practice benefits complex authentic classroom material"

- id: settles-2016-spaced-repetition
  title: "A Trainable Spaced Repetition Model for Language Learning"
  identifier: "doi:10.18653/v1/P16-1174"
  license: CC BY 4.0
  license_evidence: "https://aclanthology.org/P16-1174/"
  fetch:
    method: pdf-url
    url: "https://aclanthology.org/P16-1174.pdf"
  role: "Extends the testing effect to deployed adaptive scheduling"
  repo: "https://github.com/duolingo/halflife-regression"

- id: morrison-2020-offloading
  title: "Offloading items from memory: individual differences in cognitive offloading in a short-term memory task"
  identifier: "doi:10.1186/s41235-019-0201-4"
  license: CC BY 4.0
  license_evidence: "https://cognitiveresearchjournal.springeropen.com/articles/10.1186/s41235-019-0201-4"
  fetch:
    method: pmc-oa
    url: "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC6942100"
  role: "External-memory/offloading anchor (registered report); supports the card-index row"

- id: ose-askvik-2020-handwriting
  title: "The Importance of Cursive Handwriting Over Typewriting for Learning in the Classroom: A High-Density EEG Study of 12-Year-Old Children and Young Adults"
  identifier: "doi:10.3389/fpsyg.2020.01810"
  license: CC BY 4.0
  license_evidence: "https://www.frontiersin.org/articles/10.3389/fpsyg.2020.01810/full"
  fetch:
    method: pmc-oa
    url: "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC7399101"
  role: "Note-taking medium (encoding vs storage); in tension with the offloading row's storage framing"

- id: schmidt-2018-luhmann-card-index
  title: "Niklas Luhmann's Card Index: The Fabrication of Serendipity"
  identifier: "doi:10.6092/issn.1971-8853/8350"
  license: CC BY 4.0
  license_evidence: "https://sociologica.unibo.it/article/view/8350"
  fetch:
    method: pdf-url
    url: "https://sociologica.unibo.it/article/download/8350/8272"
  role: "PKM/Zettelkasten anchor - the vault's own lineage"

- id: mirzababaei-2021-toulmin-agent
  title: "Developing a Conversational Agent's Capability to Identify Structural Wrongness in Arguments Based on Toulmin's Model of Arguments"
  identifier: "doi:10.3389/frai.2021.645516"
  license: CC BY 4.0
  license_evidence: "https://www.frontiersin.org/articles/10.3389/frai.2021.645516/full"
  fetch:
    method: pmc-oa
    url: "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC8680349"
  role: "Toulmin argumentation operationalized in an agent; bridges to the OpenScholar row"

- id: asai-2024-openscholar
  title: "OpenScholar: Synthesizing Scientific Literature with Retrieval-augmented LMs"
  identifier: "arxiv:2411.14199v1"
  license: CC BY 4.0
  license_evidence: "https://arxiv.org/abs/2411.14199v1"
  fetch:
    method: arxiv-pdf
    url: "https://export.arxiv.org/pdf/2411.14199v1"
  role: "The paper+repo pair: retrieval-augmented literature synthesis with a live companion repo"
  repo: "https://github.com/AkariAsai/OpenScholar"
```

In `pyproject.toml`, inside `[tool.setuptools.package-data]` (after line 31, `"memoria_vault.product.capabilities.operations" = ["*.md"]`), add:

```toml
"memoria_vault.product.seed_corpus" = ["*.yaml"]
```

In `tests/conftest.py` `TEST_LEVELS` (dict at :18), add alphabetically (immediately before `"test_seeded_errors.py": "runtime",` at :104):

```python
    "test_seed_manifest.py": "contract",
```

- [ ] **Step 4: Run to pass** — `python -m pytest tests/test_seed_manifest.py -v` → 8 passed.

- [ ] **Step 5: Perform the manual half of the §1 impl-start check** — open each of the eight `license_evidence` URLs in a browser, confirm the stated CC license and (for rows 4, 5, 7) the full titles the manifest ships; a failed row is replaced, never waived (spec §1). Record the check date in the commit body.

- [ ] **Step 6: Commit**

```
git add src/memoria_vault/product/seed_corpus/__init__.py src/memoria_vault/product/seed_corpus/manifest.yaml tests/test_seed_manifest.py tests/conftest.py pyproject.toml
git commit -m "feat(seed): ship the seed-corpus manifest, loader, and license impl-start check

Eight spec-pinned rows (O1 spec section 2); loader enforces the section 1
license floor and fetch-method enum; license evidence re-verified against
every row's evidence URL on the commit date.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task M.2: The per-method fetch/resolve layer (`resolve_fetch`)

**The capture seam, read first (required by this task).** `memoria work add --pdf` builds a `capture-pdf-source` payload from a *local* file (cli.py:877-895: `raw_pdf_base64` = base64 of `path.read_bytes()`), which the worker decodes and hands to the shipped local-PDF seam (worker.py:1276-1314). That seam's exact signature (runtime/capture.py:461-476):

```python
stage_pdf_source(
    vault: Path,
    work_id: str,
    title: str,
    description: str,
    raw_bytes: bytes,
    *,
    context: OperationContext,
    raw_filename: str = "source.pdf",
    resource: str = "",
    item_type: str = "article",
    identifiers: dict[str, Any] | None = None,
    csl_json: dict[str, Any] | None = None,
    provider_coverage: str = "partial",
    citekey: str = "",
) -> dict[str, Any]
```

It extracts page text via `_extract_pdf_pages` (capture.py:698-720, optional PyMuPDF — tests monkeypatch it, mirroring tests/test_capture.py:197-205), runs a coherence check, and stages an unchecked catalog row + blobs with a per-source commit (`stage_catalog_source`, capture.py:73-182). The spec's rationale for this layer: the shipped paths alone don't fit (`--url` runs HTML extraction on fetched bytes, `--pdf` reads only local files, `--doi` is metadata-only — cli.py:877-928, capture.py:433-434). M.2 supplies the download half: bytes in, `stage_pdf_source`-ready bytes out.

**Files:**

- Create `src/memoria_vault/runtime/seed_install.py` (this task: `resolve_fetch` + fetch helpers; M.3 adds `seed_install` to the same module)
- Create `tests/test_seed_install.py`
- Modify `tests/conftest.py` — `TEST_LEVELS` at :18 (new file registration; M.3 then extends this registered file with no further conftest change)

**Interfaces:**

- Consumes: `urllib.request.urlopen` (default opener only; never called in tests — bandit S310 is globally ignored for fixed-base URLs, pyproject.toml:122); stdlib `tarfile`, `io`, `xml.etree.ElementTree`.
- Produces: `resolve_fetch(row: dict[str, Any], *, opener: Callable[[str], Any] | None = None) -> bytes` — `opener(url)` must return a context-manager response exposing `.read() -> bytes`; `None` means the module-level `_default_opener` (urlopen with a 30 s timeout), resolved at call time so tests and the M.3 CLI test can monkeypatch `memoria_vault.runtime.seed_install._default_opener`. PMC handling: `oa.fcgi` XML record → prefer the `format="pdf"` link, else the `format="tgz"` package (PDF member extracted from the tarball); `ftp://` hrefs are rewritten to `https://` on the same host; `<error>` records and non-`%PDF-` payloads raise `ValueError` naming the URL.

- [ ] **Step 1: Write the failing tests** — create `tests/test_seed_install.py`:

```python
"""Contract tests for the seed-corpus fetch/resolve layer and seed install.

No network anywhere: every test injects a fake opener with canned XML, PDF,
and tar.gz bytes (spec section 1 fetch rule is exercised as URL assertions,
never as live fetches).
"""

from __future__ import annotations

import io
import tarfile

from memoria_vault.runtime.seed_install import resolve_fetch

PDF_BYTES = b"%PDF-1.4 seed fixture bytes\n"


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *_exc: object) -> bool:
        return False


def _opener(responses: dict[str, bytes]):
    calls: list[str] = []

    def opener(url: str) -> _FakeResponse:
        calls.append(url)
        if url not in responses:
            raise AssertionError(f"unexpected fetch: {url}")
        return _FakeResponse(responses[url])

    opener.calls = calls
    return opener


def _poisoned_opener(url: str) -> _FakeResponse:
    raise AssertionError(f"this run must not fetch: {url}")


def _pdf_url_row() -> dict:
    return {
        "id": "moreira-2019-retrieval-practice",
        "title": "Retrieval Practice in Classroom Settings: A Review of Applied Research",
        "identifier": "doi:10.3389/feduc.2019.00005",
        "license": "CC BY",
        "license_evidence": "https://www.frontiersin.org/articles/10.3389/feduc.2019.00005/full",
        "fetch": {
            "method": "pdf-url",
            "url": "https://www.frontiersin.org/articles/10.3389/feduc.2019.00005/pdf",
        },
        "role": "Tension pair B",
    }


def _pmc_row() -> dict:
    return {
        "id": "chen-2018-undesirable-difficulty",
        "title": "Undesirable Difficulty Effects in the Learning of High-Element "
        "Interactivity Materials",
        "identifier": "doi:10.3389/fpsyg.2018.01483",
        "license": "CC BY 4.0",
        "license_evidence": "https://www.frontiersin.org/articles/10.3389/fpsyg.2018.01483/full",
        "fetch": {
            "method": "pmc-oa",
            "url": "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC6099118",
        },
        "role": "Tension pair A",
    }


def _pmc_record_xml(pmcid: str, href: str, link_format: str) -> bytes:
    return (
        f'<OA><records returned-count="1" total-count="1">'
        f'<record id="{pmcid}" license="CC BY">'
        f'<link format="{link_format}" href="{href}"/>'
        f"</record></records></OA>"
    ).encode()


def _tarball(members: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, payload in members.items():
            info = tarfile.TarInfo(name=name)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
    return buffer.getvalue()


def test_resolve_fetch_pdf_url_downloads_the_pinned_pdf() -> None:
    row = _pdf_url_row()
    opener = _opener({row["fetch"]["url"]: PDF_BYTES})

    assert resolve_fetch(row, opener=opener) == PDF_BYTES
    assert opener.calls == [row["fetch"]["url"]]


def test_resolve_fetch_arxiv_pdf_downloads_the_pinned_version() -> None:
    row = _pdf_url_row()
    row["fetch"] = {"method": "arxiv-pdf", "url": "https://export.arxiv.org/pdf/2411.14199v1"}
    opener = _opener({"https://export.arxiv.org/pdf/2411.14199v1": PDF_BYTES})

    assert resolve_fetch(row, opener=opener) == PDF_BYTES


def test_resolve_fetch_pmc_oa_follows_the_pdf_link_and_rewrites_ftp() -> None:
    row = _pmc_row()
    ftp_href = "ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/aa/bb/PMC6099118.pdf"
    https_href = "https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/aa/bb/PMC6099118.pdf"
    opener = _opener(
        {
            row["fetch"]["url"]: _pmc_record_xml("PMC6099118", ftp_href, "pdf"),
            https_href: PDF_BYTES,
        }
    )

    assert resolve_fetch(row, opener=opener) == PDF_BYTES
    assert opener.calls == [row["fetch"]["url"], https_href]


def test_resolve_fetch_pmc_oa_extracts_the_pdf_member_from_a_tgz_package() -> None:
    row = _pmc_row()
    tgz_href = "https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_package/aa/bb/PMC6099118.tar.gz"
    package = _tarball(
        {
            "PMC6099118/fpsyg-09-01483.nxml": b"<article/>",
            "PMC6099118/fpsyg-09-01483.pdf": PDF_BYTES,
        }
    )
    opener = _opener(
        {
            row["fetch"]["url"]: _pmc_record_xml("PMC6099118", tgz_href, "tgz"),
            tgz_href: package,
        }
    )

    assert resolve_fetch(row, opener=opener) == PDF_BYTES


def test_resolve_fetch_pmc_oa_rejects_a_package_without_a_pdf_member() -> None:
    row = _pmc_row()
    tgz_href = "https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_package/aa/bb/PMC6099118.tar.gz"
    opener = _opener(
        {
            row["fetch"]["url"]: _pmc_record_xml("PMC6099118", tgz_href, "tgz"),
            tgz_href: _tarball({"PMC6099118/fpsyg-09-01483.nxml": b"<article/>"}),
        }
    )
    try:
        resolve_fetch(row, opener=opener)
    except ValueError as exc:
        assert "no PDF member" in str(exc)
    else:
        raise AssertionError("a package without a PDF member must fail the fetch")


def test_resolve_fetch_pmc_oa_surfaces_service_errors() -> None:
    row = _pmc_row()
    xml = b'<OA><error code="idIsNotOpenAccess">not in the OA subset</error></OA>'
    opener = _opener({row["fetch"]["url"]: xml})
    try:
        resolve_fetch(row, opener=opener)
    except ValueError as exc:
        assert "idIsNotOpenAccess" in str(exc)
    else:
        raise AssertionError("an OA-service error record must fail the fetch")


def test_resolve_fetch_rejects_non_pdf_bytes() -> None:
    row = _pdf_url_row()
    opener = _opener({row["fetch"]["url"]: b"<html>login wall</html>"})
    try:
        resolve_fetch(row, opener=opener)
    except ValueError as exc:
        assert "not a PDF" in str(exc)
    else:
        raise AssertionError("non-PDF bytes must fail the fetch")


def test_resolve_fetch_requires_https() -> None:
    row = _pdf_url_row()
    row["fetch"]["url"] = "http://insecure.test/paper.pdf"
    try:
        resolve_fetch(row, opener=_opener({}))
    except ValueError as exc:
        assert "https" in str(exc)
    else:
        raise AssertionError("non-https fetch URLs must be refused")
```

- [ ] **Step 2: Run and watch it fail** — `python -m pytest tests/test_seed_install.py -v` → collection error: `ModuleNotFoundError: No module named 'memoria_vault.runtime.seed_install'`.

- [ ] **Step 3: Minimal implementation.** Create `src/memoria_vault/runtime/seed_install.py`:

```python
"""Seed-corpus fetch/resolve layer in front of the shipped capture seams.

O1 spec section 2: the shipped capture paths alone do not fit the corpus
(cli.py work-add: --url runs HTML extraction, --pdf reads only local files,
--doi is metadata-only), so this module downloads each manifest row with no
credentials and hands raw PDF bytes to capture.stage_pdf_source - the same
code path as `memoria work add --pdf`, fed from a download instead of a file.
"""

from __future__ import annotations

import io
import tarfile
import xml.etree.ElementTree as ElementTree
from collections.abc import Callable
from typing import Any
from urllib.request import urlopen


def _default_opener(url: str):
    return urlopen(url, timeout=30.0)


def resolve_fetch(
    row: dict[str, Any], *, opener: Callable[[str], Any] | None = None
) -> bytes:
    """Fetch one manifest row's PDF bytes per its declared fetch method."""
    opener = opener or _default_opener
    fetch = row.get("fetch") if isinstance(row.get("fetch"), dict) else {}
    method = str(fetch.get("method") or "")
    url = str(fetch.get("url") or "")
    if method in {"pdf-url", "arxiv-pdf"}:
        return _require_pdf(_fetch_bytes(url, opener), url)
    if method == "pmc-oa":
        return _resolve_pmc_oa(url, opener)
    raise ValueError(f"seed row {row.get('id')}: unsupported fetch method {method!r}")


def _fetch_bytes(url: str, opener: Callable[[str], Any]) -> bytes:
    if not url.startswith("https://"):
        raise ValueError(f"seed fetch requires an https URL: {url}")
    with opener(url) as response:
        return response.read()


def _require_pdf(raw: bytes, url: str) -> bytes:
    if not raw.startswith(b"%PDF-"):
        raise ValueError(f"fetched bytes from {url} are not a PDF")
    return raw


def _resolve_pmc_oa(record_url: str, opener: Callable[[str], Any]) -> bytes:
    """Resolve one PMC OA-service record (oa.fcgi XML) to its PDF bytes."""
    record = _fetch_bytes(record_url, opener)
    root = ElementTree.fromstring(record)  # noqa: S314 -- fixed NCBI OA endpoint over https; stdlib etree does not resolve external entities.
    error = root.find(".//error")
    if error is not None:
        code = error.get("code") or "unknown"
        raise ValueError(f"PMC OA service error for {record_url}: {code}")
    links = {
        str(link.get("format") or ""): str(link.get("href") or "")
        for link in root.iter("link")
    }
    if pdf_href := links.get("pdf"):
        return _require_pdf(_fetch_bytes(_https_href(pdf_href), opener), pdf_href)
    if tgz_href := links.get("tgz"):
        package = _fetch_bytes(_https_href(tgz_href), opener)
        return _pdf_from_tarball(package, tgz_href)
    raise ValueError(f"PMC OA record at {record_url} carries no pdf or tgz link")


def _https_href(href: str) -> str:
    # The OA service hands out ftp:// hrefs; ftp.ncbi.nlm.nih.gov serves the
    # same paths over https, and the section 1 fetch rule is https-only.
    if href.startswith("ftp://"):
        return "https://" + href.removeprefix("ftp://")
    return href


def _pdf_from_tarball(package: bytes, href: str) -> bytes:
    with tarfile.open(fileobj=io.BytesIO(package), mode="r:gz") as archive:
        for member in archive.getmembers():
            if member.isfile() and member.name.lower().endswith(".pdf"):
                handle = archive.extractfile(member)
                if handle is None:
                    continue
                return _require_pdf(handle.read(), f"{href}!{member.name}")
    raise ValueError(f"PMC OA package from {href} contains no PDF member")
```

In `tests/conftest.py` `TEST_LEVELS` (dict at :18), add alphabetically (immediately before the M.1 entry `"test_seed_manifest.py": "contract",`):

```python
    "test_seed_install.py": "contract",
```

- [ ] **Step 4: Run to pass** — `python -m pytest tests/test_seed_install.py -v` → 8 passed.

- [ ] **Step 5: Commit**

```
git add src/memoria_vault/runtime/seed_install.py tests/test_seed_install.py tests/conftest.py
git commit -m "feat(seed): per-method fetch/resolve layer for the seed corpus

pdf-url/arxiv-pdf download the pinned PDF directly; pmc-oa resolves the
oa.fcgi XML record to its pdf or tgz link (PDF member extracted from the
package), all https-only via an injectable opener.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task M.3: `memoria seed install` — engine function, worker operation, CLI

**Files:**

- Modify `src/memoria_vault/runtime/seed_install.py` (add `seed_install` + row-metadata helpers + the guarded telemetry emit; module created in M.2)
- Create `src/memoria_vault/product/capabilities/operations/seed-install.md` (capability manifest; shape mirrors `capture-pdf-source.md:1-30`; `runner` is auto-defaulted by `_manifest_frontmatter`, runtime/capabilities.py:157-163)
- Modify `src/memoria_vault/runtime/worker.py` — `PROTECTED_OPERATION_ACTORS` (:53-66, add pi-only entry) and the operation dispatch (insert branch after the `capture-pdf-source` branch at :1041-1042)
- Modify `src/memoria_vault/cli.py` — register `_seed_commands(sub)` after `_work_commands(sub)` (:133); new `_seed_commands` + `_cmd_seed_install`
- Modify `tests/floor_lib.py` — `OPERATION_REGISTRY` (:450) gains the `seed-install` entry (required by `test_every_operation_has_a_floor_entry`, tests/test_floor_coverage.py:37-42)
- Modify `tests/test_cli.py` — the exact-command-surface set (:73-146) gains `"memoria seed install"`
- Modify `tests/test_seed_install.py` (extend the M.2 file — already registered in `TEST_LEVELS`, so **no conftest change** in this task)

**Interfaces:**

- Consumes: `stage_pdf_source(...)` (exact signature in M.2's header; runtime/capture.py:461-476); `state.catalog_source(vault: Path, source_ref: str) -> dict[str, Any] | None` (runtime/state.py:1603-1612); `load_seed_manifest() -> list[dict[str, Any]]` (M.1); `resolve_fetch(row, *, opener=None) -> bytes` (M.2); `iter_markdown(vault, skip_dirs=None) -> Iterator[Path]` (runtime/vaultio.py:217-226) and `read_frontmatter(path) -> dict[str, Any]` (runtime/vaultio.py:66-67); `validate_operation_context(vault, context)` / `OperationContext` (runtime/trusted_writer.py, as used at capture.py:94); `engine_api.run_operation(...)` via `cli._enqueue_and_run(args, operation_id, payload)` (cli.py:2087-2098); `_csl_json` shape (cli.py:2544-2550, mirrored); **section T seam (order-tolerant):** `emit_onboarding_step(vault: Path, step: str) -> None` — guarded import from `memoria_vault.runtime.onboarding_steps`; run `grep -rn "def emit_onboarding_step" src/memoria_vault/` first and re-anchor if T placed it elsewhere; empty grep ⇒ the guard no-ops with the recorded gap.
- Produces: `seed_install(vault: Path, rows: list[dict[str, Any]] | None = None, *, opener: Callable[[str], Any] | None = None, context: OperationContext) -> dict[str, Any]` returning `{"admitted": list[str], "skipped": list[str], "failed": list[dict[str, str]] (each {"id", "error"}), "notices": list[str], "telemetry": "emitted" | "skipped-helper-not-landed"}` — raises `ValueError` (⇒ failed job ⇒ CLI exit 1) iff `admitted + skipped` is empty; worker operation id `"seed-install"` (PI-only, payload `{}`); CLI `memoria seed install --workspace <path> [--json|--quiet] [--actor pi|agent]` — the tutorial section (chapter 02 rewiring) and LOOP.13's amended time-to-first-answer block cite this exact CLI path, so this task must merge before any docs task backticks it (doc-claims gate sequencing).

- [ ] **Step 1: Grep-first order-tolerance check** — run `grep -rn "def emit_onboarding_step" src/memoria_vault/`. If it hits, note the module and use it in the guarded import below; if empty (section T not landed), keep `memoria_vault.runtime.onboarding_steps` as written (section T's declared home).

- [ ] **Step 2: Write the failing tests** — extend `tests/test_seed_install.py`. Replace the import block with:

```python
from __future__ import annotations

import io
import json
import sys
import tarfile
import types
from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.seed_install import resolve_fetch, seed_install
from tests.helpers import (
    call_with_context,
    copy_memoria_dirs,
    git,
    init_cli_workspace,
    init_git,
)
```

Append (arrange blocks mirror the capture fixtures: `workspace` = tests/test_capture.py:59-62; the `_extract_pdf_pages` monkeypatch = tests/test_capture.py:197-205; context plumbing = `call_with_context`, tests/helpers.py:71-83):

```python
def _workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas")
    init_git(tmp_path, "seed@example.invalid", "Seed")
    return tmp_path


def _patch_pdf_pages(monkeypatch) -> None:
    monkeypatch.setattr(
        "memoria_vault.runtime.capture._extract_pdf_pages",
        lambda _raw: [{"page": 1, "text": "The seed fixture reports one anchored finding."}],
    )


def _seed_install(vault: Path, **kwargs):
    return call_with_context(seed_install, vault, **kwargs)


def test_seed_install_admits_rows_through_the_pdf_capture_seam(tmp_path, monkeypatch) -> None:
    vault = _workspace(tmp_path)
    _patch_pdf_pages(monkeypatch)
    pdf_row, pmc_row = _pdf_url_row(), _pmc_row()
    href = "https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/aa/bb/PMC6099118.pdf"
    opener = _opener(
        {
            pdf_row["fetch"]["url"]: PDF_BYTES,
            pmc_row["fetch"]["url"]: _pmc_record_xml(
                "PMC6099118", "ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/aa/bb/PMC6099118.pdf", "pdf"
            ),
            href: PDF_BYTES,
        }
    )

    result = _seed_install(vault, rows=[pdf_row, pmc_row], opener=opener)

    assert result["admitted"] == [pdf_row["id"], pmc_row["id"]]
    assert result["skipped"] == []
    assert result["failed"] == []
    source = state.catalog_source(vault, pdf_row["id"])
    assert source is not None
    assert source["check_status"] == "unchecked"
    assert source["identifiers"]["doi"] == "10.3389/feduc.2019.00005"
    assert source["resource"] == "https://doi.org/10.3389/feduc.2019.00005"
    assert source["csl_json"]["DOI"] == "10.3389/feduc.2019.00005"
    assert state.catalog_source(vault, pmc_row["id"]) is not None


def test_seed_install_rerun_skips_without_fetch_journal_or_commit(tmp_path, monkeypatch) -> None:
    vault = _workspace(tmp_path)
    _patch_pdf_pages(monkeypatch)
    row = _pdf_url_row()
    first = _seed_install(vault, rows=[row], opener=_opener({row["fetch"]["url"]: PDF_BYTES}))
    assert first["admitted"] == [row["id"]]
    journal = vault / ".memoria/journal/test-machine.jsonl"
    events_before = journal.read_text(encoding="utf-8").count("\n")
    head_before = git(vault, "rev-parse", "HEAD")

    rerun = _seed_install(vault, rows=[row], opener=_poisoned_opener)

    assert rerun["admitted"] == []
    assert rerun["failed"] == []
    assert rerun["skipped"] == [row["id"]]
    assert journal.read_text(encoding="utf-8").count("\n") == events_before
    assert git(vault, "rev-parse", "HEAD") == head_before


def test_seed_install_continues_past_a_failed_row(tmp_path, monkeypatch) -> None:
    vault = _workspace(tmp_path)
    _patch_pdf_pages(monkeypatch)
    bad, good = _pmc_row(), _pdf_url_row()
    xml = b'<OA><error code="idIsNotOpenAccess">nope</error></OA>'
    opener = _opener({bad["fetch"]["url"]: xml, good["fetch"]["url"]: PDF_BYTES})

    result = _seed_install(vault, rows=[bad, good], opener=opener)

    assert result["admitted"] == [good["id"]]
    assert [entry["id"] for entry in result["failed"]] == [bad["id"]]
    assert "idIsNotOpenAccess" in result["failed"][0]["error"]


def test_seed_install_fails_only_when_zero_rows_present(tmp_path, monkeypatch) -> None:
    vault = _workspace(tmp_path)
    _patch_pdf_pages(monkeypatch)
    row = _pdf_url_row()
    opener = _opener({row["fetch"]["url"]: b"<html>outage page</html>"})
    try:
        _seed_install(vault, rows=[row], opener=opener)
    except ValueError as exc:
        assert "zero rows present" in str(exc)
        assert row["id"] in str(exc)
    else:
        raise AssertionError("first-run emptiness must be the failure exit")


def test_frame_first_notice_tracks_active_projects(tmp_path, monkeypatch) -> None:
    vault = _workspace(tmp_path)
    _patch_pdf_pages(monkeypatch)
    row = _pdf_url_row()

    result = _seed_install(vault, rows=[row], opener=_opener({row["fetch"]["url"]: PDF_BYTES}))
    assert any("frame your" in notice for notice in result["notices"])

    archived = vault / "projects/old/project.md"
    archived.parent.mkdir(parents=True)
    archived.write_text(
        "---\ntype: project\ntitle: Old project\nlifecycle: archived\n"
        "tags: []\nlinks: {}\n---\n# Old project\n",
        encoding="utf-8",
    )
    rerun = _seed_install(vault, rows=[row], opener=_poisoned_opener)
    assert any("frame your" in notice for notice in rerun["notices"])

    active = vault / "projects/tutorial/project.md"
    active.parent.mkdir(parents=True)
    active.write_text(
        "---\ntype: project\ntitle: Tutorial project\ntags: []\nlinks: {}\n"
        "---\n# Tutorial project\n",
        encoding="utf-8",
    )
    final = _seed_install(vault, rows=[row], opener=_poisoned_opener)
    assert final["notices"] == []


def test_seed_installed_step_emits_when_the_section_t_helper_exists(
    tmp_path, monkeypatch
) -> None:
    vault = _workspace(tmp_path)
    _patch_pdf_pages(monkeypatch)
    calls: list[tuple[Path, str]] = []
    fake = types.ModuleType("memoria_vault.runtime.onboarding_steps")
    fake.emit_onboarding_step = lambda vault, step: calls.append((Path(vault), step))
    monkeypatch.setitem(sys.modules, "memoria_vault.runtime.onboarding_steps", fake)
    row = _pdf_url_row()

    result = _seed_install(vault, rows=[row], opener=_opener({row["fetch"]["url"]: PDF_BYTES}))

    assert result["telemetry"] == "emitted"
    assert calls == [(vault, "seed-installed")]


def test_seed_installed_step_noops_when_the_helper_is_absent(tmp_path, monkeypatch) -> None:
    vault = _workspace(tmp_path)
    _patch_pdf_pages(monkeypatch)
    # None in sys.modules makes the import raise ImportError deterministically,
    # even after section T lands - this pins the order-tolerance guard forever.
    monkeypatch.setitem(sys.modules, "memoria_vault.runtime.onboarding_steps", None)
    row = _pdf_url_row()

    result = _seed_install(vault, rows=[row], opener=_opener({row["fetch"]["url"]: PDF_BYTES}))

    assert result["telemetry"] == "skipped-helper-not-landed"


def test_memoria_seed_install_cli_end_to_end_offline(tmp_path, capsys, monkeypatch) -> None:
    from memoria_vault.cli import main
    from memoria_vault.product.seed_corpus import load_seed_manifest

    workspace = init_cli_workspace(tmp_path, capsys)
    _patch_pdf_pages(monkeypatch)
    responses: dict[str, bytes] = {}
    for row in load_seed_manifest():
        url = row["fetch"]["url"]
        if row["fetch"]["method"] == "pmc-oa":
            pmcid = url.rsplit("=", 1)[-1]
            responses[url] = _pmc_record_xml(
                pmcid, f"ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/{pmcid}.pdf", "pdf"
            )
            responses[f"https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/{pmcid}.pdf"] = PDF_BYTES
        else:
            responses[url] = PDF_BYTES
    monkeypatch.setattr(
        "memoria_vault.runtime.seed_install._default_opener", _opener(responses)
    )

    rc = main(["seed", "install", "--workspace", str(workspace), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["ok"] is True
    all_ids = sorted(row["id"] for row in load_seed_manifest())
    assert sorted(payload["result"]["admitted"]) == all_ids
    assert any("frame your" in notice for notice in payload["result"]["notices"])

    # Acceptance-criteria idempotence: the re-run admits nothing new, exits
    # clean, and performs zero fetches (a fetch would raise loudly).
    monkeypatch.setattr(
        "memoria_vault.runtime.seed_install._default_opener", _poisoned_opener
    )
    rc = main(["seed", "install", "--workspace", str(workspace), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["result"]["admitted"] == []
    assert sorted(payload["result"]["skipped"]) == all_ids


def test_seed_install_requires_pi_actor(tmp_path, capsys) -> None:
    from memoria_vault.cli import main

    workspace = init_cli_workspace(tmp_path, capsys)

    rc = main(["seed", "install", "--workspace", str(workspace), "--actor", "agent", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert payload["ok"] is False
    assert "requires PI actor authority" in str(payload["result"]["error"])
```

Also edit `tests/test_cli.py`: in `test_cli_command_surface_is_exact` (:73-146), add `"memoria seed install",` after `"memoria work export",` (:94).

- [ ] **Step 3: Run and watch it fail** — `python -m pytest tests/test_seed_install.py tests/test_cli.py::test_cli_command_surface_is_exact -v` → `ImportError: cannot import name 'seed_install' from 'memoria_vault.runtime.seed_install'` (collection), and the surface test fails on the missing `memoria seed install` once collection is fixed.

- [ ] **Step 4: Minimal implementation.**

**(a)** Append to `src/memoria_vault/runtime/seed_install.py` (extend the M.2 import block with `from pathlib import Path`, `from memoria_vault.product.seed_corpus import load_seed_manifest`, `from memoria_vault.runtime import state`, `from memoria_vault.runtime.capture import stage_pdf_source`, `from memoria_vault.runtime.trusted_writer import OperationContext, validate_operation_context`, `from memoria_vault.runtime.vaultio import iter_markdown, read_frontmatter`):

```python
def seed_install(
    vault: Path,
    rows: list[dict[str, Any]] | None = None,
    *,
    opener: Callable[[str], Any] | None = None,
    context: OperationContext,
) -> dict[str, Any]:
    """Install the seed corpus through the shipped local-PDF capture seam.

    Idempotency and honesty (O1 spec section 2): each row pre-checks
    state.catalog_source and skips on a hit - no fetch, no journal event,
    no commit; failures are per-row and named; the failure exit fires only
    when zero rows are present (admitted + skipped both empty).
    """
    validate_operation_context(vault, context)
    vault = Path(vault)
    if rows is None:
        rows = load_seed_manifest()
    admitted: list[str] = []
    skipped: list[str] = []
    failed: list[dict[str, str]] = []
    for row in rows:
        work_id = str(row["id"])
        if state.catalog_source(vault, work_id) is not None:
            skipped.append(work_id)
            continue
        try:
            raw = resolve_fetch(row, opener=opener)
            stage_pdf_source(
                vault,
                work_id,
                str(row["title"]),
                f"Seed corpus source: {row['title']}",
                raw,
                context=context,
                raw_filename=f"{work_id}.pdf",
                resource=_row_resource(row),
                identifiers=_row_identifiers(row),
                csl_json=_row_csl(row),
            )
        except Exception as exc:  # noqa: BLE001 -- per-row honesty: name the row, keep going.
            failed.append({"id": work_id, "error": str(exc)})
            continue
        admitted.append(work_id)
    if not admitted and not skipped:
        names = ", ".join(entry["id"] for entry in failed) or "<no rows>"
        raise ValueError(f"seed install left zero rows present; failed rows: {names}")
    notices: list[str] = []
    if not _has_active_project(vault):
        notices.append(
            "no active project found - frame your tutorial project first "
            "(docs/tutorials/01) or discovery ranking starts empty"
        )
    return {
        "admitted": admitted,
        "skipped": skipped,
        "failed": failed,
        "notices": notices,
        "telemetry": _emit_seed_installed(vault),
    }


def _row_identifiers(row: dict[str, Any]) -> dict[str, Any]:
    identifier = str(row.get("identifier") or "")
    if identifier.startswith("doi:"):
        return {"doi": identifier.removeprefix("doi:")}
    if identifier.startswith("arxiv:"):
        return {"arxiv": identifier.removeprefix("arxiv:")}
    return {}


def _row_resource(row: dict[str, Any]) -> str:
    identifier = str(row.get("identifier") or "")
    if identifier.startswith("doi:"):
        return f"https://doi.org/{identifier.removeprefix('doi:')}"
    if identifier.startswith("arxiv:"):
        return f"https://arxiv.org/abs/{identifier.removeprefix('arxiv:')}"
    return str(row.get("license_evidence") or "")


def _row_csl(row: dict[str, Any]) -> dict[str, Any]:
    # Mirrors cli._csl_json (cli.py:2544-2550) so seed rows carry the same
    # catalog metadata shape as `memoria work add`.
    csl: dict[str, Any] = {
        "id": str(row["id"]),
        "type": "article-journal",
        "title": str(row["title"]),
    }
    identifiers = _row_identifiers(row)
    if "doi" in identifiers:
        csl["DOI"] = identifiers["doi"]
    resource = _row_resource(row)
    if resource:
        csl["URL"] = resource
    return csl


def _has_active_project(vault: Path) -> bool:
    # Active = type: project and not lifecycle archived/retracted - the repo's
    # concept-file convention (knowledge.py _is_current_frontmatter); covers
    # projects/<slug>.md and projects/<slug>/project.md homes.
    projects_root = vault / "projects"
    if not projects_root.is_dir():
        return False
    for path in iter_markdown(projects_root):
        frontmatter = read_frontmatter(path)
        if frontmatter.get("type") != "project":
            continue
        if frontmatter.get("lifecycle") in {"retracted", "archived"}:
            continue
        return True
    return False


def _emit_seed_installed(vault: Path) -> str:
    """Order-tolerant onboarding-step emit; section T owns the helper."""
    try:
        from memoria_vault.runtime.onboarding_steps import emit_onboarding_step
    except ImportError:
        return "skipped-helper-not-landed"
    emit_onboarding_step(vault, "seed-installed")
    return "emitted"
```

**(b)** Create `src/memoria_vault/product/capabilities/operations/seed-install.md`:

```markdown
---
title: Seed corpus install
type: operation
description: Install the shipped seed-corpus manifest rows as catalog Work rows.
operation_id: seed-install
allowed_tools:
- trusted_writer
allowed_paths:
- .memoria/blobs/source-content/
- .memoria/journal/
allowed_network:
- https://
prompt_version: seed-install.v1
io_schema:
  input: seed_manifest
  output: catalog_work_rows
risk_class: medium
required_checks:
- memoria-runtime
tags:
- onboarding
- capture
id: operations/seed-install
links: {}
---

# Operation

Iterate the shipped seed corpus manifest, skip rows already present in the
catalog, download each remaining row over https with no credentials, and
stage the bytes through the local PDF capture seam as unchecked catalog Work
rows. PI-only: onboarding is a PI action, so agent surfaces cannot trigger
these fetches.
```

**(c)** `src/memoria_vault/runtime/worker.py`: in `PROTECTED_OPERATION_ACTORS` (:53-66) add `"seed-install": "pi",` after `"cascade-rollback": "pi",` (:63). In `_run_operation_job`, insert after the `capture-pdf-source` branch (:1041-1042):

```python
    if operation_id == "seed-install":
        from memoria_vault.runtime.seed_install import seed_install

        return seed_install(vault, context=context)
```

(The returned dict has no `status` key, so `_run_claimed_job`'s `job.update({..., **result})` at worker.py:228 stays honest.)

**(d)** `src/memoria_vault/cli.py`: add `_seed_commands(sub)` on its own line after `_work_commands(sub)` (:133), and define (near `_work_commands`, after :256):

```python
def _seed_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    seed = sub.add_parser("seed")
    seed_sub = seed.add_subparsers(dest="seed_command", required=True)

    install = seed_sub.add_parser("install")
    _common(install)
    install.set_defaults(handler=_cmd_seed_install)


def _cmd_seed_install(args: argparse.Namespace) -> int:
    output = _enqueue_and_run(args, "seed-install", {})
    result = output.get("result") if isinstance(output.get("result"), dict) else {}
    if not args.json and not args.quiet:
        for notice in result.get("notices") or []:
            print(f"notice: {notice}", file=sys.stderr)
        for entry in result.get("failed") or []:
            print(f"failed row {entry.get('id')}: {entry.get('error')}", file=sys.stderr)
    return _emit(output, args)
```

**(e)** `tests/floor_lib.py`: in `OPERATION_REGISTRY` (:450), add alphabetically among the existing entries:

```python
    # seed-install is PROTECTED_OPERATION_ACTORS "pi"-only (worker.py) and the
    # sweep enqueues as actor="agent", so - like curate-note-link above - the
    # actor-authority check refuses deterministically before the operation
    # body (and its https fetches, which this offline harness must never
    # depend on) ever runs.
    "seed-install": {
        "payload": {},
        "expect": "refused",
        "reason": "requires PI actor authority",
    },
```

- [ ] **Step 5: Run to pass** — `python -m pytest tests/test_seed_install.py tests/test_seed_manifest.py tests/test_cli.py tests/test_capabilities.py tests/test_floor_coverage.py -v` → all pass (test_capabilities.py:61-79 proves the manifest/dispatch two-way parity; test_floor_coverage.py:37-42 proves the floor entry).

- [ ] **Step 6: Section gate** — run `python scripts/verify` and confirm a clean exit (lint incl. cspell/yamllint on the new files, contract + floor suites, offline e2e smoke, syntax checks).

- [ ] **Step 7: Commit**

```
git add src/memoria_vault/runtime/seed_install.py src/memoria_vault/cli.py src/memoria_vault/runtime/worker.py src/memoria_vault/product/capabilities/operations/seed-install.md tests/floor_lib.py tests/test_cli.py tests/test_seed_install.py
git commit -m "feat(seed): memoria seed install - engine, worker operation, CLI

Per-row work_id pre-check (skip on hit: no fetch/journal/commit), per-row
failure honesty, zero-rows-present failure exit, frame-first notice, and an
order-tolerant seed-installed onboarding-step emit (section T owns the
helper; guarded import no-ops with a recorded gap until it lands). PI-only
worker operation with capability manifest and floor-registry entry.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

# S — Derived steering + thin override

Implements spec §4 (steering: derived signal + thin override — the *steering vs projects* rethink-audit verdict) as §9 slices 3–4, and satisfies the §8 acceptance sentences on project-ranked candidates, muted-term subtraction, non-empty effective steering from one framed project, and a reseeded `steering.md` that contributes zero tokens beyond watch entries. Three tasks: **S.1** builds the derived-token unit in a new `runtime/steering.py` (the tokenizer moves there from `knowledge.py`), **S.2** switches the single discovery-relevance call site onto it and deletes the whole-file `_steering_tokens`, **S.3** reseeds `steering.md` as the two-section override file and repoints `memoria steering show` at the provenance render.

**Grounding verified at origin/main post-#1502 (07bedc74):**

- `knowledge.py:1193-1197` `_steering_tokens(vault) -> set[str]` (whole-file bag), `:1200-1226` `_discovery_relevance(steering_tokens, source, edge)` with the channel rule at `:1214` (`channel = "ranked" if title_overlap or tag_overlap else "exploration"`), `:1229-1235` `_relevance_tokens(*values) -> set[str]`, `:85-100` `_DISCOVERY_RELEVANCE_STOPWORDS = _TAG_CANDIDATE_STOPWORDS | {…}` (`_TAG_CANDIDATE_STOPWORDS` itself at `:70-84` stays — its other consumer is the tag-candidate sweep at `:1299`).
- **Single call site confirmed:** `_steering_tokens` is called once at `knowledge.py:1142` and `_discovery_relevance` once at `:1160`, both inside `_write_gap_discovery_candidates` (`:1124-1190`). **The enrichment discovery path computes no relevance:** `enrichment.py:283` calls `_write_discovery_candidate(vault, source, edge)` bare, and `_write_discovery_candidate` (`enrichment.py:438-476`) only writes the candidate file — relevance annotation happens exclusively in the gap path via `_annotate_discovery_candidate` (`knowledge.py:1162`, `:1238-1250`). So S.2 switches exactly one call site; enrichment-raised candidates stay un-annotated as shipped (out of scope — no behavior change there).
- Because the mute is token-set subtraction feeding the unchanged `:1214` channel rule, a candidate matching a muted term *and* a surviving project token still ranks — **no change to `_discovery_relevance` is needed**, only to the set passed in.
- `cli.py:139` wires `steering {show, edit}` via `_simple_resource` (`:509-515`); `_cmd_steering_show` at `:2001-2007` renders the raw body; `_cmd_steering_edit` at `:2010-2034` is untouched. `_emit` (`:3092`) prints the `path` key in non-JSON mode, and `_cmd_export` (`:1256-1261`) is the shipped precedent for a custom non-JSON render before falling through to `_emit`.
- Seeded file: `src/memoria_vault/product/workspace_seed/steering.md` (49 lines, five authored sections + placeholder bullets — the pollution the audit named). Seed schemas: `project.yaml` (`archived` :11, `thesis` :13), `hub.yaml` (required `tag` :9, `archived` :12), `note.yaml` (`mode` enum `[claim, question, definition, work]` :4, `question_status` `[open, resolved]` :5, `archived` :17).
- Readers are tolerant: `read_frontmatter` (`vaultio.py:66`) returns `{}` for missing/invalid frontmatter; `iter_markdown` (`vaultio.py:217-226`) prunes `DEFAULT_SKIP_DIRS` (`:15` — `.git`, `.memoria`, `.obsidian`, `node_modules`), so machine staging under `.memoria/staging/` never contributes.
- Existing coverage: `tests/test_gap_analysis.py:394-442` is the one steering-driven relevance test (it writes whole-file prose — S.2 rewrites its arrange); `tests/test_cli_workspace_requests.py:1482-1484` smoke-asserts only `steering["path"] == "steering.md"`, which the new payload retains, so it keeps passing untouched. `tests/conftest.py:18-121` `TEST_LEVELS` registration is enforced by `tests/test_testing_levels.py:10-14`.

**Cross-plan boundaries:** no task in this section records telemetry, so the I1 `record_telemetry_event` seam is not consumed here (the `onboarding-step` emits are slice 5, another section). The docs sweep (chapter 07, `memory-model.md`, `run-the-weekly-review.md`, `cli.md` rows) is slice 7, another section — this section touches no file under `docs/`, so the doc-claims gate is unaffected (it also skips product seed files by construction, `scripts/checks/doc_claims_gate.py:67-74`).

**SPEC GAP resolutions** (each also restated at its point of use):

1. **Hub singular `tag` field.** Spec §4.1 says hubs contribute "title + tags"; `hub.yaml:9` also *requires* a singular `tag: str` while `tags` may be empty on hand-authored hubs. Resolution: include `tag` in the hub contribution. For CLI-created hubs it is a no-op (`_cmd_new_hub`, `cli.py:844`, already puts the tag into `tags`); for hand-authored hubs it is the hub's topic identity.
2. **Archived hubs and question notes.** Spec §4.1 states the archived exclusion only for projects. Resolution: apply `archived: true` exclusion uniformly — `hub.yaml:12` and `note.yaml:17` both define `archived: bool`, and boosting archived hubs would recreate the inactive-topics-boost defect the audit verdict subsumed (spec appendix).
3. **Resolved question notes.** Spec §4.1 says "`mode: question` notes — title tokens" with the gloss "open questions are vault content"; `note.yaml` requires `question_status` (`open`/`resolved`) on question notes. Resolution: exclude `question_status: resolved` — a settled question must not keep steering discovery.
4. **`steering show` on a missing `steering.md`.** Spec §4.3 is silent; derived tokens are computable without the file. Resolution: keep the shipped not-found failure (`cli.py:2003-2004`) — `memoria init` always seeds the file, and preserving the guard keeps the existing CLI failure contract unchanged.

---

### Task S.1: `effective_steering_tokens` in a new `runtime/steering.py` (tokenizer moves in)

**Decision (move direction):** `_relevance_tokens` + its stopword set move *into* `steering.py`, and `knowledge.py` imports the tokenizer from there. The other direction (steering importing from knowledge) is wrong twice over: `knowledge.py` is a 3,300-line module with heavy transitive imports (`operations`, `trusted_writer`, `state`), and S.2 adds a `knowledge → steering` import, so `steering → knowledge` would cycle. `RELEVANCE_STOPWORDS` is written as one flat frozenset (the expanded union of `knowledge.py:70-84`'s 11 function words and `:85-100`'s 14 vault-vocabulary words); `_TAG_CANDIDATE_STOPWORDS` stays in `knowledge.py` for its remaining consumer at `:1299`. This task is behavior-preserving: `_steering_tokens` still exists (whole-file) until S.2, now calling the moved tokenizer.

**Files:**
- Create: `src/memoria_vault/runtime/steering.py`
- Modify: `src/memoria_vault/runtime/knowledge.py` (delete `:85-100` `_DISCOVERY_RELEVANCE_STOPWORDS` and `:1229-1235` `_relevance_tokens`; add one import between `:33` and `:34`; repoint the three `_relevance_tokens` uses at `:1197`, `:1207`, `:1211`)
- Create: `tests/test_steering_tokens.py`
- Modify: `tests/conftest.py` (register the new file in `TEST_LEVELS`, between `:107` and `:108`)

**Interfaces:**
- Consumes: `iter_markdown(vault: Path, skip_dirs: set[str] | frozenset[str] | None = None) -> Iterator[Path]` (`vaultio.py:217`); `read_frontmatter(path: Path) -> dict[str, Any]` (`vaultio.py:66`); `split_frontmatter(text: str) -> tuple[dict[str, Any], str]` (`vaultio.py:70`).
- Produces: `memoria_vault.runtime.steering.relevance_tokens(*values: object) -> set[str]`; `RELEVANCE_STOPWORDS: frozenset[str]`; `steering_overrides(vault: Path) -> tuple[set[str], set[str]]` (watch, mute); `effective_steering_tokens(vault: Path) -> set[str]`; private `_token_sources(vault: Path) -> dict[str, set[str]]` (token → labels `project:<rel>` / `hub:<rel>` / `question:<rel>` / `watch` — S.3's provenance render consumes this).

**Steps:**

- [ ] Write the failing test file `tests/test_steering_tokens.py` (new file — register it in the same step; the vault fixtures are bare `tmp_path` directories, no git/schemas needed because `steering.py` only reads markdown):

```python
"""Contract tests for the derived-steering unit (runtime/steering.py)."""

from __future__ import annotations

from pathlib import Path

from memoria_vault.runtime.steering import (
    RELEVANCE_STOPWORDS,
    effective_steering_tokens,
    relevance_tokens,
    steering_overrides,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _concept(path: Path, frontmatter: str) -> None:
    _write(path, f"---\n{frontmatter}---\n\nBody.\n")


def test_relevance_tokens_casefold_stopword_short_and_digit_filters() -> None:
    tokens = relevance_tokens("The Spaced-Repetition MODEL", "v2", 2024, None, "")

    assert tokens == {"spaced", "repetition", "model"}
    assert {"the", "steering", "works"} <= RELEVANCE_STOPWORDS


def test_steering_overrides_reads_only_watch_and_muted_bullets(tmp_path: Path) -> None:
    _write(
        tmp_path / "steering.md",
        "---\ntype: system\ntitle: Steering\n---\n\n"
        "# Steering\n\n"
        "Prose about desirable difficulties never contributes.\n\n"
        "## Watch for\n\n"
        "> guidance blockquote is ignored\n\n"
        "- retrieval practice\n"
        "* interleaving\n\n"
        "## Muted\n\n"
        "- spaced repetition\n\n"
        "## Legacy section\n\n"
        "- ignored bullet\n",
    )

    watch, mute = steering_overrides(tmp_path)

    assert watch == {"retrieval", "practice", "interleaving"}
    assert mute == {"spaced", "repetition"}


def test_steering_overrides_without_file_is_empty(tmp_path: Path) -> None:
    assert steering_overrides(tmp_path) == (set(), set())


def test_effective_steering_unions_projects_hubs_questions_and_watch(tmp_path: Path) -> None:
    _concept(
        tmp_path / "projects/tutorial/project.md",
        "type: project\ntitle: Testing Effect\nthesis: Retrieval strengthens memory\n"
        "tags: [cognition]\nlinks: {}\n",
    )
    _concept(
        tmp_path / "hubs/note-taking.md",
        "type: hub\ntitle: Note Taking\ntag: note-taking\ntags: [handwriting]\nlinks: {}\n",
    )
    _concept(
        tmp_path / "notes/q-offloading.md",
        "type: note\nmode: question\nquestion_status: open\n"
        "title: Does offloading erode recall\ntags: []\nlinks: {}\n",
    )
    _write(
        tmp_path / "steering.md",
        "---\ntype: system\ntitle: Steering\n---\n\n## Watch for\n\n- interleaving\n\n## Muted\n",
    )

    tokens = effective_steering_tokens(tmp_path)

    assert tokens == {
        "testing", "effect", "retrieval", "strengthens", "memory", "cognition",
        "note", "taking", "handwriting",
        "does", "offloading", "erode", "recall",
        "interleaving",
    }


def test_effective_steering_excludes_archived_and_resolved_artifacts(tmp_path: Path) -> None:
    _concept(
        tmp_path / "projects/old/project.md",
        "type: project\ntitle: Abandoned Cartography\narchived: true\ntags: []\nlinks: {}\n",
    )
    _concept(
        tmp_path / "hubs/dormant.md",
        "type: hub\ntitle: Dormant Volcanoes\ntag: volcanoes\narchived: true\n"
        "tags: []\nlinks: {}\n",
    )
    _concept(
        tmp_path / "notes/q-settled.md",
        "type: note\nmode: question\nquestion_status: resolved\n"
        "title: Settled Wording\ntags: []\nlinks: {}\n",
    )
    _concept(
        tmp_path / "notes/claim.md",
        "type: note\nmode: claim\nclaim_text: x\ntitle: Claim Notes Excluded\n"
        "tags: []\nlinks: {}\n",
    )

    assert effective_steering_tokens(tmp_path) == set()


def test_effective_steering_subtracts_muted_tokens_per_word(tmp_path: Path) -> None:
    _concept(
        tmp_path / "projects/srs/project.md",
        "type: project\ntitle: Spaced Repetition Scheduling\ntags: []\nlinks: {}\n",
    )
    _write(
        tmp_path / "steering.md",
        "---\ntype: system\ntitle: Steering\n---\n\n"
        "## Watch for\n\n## Muted\n\n- spaced repetition\n",
    )

    assert effective_steering_tokens(tmp_path) == {"scheduling"}
```

- [ ] Register the new file in `tests/conftest.py` `TEST_LEVELS` — insert between the `test_source_enrichment.py` row (`:107`) and the `test_surface_contract.py` row (`:108`); `tests/test_testing_levels.py:10-14` fails otherwise:

```python
    "test_steering_tokens.py": "contract",
```

- [ ] Run and confirm the failure is the missing module:

```
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_steering_tokens.py -q
```

Expected: collection error — `ModuleNotFoundError: No module named 'memoria_vault.runtime.steering'`.

- [ ] Create `src/memoria_vault/runtime/steering.py` (complete file):

```python
"""Derived steering: the effective token set discovery ranking reads.

Effective steering is derived from the vault substrate -- active projects
(title + thesis + tags), hubs (title + tag + tags), and open question notes
(title) -- plus the thin ``steering.md`` override: ``## Watch for`` bullets
boost, ``## Muted`` bullets suppress. Suppression is token-set subtraction:
bullets run through :func:`relevance_tokens`, so a multi-word entry mutes
each of its words. Archived artifacts never contribute, so steering needs
no separate aging mechanism.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from memoria_vault.runtime.vaultio import iter_markdown, read_frontmatter, split_frontmatter

# Flat expansion of knowledge.py's retired _DISCOVERY_RELEVANCE_STOPWORDS
# (its 11-word function-word base stays in knowledge.py as
# _TAG_CANDIDATE_STOPWORDS for the tag-candidate sweep).
RELEVANCE_STOPWORDS = frozenset(
    {
        "about",
        "also",
        "and",
        "are",
        "but",
        "for",
        "from",
        "into",
        "the",
        "this",
        "with",
        "candidate",
        "current",
        "paper",
        "papers",
        "priority",
        "question",
        "questions",
        "research",
        "source",
        "sources",
        "steering",
        "system",
        "work",
        "works",
    }
)

_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_BULLET = re.compile(r"^\s*[-*]\s+(.+?)\s*$")


def relevance_tokens(*values: object) -> set[str]:
    """Tokenize values exactly the way discovery relevance always has."""
    text = " ".join(str(value) for value in values if value)
    return {
        token
        for token in re.findall(r"[a-z0-9]{3,}", text.casefold())
        if token not in RELEVANCE_STOPWORDS and not token.isdigit()
    }


def steering_overrides(vault: Path) -> tuple[set[str], set[str]]:
    """Return the (watch, mute) token sets from steering.md's override sections.

    Only bullets under ``## Watch for`` and ``## Muted`` contribute; prose,
    blockquote guidance, and bullets under any other heading never do.
    """
    path = Path(vault) / "steering.md"
    if not path.is_file():
        return set(), set()
    _frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
    watch: set[str] = set()
    mute: set[str] = set()
    target: set[str] | None = None
    for line in body.splitlines():
        heading = _HEADING.match(line)
        if heading:
            target = {"watch for": watch, "muted": mute}.get(heading.group(2).casefold())
            continue
        if target is None:
            continue
        bullet = _BULLET.match(line)
        if bullet:
            target.update(relevance_tokens(bullet.group(1)))
    return watch, mute


def _tags(frontmatter: dict[str, Any]) -> list[object]:
    tags = frontmatter.get("tags")
    return list(tags) if isinstance(tags, list) else []


def _token_sources(vault: Path) -> dict[str, set[str]]:
    """Map each candidate steering token to its contributing source labels.

    Labels: ``project:<rel>``, ``hub:<rel>``, ``question:<rel>``, ``watch``.
    Muted subtraction happens in the callers so provenance can also report
    what a mute removed.
    """
    vault = Path(vault)
    sources: dict[str, set[str]] = {}

    def contribute(tokens: set[str], label: str) -> None:
        for token in tokens:
            sources.setdefault(token, set()).add(label)

    for path in iter_markdown(vault):
        frontmatter = read_frontmatter(path)
        if not frontmatter or frontmatter.get("archived") is True:
            continue
        concept_type = frontmatter.get("type")
        if concept_type not in {"project", "hub", "note"}:
            continue
        rel = path.relative_to(vault).as_posix()
        if concept_type == "project":
            contribute(
                relevance_tokens(
                    frontmatter.get("title"), frontmatter.get("thesis"), *_tags(frontmatter)
                ),
                f"project:{rel}",
            )
        elif concept_type == "hub":
            contribute(
                relevance_tokens(
                    frontmatter.get("title"), frontmatter.get("tag"), *_tags(frontmatter)
                ),
                f"hub:{rel}",
            )
        elif frontmatter.get("mode") == "question":
            if frontmatter.get("question_status") == "resolved":
                continue
            contribute(relevance_tokens(frontmatter.get("title")), f"question:{rel}")
    watch, _mute = steering_overrides(vault)
    contribute(watch, "watch")
    return sources


def effective_steering_tokens(vault: Path) -> set[str]:
    """The steering token set discovery relevance ranks against.

    Union of active projects, hubs, open question notes, and ``## Watch
    for`` bullets, minus ``## Muted`` bullets (per-token subtraction).
    """
    _watch, mute = steering_overrides(vault)
    return set(_token_sources(vault)) - mute
```

The SPEC GAP resolutions land here: hubs contribute the required singular `tag` alongside `tags` (gap 1); `archived: true` excludes uniformly across the three types (gap 2); `question_status: resolved` questions are skipped (gap 3).

- [ ] Move the tokenizer out of `knowledge.py` — four edits, behavior-preserving:

Delete the block at `knowledge.py:85-100`:

```python
_DISCOVERY_RELEVANCE_STOPWORDS = _TAG_CANDIDATE_STOPWORDS | {
    "candidate",
    "current",
    "paper",
    "papers",
    "priority",
    "question",
    "questions",
    "research",
    "source",
    "sources",
    "steering",
    "system",
    "work",
    "works",
}
```

Add the import between the `read_barrier` import (`:33`) and the `subsystems.lib` import (`:34`), preserving isort order:

```python
from memoria_vault.runtime.steering import relevance_tokens
```

Repoint `_steering_tokens` (`:1197`): `return _relevance_tokens(path.read_text(encoding="utf-8"))` becomes `return relevance_tokens(path.read_text(encoding="utf-8"))`. Repoint `_discovery_relevance`: at `:1207` `& _relevance_tokens(edge.get("target_title"), edge.get("target_id"), edge.get("target_doi"))` becomes `& relevance_tokens(...)` (same arguments), and at `:1211` `tag_tokens.update(_relevance_tokens(term))` becomes `tag_tokens.update(relevance_tokens(term))`. Then delete the `_relevance_tokens` definition at `:1229-1235`. (`re` stays imported — `knowledge.py` still uses it at `:1298`, `:2282`, `:3318`, `:3344-3345`.)

- [ ] Run to pass, including the untouched whole-file behavior at the call site and the registration gate:

```
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_steering_tokens.py tests/test_gap_analysis.py tests/test_testing_levels.py -q
```

Expected: all pass (6 new tests + existing suites; `test_analyze_gaps_ranks_discovery_candidates_against_steering` still passes because `_steering_tokens` is still whole-file until S.2).

- [ ] Commit:

```
git add src/memoria_vault/runtime/steering.py src/memoria_vault/runtime/knowledge.py tests/test_steering_tokens.py tests/conftest.py
git commit -m "$(cat <<'EOF'
feat(steering): add derived effective-steering module; move relevance tokenizer out of knowledge.py

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task S.2: call-site switch — discovery relevance ranks against effective steering

**Decision (delete vs deprecate):** `_steering_tokens` is **deleted**, not kept as a re-export. Grep confirms exactly one caller (`knowledge.py:1142`) and zero test imports; there is no production vault to migrate, and the repo's sweep discipline prefers deletion over a deprecation mechanism.

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py` (`:1142` call site; delete `_steering_tokens` at `:1193-1197`; widen the S.1 import line)
- Modify: `tests/test_gap_analysis.py` (rewrite the arrange of `test_analyze_gaps_ranks_discovery_candidates_against_steering` at `:394-442`; add two tests — file already registered at `conftest.py:57` as `runtime`, so no conftest change)

**Interfaces:**
- Consumes: `effective_steering_tokens(vault: Path) -> set[str]` (S.1); the unchanged `_discovery_relevance(steering_tokens: set[str], source: dict[str, Any], edge: dict[str, Any]) -> dict[str, Any]` channel rule at `knowledge.py:1214` — token-set subtraction upstream gives mute semantics for free, verified: a candidate routes `exploration` iff its overlap with the post-subtraction set is empty.
- Produces: the spec §8 discovery behavior — project-matched candidates rank, muted-only candidates explore, watch bullets rank, steering prose contributes nothing.

**Steps:**

- [ ] Rewrite the existing test's arrange (`tests/test_gap_analysis.py:394-442`) — replace the whole-file prose write at `:396-398` with an active-project write and rename the test; every assertion below the arrange stays byte-identical to the shipped test (the arrange otherwise mirrors the shipped fixture at `tests/test_gap_analysis.py:399-424`; `_md` is already imported at `:17`, the `workspace` fixture is `:38-41`):

```python
def test_analyze_gaps_ranks_discovery_candidates_against_effective_steering(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path / "vault")
    _md(
        vault / "projects/neural-retrieval/project.md",
        "type: project\ntitle: Neural Retrieval Evaluation\ntags: []\nlinks: {}\n",
    )
    state.upsert_catalog_record(
        vault,
        work_id="db-alpha",
        title="DB Alpha",
        text_status="full-text",
        check_status="checked",
        csl_json={"memoria": {"research_area": ["catalog-only"]}},
    )
    state.replace_work_graph_edges(
        vault,
        "db-alpha",
        [
            {
                "relation_type": "related",
                "target_id": "https://openalex.org/W111",
                "target_title": "Unrelated Work",
                "source_provider": "openalex",
            },
            {
                "relation_type": "related",
                "target_id": "https://openalex.org/W999",
                "target_title": "Neural Retrieval Evaluation",
                "source_provider": "openalex",
            },
        ],
    )

    result = analyze_gaps(vault, dense_threshold=1, machine="gap-machine")

    assert result["discovery_candidate_paths"] == [
        "inbox/candidate-work-db-alpha-related-https___openalex.org_W999.md",
        "inbox/candidate-work-db-alpha-related-https___openalex.org_W111.md",
    ]
    assert result["discovery_candidate_channels"] == {"ranked": 1, "exploration": 1}
    ranked = read_frontmatter(vault / result["discovery_candidate_paths"][0])
    exploration = read_frontmatter(vault / result["discovery_candidate_paths"][1])
    assert ranked["discovery_relevance_channel"] == "ranked"
    assert ranked["discovery_relevance_score"] > exploration["discovery_relevance_score"]
    assert ranked["discovery_relevance_factors"]["title_overlap"] == [
        "evaluation",
        "neural",
        "retrieval",
    ]
    assert exploration["discovery_relevance_channel"] == "exploration"
```

The unchecked project file is inert everywhere else in `analyze_gaps`: project-argument gaps only fire when `project_path` is passed (`knowledge.py:432-435`), and `_checked_concepts` skips it (no recorded verdict).

- [ ] Add the mute-subtraction test (the §8 acceptance sentence, exactly — the muted term also appears in the project title, and a candidate carrying a surviving token still ranks):

```python
def test_analyze_gaps_muted_terms_subtract_from_effective_steering(tmp_path: Path) -> None:
    vault = workspace(tmp_path / "vault")
    _md(
        vault / "projects/srs/project.md",
        "type: project\ntitle: Spaced Repetition Scheduling\ntags: []\nlinks: {}\n",
    )
    (vault / "steering.md").write_text(
        "---\ntype: system\ntitle: Steering\n---\n\n"
        "## Watch for\n\n## Muted\n\n- spaced repetition\n",
        encoding="utf-8",
    )
    state.upsert_catalog_record(
        vault,
        work_id="db-alpha",
        title="DB Alpha",
        text_status="full-text",
        check_status="checked",
        csl_json={"memoria": {"research_area": ["catalog-only"]}},
    )
    state.replace_work_graph_edges(
        vault,
        "db-alpha",
        [
            {
                "relation_type": "related",
                "target_id": "https://openalex.org/W111",
                "target_title": "Spaced Repetition Flashcards",
                "source_provider": "openalex",
            },
            {
                "relation_type": "related",
                "target_id": "https://openalex.org/W999",
                "target_title": "Spaced Repetition Scheduling Systems",
                "source_provider": "openalex",
            },
        ],
    )

    result = analyze_gaps(vault, dense_threshold=1, machine="gap-machine")

    channels = {
        rel: read_frontmatter(vault / rel)["discovery_relevance_channel"]
        for rel in result["discovery_candidate_paths"]
    }
    assert channels == {
        "inbox/candidate-work-db-alpha-related-https___openalex.org_W999.md": "ranked",
        "inbox/candidate-work-db-alpha-related-https___openalex.org_W111.md": "exploration",
    }
```

- [ ] Add the watch-plus-prose test (discriminating pre/post: under the whole-file bag the prose-matched candidate ranks, which is the placeholder-pollution defect):

```python
def test_analyze_gaps_watch_entries_rank_and_prose_stops_polluting(tmp_path: Path) -> None:
    vault = workspace(tmp_path / "vault")
    (vault / "steering.md").write_text(
        "---\ntype: system\ntitle: Steering\n---\n\n"
        "Guidance prose mentioning template placeholder terms contributes nothing.\n\n"
        "## Watch for\n\n- neural retrieval\n\n"
        "## Muted\n",
        encoding="utf-8",
    )
    state.upsert_catalog_record(
        vault,
        work_id="db-alpha",
        title="DB Alpha",
        text_status="full-text",
        check_status="checked",
        csl_json={"memoria": {"research_area": ["catalog-only"]}},
    )
    state.replace_work_graph_edges(
        vault,
        "db-alpha",
        [
            {
                "relation_type": "related",
                "target_id": "https://openalex.org/W111",
                "target_title": "Template Placeholder Terms",
                "source_provider": "openalex",
            },
            {
                "relation_type": "related",
                "target_id": "https://openalex.org/W999",
                "target_title": "Neural Retrieval Evaluation",
                "source_provider": "openalex",
            },
        ],
    )

    result = analyze_gaps(vault, dense_threshold=1, machine="gap-machine")

    channels = {
        rel: read_frontmatter(vault / rel)["discovery_relevance_channel"]
        for rel in result["discovery_candidate_paths"]
    }
    assert channels == {
        "inbox/candidate-work-db-alpha-related-https___openalex.org_W999.md": "ranked",
        "inbox/candidate-work-db-alpha-related-https___openalex.org_W111.md": "exploration",
    }
```

- [ ] Run and confirm all three fail against the whole-file implementation:

```
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_gap_analysis.py -q -k steering
```

Expected: 3 failures, all `AssertionError` — the project-based test finds both candidates in `exploration` (no `steering.md`, empty bag flips the expected path order too); the mute test finds `Spaced Repetition Flashcards` ranked (whole-file bag contains the muted words); the watch test finds `Template Placeholder Terms` ranked (prose pollutes the bag).

- [ ] Implement the switch in `knowledge.py` — three edits. Widen the S.1 import line:

```python
from memoria_vault.runtime.steering import effective_steering_tokens, relevance_tokens
```

Change the call site (`:1142`):

```python
    steering_tokens = effective_steering_tokens(vault)
```

Delete the `_steering_tokens` definition (`:1193-1197`):

```python
def _steering_tokens(vault: Path) -> set[str]:
    path = vault / "steering.md"
    if not path.is_file():
        return set()
    return relevance_tokens(path.read_text(encoding="utf-8"))
```

No other change: `_discovery_relevance`, `_annotate_discovery_candidate`, `_sort_discovery_candidate_paths`, and `exploration_channel` (`:1270`) all consume the token set or the written frontmatter and are indifferent to how the set was derived.

- [ ] Run to pass, then the neighboring runtime suites:

```
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_gap_analysis.py -q -k steering
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_gap_analysis.py tests/test_knowledge.py tests/test_exploration_channel.py tests/test_worker_knowledge_cycle.py tests/test_steering_tokens.py -q
```

Expected: 3 passed on the first, all green on the second.

- [ ] Commit:

```
git add src/memoria_vault/runtime/knowledge.py tests/test_gap_analysis.py
git commit -m "$(cat <<'EOF'
feat(steering): rank discovery candidates against derived effective steering

Deletes the whole-file _steering_tokens bag; mute is token-set subtraction
feeding the unchanged channel rule.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task S.3: reseed `steering.md` as the thin override + provenance render in `steering show`

**Files:**
- Modify: `src/memoria_vault/product/workspace_seed/steering.md` (full rewrite; frontmatter unchanged — `type: system`, `title: Steering`)
- Modify: `src/memoria_vault/runtime/steering.py` (add `effective_steering_provenance`)
- Modify: `src/memoria_vault/cli.py` (`_cmd_steering_show`, `:2001-2007`; `_cmd_steering_edit` at `:2010-2034` untouched)
- Modify: `tests/test_steering_tokens.py`, `tests/test_cli.py` (both registered — `conftest.py:25` has `test_cli.py: contract`; no conftest change)

**Interfaces:**
- Consumes: `_token_sources(vault) -> dict[str, set[str]]` and `steering_overrides(vault) -> tuple[set[str], set[str]]` (S.1); cli helpers `_workspace(args) -> Path` (`:2130`), `_emit(payload, args) -> int` (`:3092`), `_fail(message, *, json_output) -> int` (`:3234`); the custom non-JSON render precedent `_cmd_export` (`cli.py:1256-1261`); `WORKSPACE_SEED` (`tests/helpers.py:18`).
- Produces: `effective_steering_provenance(vault: Path) -> list[dict[str, Any]]` (rows `{"token": str, "sources": list[str]}`, sorted by token, muted tokens excluded); `memoria steering show` JSON payload `{"ok": True, "path": "steering.md", "tokens": [...], "muted": [...]}` (the retained `path` key keeps the `test_cli_workspace_requests.py:1482-1484` smoke green); the reseeded two-section override file.

**Sequencing note (doc-claims gate):** this task edits no file under `docs/` — the seed file lives in `product/workspace_seed/` which the gate does not walk (`doc_claims_gate.py:67-74` iterates `docs/` only), and the `memoria steering show` path it names in backticks ships already (`cli.py:139`). The slice-7 docs sweep (another section) depends on this task landing first so its rewritten steering semantics describe shipped behavior.

**Steps:**

- [ ] Add the failing tests to `tests/test_steering_tokens.py` (extend the S.1 imports with `effective_steering_provenance` and add `from tests.helpers import WORKSPACE_SEED`):

```python
def test_effective_steering_provenance_labels_every_source(tmp_path: Path) -> None:
    _concept(
        tmp_path / "projects/tutorial/project.md",
        "type: project\ntitle: Retrieval Practice\ntags: []\nlinks: {}\n",
    )
    _concept(
        tmp_path / "hubs/note-taking.md",
        "type: hub\ntitle: Note Taking\ntag: note-taking\ntags: []\nlinks: {}\n",
    )
    _concept(
        tmp_path / "notes/q-offloading.md",
        "type: note\nmode: question\nquestion_status: open\n"
        "title: Offloading Retrieval\ntags: []\nlinks: {}\n",
    )
    _write(
        tmp_path / "steering.md",
        "---\ntype: system\ntitle: Steering\n---\n\n"
        "## Watch for\n\n- interleaving\n\n## Muted\n\n- practice\n",
    )

    provenance = effective_steering_provenance(tmp_path)

    by_token = {row["token"]: row["sources"] for row in provenance}
    assert [row["token"] for row in provenance] == sorted(by_token)
    assert by_token["retrieval"] == [
        "project:projects/tutorial/project.md",
        "question:notes/q-offloading.md",
    ]
    assert by_token["interleaving"] == ["watch"]
    assert by_token["note"] == ["hub:hubs/note-taking.md"]
    assert "practice" not in by_token


def test_shipped_seed_steering_is_override_only_and_contributes_no_tokens(
    tmp_path: Path,
) -> None:
    text = (WORKSPACE_SEED / "steering.md").read_text(encoding="utf-8")
    _write(tmp_path / "steering.md", text)

    assert "## Watch for" in text
    assert "## Muted" in text
    assert steering_overrides(tmp_path) == (set(), set())
    assert effective_steering_tokens(tmp_path) == set()
```

- [ ] Add the failing CLI test to `tests/test_cli.py` (arrange mirrors the init-then-create pattern of `test_memoria_new_defaults_include_description_key`, `tests/test_cli.py:319-333`; `json`, `main`, `Path`, `pytest` are already imported at `:4/:11/:6/:8`):

```python
def test_steering_show_renders_effective_steering_provenance(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    assert (
        main(
            [
                "new",
                "project",
                "Retrieval Practice",
                "--workspace",
                str(workspace),
                "--json",
                "--idempotency-key",
                "steering-show-project",
            ]
        )
        == 0
    )
    created = json.loads(capsys.readouterr().out)
    assert (
        main(
            [
                "steering",
                "edit",
                "--workspace",
                str(workspace),
                "--body",
                "---\ntype: system\ntitle: Steering\n---\n\n"
                "## Watch for\n\n- interleaving\n\n## Muted\n\n- practice\n",
                "--json",
            ]
        )
        == 0
    )
    capsys.readouterr()

    assert main(["steering", "show", "--workspace", str(workspace), "--json"]) == 0
    shown = json.loads(capsys.readouterr().out)

    assert shown["ok"] is True
    assert shown["path"] == "steering.md"
    assert shown["muted"] == ["practice"]
    by_token = {row["token"]: row["sources"] for row in shown["tokens"]}
    assert by_token["retrieval"] == [f"project:{created['path']}"]
    assert by_token["interleaving"] == ["watch"]
    assert "practice" not in by_token

    assert main(["steering", "show", "--workspace", str(workspace)]) == 0
    readable = capsys.readouterr().out
    assert "interleaving" in readable
    assert "muted: practice" in readable
```

- [ ] Run and confirm the failures:

```
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_steering_tokens.py -q
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_cli.py -q -k steering_show
```

Expected: the first errors at collection — `ImportError: cannot import name 'effective_steering_provenance' from 'memoria_vault.runtime.steering'`; the second fails with `KeyError: 'muted'` (the shipped payload carries `body`, not `tokens`/`muted`).

- [ ] Append the provenance render to `src/memoria_vault/runtime/steering.py`:

```python
def effective_steering_provenance(vault: Path) -> list[dict[str, Any]]:
    """Effective tokens with contributing sources, sorted by token.

    Muted tokens are excluded, matching :func:`effective_steering_tokens`.
    """
    _watch, mute = steering_overrides(vault)
    return [
        {"token": token, "sources": sorted(labels)}
        for token, labels in sorted(_token_sources(vault).items())
        if token not in mute
    ]
```

- [ ] Rewrite `src/memoria_vault/product/workspace_seed/steering.md` (complete file — same frontmatter; guidance is blockquote prose, never bullets, so a fresh seed contributes zero tokens; the multi-word over-suppression consequence is documented; the two Pages URLs are retained verbatim from the shipped seed so `tests/test_workspace_seed_links.py` keeps resolving them):

```markdown
---
type: system
title: Steering
---

# Steering

Steering is **derived, not authored**. Discovery ranking reads the vault
itself: every active project (title, thesis, tags), every hub (title, tags),
and every open question note contributes terms to the effective steering
set. Archive a project and its terms drop out on their own — the projects
*are* the priorities, so there is no priority list to keep current here.

Run `memoria steering show` to see the effective set and which project,
hub, question note, or watch entry contributed each term.

This file is the thin override on top of that derived signal: two lists,
both empty by default, both optional.

## Watch for

> Terms to boost that fit no project, hub, or question note yet — one per
> bullet. Once a watch term grows into a real project or hub, delete the
> bullet; the artifact carries it from then on.

## Muted

> Terms to suppress even when an active project or hub mentions them — one
> per bullet.

**Muting is per-word.** Entries are split into words: muting
`spaced repetition` suppresses both `spaced` and `repetition` wherever they
appear, including inside phrases you still care about. Prefer the single
word you actually want gone. A candidate that also matches a surviving
term still ranks — muting removes terms from the effective set, it does
not veto candidates outright.

---

**Refresh cadence.** During the Friday [weekly review](https://eranroseman.github.io/memoria-vault/how-to-guides/inbox/run-the-weekly-review):
archive stale projects, prune these two lists. Where steering sits in
Memoria's memory model: [The memory model](https://eranroseman.github.io/memoria-vault/explanation/architecture/memory-model#why-each-substrate-has-its-scope).
```

- [ ] Repoint `_cmd_steering_show` (`cli.py:2001-2007` — full replacement; local import matches the `_cmd_steering_edit` pattern at `:2011`, the custom non-JSON render matches `_cmd_export` at `:1256-1261`; the not-found guard is kept per SPEC GAP 4):

```python
def _cmd_steering_show(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.steering import effective_steering_provenance, steering_overrides

    workspace = _workspace(args)
    if not (workspace / "steering.md").is_file():
        return _fail("steering.md not found", json_output=args.json)
    tokens = effective_steering_provenance(workspace)
    _watch, mute = steering_overrides(workspace)
    payload = {"ok": True, "path": "steering.md", "tokens": tokens, "muted": sorted(mute)}
    if not args.json and not args.quiet:
        if tokens:
            width = max(len(str(row["token"])) for row in tokens)
            for row in tokens:
                print(f"{str(row['token']):<{width}}  {', '.join(row['sources'])}")
        else:
            print("no effective steering tokens - frame a project or add Watch for bullets")
        if payload["muted"]:
            print(f"muted: {', '.join(payload['muted'])}")
        return 0
    return _emit(payload, args)
```

- [ ] Run the task's tests to pass, plus the seed and smoke neighbors:

```
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_steering_tokens.py tests/test_cli.py tests/test_cli_workspace_requests.py tests/test_workspace_seed_links.py tests/test_package_spine.py -q
```

Expected: all pass (8 tests in `test_steering_tokens.py`; the workspace-requests smoke at `:1482-1484` passes on the retained `path` key; seed-links and package-spine confirm the rewritten seed file is well-formed and still shipped).

- [ ] Section-final gate — run the full verification roster and confirm it exits clean (lint incl. markdownlint/cspell over the rewritten seed, product gates incl. the doc-claims gate, full test suite, offline smoke):

```
python scripts/verify
```

- [ ] Commit:

```
git add src/memoria_vault/runtime/steering.py src/memoria_vault/cli.py src/memoria_vault/product/workspace_seed/steering.md tests/test_steering_tokens.py tests/test_cli.py
git commit -m "$(cat <<'EOF'
feat(steering): reseed steering.md as thin override; steering show renders effective-steering provenance

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
EOF
)"
```
# T — Onboarding-step telemetry + diary template

Implements O1 spec §5 (time-to-first-answer instrumentation: the `onboarding-step` native event type and its five emit points, including the exact `first-answer` rule) and §6's diary line (the five-line session-diary template seeded at `system/templates/session-diary.md`) — implementation slices 5 and 6 of `docs/superpowers/specs/2026-07-16-o1-onboarding-seed-design.md`.

**Cross-plan ownership (binding).** The telemetry substrate belongs to the I1 plan (`docs/superpowers/plans/2026-07-16-i1-full-wiring.md`): its Task T.1 creates the v19 `telemetry_events` table `(event_id, ts, event_type, session_id, surface, payload_json)` + `idx_telemetry_type_ts` (I1 plan :23, :39-141), and its Task T.2 creates `src/memoria_vault/runtime/telemetry.py` with (quoting the planned shape, I1 plan :233-259):

```python
NATIVE_EVENT_FIELDS = {
    "attention-admitted": frozenset({"card_path", "kind", "loudness", "raised_by"}),
    "producer-run-skipped": frozenset({"producer", "reason"}),
}


def record_telemetry_event(vault: Path, event_type: str, payload: dict[str, Any]) -> str:
    """Validate and insert one analytics-only event. No journal append, no git effect."""
```

The validator is all-string per native type (I1 plan :271-280), so `onboarding-step` `{step}` needs **no validator change** — exactly what spec §5 promises ("all-string, so I1's validator needs no change"). This section adds one `NATIVE_EVENT_FIELDS` row to that I1-owned file (recorded here as an O1 addition to the I1-owned table) and everything else in O1-owned files. At `07bedc74`, `runtime/telemetry.py` does **not** exist and `state.SCHEMA_VERSION` is 12 — **Task T.1 hard-blocks on I1 plan Tasks T.1–T.2** (grep-first check below). Every runtime emit is a guarded observer: if the telemetry module or table is absent or the insert fails, the emit returns `None` and the command proceeds — an observer, never a gate.

Other cross-plan seams, all order-tolerant: `memoria onboard` is owned by the surfaces plan BOOT-D.7 (`2026-07-15-surfaces-bootstrap-and-plugins.md:5445-5608`, not shipped at `07bedc74`); `memoria seed install` and `load_seed_manifest` are owned by this composite plan's section M (M.3 consumes this section's `emit_onboarding_step` for the `seed-installed` step); `SEED_FILES` (`cli.py:47-51`) is also extended by alpha23 R1NG.1 (five `.base` pairs, alpha23 plan :106, :428-431) and surfaces BOOT-D.6 (`Start here.md`) — whichever lands second rebases the tuple and the pinned test lists (the surfaces plan's Global Constraint 11 sets that precedent).

**SPEC GAP resolutions** (each restated at its task):

1. *`project-framed` cadence.* Spec §5 names the step but not whether every `memoria new project` emits. Emitting per project is noisy and makes the §5 deltas ambiguous. **Resolution:** emit only when no prior `project-framed` row exists (`emit_onboarding_step_once`), mirroring the spec's explicit `first-answer` dedupe, so `project-framed.ts − init-done.ts` is deterministic. (On a pre-O1 vault with existing projects, the first post-upgrade `new project` emits — acceptable: §5 measures fresh-vault onboarding.)
2. *Which ask surface counts for `first-answer`.* Both `memoria ask` (`cli.py:706-712`) and `memoria project ask` (`cli.py:1010-1018`) run `answer-query`. **Resolution:** only `memoria ask` emits — spec §3's arc ends at "ask" meaning the tutorial's `memoria ask` rung, and §5's bar measures that doc arc; `project ask` is a later-stage project surface. Repo convention: the smallest change that solves the problem.
3. *What counts as "onboard done".* Spec §5 names the step; BOOT-D.5's `run_onboarding` payload carries a `completed` flag (surfaces plan :5493, :5519). **Resolution:** emit iff `payload.get("completed")` is truthy, at the single choke point `_run_onboarding_for_args` (covers both `memoria onboard` and `init --onboard`).
4. *`init-done` on re-init.* **Resolution:** plain emit every successful init (an honest observer records real re-inits); readers compute §5 deltas from the first row per step (`MIN(ts)`), which LOOP.13's amended block already does implicitly by reading "the two event timestamps" of a fresh vault.

### Task T.1: `onboarding-step` native type + guarded emit helper

**Files:**
- Modify: `src/memoria_vault/runtime/telemetry.py` (I1-owned, created by I1 plan T.2 — add one `NATIVE_EVENT_FIELDS` entry beside `"attention-admitted"`/`"producer-run-skipped"`, I1 plan :233-236)
- Create: `src/memoria_vault/runtime/onboarding_steps.py`
- Create: `tests/test_onboarding_steps.py`
- Modify: `tests/conftest.py` (`TEST_LEVELS` dict at `:18`; insert alphabetically after `"test_node_tooling.py": "static",` at `:77`)

**Interfaces:**
- Consumes: `memoria_vault.runtime.telemetry.record_telemetry_event(vault: Path, event_type: str, payload: dict[str, Any]) -> str` and `NATIVE_EVENT_FIELDS: dict[str, frozenset[str]]` (I1 plan T.2); the v19 `telemetry_events` table (I1 plan T.1); shipped `memoria_vault.runtime.state.connect(vault: Path) -> sqlite3.Connection` (`state.py:472-481`, `sqlite3.Row` factory at `:476`).
- Produces (later tasks and section M rely on these exact names):
  - `memoria_vault.runtime.onboarding_steps.ONBOARDING_STEPS: frozenset[str]` — exactly `{"init-done", "onboard-done", "project-framed", "seed-installed", "first-answer"}`
  - `emit_onboarding_step(vault: Path, step: str) -> str | None` — the seam **M.3 imports** for `seed-installed`
  - `emit_onboarding_step_once(vault: Path, step: str) -> str | None`
  - `has_onboarding_step(vault: Path, step: str) -> bool`
  - `NATIVE_EVENT_FIELDS["onboarding-step"] == frozenset({"step"})`

- [ ] **Step 0: Grep-first dependency check (hard block).** Run:

```bash
test -f src/memoria_vault/runtime/telemetry.py && grep -n "NATIVE_EVENT_FIELDS" src/memoria_vault/runtime/telemetry.py
python -c "from memoria_vault.runtime import state; print(state.SCHEMA_VERSION)"
```

Required: the file exists with `NATIVE_EVENT_FIELDS`, and `SCHEMA_VERSION >= 19` (the v19 `telemetry_events` migration). At `07bedc74` both fail (`SCHEMA_VERSION` is 12, the module is absent). **If either check fails, STOP: this task blocks on I1 plan Tasks T.1–T.2 (I1 slices 1–2). Do not create a stub `runtime/telemetry.py` and do not renumber schema versions — report the block and land I1 T.1–T.2 first.** If I1 landed with drifted line numbers, re-anchor by symbol (`NATIVE_EVENT_FIELDS`, `record_telemetry_event`).

- [ ] **Step 1: Write the failing tests.** Create `tests/test_onboarding_steps.py`:

```python
"""Contract tests for onboarding-step telemetry (O1 spec §5): an observer, never a gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.onboarding_steps import (
    ONBOARDING_STEPS,
    emit_onboarding_step,
    emit_onboarding_step_once,
    has_onboarding_step,
)


def test_onboarding_step_is_a_registered_all_string_native_type() -> None:
    from memoria_vault.runtime.telemetry import NATIVE_EVENT_FIELDS

    assert NATIVE_EVENT_FIELDS["onboarding-step"] == frozenset({"step"})


def test_onboarding_steps_roster_is_the_spec_five() -> None:
    assert ONBOARDING_STEPS == {
        "init-done",
        "onboard-done",
        "project-framed",
        "seed-installed",
        "first-answer",
    }


def test_emit_onboarding_step_records_one_server_side_row(tmp_path: Path) -> None:
    event_id = emit_onboarding_step(tmp_path, "init-done")

    assert event_id
    with state.connect(tmp_path) as conn:
        row = conn.execute(
            "SELECT event_type, session_id, surface, payload_json FROM telemetry_events"
            " WHERE event_id = ?",
            (event_id,),
        ).fetchone()
    assert row["event_type"] == "onboarding-step"
    assert row["session_id"] is None  # spec §5: server-side, session_id NULL
    assert row["surface"] is None
    assert json.loads(row["payload_json"]) == {"step": "init-done"}
    assert has_onboarding_step(tmp_path, "init-done") is True
    assert has_onboarding_step(tmp_path, "first-answer") is False


def test_emit_onboarding_step_rejects_unknown_steps(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown onboarding step"):
        emit_onboarding_step(tmp_path, "made-up-step")
    with pytest.raises(ValueError, match="unknown onboarding step"):
        has_onboarding_step(tmp_path, "made-up-step")


def test_emit_onboarding_step_no_ops_when_the_sink_table_is_gone(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        conn.execute("DROP TABLE telemetry_events")

    assert emit_onboarding_step(tmp_path, "init-done") is None  # observer, never a gate
    assert has_onboarding_step(tmp_path, "init-done") is False


def test_emit_onboarding_step_no_ops_without_the_telemetry_module(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(sys.modules, "memoria_vault.runtime.telemetry", None)

    assert emit_onboarding_step(tmp_path, "init-done") is None


def test_emit_onboarding_step_once_skips_when_a_prior_row_exists(tmp_path: Path) -> None:
    first = emit_onboarding_step_once(tmp_path, "project-framed")
    second = emit_onboarding_step_once(tmp_path, "project-framed")

    assert first
    assert second is None
    with state.connect(tmp_path) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM telemetry_events WHERE event_type = 'onboarding-step'"
        ).fetchone()[0]
    assert count == 1
```

Register the new file in `tests/conftest.py` `TEST_LEVELS` (this is a **new** test file, so registration is required; insert alphabetically after `"test_node_tooling.py": "static",` at `tests/conftest.py:77` — order-tolerant against surfaces BOOT-D.1's `"test_onboarding.py": "unit",` which sorts immediately before it):

```python
    "test_onboarding_steps.py": "contract",
```

The drop-table arrangement is a real environmental failure: `state._init` (`state.py:2406-2411`) migrates by `PRAGMA user_version`, so a reconnect after `DROP TABLE telemetry_events` does not recreate the table.

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_onboarding_steps.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'memoria_vault.runtime.onboarding_steps'` at collection.

- [ ] **Step 3: Minimal implementation.** In `src/memoria_vault/runtime/telemetry.py`, extend `NATIVE_EVENT_FIELDS` (alphabetical position, between the existing two entries planned at I1 :233-236):

```python
NATIVE_EVENT_FIELDS = {
    "attention-admitted": frozenset({"card_path", "kind", "loudness", "raised_by"}),
    "onboarding-step": frozenset({"step"}),
    "producer-run-skipped": frozenset({"producer", "reason"}),
}
```

Create `src/memoria_vault/runtime/onboarding_steps.py`:

```python
"""Onboarding-step telemetry (O1 spec §5): five step events, emitted as observers, never gates.

Each row's own ``ts`` is the timestamp; every delta (the <=30-min bar) is
computed at read time from the first row per step. No duration field, no
cross-process t0 state.
"""

from __future__ import annotations

from pathlib import Path

from memoria_vault.runtime import state

ONBOARDING_STEPS = frozenset(
    {"init-done", "onboard-done", "project-framed", "seed-installed", "first-answer"}
)

_STEP_QUERY = (
    "SELECT 1 FROM telemetry_events"
    " WHERE event_type = 'onboarding-step'"
    " AND json_extract(payload_json, '$.step') = ? LIMIT 1"
)


def _known(step: str) -> str:
    if step not in ONBOARDING_STEPS:
        raise ValueError(f"unknown onboarding step: {step}")
    return step


def emit_onboarding_step(vault: Path, step: str) -> str | None:
    """Record one onboarding-step event; return None instead of raising on any sink failure."""
    _known(step)
    try:
        from memoria_vault.runtime.telemetry import record_telemetry_event
    except ImportError:
        return None
    try:
        return record_telemetry_event(vault, "onboarding-step", {"step": step})
    except Exception:  # noqa: BLE001 -- telemetry is an observer, never a gate (O1 spec §5).
        return None


def has_onboarding_step(vault: Path, step: str) -> bool:
    """True when a prior row for ``step`` exists; False on any sink failure."""
    _known(step)
    try:
        with state.connect(vault) as conn:
            return conn.execute(_STEP_QUERY, (step,)).fetchone() is not None
    except Exception:  # noqa: BLE001 -- absent table reads as "no prior step".
        return False


def emit_onboarding_step_once(vault: Path, step: str) -> str | None:
    """Emit only when no prior row for ``step`` exists — deterministic deltas (O1 spec §5)."""
    if has_onboarding_step(vault, step):
        return None
    return emit_onboarding_step(vault, step)
```

Unknown steps raise `ValueError` deliberately: a bad step name is a programmer error at a call site, not an environmental sink failure — only the latter no-ops.

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_onboarding_steps.py tests/test_telemetry_events.py -v`
Expected: PASS (including I1's `test_telemetry_events.py` — the new native row must not disturb its unknown-type/missing-field error contracts).

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/telemetry.py src/memoria_vault/runtime/onboarding_steps.py \
    tests/test_onboarding_steps.py tests/conftest.py
git commit -m "feat(telemetry): onboarding-step native event type + guarded emit helper (O1 spec §5)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task T.2: the five emit points (init-done, project-framed, seed-installed, onboard-done, first-answer)

**Files:**
- Modify: `src/memoria_vault/cli.py` — top imports (`:26`, `from memoria_vault.runtime import state` becomes `from memoria_vault.runtime import onboarding_steps, state`); `_cmd_init` (`:578-589`); `_cmd_ask` (`:706-712`); `_cmd_new_project` (`:854-869`); conditionally `_run_onboarding_for_args` (only if surfaces BOOT-D.7 landed) and the section-M seed-install handler (only if section M landed) — grep-first steps below
- Modify: `src/memoria_vault/runtime/onboarding_steps.py` (append the first-answer rule helpers)
- Modify: `tests/test_onboarding_steps.py` (extend — already registered `contract` by T.1, no conftest change), `tests/test_cli.py` (extend — already registered `contract` at `tests/conftest.py:25`, no conftest change)
- Conditionally modify: `docs/superpowers/plans/2026-07-15-surfaces-bootstrap-and-plugins.md` (BOOT-D.7 note — only when `_cmd_onboard` has NOT landed; `docs/superpowers` is in the doc-claims gate's `SKIP_DIRS`, `scripts/checks/doc_claims_gate.py:23`, so naming the unshipped `memoria onboard` there is gate-safe)

**Interfaces:**
- Consumes: T.1's `emit_onboarding_step` / `emit_onboarding_step_once`; shipped `engine_api.write_new_concept(...) -> dict` returning `{"ok": bool, "path", "concept", "job", "result", "commit"}` (`engine/api.py:552-559`); shipped `run_operation` CLI result `{"ok": bool, "job": dict, "result": dict}` (`engine/api.py:440-444`) where for `answer-query` `result` merges the job record with the answer contract `{"query", "engine", "sources", "unknowns", "staleness", "contradictions"}` (`worker.py:228`, `search_index.py:239-249`) and each `sources` row is `{"path": str, "title": str, "type": str, "score": float}` (`search_index.py:226-232`); catalog-work source paths are the generated docs `fulltexts/<work_id>.md` (`search_index.py:444`), `graph-neighborhoods/<work_id>.md` (`search_index.py:471`), and the bundle-root digests `digests/<work_id>.md`; **section M's** `memoria_vault.product.seed_corpus.load_seed_manifest() -> list[dict[str, Any]]` (rows carry `id` = catalog `work_id`, spec §2 :107; consumed via guarded import — re-anchor the module path with `grep -rn "def load_seed_manifest" src/` if M placed it elsewhere); **surfaces BOOT-D.5/D.7's** `run_onboarding` payload `completed` key and `_run_onboarding_for_args(workspace, args)` (surfaces plan :5589-5608; order-tolerant).
- Produces:
  - `memoria_vault.runtime.onboarding_steps.answer_work_ids(answer: dict[str, Any]) -> frozenset[str]`
  - `memoria_vault.runtime.onboarding_steps.seed_manifest_work_ids(manifest_loader: Callable[[], list[dict[str, Any]]] | None = None) -> frozenset[str]`
  - `memoria_vault.runtime.onboarding_steps.emit_first_answer_if_seed_grounded(vault: Path, answer: dict[str, Any], *, manifest_loader: Callable[[], list[dict[str, Any]]] | None = None) -> str | None`
  - CLI behavior: `memoria init` emits `init-done`; `memoria new project` emits `project-framed` once per vault; `memoria ask` routes every ok answer through the first-answer rule; a completed onboarding runway emits `onboard-done`.

The **first-answer rule, exactly as spec §5 states it**: emit when (a) the `answer-query` result's `sources` contain at least one path resolving to a `work_id` present in the seed manifest, and (b) no prior `first-answer` row exists. Path→work_id resolution uses the three generated/bundle work-doc shapes above (`_answer_from_hits` sources carry no `work_id` field — verified at `search_index.py:226-232` — so the stem of a two-segment path under `fulltexts/`, `digests/`, or `graph-neighborhoods/` is the work id; `tests/test_cli_work_project.py:437-441` pins this shape: `"fulltexts/doi-10.1000_alpha.md"`). The manifest loader is **injectable** (no network, no import-order coupling in tests); its guarded default is semantically honest, not merely tolerant: before section M lands there is no seed manifest, hence no seed work ids, hence no seed-grounded answer — the helper stays silent with no gap to record.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_onboarding_steps.py`:

```python
def test_answer_work_ids_resolve_only_work_document_paths() -> None:
    from memoria_vault.runtime.onboarding_steps import answer_work_ids

    answer = {
        "sources": [
            {"path": "fulltexts/oa-chen-2018.md", "title": "Chen 2018", "type": "fulltext", "score": 2.0},
            {"path": "digests/oa-morrison-2020.md", "title": "d", "type": "digest", "score": 1.5},
            {"path": "graph-neighborhoods/oa-schmidt-2018.md", "title": "g", "type": "graph-neighborhood", "score": 1.1},
            {"path": "notes/my-claim.md", "title": "n", "type": "note", "score": 1.0},
            {"path": "hubs/memory.md", "title": "h", "type": "hub", "score": 0.9},
        ]
    }

    assert answer_work_ids(answer) == frozenset(
        {"oa-chen-2018", "oa-morrison-2020", "oa-schmidt-2018"}
    )
    assert answer_work_ids({"sources": []}) == frozenset()
    assert answer_work_ids({}) == frozenset()


def test_seed_manifest_work_ids_default_loader_never_raises() -> None:
    from memoria_vault.runtime.onboarding_steps import seed_manifest_work_ids

    assert isinstance(seed_manifest_work_ids(), frozenset)  # empty before section M lands
    assert seed_manifest_work_ids(lambda: [{"id": "a"}, {"id": " "}, {"title": "no id"}]) == (
        frozenset({"a"})
    )
    assert seed_manifest_work_ids(lambda: (_ for _ in ()).throw(OSError("boom"))) == frozenset()


def test_first_answer_emits_once_and_only_for_seed_grounded_answers(tmp_path: Path) -> None:
    from memoria_vault.runtime.onboarding_steps import emit_first_answer_if_seed_grounded

    def manifest() -> list[dict[str, str]]:
        return [{"id": "oa-chen-2018"}, {"id": "arxiv-2411.14199v1"}]

    off_corpus = {"sources": [{"path": "notes/my-claim.md", "title": "n", "type": "note", "score": 1.0}]}
    grounded = {
        "sources": [
            {"path": "fulltexts/oa-chen-2018.md", "title": "Chen 2018", "type": "fulltext", "score": 2.0}
        ]
    }

    assert emit_first_answer_if_seed_grounded(tmp_path, off_corpus, manifest_loader=manifest) is None
    assert not has_onboarding_step(tmp_path, "first-answer")

    first = emit_first_answer_if_seed_grounded(tmp_path, grounded, manifest_loader=manifest)
    second = emit_first_answer_if_seed_grounded(tmp_path, grounded, manifest_loader=manifest)

    assert first
    assert second is None  # spec §5 rule (b): no prior first-answer row
    with state.connect(tmp_path) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM telemetry_events WHERE event_type = 'onboarding-step'"
            " AND json_extract(payload_json, '$.step') = 'first-answer'"
        ).fetchone()[0]
    assert count == 1
```

Append to `tests/test_cli.py` (arrange blocks mirror the existing init-test shape at `tests/test_cli.py:380-388` — `main(["init", "--workspace", ..., "--yes", ...])` on a `tmp_path` workspace; `main`, `state`, `json`, `pytest` are already imported at `tests/test_cli.py:4-13`):

```python
def test_cli_init_emits_the_init_done_onboarding_step(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"

    rc = main(["init", "--workspace", str(workspace), "--yes", "--quiet"])
    capsys.readouterr()

    assert rc == 0
    with state.connect(workspace) as conn:
        steps = [
            json.loads(row["payload_json"])["step"]
            for row in conn.execute(
                "SELECT payload_json FROM telemetry_events"
                " WHERE event_type = 'onboarding-step' ORDER BY ts"
            )
        ]
    assert steps == ["init-done"]


def test_cli_new_project_emits_project_framed_only_once(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--quiet"]) == 0
    assert main(["new", "project", "Tutorial project", "--workspace", str(workspace), "--quiet"]) == 0
    assert main(["new", "project", "Second project", "--workspace", str(workspace), "--quiet"]) == 0
    capsys.readouterr()

    with state.connect(workspace) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM telemetry_events WHERE event_type = 'onboarding-step'"
            " AND json_extract(payload_json, '$.step') = 'project-framed'"
        ).fetchone()[0]
    assert count == 1


def test_cli_ask_routes_the_answer_through_the_first_answer_rule(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from memoria_vault.runtime import onboarding_steps

    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--quiet"]) == 0
    seen: list[tuple[Path, dict[str, object]]] = []

    def fake_first_answer(vault: Path, answer: dict[str, object], **kwargs: object) -> None:
        seen.append((vault, answer))

    monkeypatch.setattr(onboarding_steps, "emit_first_answer_if_seed_grounded", fake_first_answer)
    rc = main(["ask", "--workspace", str(workspace), "--question", "seed corpus", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert len(seen) == 1
    assert seen[0][0] == workspace.resolve()
    assert "sources" in seen[0][1]


def test_cli_onboard_emits_onboard_done_when_the_runway_completes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    import memoria_vault.cli as cli

    if not hasattr(cli, "_cmd_onboard"):
        pytest.skip("memoria onboard not shipped yet (surfaces plan BOOT-D.7)")
    from memoria_vault.runtime import onboarding

    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--quiet"]) == 0

    def fake_run_onboarding(ws: Path, **kwargs: object) -> dict[str, object]:
        return {"ok": True, "workspace": str(ws), "completed": True, "steps": []}

    monkeypatch.setattr(onboarding, "run_onboarding", fake_run_onboarding)
    rc = main(["onboard", "--workspace", str(workspace), "--json"])
    capsys.readouterr()

    assert rc == 0
    with state.connect(workspace) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM telemetry_events WHERE event_type = 'onboarding-step'"
            " AND json_extract(payload_json, '$.step') = 'onboard-done'"
        ).fetchone()[0]
    assert count == 1
```

The ask test's empty-vault arrangement is safe: on a freshly initialized workspace `memoria ask --json` returns `ok: true`, `result.status == "done"`, `sources: []` (verified against `07bedc74` by driving the CLI on a disposable scratchpad vault). The onboard test is the order-tolerant half of emit point 4: it self-skips until BOOT-D.7 lands, then activates and enforces the emit.

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_onboarding_steps.py tests/test_cli.py -v`
Expected: FAIL — `ImportError`/`AttributeError` for `answer_work_ids`, `seed_manifest_work_ids`, `emit_first_answer_if_seed_grounded`; `steps == ["init-done"]` fails with `[]`; project-framed count `0 != 1`; the onboard test SKIPS (or fails on the missing emit if BOOT-D.7 already landed).

- [ ] **Step 3: Minimal implementation.**

(a) Append to `src/memoria_vault/runtime/onboarding_steps.py` (add `from collections.abc import Callable`, `from pathlib import PurePosixPath`, and `from typing import Any` to the imports):

```python
_ANSWER_WORK_ROOTS = frozenset({"digests", "fulltexts", "graph-neighborhoods"})


def answer_work_ids(answer: dict[str, Any]) -> frozenset[str]:
    """Work ids an answer's sources resolve to, via the generated work-document path shapes."""
    ids: set[str] = set()
    sources = answer.get("sources")
    for source in sources if isinstance(sources, list) else []:
        if not isinstance(source, dict):
            continue
        parts = PurePosixPath(str(source.get("path") or "")).parts
        if len(parts) == 2 and parts[0] in _ANSWER_WORK_ROOTS and parts[1].endswith(".md"):
            ids.add(parts[1].removesuffix(".md"))
    return frozenset(ids)


def seed_manifest_work_ids(
    manifest_loader: Callable[[], list[dict[str, Any]]] | None = None,
) -> frozenset[str]:
    """Manifest work ids; empty when no seed manifest exists (then nothing is seed-grounded)."""
    if manifest_loader is None:
        try:
            from memoria_vault.product.seed_corpus import load_seed_manifest as manifest_loader
        except ImportError:
            return frozenset()
    try:
        rows = manifest_loader()
    except Exception:  # noqa: BLE001 -- an unreadable manifest must not gate the answer.
        return frozenset()
    return frozenset(
        work_id
        for row in rows
        if isinstance(row, dict) and (work_id := str(row.get("id") or "").strip())
    )


def emit_first_answer_if_seed_grounded(
    vault: Path,
    answer: dict[str, Any],
    *,
    manifest_loader: Callable[[], list[dict[str, Any]]] | None = None,
) -> str | None:
    """O1 spec §5 first-answer rule: seed-grounded sources AND no prior first-answer row."""
    if not answer_work_ids(answer) & seed_manifest_work_ids(manifest_loader):
        return None
    return emit_onboarding_step_once(vault, "first-answer")
```

**Grep-first re-anchor for the section-M import:** run `grep -rn "def load_seed_manifest" src/`. If section M landed the loader under a different module (spec §2 fixes only the data file, `src/memoria_vault/product/seed_corpus/manifest.yaml`), update the one guarded import above to M's actual module path — the function name `load_seed_manifest` is M's contract. If the grep is empty (M not landed), leave the import as written: the `ImportError` guard is the correct pre-M behavior.

(b) In `src/memoria_vault/cli.py`: change line 26 to `from memoria_vault.runtime import onboarding_steps, state`, then replace the three handlers (current bodies at `:578-589`, `:706-712`, `:854-869`; call through the module attribute so tests can monkeypatch):

```python
def _cmd_init(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace or ".").resolve()
    created = _workspace_plan(workspace)
    include_obsidian = not args.no_obsidian
    if args.dry_run:
        return _emit(
            _init_dry_run_report(workspace, created, include_obsidian=include_obsidian), args
        )
    if not args.yes and workspace.exists() and any(workspace.iterdir()):
        return _fail("init on a non-empty workspace requires --yes", json_output=args.json)
    _initialize_workspace_files(workspace, include_obsidian=include_obsidian)
    onboarding_steps.emit_onboarding_step(workspace, "init-done")
    return _emit({"ok": True, "workspace": str(workspace), "created": created}, args)
```

```python
def _cmd_ask(args: argparse.Namespace) -> int:
    result = _enqueue_and_run(
        args,
        "answer-query",
        {"query": args.question, "k": 5},
    )
    if result.get("ok"):
        onboarding_steps.emit_first_answer_if_seed_grounded(
            _workspace(args), result.get("result") or {}
        )
    return _emit(result, args)
```

```python
def _cmd_new_project(args: argparse.Namespace) -> int:
    body = _concept_template_body(args.name, args.direction)
    result = engine_api.write_new_concept(
        _workspace(args),
        "project",
        args.name,
        body=body,
        tags=[],
        extra={"description": args.description, "outcome_frame": {}, "paper_plan": {}},
        idempotency_key=args.idempotency_key,
        schedule_id=args.schedule_id,
        actor=args.actor,
    )
    if result.get("ok"):
        onboarding_steps.emit_onboarding_step_once(_workspace(args), "project-framed")
    return _emit(result, args)
```

If BOOT-D.7 already landed, `_cmd_init` ends with the `payload`/`--onboard` tail instead (surfaces plan :5567-5581) — the insertion rule is positional either way: **the emit goes immediately after the `_initialize_workspace_files(...)` call, before the return**. SPEC GAP resolutions 1, 2, and 4 (intro) govern the once-guard on `project-framed`, the `memoria ask`-only scope of the first-answer emit, and the plain (non-deduped) `init-done` emit.

(c) **`onboard-done`, grep-first with both branches.** Run `grep -n "_cmd_onboard\|_run_onboarding_for_args" src/memoria_vault/cli.py`.
  - **Branch A (BOOT-D.7 landed):** in `_run_onboarding_for_args` (single choke point for both `memoria onboard` and `init --onboard`), capture the payload and emit before returning:

    ```python
        payload = onboarding.run_onboarding(
            workspace,
            sys_platform=sys.platform,
            env=os.environ,
            home=Path.home(),
            ask=ask,
            say=say,
        )
        if payload.get("completed"):
            onboarding_steps.emit_onboarding_step(workspace, "onboard-done")
        return payload
    ```

    The skip-guarded CLI test from Step 1 now runs and enforces this.
  - **Branch B (BOOT-D.7 not landed):** make no cli.py change for this step. Record the one-line insertion where BOOT-D.7's executor will meet it — append one step bullet to Task BOOT-D.7's Steps list in `docs/superpowers/plans/2026-07-15-surfaces-bootstrap-and-plugins.md` (after the "Write minimal implementation" bullet, :5540):

    ```markdown
    - [ ] O1 cross-plan (O1 plan Task T.2): before `_run_onboarding_for_args`
      returns, emit the onboarding step — when `payload.get("completed")` is
      truthy, call `onboarding_steps.emit_onboarding_step(workspace,
      "onboard-done")` (cli.py already imports the module at top). The
      skip-guarded test
      `tests/test_cli.py::test_cli_onboard_emits_onboard_done_when_the_runway_completes`
      activates and enforces this once `_cmd_onboard` exists.
    ```

(d) **`seed-installed`, grep-first with both branches.** Run `grep -rn "seed" src/memoria_vault/cli.py | grep -i install` and `grep -rn "emit_onboarding_step" src/memoria_vault/`.
  - **If section M's `memoria seed install` handler exists and already emits** `seed-installed` (M.3's declared consumption of this section's `emit_onboarding_step(vault, step) -> str | None`): verify the call sits on the success exit (spec §2: the non-failure exit fires whenever ≥1 manifest row is present — newly admitted or already admitted, so an idempotent re-run still counts as installed) and move on — no change.
  - **If the handler exists without the emit:** add `onboarding_steps.emit_onboarding_step(workspace, "seed-installed")` on that success exit, immediately before the handler's final `_emit(...)`, and extend M's own test file with a row-count assertion shaped exactly like `test_cli_new_project_emits_project_framed_only_once` above (swap the step string; no once-guard — re-runs of an idempotent install may re-emit, and readers take the first row).
  - **If absent (M not landed):** no change — the composite plan's cross-section contract binds M.3 to call this seam; nothing here can wire a command that does not exist.

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_onboarding_steps.py tests/test_cli.py -v`
Expected: PASS (the onboard test passes in Branch A, skips in Branch B).

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/cli.py src/memoria_vault/runtime/onboarding_steps.py \
    tests/test_onboarding_steps.py tests/test_cli.py
# Branch B only, additionally:
git add docs/superpowers/plans/2026-07-15-surfaces-bootstrap-and-plugins.md
git commit -m "feat(cli): onboarding-step emit points — init-done, project-framed, onboard-done, first-answer rule (O1 spec §5)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task T.3: session-diary template seed (`system/templates/session-diary.md`)

**Files:**
- Create: `src/memoria_vault/product/workspace_seed/system/templates/session-diary.md`
- Modify: `src/memoria_vault/cli.py:47-51` (`SEED_FILES` tuple)
- Modify: `pyproject.toml:29-46` (`[tool.setuptools.package-data]` — the seed globs cover only `"system/*.md"` at `:45`, which does **not** match nested `system/templates/`; without a new glob the wheel silently drops the file)
- Modify: `tests/test_cli.py:414` (pinned `seed_files` list) + append one init test; `tests/test_installer_skeleton.py:31-54` (`expected_files` exact set — `_seed_files()` at `:12-19` rglobs the whole seed dir, so the exact-set assertion fails on any unregistered file); `tests/test_package_spine.py:86-103` (packaged-seed positive list)

All four touched test files are already registered in `TEST_LEVELS` (`test_cli.py: "contract"` at `conftest.py:25`, `test_installer_skeleton.py: "package"` at `:67`, `test_package_spine.py: "package"` at `:80`, `test_workspace_seed_links.py: "static"` at `:114`) — extending registered files needs no conftest change, and no new test file is created.

**Copy-mechanism finding (the grep the task demands):** `system/` files are **not** seeded as a tree — `SEED_TREES` (`cli.py:39-46`) carries no `system` pair; `system/vocabulary.md` rides `SEED_FILES` as an explicit file pair (`cli.py:50`), copied by `_copy_seed_file` (`cli.py:2466-2470`), which creates the parent directory (`target.parent.mkdir(parents=True, ...)`), so `system/templates/` needs no skeleton change. Therefore a new nested file is **not** picked up automatically: it requires its own `SEED_FILES` entry, and `_repair_write_targets` (`cli.py:2281`) then admits the repair target automatically from that same tuple. The content-side guard already anticipates this directory: `tests/test_workspace_seed_links.py:127-130` runs template-frontmatter checks over `system/templates/*.md` (no `mode:`/`audience:`/`tags:` keys inside YAML fences — the template below has no YAML fences) and `:139` excludes `templates` from wikilink/link-text checks; `_check_seed_docs_refs` (`:55-72`) still applies, so the template must not reference nonexistent `docs/` paths (it references none). No extension of `test_workspace_seed_links.py` is needed — its existing `system/templates` hook starts covering the file the moment it exists; the init-lands-the-file test goes in `test_cli.py`.

**Interfaces:**
- Consumes: `SEED_FILES: tuple[tuple[str, str], ...]` (`cli.py:47-51`), `_copy_seed_file(source_rel: str, target: Path, *, overwrite: bool) -> None` (`cli.py:2466-2470`), `tests.helpers.WORKSPACE_SEED: Path` (already imported by `test_installer_skeleton.py:6`).
- Produces: the seeded vault file `system/templates/session-diary.md` (present after `memoria init` and restored by `doctor --repair`); `SEED_FILES` extended with `("system/templates/session-diary.md", "system/templates/session-diary.md")` — **cross-plan rebase note:** alpha23 R1NG.1 (plan `:106`, `:428-431`) and surfaces BOOT-D.6 also extend this tuple and the same pinned test lists; whichever plan lands second rebases both (surfaces plan Global Constraint 11).

- [ ] **Step 1: Write the failing tests.** In `tests/test_cli.py:414`, extend the pinned list (the dry-run report at `cli.py:2216` preserves `SEED_FILES` tuple order, so the new entry appends last):

```python
    assert output["package"]["seed_files"] == [
        ".gitignore",
        "steering.md",
        "system/vocabulary.md",
        "system/templates/session-diary.md",
    ]
```

Append to `tests/test_cli.py` (arrange mirrors the init test at `tests/test_cli.py:380-388`):

```python
def test_cli_init_seeds_the_session_diary_template(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"

    rc = main(["init", "--workspace", str(workspace), "--yes", "--quiet"])
    capsys.readouterr()

    assert rc == 0
    template = workspace / "system/templates/session-diary.md"
    assert template.is_file()
    text = template.read_text(encoding="utf-8")
    for field in ("Goal", "Workflow used", "Artifact kept", "Blocker hit", "Fallback used"):
        assert f"- {field}:" in text
    assert "delete or archive" in text.lower()
```

In `tests/test_installer_skeleton.py:31-54`, add to `expected_files` (alphabetical, after `"steering.md",` at `:52`):

```python
        "system/templates/session-diary.md",
```

In `tests/test_package_spine.py:86-103`, add to the packaged positive tuple (after `"steering.md",` at `:101`):

```python
        "system/templates/session-diary.md",
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_cli.py::test_cli_init_dry_run_reports_runtime_setup_without_mutation tests/test_cli.py::test_cli_init_seeds_the_session_diary_template tests/test_installer_skeleton.py tests/test_package_spine.py -v`
Expected: FAIL — the pinned `seed_files` list mismatches, `template.is_file()` is False, `_seed_files() == expected_files` mismatches (`system/templates/session-diary.md` expected but absent), and the package-spine `is_file()` assertion fails.

- [ ] **Step 3: Minimal implementation.**

(a) Create `src/memoria_vault/product/workspace_seed/system/templates/session-diary.md` (Phase 0's exact five fields, empirical plan `0.1.0-beta.1-empirical-use-action-plan.md:73-74`; the honest prose line is §6's operating rule, `:187`, quoted by O1 spec §6):

```markdown
# Session diary

Copy this template once per session (into `tmp/` or anywhere outside the
bundle roots) and fill the five lines right after the session ends. Diary
copies are local raw material, never vault knowledge: delete or archive
them once the decisions they fed are recorded.

- Goal:
- Workflow used:
- Artifact kept:
- Blocker hit:
- Fallback used:
```

(b) In `src/memoria_vault/cli.py:47-51`, extend `SEED_FILES`:

```python
SEED_FILES = (
    (".gitignore", ".gitignore"),
    ("steering.md", "steering.md"),
    ("system/vocabulary.md", "system/vocabulary.md"),
    ("system/templates/session-diary.md", "system/templates/session-diary.md"),
)
```

(If R1NG.1's `.base` pairs or BOOT-D.6's `Start here.md` already landed here, append after their entries and reconcile the three pinned test lists in the same edit — rebase note above.)

(c) In `pyproject.toml`, inside the `"memoria_vault.product.workspace_seed"` package-data list, add after `"system/*.md",` (`:45`):

```toml
  "system/templates/*.md",
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_cli.py tests/test_installer_skeleton.py tests/test_package_spine.py tests/test_workspace_seed_links.py -v`
Expected: PASS — including `test_workspace_seed_links.py`, whose `system/templates` frontmatter hook (`:127-130`) now exercises the new file.

- [ ] **Step 5: Section gate — run the one correctness command**

Run: `python scripts/verify`
Expected: green. This section edits no published `docs/` page, and its only doc touch (Branch B's note in `docs/superpowers/plans/`) sits inside the doc-claims gate's `SKIP_DIRS` (`scripts/checks/doc_claims_gate.py:23`), so no unshipped `memoria` CLI path can trip the gate; the package-level smoke in verify also proves the wheel carries the new template via the Step 3(c) glob.

- [ ] **Step 6: Commit**

```bash
git add src/memoria_vault/product/workspace_seed/system/templates/session-diary.md \
    src/memoria_vault/cli.py pyproject.toml \
    tests/test_cli.py tests/test_installer_skeleton.py tests/test_package_spine.py
git commit -m "feat(seed): session-diary template at system/templates (O1 spec §6, empirical plan Phase 0)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```
# D — Tutorial restructure + stale-steering doc sweep

Implements spec §3 (the wizard **is** the doc arc — chapter 01 gains the frame-your-project step, chapter 02 rewires onto `memoria seed install`, chapter 04 reconciles onto the already-framed project, plus §3's Start-here co-PI-link repoint), §4.5 (steering doc updates ride along) and slice 7 of `docs/superpowers/specs/2026-07-16-o1-onboarding-seed-design.md` (chapter 07 rewrite against the derived steering model + the stale-steering page sweep).

**Sequencing (binding).** This section runs **last among the O1 sections**:

- D.1 requires **M.3** (`memoria seed install` in the live argparse tree) — the doc-claims gate (`scripts/checks/doc_claims_gate.py:24,41-53`) walks the real parser and fails any doc that backticks a `memoria` path that does not exist; D.1's chapter 02 deliberately carries one inline `` `memoria seed install` `` so the gate actively guards the dependency.
- D.2 and D.3 require the spec-§4 steering tasks of this plan (`effective_steering_tokens`, the two-section `steering.md` reseed, and the `steering show` provenance repoint) — grep-gated preconditions are written into each task; if the greps miss, hold the task (the docs must not describe unshipped behavior).
- D.4 is order-tolerant against surfaces-plan BOOT-D.6 (`docs/superpowers/plans/2026-07-15-surfaces-bootstrap-and-plugins.md:5278-5427`): grep confirmed `Start here.md` is **not yet seeded** at 07bedc74 (`grep -rni "start here" src/` → no hits), so the default execution path records the repoint as a one-line amendment inside BOOT-D.6 rather than editing a seed file that doesn't exist.
- Section D records **no telemetry** — the I1 `record_telemetry_event` seam is not consumed here (the O1 emit points are code tasks in other sections).
- **No new test files** are created in this section, so `tests/conftest.py` `TEST_LEVELS` is untouched; the only test file touched (`tests/test_cli.py`, D.4's already-executed branch only) is already registered (`tests/conftest.py:25`, level `contract`).
- The tutorials deliberately do **not** backtick `memoria onboard` anywhere (BOOT-D owns it and may not have landed); the arc's onboard rung stays expressed by the bootstrap-seeded `Start here.md`, not by tutorial prose.

Verified CLI surfaces these docs instruct (all at 07bedc74): `memoria new project <name> --workspace <path> [--description] [--direction]` (`src/memoria_vault/cli.py:171-176`); `memoria steering show --workspace <path>` renders the raw file body today (`cli.py:2001-2007`) and becomes the effective-provenance render after the §4 repoint; `memoria steering edit --workspace <path> (--body <str> | --file <path>)` — **exactly one required**, wholesale-replaces `steering.md`, journals, and commits (`cli.py:511-515`, `cli.py:2010-2034`); `memoria list --type note|work|hub|project` (`cli.py:280`); `memoria work update <work-id> --check-status unchecked|checked|quarantined` (`cli.py:245`); `memoria work add --url/--pdf/--file` routing (`cli.py:877-931`).

### Task D.1: tutorial restructure — chapter 01 frames, chapter 02 seeds, chapter 04 reconciles

**Files:**

- Modify: `docs/tutorials/01-system-tour.md` (intro at :9-10; insert steps 4-5 after the fresh-vault JSON block ending :62; bullet list at :64-68)
- Modify: `docs/tutorials/02-first-source.md` (full-file replacement)
- Modify: `docs/tutorials/04-draft-section.md` (step 1 at :15-25; step 2 trailing paragraph at :32-33)
- Modify: `docs/tutorials/README.md` (intro paragraph :10-12; rows 01/02/04 at :19-22)
- Modify: `project-words.txt` (three cspell entries: `akari` after `affordances` :2, `asai` after `andrej` :4, `openscholar` after `openalex` :183 — the scope guard is `tests/test_cspell_scope.py`, no config change)

**Interfaces:**

- Consumes: `memoria seed install --workspace <path>` (produced by **M.3**: iterates the shipped manifest, per-row honesty, work_id pre-check idempotency, frame-first notice — spec §2); `memoria new project "Tutorial project" --workspace . --description <str>` (`cli.py:171-176`); `memoria steering show --workspace .` post-§4-repoint provenance render; `memoria work add --url <url> --title <str>` (`cli.py:877-884`, operation `capture-url-source`); `memoria work update <work-id> --check-status checked` (`cli.py:245`); `memoria work digest <work-id> --mode test`; `scripts/checks/doc_claims_gate.py`.
- Produces: the restructured arc order **init → onboard → frame project (ch. 01) → seed install (ch. 02) → … → ask** — the published pages `Start here.md` links to, and the pages the O1 telemetry emit points (`project-framed`, `seed-installed`) correspond to.

**Steps:**

- [ ] Precondition (order tolerance for M.3 — hold this task if it fails):

  ```bash
  python3 - <<'EOF'
  import argparse, sys
  sys.path.insert(0, "src")
  from memoria_vault.cli import _build_parser
  def walk(p, prefix=()):
      out = {prefix} if prefix else set()
      for a in p._actions:
          if isinstance(a, argparse._SubParsersAction):
              for name, sub in a.choices.items():
                  out |= walk(sub, (*prefix, name))
      return out
  paths = {" ".join(x) for x in walk(_build_parser())}
  assert "seed install" in paths, "M.3 has not landed - hold D.1"
  print("seed install present")
  EOF
  ```

- [ ] Red state (the failing check — both greps must exit 1 before editing):

  ```bash
  grep -n "memoria seed install" docs/tutorials/02-first-source.md
  grep -n "Frame your tutorial project" docs/tutorials/01-system-tour.md
  ```

  Expected: no matches, exit code 1 on each.

- [ ] Edit `docs/tutorials/01-system-tour.md`. Replace the intro (lines 9-10):

  old:

  ```markdown
  This first pass is read-only. You will inspect the workspace shape, the CLI
  surface, and the checked-read boundary before adding research material.
  ```

  new:

  ```markdown
  This first pass inspects the workspace shape, the CLI surface, and the
  checked-read boundary, then closes with the one write that aims everything
  after it: framing your tutorial project.
  ```

  Insert steps 4-5 between the fresh-vault JSON block (ends line 62) and `## What you should have seen` (line 64):

  ````markdown
  **4. Frame your tutorial project.**

  ```bash
  memoria new project "Tutorial project" \
    --workspace . \
    --description "A small project for learning the project WRITE loop."
  ```

  Save the created project path.
  Notice that the path is under `projects/`. Framing is not paperwork: active
  projects are what aim the system — discovery ranking and the steering
  surface derive directly from them, so the arc frames before it captures.

  **5. See the project aim the workspace.**

  ```bash
  memoria steering show --workspace .
  ```

  The command renders the effective steering: every token with its
  provenance. Right now each token traces to the project you just framed.
  `steering.md` at the vault root stays thin — it holds only your watch/mute
  overrides, which [07: Customize](07-customize.md) exercises.
  ````

  Append one bullet to `## What you should have seen` — old:

  ```markdown
  - Checked reads come from engine projections over checked Concepts and catalog rows.
  ```

  new:

  ```markdown
  - Checked reads come from engine projections over checked Concepts and catalog rows.
  - Steering is derived: framing a project is what aims discovery.
  ```

- [ ] Replace the full contents of `docs/tutorials/02-first-source.md` with (the old `--file` example survives verbatim as the offline path — task binding; **SPEC GAP:** spec §1 names `memoria work add --pdf` as the offline fallback while the shipped chapter exercises `--file`; resolution: keep `--file` as the exercised path and name `--pdf` inline — spec §8 accepts "local-file/-PDF alternative path (arbitrary local content)", so either satisfies):

  ````markdown
  ---
  title: "02: First source"
  parent: Tutorials
  nav_order: 2
  ---

  # 02: First source

  This tutorial fills the catalog with `memoria seed install` — eight openly
  licensed sources on knowledge-work cognition (note-taking, external memory,
  spaced retrieval, argumentation, LLM-assisted research), fetched keyless
  from a shipped manifest. If you are offline, one local file gives you the
  same capture path; the corpus is the paved road, never a gate.

  ## Steps

  **1. Install the seed corpus.**

  ```bash
  memoria seed install --workspace .
  ```

  The command iterates the shipped manifest (pinned identifiers, verified
  licenses, keyless fetch URLs), downloads each source, and routes it through
  the same capture path as a local PDF. Failures are per-row: a fetch that
  fails names its row and the run continues. Re-running is safe — already
  admitted rows are skipped, and a full-skip re-run performs no fetches and
  exits clean.
  Notice the admitted rows in the output. If you had skipped the framing step
  in Tutorial 01, the command would print a frame-your-project-first notice
  and proceed.

  **2. Offline alternative: capture one local file instead.**

  No network? The same capture path accepts any local content (a local PDF
  works too, via `--pdf`):

  ```bash
  mkdir -p tmp/tutorial
  printf 'A short source about just-in-time adaptive interventions.\n' > tmp/tutorial/first-source.txt
  memoria work add --workspace . \
    --file tmp/tutorial/first-source.txt \
    --title "First tutorial source" \
    --json
  ```

  Either way — seed corpus or local file — capture creates a worker request,
  writes a catalog row, stores source blobs under
  `.memoria/blobs/source-content/`, and journals the capture.

  **3. Inspect one Work record.**

  List the catalog and pick one `work_id` (from the seed install output or
  the JSON below):

  ```bash
  memoria list --workspace . --type work --json
  memoria work export --workspace . <work-id> --json
  ```

  Look for `check_status`, `content_path`, `raw_path`, and hash fields. Those
  are the provenance anchors the rest of the system reads.
  The paths should point under `.memoria/blobs/source-content/`.

  **4. Check the Work after reviewing it.**

  Captures start unchecked. After inspecting the exported record and source
  text, record the PI decision that makes it available to checked-read
  operations:

  ```bash
  memoria work update --workspace . <work-id> --check-status checked
  ```

  **5. Capture a paper's companion repository.**

  One corpus paper (OpenScholar) ships with its open-source companion repo.
  A paper's repo is often the method's only complete specification —
  capturing both is the habit worth building:

  ```bash
  memoria work add --workspace . \
    --url https://github.com/AkariAsai/OpenScholar \
    --title "OpenScholar companion repository"
  ```

  **6. Compile a digest when a source is ready.**

  ```bash
  memoria work digest --workspace . <work-id> --mode test
  ```

  The digest path uses the manifest-pinned runner for the selected mode. Use
  `--mode live` only after provider config and the seeded-error gate support
  it.
  Notice the digest path or request result. The digest is the first
  source-derived artifact you can inspect.

  ## What you should have seen

  - The seed corpus is fetched on onboarding from a shipped manifest —
    pinned, openly licensed, keyless — never bundled content.
  - Capture enters through the request/worker path, online or offline.
  - Source bytes and normalized text are blobs, not frontmatter.
  - A captured Work remains unchecked until the PI checks it.
  - A digest is source-derived material keyed by `work_id`.

  For more detail on capturing sources by DOI, URL, or PDF:
  [Capture and ingest](../how-to-guides/library/capture-and-ingest.md).

  Next: [03: Connect notes](03-connect-notes.md).
  ````

- [ ] Edit `docs/tutorials/04-draft-section.md`. Replace step 1 (lines 15-25):

  old:

  ````markdown
  **1. Create a project Concept.**

  ```bash
  memoria new project "Tutorial project" \
    --workspace . \
    --description "A small project for learning the project WRITE loop."
  ```

  Save the created project path.
  Notice that the path is under `projects/`.
  ````

  new:

  ````markdown
  **1. Use the tutorial project you framed in Tutorial 01.**

  The project already exists — you framed it at the end of
  [01: System tour](01-system-tour.md), and it has been aiming discovery
  ever since. Recover its path if you did not save it:

  ```bash
  memoria list --workspace . --type project --json
  ```

  Save the project path.
  Notice that the path is under `projects/`, and that the WRITE loop reuses
  the framed project instead of creating a new one.
  ````

  Replace the step 2 trailing paragraph (lines 32-33):

  old:

  ```markdown
  New Concepts start unchecked. The slice operation reads only checked project
  and note state.
  ```

  new:

  ```markdown
  Like every new Concept, the project started unchecked when Tutorial 01
  created it. The slice operation reads only checked project and note state.
  ```

- [ ] Edit `docs/tutorials/README.md`. Replace the intro paragraph (lines 10-12):

  old:

  ```markdown
  This tutorial arc walks through one small research loop in a fresh vault. By the
  end, you will have captured a source, created checked notes, drafted from a
  project slice, verified the draft, and made one workspace customization.
  ```

  new:

  ```markdown
  This tutorial arc walks through one small research loop in a fresh vault. By the
  end, you will have framed a project, installed the seed corpus (or captured one
  local source offline), created checked notes, drafted from a project slice,
  verified the draft, and made one workspace customization.
  ```

  Replace the three table rows (lines 19, 20, 22):

  old:

  ```markdown
  | [01: System tour](01-system-tour.md) | Inspect the workspace, command surface, and checked-read boundary |
  | [02: First source](02-first-source.md) | Capture one local source and compile a digest |
  ```

  new:

  ```markdown
  | [01: System tour](01-system-tour.md) | Inspect the workspace and checked-read boundary, then frame the tutorial project |
  | [02: First source](02-first-source.md) | Install the seed corpus (or capture one local source offline) and compile a digest |
  ```

  old:

  ```markdown
  | [04: Draft section](04-draft-section.md) | Create a project slice, compose a draft, and verify it |
  ```

  new:

  ```markdown
  | [04: Draft section](04-draft-section.md) | Slice the tutorial project, compose a draft, and verify it |
  ```

- [ ] Edit `project-words.txt`: insert `akari` between `affordances` (line 2) and `amershi` (line 3); insert `asai` between `andrej` (line 4) and `asreview` (line 5); insert `openscholar` between `openalex` (line 183) and `operationalizes` (line 184).

- [ ] Green state:

  ```bash
  grep -n "memoria seed install" docs/tutorials/02-first-source.md   # >=1 hit
  grep -n "Frame your tutorial project" docs/tutorials/01-system-tour.md  # 1 hit
  grep -c "memoria new project" docs/tutorials/04-draft-section.md   # prints 0
  python3 scripts/checks/doc_claims_gate.py                          # doc-claims-gate: clean
  python -m pytest tests/test_cspell_scope.py -q                     # passes
  ```

- [ ] Commit:

  ```bash
  git add docs/tutorials/01-system-tour.md docs/tutorials/02-first-source.md docs/tutorials/04-draft-section.md docs/tutorials/README.md project-words.txt
  git commit -m "docs(tutorials): frame project in ch.01, rewire ch.02 onto seed corpus, reconcile ch.04 (O1 slice 7)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

### Task D.2: chapter 07 steering exercise rewrite + tutorials/README row

**Files:**

- Modify: `docs/tutorials/07-customize.md` (full-file replacement — the shipped page's step 2 does `memoria steering edit --body "Focus this tutorial workspace on…"`, `07-customize.md:27-29`, a whole-file free-prose replace that is dead under the derived model)
- Modify: `docs/tutorials/README.md` (row 07 at :25; intro clause as left by D.1)

**Interfaces:**

- Consumes: the spec-§4 tasks of this plan — `effective_steering_tokens(vault)` replacing `_steering_tokens` at its single call-site (`src/memoria_vault/runtime/knowledge.py:1142,1193-1197`), the reseeded two-section `steering.md` (`## Watch for` / `## Muted`, same frontmatter `type: system` / `title: Steering` as today's seed, `src/memoria_vault/product/workspace_seed/steering.md:1-4`), and the repointed `memoria steering show` provenance render; `memoria steering edit --workspace . --file <path>` (`cli.py:511-515,2010-2034` — verified: `--body`/`--file` mutually exclusive, one required, wholesale replace). **SPEC GAP:** spec §4.3 says `steering edit` "still opens the override file", but the shipped command opens nothing — it takes `--body`/`--file` and replaces `steering.md` wholesale; resolution: the tutorial documents the shipped mechanism (`--file` with a prepared file, repo convention from ch. 02's `printf` pattern); any edit-UX change belongs to the §4 code tasks, not to docs.
- Produces: the derived-model steering exercise (watch → provenance appears; mute → token subtracted even when project-contributed — mirroring spec §8's acceptance case where the muted term also sits in a project title).

**Steps:**

- [ ] Precondition (order tolerance for the §4 tasks — hold D.2 and D.3 if either grep misses):

  ```bash
  grep -rn "effective_steering_tokens" src/memoria_vault/          # >=1 hit
  grep -n "## Watch for" "src/memoria_vault/product/workspace_seed/steering.md"  # 1 hit
  ```

  If the reseed task changed the seed frontmatter, mirror the actual seeded frontmatter in the heredocs below instead of `type: system` / `title: Steering`.

- [ ] Red state: `grep -n "## Watch for" docs/tutorials/07-customize.md` — expected: no match, exit 1.

- [ ] Replace the full contents of `docs/tutorials/07-customize.md` with (**SPEC GAP:** spec slice 7 says only "chapter 07's steering exercise rewrites against the derived model" and does not say whether the old page's second-project step survives; resolution: keep it — creating "Burden follow-up" is the cleanest demonstration that steering derives from projects, and it supplies the term-also-in-a-project-title case that spec §8's mute acceptance requires):

  ````markdown
  ---
  title: "07: Customize"
  parent: Tutorials
  nav_order: 7
  ---

  # 07: Customize

  Now that one loop works, tune what the workspace pursues and confirm that
  Memoria reads it back. Steering is derived from your active projects, hubs,
  and question notes; `steering.md` is a thin override with exactly two
  levers — **Watch for** (terms that fit no artifact yet) and **Muted**
  (terms to suppress). This chapter exercises all three moves: a new
  project, a watch entry, and a mute entry.

  ## Steps

  **1. Read the effective steering.**

  ```bash
  memoria steering show --workspace .
  ```

  Every steering token renders with its provenance — which project, hub,
  question note, or watch entry contributed it. In this workspace the tokens
  trace to the tutorial project you framed in Tutorial 01. Nothing here was
  authored as steering prose; it is derived from what you are actually
  working on.

  **2. Create a second, narrower project.**

  ```bash
  memoria new project "Burden follow-up" \
    --workspace . \
    --description "A follow-up question about participant burden in JITAIs."
  ```

  Run the read command again:

  ```bash
  memoria steering show --workspace .
  ```

  New tokens appear with the new project as their provenance. That is the
  main steering move in Memoria: frame a project, and the system pursues it.
  Archiving a project is equally structural — an archived project simply
  stops contributing.

  **3. Add a Watch-for entry.**

  Some terms are worth pursuing before any project or note exists for them.
  Those go in the override file's **Watch for** section. Replace the
  override with one watch entry:

  ```bash
  mkdir -p tmp/tutorial
  cat > tmp/tutorial/steering.md <<'EOF'
  ---
  type: system
  title: Steering
  ---

  # Steering

  ## Watch for

  - ecological momentary assessment

  ## Muted
  EOF
  memoria steering edit --workspace . --file tmp/tutorial/steering.md
  memoria steering show --workspace .
  ```

  The watch entry's tokens now appear in the effective steering with watch
  provenance — steering the system toward material no artifact expresses
  yet.

  **4. Mute a term.**

  Muting is token-set subtraction: a muted term is removed from the
  effective steering even when an active project contributes it. Rewrite the
  override with a Muted entry:

  ```bash
  cat > tmp/tutorial/steering.md <<'EOF'
  ---
  type: system
  title: Steering
  ---

  # Steering

  ## Watch for

  - ecological momentary assessment

  ## Muted

  - burden
  EOF
  memoria steering edit --workspace . --file tmp/tutorial/steering.md
  memoria steering show --workspace .
  ```

  The token contributed by "Burden follow-up" is gone from the effective
  set. From now on, a discovery candidate matching only that term routes to
  the exploration channel instead of the ranked list; a candidate that also
  matches a surviving token still ranks. One caution: a multi-word entry
  mutes each of its words separately, so keep mute entries narrow.

  **5. Check what changed.**

  ```bash
  memoria workspace scan --workspace .
  memoria status --workspace .
  git status --short
  ```

  The changed files should be ordinary workspace files. Nothing about this
  step requires Obsidian, Zotero, or a live model provider.

  ## What you should have seen

  - Steering is derived: projects, hubs, and question notes aim the system;
    archiving is how a topic goes quiet.
  - `steering.md` is a thin override — watch terms that fit no artifact yet,
    mute terms to suppress — not an essay about your research.
  - `memoria steering show` is the read surface: every effective token with
    its provenance.

  For optional setup, continue with [How-to guides](../how-to-guides/README.md).
  ````

- [ ] Edit `docs/tutorials/README.md`. Replace row 07 (line 25):

  old:

  ```markdown
  | [07: Customize](07-customize.md) | Change steering and create one narrower project |
  ```

  new:

  ```markdown
  | [07: Customize](07-customize.md) | Watch, mute, and see steering derive from your projects |
  ```

  Replace the intro's closing clause (as left by D.1):

  old: `verified the draft, and made one workspace customization.`
  new: `verified the draft, and tuned the steering override with one watch and one mute entry.`

- [ ] Green state:

  ```bash
  grep -n "## Watch for" docs/tutorials/07-customize.md              # >=2 hits (both heredocs)
  grep -c -- "--body \"Focus this tutorial" docs/tutorials/07-customize.md  # prints 0
  python3 scripts/checks/doc_claims_gate.py                          # doc-claims-gate: clean
  ```

- [ ] Commit:

  ```bash
  git add docs/tutorials/07-customize.md docs/tutorials/README.md
  git commit -m "docs(tutorials): rewrite ch.07 steering exercise against the derived model (O1 spec 4)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

### Task D.3: stale-steering sweep across the seven named pages

Spec slice 7 names eight stale-steering surfaces; seven are published doc pages swept here, the eighth (the seeded `Start here.md` co-PI link) is D.4. Every edit below asserts the derived model — steering derives from active projects/hubs/question notes, `steering.md` is the watch/mute override, `memoria steering show` is the effective render with provenance — and stays within one-to-three line edits per page except where noted. Same §4 precondition as D.2 (the greps at the top of D.2 — run them again; hold if they miss).

**Files:**

- Modify: `docs/reference/pipelines-and-io/memory-substrates.md` (:19, :32, :45, :49 — four line edits, one over the guideline, because the spec's own range `:19-49` covers four distinct stale assertions and leaving :49 would keep `steering.md` as a preferences home, contradicting the override-only model)
- Modify: `docs/explanation/architecture/memory-model.md` (:23-24)
- Modify: `docs/how-to-guides/using-obsidian/README.md` (:17)
- Modify: `docs/reference/commands-and-transports/cli.md` (:66 — the roster lines :130-131 and the PI-only note :200 stay correct and are untouched)
- Modify: `docs/reference/system/on-disk-layout.md` (:31, :120)
- Modify: `docs/how-to-guides/knowledge/build-a-hub.md` (:79)
- Modify: `docs/how-to-guides/inbox/run-the-weekly-review.md` (:10-11, :22, :24, :85 — this page gets four edits because spec §4.5 additionally mandates the "refresh your steering" line, which lives at :10, alongside the task-named :24 and :85)

**Interfaces:**

- Consumes: the §4 steering seams (as D.2); `_relevance_tokens` semantics for honest mute prose (`src/memoria_vault/runtime/knowledge.py:1229-1235` — per-token, so multi-word entries suppress each word); the `archived: bool` project frontmatter field (`src/memoria_vault/product/workspace_seed/.memoria/schemas/types/project.yaml:11`) for the archive instruction; ranked/exploration routing (`knowledge.py:1214`).
- Produces: a doc corpus with zero remaining assertions of the retired five-section authored-steering model on the spec-named pages.

**Steps:**

- [ ] Red state — confirm every stale line is present (each grep hits exactly once):

  ```bash
  grep -n "The PI authors \`steering.md\`" docs/reference/pipelines-and-io/memory-substrates.md
  grep -n "\`steering\` discovery priorities" docs/explanation/architecture/memory-model.md
  grep -n "Open \`steering.md\` when you need the project direction" docs/how-to-guides/using-obsidian/README.md
  grep -n "Read steering; editing is PI-only" docs/reference/commands-and-transports/cli.md
  grep -n "program memory; the PI's standing steering" docs/reference/system/on-disk-layout.md
  grep -n "Standing program memory read and edited" docs/reference/system/on-disk-layout.md
  grep -n "link it from \`steering.md\` or a parent hub" docs/how-to-guides/knowledge/build-a-hub.md
  grep -n "refresh your steering" docs/how-to-guides/inbox/run-the-weekly-review.md
  ```

- [ ] `docs/reference/pipelines-and-io/memory-substrates.md` — four exact line edits:

  :19 old:

  ```markdown
  | **Program memory** | Memoria — vault files | Whole research program | Persistent | Vault root (`steering.md`) | Standing steering: discovery priorities, review mode. The PI's main lever over what the system pursues. |
  ```

  :19 new:

  ```markdown
  | **Program memory** | Memoria — derived + vault files | Whole research program | Persistent | Active projects, hubs, and question notes; vault-root `steering.md` (watch/mute override) | Standing steering, derived from the artifacts you keep active; `memoria steering show` renders it with per-token provenance. The main lever is framing and archiving projects. |
  ```

  :32 old:

  ```markdown
  | Program memory is the PI's steering | The PI authors `steering.md`; every operation can read it; it never archives. |
  ```

  :32 new:

  ```markdown
  | Program memory is the PI's steering | Derived from active projects, hubs, and question notes; the PI authors only the `steering.md` watch/mute override; it never archives. |
  ```

  :45 old:

  ```markdown
  | What you want the system to pursue | Program memory (`steering.md`) | local tool config (that's config, not recall) |
  ```

  :45 new:

  ```markdown
  | What you want the system to pursue | Program memory (active projects and hubs; `steering.md` for watch/mute overrides) | local tool config (that's config, not recall) |
  ```

  :49 old:

  ```markdown
  | The PI's preferences and style | Program memory (`steering.md`) or checked preference notes | Adapter chat/session history |
  ```

  :49 new:

  ```markdown
  | The PI's preferences and style | Checked preference notes | Adapter chat/session history |
  ```

- [ ] `docs/explanation/architecture/memory-model.md` — :23-24 old:

  ```markdown
  **Program memory** (your standing steering — `steering` discovery priorities +
  `screening-protocol` review mode), **project memory** (one sub-project's
  ```

  new (the dropped `screening-protocol` token names no shipped seed file — the seed carries only `steering.md` and `system/vocabulary.md` — so it goes with the stale framing):

  ```markdown
  **Program memory** (your standing steering — derived from active projects,
  hubs, and question notes, plus the `steering.md` watch/mute override),
  **project memory** (one sub-project's
  ```

- [ ] `docs/how-to-guides/using-obsidian/README.md` — :17 old:

  ```markdown
  2. Open `steering.md` when you need the project direction.
  ```

  new:

  ```markdown
  2. Run `memoria steering show` when you need the program direction — it is
     derived from your active projects, hubs, and question notes; `steering.md`
     holds only your watch/mute override.
  ```

- [ ] `docs/reference/commands-and-transports/cli.md` — :66 old:

  ```markdown
  | `memoria steering show/edit` | Read steering; editing is PI-only. |
  ```

  new:

  ```markdown
  | `memoria steering show/edit` | Render effective steering (derived from active projects, hubs, and question notes, plus the watch/mute override) with per-token provenance; edit the `steering.md` override. Editing is PI-only. |
  ```

- [ ] `docs/reference/system/on-disk-layout.md` — :31 old:

  ```text
  ├── steering.md              program memory; the PI's standing steering
  ```

  new:

  ```text
  ├── steering.md              watch/mute steering override (effective steering derives from projects, hubs, and question notes)
  ```

  :120 old:

  ```markdown
  | `steering.md` | Standing program memory read and edited through the CLI and knowledge runtime. |
  ```

  new:

  ```markdown
  | `steering.md` | Watch/mute steering override read by the knowledge runtime and the steering CLI; effective steering derives from active projects, hubs, and question notes. |
  ```

- [ ] `docs/how-to-guides/knowledge/build-a-hub.md` — :79 old:

  ```markdown
  - The hub shows up where you'd look for the topic — link it from `steering.md` or a parent hub if not
  ```

  new:

  ```markdown
  - The hub shows up where you'd look for the topic — link it from a parent hub if not; its title and tags already feed effective steering (`memoria steering show` renders them with hub provenance)
  ```

- [ ] `docs/how-to-guides/inbox/run-the-weekly-review.md` — spec §4.5's exact rewording plus the two task-named lines:

  :10-11 old:

  ```markdown
  Walk the Friday ritual: refresh your steering, sweep the Inbox, inspect new
  material, and run the structural checks. Allow up to ~60 minutes; closer to
  ```

  new:

  ```markdown
  Walk the Friday ritual: archive stale projects and prune watch/mute, sweep
  the Inbox, inspect new material, and run the structural checks. Allow up to
  ~60 minutes; closer to
  ```

  :22 old:

  ```markdown
  **Step 1 — Refresh research priorities (2 min).**
  ```

  new:

  ```markdown
  **Step 1 — Archive stale projects, prune watch/mute (2 min).**
  ```

  :24 old:

  ```markdown
  Open `steering.md`. Confirm or update the active questions and reading focus — the [Librarian](../../explanation/execution/operation-postures/librarian.md) reads this to aim discovery, and it sets the lens for every decision below.
  ```

  new:

  ```markdown
  Run `memoria steering show`. Effective steering derives from your active projects, hubs, and question notes, minus `steering.md` mutes — archive projects that are no longer live (set `archived: true` in the project's frontmatter) and prune stale watch/mute entries. The [Librarian](../../explanation/execution/operation-postures/librarian.md) reads this to aim discovery, and it sets the lens for every decision below.
  ```

  :85 old:

  ```markdown
  - `steering.md` reflects what you actually intend to read next week
  ```

  new:

  ```markdown
  - `memoria steering show` reflects what you actually intend to read next week — active projects current, watch/mute pruned
  ```

- [ ] **SPEC GAP:** two pages outside the spec's named list still mention `steering.md` generically — `docs/explanation/rationale/boundaries/why-not-autonomous.md:107-108` ("The human sets the strategy (`steering.md`, `screening-protocol.md`)") and `docs/explanation/surfaces/obsidian/README.md:22` ("A fresh workspace gives you `steering.md`"). Resolution: the spec's page list was adversarially verified and is decided; both statements stay literally true under the derived model (the file exists at the root and the PI still authors it), so they are left untouched here and flagged for the next consistency-audit rather than swept.

- [ ] Green state — every red-state grep from step 1 now exits 1, then:

  ```bash
  python3 scripts/checks/doc_claims_gate.py       # doc-claims-gate: clean
  python -m pytest tests/test_workspace_seed_links.py -q  # passes (seed->docs refs unchanged)
  ```

- [ ] Commit:

  ```bash
  git add docs/reference/pipelines-and-io/memory-substrates.md docs/explanation/architecture/memory-model.md docs/how-to-guides/using-obsidian/README.md docs/reference/commands-and-transports/cli.md docs/reference/system/on-disk-layout.md docs/how-to-guides/knowledge/build-a-hub.md docs/how-to-guides/inbox/run-the-weekly-review.md
  git commit -m "docs: stale-steering sweep - assert the derived steering model on the seven spec-named pages (O1 slice 7)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

### Task D.4: Start here.md co-PI-variant link repoint (order-tolerant) + section gate

Spec §3, last bullet: the bootstrap-seeded `Start here.md` link to "the co-PI variant" repoints at the ADR-113 re-deferral note (the #902 comment shipped with the spec PR — already done, do not re-post) until ADR-113's preconditions close, so no seeded link dangles. BOOT-D.6 as currently planned seeds a co-PI bullet pointing at `.claude/skills/memoria-copi/SKILL.md` (`docs/superpowers/plans/2026-07-15-surfaces-bootstrap-and-plugins.md:5376-5378`) and asserts that path in its test (`:5338`) — the U4 plugin that would put a file there is designed but unimplemented.

**Files:**

- Modify (branch A — BOOT-D.6 not yet executed, the state verified at 07bedc74): `docs/superpowers/plans/2026-07-15-surfaces-bootstrap-and-plugins.md` (insert one amendment note after the BOOT-D.6 heading at :5278)
- Modify (branch B — BOOT-D.6 already executed): `src/memoria_vault/product/workspace_seed/Start here.md` (co-PI bullet), `tests/test_cli.py` (the `.claude/skills/memoria-copi/SKILL.md` assertion inside `test_cli_init_seeds_start_here_front_door`), `tests/fixtures/floor/goldens/*.json` (regenerated — the floor digest hashes every seeded file per BOOT-D.6)

**Interfaces:**

- Consumes: surfaces-plan BOOT-D.6 seed content and test (`2026-07-15-surfaces-bootstrap-and-plugins.md:5278-5427`); `tests/test_workspace_seed_links.py` seed-link rules (external GitHub issue URLs are exempt from the link-text checks, `test_workspace_seed_links.py:36-38`; only `github.com/.../blob/main/docs/` URLs are rejected, `:71-72`).
- Produces: a seeded co-PI pointer that resolves (issue #902 re-deferral) instead of a dangling SKILL.md path — consumed by whoever executes BOOT-D.6, or shipped directly when it already ran.

**Steps:**

- [ ] Branch selection (grep-first, run at execution time):

  ```bash
  ls "src/memoria_vault/product/workspace_seed/Start here.md" 2>/dev/null && echo BRANCH-B || echo BRANCH-A
  ```

  At 07bedc74 this prints `BRANCH-A` (verified: `grep -rni "start here" src/` returns nothing).

- [ ] **Branch A** — red state: `grep -n "O1 §3 amendment" docs/superpowers/plans/2026-07-15-surfaces-bootstrap-and-plugins.md` → no match, exit 1. Then insert immediately after the heading line `### Task BOOT-D.6: seed \`Start here.md\` at the vault root from \`init\`` (:5278) and its blank line:

  ```markdown
  > **O1 §3 amendment (2026-07-16):** ADR-113 is re-deferred (see the note on
  > [issue #902](https://github.com/eranroseman/memoria-vault/issues/902)) and
  > the U4 co-PI plugin is unimplemented — when executing this task, seed the
  > co-PI bullet as
  > `- **Co-PI agent** (deferred): a guided co-PI walk-through is designed but
  > re-deferred until its preconditions close — see the ADR-113 status note on
  > [issue #902](https://github.com/eranroseman/memoria-vault/issues/902). The
  > tutorial arc above is the script it will dramatize.`
  > and assert `"issues/902" in text` instead of the
  > `.claude/skills/memoria-copi/SKILL.md` assertion, so no seeded link
  > dangles.
  ```

  Green: the red grep now hits. `docs/superpowers/` is excluded from the doc-claims gate (`scripts/checks/doc_claims_gate.py:23`) and from cspell (`cspell.json` ignorePaths), so no gate interaction.

- [ ] **Branch B** — red state: `grep -n "memoria-copi" "src/memoria_vault/product/workspace_seed/Start here.md"` → 1 hit (the dangling pointer is present). Replace the seeded co-PI bullet:

  old:

  ```markdown
  - **Co-PI agent**: open an agent session in this vault. The method is
    vault-embedded at `.claude/skills/memoria-copi/SKILL.md` and loads
    automatically; ask the agent to walk the tutorial with you.
  ```

  new:

  ```markdown
  - **Co-PI agent** (deferred): a guided co-PI walk-through is designed but
    re-deferred until its preconditions close — see the ADR-113 status note on
    [issue #902](https://github.com/eranroseman/memoria-vault/issues/902). The
    tutorial arc above is the script it will dramatize.
  ```

  In `tests/test_cli.py::test_cli_init_seeds_start_here_front_door`, replace the line
  `assert ".claude/skills/memoria-copi/SKILL.md" in text` with
  `assert "issues/902" in text`
  (re-anchor by test name — BOOT-D.6 appends it after `test_cli_init_dry_run_reports_runtime_setup_without_mutation`; `tests/test_cli.py` is already registered in `tests/conftest.py:25`, level `contract` — no `TEST_LEVELS` change). Then regenerate the floor goldens, which hash every seeded file:

  ```bash
  MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest tests/test_floor_coverage.py tests/test_floor_sweep_operations.py -v
  python -m pytest tests/test_cli.py tests/test_workspace_seed_links.py tests/test_floor_coverage.py tests/test_floor_sweep_operations.py tests/test_floor_seed.py tests/test_floor_invariants.py -v
  ```

  Expected: all pass; `test_workspace_seed_links` accepts the issue URL (external link, exempt from link-text rules).

- [ ] Section gate — run the one correctness command from the repo root:

  ```bash
  python scripts/verify
  ```

  Expected: full pass, including `scripts/checks/doc_claims_gate.py` (clean — every backticked `memoria` path introduced by D.1-D.3 exists in the live argparse tree by now) and the static/contract test levels touched above.

- [ ] Commit (branch A paths shown; branch B substitutes its file set):

  ```bash
  git add docs/superpowers/plans/2026-07-15-surfaces-bootstrap-and-plugins.md
  git commit -m "docs(plans): repoint BOOT-D.6 Start-here co-PI bullet at the ADR-113 re-deferral (O1 spec 3)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

  Branch B:

  ```bash
  git add "src/memoria_vault/product/workspace_seed/Start here.md" tests/test_cli.py tests/fixtures/floor/goldens
  git commit -m "seed: repoint Start-here co-PI pointer at the ADR-113 re-deferral, no dangling link (O1 spec 3)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```