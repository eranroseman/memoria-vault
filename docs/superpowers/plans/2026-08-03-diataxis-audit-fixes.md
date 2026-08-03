# Diátaxis-Audit Repairs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land every confirmed finding of the 2026-08-03 Diátaxis documentation audit: two HIGH reference-completeness defects, the mislabeled trust column that caused them, a code→docs roster-completeness gate, seven MEDIUM/LOW accuracy fixes, and the reciprocal cross-quadrant links the audit ranked highest-value.

**Architecture:** Docs-only edits across `docs/`, plus one checker extension (`scripts/checks/doc_claims_gate.py` gains a reverse-direction roster-completeness check with tests). Tasks 1–2 fix the two drifted rosters, Task 3 pins them so they cannot drift silently again, Tasks 4–10 land the remaining accuracy and link fixes, Task 11 runs the full gate and opens the PR.

**Tech Stack:** Markdown (Jekyll/just-the-docs GitHub Pages), Python 3 checker scripts, pytest (marker `static`), pre-commit (vale, markdownlint-structural, cspell).

## Global Constraints

- Work in an isolated worktree: `git worktree add .claude/worktrees/docaudit -b wip/docaudit origin/main` from the main checkout, then `EnterWorktree(path: ".claude/worktrees/docaudit")`. Another session's worktrees (`cov-*`, `docfix`) are live — never touch them, never `pkill` by pattern.
- Stage explicit paths only. NEVER `git add -A` or `git add .` — a PreToolUse hook rejects unbounded staging (the git index is shared per checkout).
- **Terminology gate:** in any file under `docs/`, the word "checked" must not appear within 100 characters of "verified", "trusted", or "approved" (`scripts/checks/checked_terminology_gate.py` fails the build). Prefer "pinned", "guarded", "machine-enforced" when describing gates.
- **Link conventions:** inside `docs/`, relative links follow the target's Pages route. Unpublished targets (root files, `design-history/`) use GitHub blob URLs (`https://github.com/eranroseman/memoria-vault/blob/main/...`). Never relative-link into `src/` — cite source files as inline-code paths.
- American English (`-ize`/`-or`); cspell is a gate; a genuinely new term goes in `project-words.txt` (lowercase, sorted), never inline-suppressed.
- Correctness command: `python scripts/verify`. Per-task, run the cheaper subset named in each task; the full gate runs once in Task 11.
- Merge by squash; `main` requires a PR plus the `verify` and `gitleaks` checks. One scope per PR — everything here is one scope (audit repairs).
- Do not edit `CHANGELOG.md` (hand-curated; a concurrent session is editing it).
- Line numbers below are from `origin/main` at commit `470b7073`. Verify each `old` block with Read before editing; if a file drifted, match on content, not line number.

## Execution order

- **Wave 1 (file-disjoint, parallelizable):** Tasks 1, 2, 4, 5, 6, 7, 8, 9, 10.
- **Wave 2 (after 1 and 2 are merged):** Task 3 — the gate must see the repaired rosters or it fails its own landing.
- **Wave 3:** Task 11.

---

### Task 1: cli.md — add the five missing commands (HIGH)

**Files:**
- Modify: `docs/reference/commands-and-transports/cli.md`

**Interfaces:**
- Produces: a "Complete command roster" list that exactly matches the runnable argparse paths. Task 3's gate parses this section under the heading `## Complete command roster`, entries formatted `` - `memoria <path>` `` — do not change the heading or the entry format.

Line 89 claims "This roster mirrors the live argparse tree:" but five runnable commands are absent: `memoria onboard`, `memoria context`, `memoria cockpit`, `memoria seed install`, `memoria journal revert-preview` (registrations at `src/memoria_vault/cli.py` L144, L152, L233, L377-383, L259/753-756; all five answer `--help` today).

- [ ] **Step 1: Insert the five roster bullets at their alphabetical slots**

The roster (L91–175) is sorted alphabetically by the full command string. Five insertions:

After `- `memoria check`` (L96), before `- `memoria dashboard`` (L97):

```markdown
- `memoria cockpit`
- `memoria context`
```

Before `- `memoria journal show`` (L110):

```markdown
- `memoria journal revert-preview`
```

After `- `memoria new project`` (L119), before `- `memoria operation list`` (L120):

```markdown
- `memoria onboard`
```

After `- `memoria secrets set`` (L149), before `- `memoria serve`` (L150):

```markdown
- `memoria seed install`
```

- [ ] **Step 2: Add the five commands to the thematic tables**

In the `## Core` table, after the `memoria dashboard` row (L36):

```markdown
| `memoria cockpit [--project <path>|--triage]` | Compose the deep-work or triage cockpit screens from registry reads. `--project` selects the deep screen, `--triage` the triage screen; the two never mix. |
| `memoria context` | Read the situated context bundle for the active session. |
| `memoria onboard` | Walk from installed engine to the tutorial open in Obsidian. |
```

In the `## Work` table, after the `memoria work import` row (L44):

```markdown
| `memoria seed install` | Install the shipped seed-corpus manifest rows as unchecked catalog Work rows — pinned identifiers, keyless fetches; re-runs skip already admitted rows. PI-only. |
```

In the `## Knowledge And Projects` table, replace the journal row (L77):

```markdown
| `memoria journal tail/show/verify` | Inspect journal entries or verify the authoritative hash chain, live-tip anchor, committed anchor prefix, and JSONL export subset. |
```

with:

```markdown
| `memoria journal tail/show/verify/revert-preview` | Inspect journal entries; verify the authoritative hash chain, live-tip anchor, committed anchor prefix, and JSONL export subset; `revert-preview <event-id>` renders the read-only cascade-rollback preview for one event. |
```

- [ ] **Step 3: Verify the gates pass**

Run (from the worktree root):

```bash
python3 scripts/checks/doc_claims_gate.py
python3 scripts/checks/checked_terminology_gate.py
pre-commit run --hook-stage manual --files docs/reference/commands-and-transports/cli.md
```

Expected: `doc-claims-gate: clean` (the existing docs→code direction validates every path you added actually exists — a typo in a command name fails here), terminology gate silent exit 0, pre-commit hooks pass.

- [ ] **Step 4: Commit**

```bash
git add docs/reference/commands-and-transports/cli.md
git commit -m "docs: cli.md roster gains the five commands the argparse tree ships (onboard, context, cockpit, seed install, journal revert-preview)"
```

---

### Task 2: system-actions rosters — two missing operation ids, one missing description (MEDIUM)

**Files:**
- Modify: `docs/reference/commands-and-transports/system-actions.md`
- Modify: `docs/reference/commands-and-transports/system-actions-operations.md`

**Interfaces:**
- Produces: an "## Operation manifest roster" section in system-actions.md whose backticked ids in bullet lines exactly match the shipped manifest set (60 ids). Task 3's gate parses backticked ids from lines starting `- ` under that heading — keep the bullet-line format.

The package ships 60 manifests in `src/memoria_vault/product/capabilities/operations/`; the roster lists 58. Missing: `apply-decision-rule-notices` and `seed-install`. (This is the manifest roster on system-actions.md — distinct from control-plane.md's Actor Authority Guard table, which already lists both and has its own gate.)

- [ ] **Step 1: Add the two ids at their alphabetical slots in system-actions.md**

Line 24 currently ends its first span at `` `answer-query`, `capture-bibtex-source` ``. Insert `` `apply-decision-rule-notices` `` between them:

```markdown
- `acknowledge-attention`, `analyze-claims`, `analyze-gaps`, `analyze-project-argument`, `answer-query`, `apply-decision-rule-notices`, `capture-bibtex-source`, `capture-pdf-source`, `capture-remote-pdf-source`, `capture-source`
```

Line 29 contains `` `run-seeded-error-verdict`, `summarize-for-recall` ``. Insert `` `seed-install` `` between them:

```markdown
- `regenerate-references-bib`, `regenerate-tracked-projections`, `render-project-argument-canvas`, `resolve-attention`, `resolve-evidence`, `run-seeded-error-verdict`, `seed-install`, `summarize-for-recall`, `surface-tensions`, `trace-integrity-scan`
```

- [ ] **Step 2: Describe `seed-install` in the catalog cluster**

`apply-decision-rule-notices` already has a row in system-actions-operations.md (L116); `seed-install` is described nowhere in the cluster. In system-actions-operations.md's "Capture pipeline" table, insert after the "Capture remote PDF source" row (L96), before "Regenerate bibliography" (L97):

```markdown
| Seed corpus install | PI-only worker operation `seed-install` + the local PDF capture seam | Iterates the shipped seed-corpus manifest, skips rows already present in the catalog, downloads each remaining row keyless over https under the manifest's finite network allowlist, and stages the bytes as unchecked catalog Work rows. Onboarding is a PI action; agent surfaces cannot trigger these fetches. |
```

(Wording sourced from the manifest `src/memoria_vault/product/capabilities/operations/seed-install.md` — verify against it before committing.)

- [ ] **Step 3: Verify and commit**

```bash
python3 scripts/checks/doc_claims_gate.py
python3 scripts/checks/checked_terminology_gate.py
pre-commit run --hook-stage manual --files docs/reference/commands-and-transports/system-actions.md docs/reference/commands-and-transports/system-actions-operations.md
git add docs/reference/commands-and-transports/system-actions.md docs/reference/commands-and-transports/system-actions-operations.md
git commit -m "docs: operation-manifest roster gains apply-decision-rule-notices and seed-install; seed-install described in the capture-pipeline catalog"
```

---

### Task 3: reverse completeness gate + truthful Source labels (MEDIUM, root cause)

**Files:**
- Modify: `scripts/checks/doc_claims_gate.py`
- Test: `tests/test_doc_claims_gate.py`
- Modify: `docs/reference/README.md`
- Modify: `docs/reference/commands-and-transports/system-actions.md:16-18`
- Modify: `docs/reference/commands-and-transports/cli.md:89`

**Interfaces:**
- Consumes: Task 1's roster section (`## Complete command roster`, `` - `memoria <path>` `` bullets) and Task 2's roster section (`## Operation manifest roster`, backticked ids on `- ` lines).
- Produces: `roster_drift_errors(root) -> list[str]` in `doc_claims_gate.py`; `main()` fails on either direction. `scripts/verify` already runs this gate (GATES line 61) — no verify change needed.

Why a checker (the bar AGENTS.md sets): three rosters drifted the same undetected direction (cli.md −5, system-actions.md −2, read-api.md −8) because `doc_claims_gate.py` validates docs→code only, while `reference/README.md` labels two of those pages "Guarded mirror". This task makes the label true for the two pages with mechanically enumerable rosters.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_doc_claims_gate.py` (existing conventions: `pytestmark = pytest.mark.static`, fixture repo under `tmp_path` via `_init_fixture_repo`, exact error-string assertions). The existing `_MINIMAL_CLI` fixture registers `project gaps` and `project trace` with no handler on bare `project`:

```python
_CLI_DOC = """## Complete command roster

This roster mirrors the live argparse tree:

- `memoria project gaps`
- `memoria project trace`

## Next section
"""

_OPERATIONS_DOC = """## Operation manifest roster

Package-owned operation manifests currently ship these operation IDs:

- `capture-source`

## Detailed action catalogs
"""


def _write_roster_docs(root: Path, cli_doc: str = _CLI_DOC, operations_doc: str = _OPERATIONS_DOC) -> None:
    docs_dir = root / "docs/reference/commands-and-transports"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "cli.md").write_text(cli_doc, encoding="utf-8")
    (docs_dir / "system-actions.md").write_text(operations_doc, encoding="utf-8")


def test_matching_rosters_are_clean(tmp_path: Path) -> None:
    _init_fixture_repo(tmp_path)
    _write_roster_docs(tmp_path)

    assert gate.roster_drift_errors(tmp_path) == []


def test_missing_roster_entries_fail_in_both_surfaces(tmp_path: Path) -> None:
    _init_fixture_repo(tmp_path)
    _write_roster_docs(
        tmp_path,
        cli_doc=_CLI_DOC.replace("- `memoria project trace`\n", ""),
        operations_doc=_OPERATIONS_DOC.replace("- `capture-source`", "- `capture-other`"),
    )

    assert gate.roster_drift_errors(tmp_path) == [
        "docs/reference/commands-and-transports/cli.md: roster is missing `memoria project trace`",
        "docs/reference/commands-and-transports/system-actions.md: roster is missing `capture-source`",
        "docs/reference/commands-and-transports/system-actions.md: roster lists `capture-other`, which no shipped manifest declares",
    ]


def test_stale_cli_roster_entry_fails(tmp_path: Path) -> None:
    _init_fixture_repo(tmp_path)
    _write_roster_docs(
        tmp_path,
        cli_doc=_CLI_DOC.replace(
            "- `memoria project trace`", "- `memoria project trace`\n- `memoria project frobnicate`"
        ),
    )

    assert gate.roster_drift_errors(tmp_path) == [
        "docs/reference/commands-and-transports/cli.md: roster lists `memoria project frobnicate`, "
        "which the argparse tree does not run",
    ]
```

Note the group-parser rule the first test pins implicitly: bare `project` (subparsers, no handler default) is not demanded from the roster.

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `python -m pytest tests/test_doc_claims_gate.py -q`
Expected: FAIL — `AttributeError: module ... has no attribute 'roster_drift_errors'`.

- [ ] **Step 3: Implement `roster_drift_errors`**

In `scripts/checks/doc_claims_gate.py`, add after the existing pattern constants (L32):

```python
CLI_DOC_REL = "docs/reference/commands-and-transports/cli.md"
CLI_ROSTER_HEADING = "## Complete command roster"
OPERATIONS_DOC_REL = "docs/reference/commands-and-transports/system-actions.md"
OPERATIONS_ROSTER_HEADING = "## Operation manifest roster"
CLI_ROSTER_ENTRY = re.compile(r"^- `memoria ((?:[a-z][a-z0-9_-]*)(?: [a-z][a-z0-9_-]*){0,3})`$", re.MULTILINE)
```

Add after `_load_operation_ids` (L89):

```python
def _roster_section(text: str, heading: str) -> str:
    start = text.index(heading)
    end = text.find("\n## ", start + len(heading))
    return text[start : end if end != -1 else len(text)]


def _runnable_cli_paths(root: Path) -> frozenset[str]:
    """Every path the parser will run: a handler is set, or it is a leaf.

    Group parsers (`memoria journal`, bare `memoria seed`) exist only to hold
    subcommands — required subparsers, no handler — and are not roster entries.
    """
    with _importable(root / "src"):
        from memoria_vault.cli import _build_parser

    def walk(parser: argparse.ArgumentParser, prefix: tuple[str, ...] = ()) -> set[tuple[str, ...]]:
        subparser_actions = [
            action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
        ]
        paths: set[tuple[str, ...]] = set()
        if prefix and (parser.get_default("handler") is not None or not subparser_actions):
            paths.add(prefix)
        for action in subparser_actions:
            for name, sub in action.choices.items():
                paths |= walk(sub, (*prefix, name))
        return paths

    return frozenset(" ".join(path) for path in walk(_build_parser()))


def roster_drift_errors(root: Path = ROOT) -> list[str]:
    """The reverse direction: the two roster pages must list the whole shipped surface."""
    root = Path(root).resolve()
    errors: list[str] = []

    cli_text = (root / CLI_DOC_REL).read_text(encoding="utf-8")
    documented = frozenset(
        match.group(1) for match in CLI_ROSTER_ENTRY.finditer(_roster_section(cli_text, CLI_ROSTER_HEADING))
    )
    runnable = _runnable_cli_paths(root)
    for missing in sorted(runnable - documented):
        errors.append(f"{CLI_DOC_REL}: roster is missing `memoria {missing}`")
    for stale in sorted(documented - runnable):
        errors.append(f"{CLI_DOC_REL}: roster lists `memoria {stale}`, which the argparse tree does not run")

    operations_text = (root / OPERATIONS_DOC_REL).read_text(encoding="utf-8")
    documented_ids: set[str] = set()
    for line in _roster_section(operations_text, OPERATIONS_ROSTER_HEADING).splitlines():
        if line.startswith("- "):
            documented_ids.update(re.findall(r"`([a-z][a-z0-9-]*)`", line))
    shipped_ids = _load_operation_ids(root)
    for missing in sorted(shipped_ids - documented_ids):
        errors.append(f"{OPERATIONS_DOC_REL}: roster is missing `{missing}`")
    for stale in sorted(documented_ids - shipped_ids):
        errors.append(f"{OPERATIONS_DOC_REL}: roster lists `{stale}`, which no shipped manifest declares")
    return errors
```

Wire into `main()` — replace the body between `args = parser.parse_args(argv)` and the final `return 0` (L127-137):

```python
    violations = find_violations(args.root)
    drift = roster_drift_errors(args.root)
    if violations or drift:
        print("doc-claims-gate: FAIL", file=sys.stderr)
        for v in violations:
            print(
                f"  {v.file}:{v.line}: {v.kind} '{v.claim}' not found in the shipped surface",
                file=sys.stderr,
            )
        for error in drift:
            print(f"  {error}", file=sys.stderr)
        return 1
    print("doc-claims-gate: clean")
    return 0
```

Extend the module docstring (L2-11): after the two-bullet list, add one line: `In the reverse direction, the two roster pages (cli.md, system-actions.md) must list the entire shipped surface — a command or manifest the docs omit fails the same gate.`

- [ ] **Step 4: Run the tests and the real gate**

```bash
python -m pytest tests/test_doc_claims_gate.py -q
python3 scripts/checks/doc_claims_gate.py
```

Expected: all tests pass; the real gate prints `doc-claims-gate: clean` against the Task-1/Task-2 rosters. If the real run reports a missing path you did not expect (a group parser that does set a handler), the code is the truth — add that path to cli.md's roster; never loosen `_runnable_cli_paths` to hide it.

- [ ] **Step 5: Make the three prose claims and Source labels truthful**

`docs/reference/commands-and-transports/system-actions.md` L16-18 — replace:

```markdown
This page mirrors the source, not the reverse. Action implementation lives in
the referenced Python modules, capability manifests, and linked reference pages;
keep the operation manifest roster in sync by hand.
```

with:

```markdown
This page mirrors the source, not the reverse. Action implementation lives in
the referenced Python modules, capability manifests, and linked reference pages.
The operation manifest roster below is pinned to the shipped manifests by
`scripts/checks/doc_claims_gate.py` in both directions.
```

`docs/reference/commands-and-transports/cli.md` L89 — replace `This roster mirrors the live argparse tree:` with:

```markdown
This roster mirrors the live argparse tree; `scripts/checks/doc_claims_gate.py`
pins the two equal in both directions:
```

`docs/reference/README.md` — three edits:

1. After L17 (`...name the owning source rather than mirroring every field and count.`), add a blank line and:

```markdown
The Source column: **Source-owned** pages quote schema-owned or generated
material; **Guarded mirror** pages are pinned to the shipped surface by a drift
gate in `scripts/verify`; **Manual** pages are maintained by hand.
```

2. L50 — change the control-plane row's Source cell from `Manual` to `Guarded mirror` (its gate is `scripts/checks/control_plane_actor_gate.py`):

```markdown
| [Control plane reference](control-and-policy/control-plane.md) | Request-control commands and state | Guarded mirror |
```

3. Two LOW fixes in the same file: the glossary row (L27) — replace `Term definitions, alphabetical` with `Term definitions, organized by domain`; and the "Analysis, diagnostics, and surfaces" table (L62-66) is missing its only page — append after the dashboards row (L66):

```markdown
| [Evidence-set review](analysis-and-surfaces/evidence-review.md) | Evidence-set hold queue, the four dispositions, and review telemetry | Manual |
```

- [ ] **Step 6: Verify and commit**

```bash
python -m pytest tests/test_doc_claims_gate.py tests/test_verify_script.py -q
python3 scripts/checks/doc_claims_gate.py
python3 scripts/checks/checked_terminology_gate.py
pre-commit run --hook-stage manual --files scripts/checks/doc_claims_gate.py tests/test_doc_claims_gate.py docs/reference/README.md docs/reference/commands-and-transports/system-actions.md docs/reference/commands-and-transports/cli.md
git add scripts/checks/doc_claims_gate.py tests/test_doc_claims_gate.py docs/reference/README.md docs/reference/commands-and-transports/system-actions.md docs/reference/commands-and-transports/cli.md
git commit -m "gate: doc_claims_gate checks the reverse direction — the two roster pages must list the whole shipped surface; Source labels made truthful"
```

---

### Task 4: wikilink-and-link-conventions.md — six relations, not three (HIGH)

**Files:**
- Modify: `docs/reference/data-model/wikilink-and-link-conventions.md:30-48`

The page says "The only frontmatter link relations are:" and lists three. `LINK_RELATIONS` in `src/memoria_vault/runtime/vocabulary/edges.py` (L39-42) defines six (everything but `tension`), and `frontmatter.md` L161-174 — the authority this very section cites — documents all six plus the `tension` caveat.

- [ ] **Step 1: Replace the relation table, YAML example, and lead-in**

Replace L32-48 (from `Knowledge Concepts carry ...` through the closing ` ``` ` of the YAML example) with:

````markdown
Knowledge Concepts carry `links:` as the authored relationship map specified by
the generated [Frontmatter fields](frontmatter.md). The six frontmatter-legal
link relations are:

| Link | Direction |
| --- | --- |
| `supports` | This Concept supports the linked Concept. |
| `contradicts` | This Concept contradicts the linked Concept. |
| `extends` | This Concept builds on the linked Concept. |
| `warrant` | This Concept licenses the inference the linked Concept makes (Toulmin role). |
| `qualifier` | This Concept bounds the linked Concept's scope or strength (Toulmin role). |
| `rebuttal` | This Concept names the condition under which the linked Concept fails (Toulmin role). |

`tension` is a seventh edge relation the machine surfaces and the PI confirms;
it is never authored in `links:`
([Frontmatter fields](frontmatter.md#links-and-catalog-resources)).

```yaml
links:
  supports:
    - notes/target.md
  contradicts: []
  extends: []
  warrant: []
  qualifier: []
  rebuttal: []
```
````

- [ ] **Step 2: Verify and commit**

```bash
python3 scripts/checks/schema_doc_drift.py
python3 scripts/checks/checked_terminology_gate.py
pre-commit run --hook-stage manual --files docs/reference/data-model/wikilink-and-link-conventions.md
git add docs/reference/data-model/wikilink-and-link-conventions.md
git commit -m "docs: link-conventions table carries all six frontmatter-legal relations plus the tension caveat, matching edges.py and frontmatter.md"
```

---

### Task 5: read-api.md — the eight undocumented functions (MEDIUM)

**Files:**
- Modify: `docs/reference/commands-and-transports/read-api.md`

`src/memoria_vault/engine/api.py` has 29 public functions; the two tables cover 21. Contract prose below is drawn from each function's docstring (signatures at api.py L238, L303, L337, L363, L478, L630, L663, L717); table style matches the existing hand-written rows (no `*` marker, defaults shown).

- [ ] **Step 1: Add seven rows to "Core reads and writes"**

After the `read_attention(...) / read_attention_card(...)` row (L24), insert:

```markdown
| `read_attention_view(workspace, summary=False, read_scope=None)` | Reads the attention pane's payload: open cards, or the cheap poll counts with `summary=True`. |
| `read_evidence_review_view(workspace, routing_type="", project="", min_age_days=0, batch=10, read_scope=None)` | Reads the evidence-set hold queue projected into one nested view-spec card per row. |
```

After the `read_journal(...)` row (L28), insert:

```markdown
| `read_dashboard(workspace)` | Reads the `dashboard.read` payload: the seven instrumentation panels, whole, in the envelope. |
| `read_dashboard_view(workspace)` | Reads the `views.dashboard` payload: one text block per raw-count panel. |
| `read_context(workspace, read_scope=None)` | Reads the situated-context bundle for the active session. |
| `read_cockpit(workspace, project_path="", triage=False, read_scope=None)` | Composes the deep-work or triage cockpit screens from registry reads. |
| `read_revert_preview(workspace, event_id, read_scope=None)` | Reads the read-only cascade-rollback preview for one journal event. |
```

- [ ] **Step 2: Add `read_canvas_forks` to "Project WRITE views"**

After the `read_draft(workspace, project_path)` row (L38), insert:

```markdown
| `read_canvas_forks(workspace, project_path, read_scope=None)` | Reads the fork status of a project's `argument.canvas`. |
```

Do not add a completeness claim to this page — an unenforced completeness sentence is the exact drift pattern Task 3 exists to prevent, and this page has no gate.

- [ ] **Step 3: Verify and commit**

```bash
python3 scripts/checks/doc_claims_gate.py
pre-commit run --hook-stage manual --files docs/reference/commands-and-transports/read-api.md
git add docs/reference/commands-and-transports/read-api.md
git commit -m "docs: read-api.md documents the eight missing public engine functions"
```

---

### Task 6: glossary `certainty` disambiguation + failure-modes sort (MEDIUM ×2)

**Files:**
- Modify: `docs/reference/data-model/glossary.md:212`
- Modify: `docs/reference/system/failure-modes.md:38-55`

- [ ] **Step 1: Disambiguate `certainty` in the glossary's Verdicts table**

Two live senses share the name: the attention-projection confidence (glossary L212) and the note-frontmatter epistemic enum (`src/memoria_vault/product/workspace_seed/.memoria/schemas/types/note.yaml` L7: `certainty: [reported, contested, unknown, hypothesized]`). House disambiguation style is inline "Distinct from ..." (see the Runner/worker/engine ruling, glossary L116-121). Replace the row:

```markdown
| `certainty` | `confident` / `likely` / `unsure` | proposing agent | calibrated confidence on an attention projection |
```

with:

```markdown
| `certainty` | `confident` / `likely` / `unsure` | proposing agent | calibrated confidence on an attention projection. Distinct from the note-frontmatter `certainty` enum (`reported` / `contested` / `unknown` / `hypothesized`), the PI-set epistemic status of a claim — see [Frontmatter fields](frontmatter.md). |
```

- [ ] **Step 2: Re-sort the failure-modes table to match its own claim**

L10 and L34 both promise severity ordering; three rows sit out of band (LOW at L43 above the MEDIUM block; HIGH at L51 and L53 below it). Reorder the 18 data rows (L38-55) so the Severity column reads CRITICAL ×2, HIGH ×5, MEDIUM ×8, LOW ×3, keeping each row's text untouched and preserving current relative order within each band. Final order by row symptom:

1. **Obsidian Linter corrupts frontmatter** (CRITICAL)
2. **Memoria-owned frontmatter overwritten** (CRITICAL)
3. DOI source stays unchecked after enrichment (HIGH)
4. Optional editor field filter returns nothing (HIGH)
5. Search index stale — `memoria ask` misses checked notes (HIGH)
6. Backup target is absent after interruption (HIGH — moved up from L51)
7. Restore reports that rollback also failed (HIGH — moved up from L53)
8. Broken frontmatter YAML (MEDIUM)
9. Optional editor adapter can't connect (MEDIUM)
10. Schema mismatch in filtered views (MEDIUM)
11. Scheduled task did not run (MEDIUM)
12. Same request fails after explicit retry (MEDIUM)
13. Request not progressing (MEDIUM)
14. `memoria doctor` reports unbacked blobs (MEDIUM)
15. Restore refuses an older journal head (MEDIUM — moved down from L52)
16. `audit.jsonl` growing without bound (LOW — moved down from L43)
17. Citekey alias not found at ingest (LOW)
18. Pandoc + BBT DOCX corrupt (LOW)

- [ ] **Step 3: Verify and commit**

```bash
python3 scripts/checks/checked_terminology_gate.py
pre-commit run --hook-stage manual --files docs/reference/data-model/glossary.md docs/reference/system/failure-modes.md
git add docs/reference/data-model/glossary.md docs/reference/system/failure-modes.md
git commit -m "docs: glossary disambiguates the two certainty senses; failure-modes table sorted the way it says it is"
```

---

### Task 7: tutorial fixes — offline break, macOS stray, recap overclaim, wrong credit (MEDIUM + LOW ×3)

**Files:**
- Modify: `docs/tutorials/01-system-tour.md:18,93`
- Modify: `docs/tutorials/02-first-source.md:75-90`
- Modify: `docs/tutorials/07-customize.md:26,126`

- [ ] **Step 1: 01-system-tour — two one-line fixes**

L18: replace `` `source .memoria/.venv/bin/activate` (Linux/macOS/WSL) or `` with `` `source .memoria/.venv/bin/activate` (Linux/WSL) or `` (macOS is not supported — Quickstart, set-up-the-vault, and the roadmap all say so; this parenthetical is the sole page implying otherwise).

L93: delete the recap bullet `- The workspace is local and git-backed.` — no step in this chapter demonstrates git (Tutorial 07 runs `git status --short` where the claim is actually shown; a tutorial recap asserts only what was seen).

- [ ] **Step 2: 02-first-source — restore the offline path in step 5, disambiguate step 6**

Replace L75-79 (the step-5 heading and framing paragraph):

```markdown
**5. Capture a paper's companion repository.**

One corpus paper (OpenScholar) ships with its open-source companion repo.
A paper's repo is often the method's only complete specification —
capturing both is the habit worth building:
```

with:

```markdown
**5. Capture a companion repository (needs network).**

A paper's repo is often the method's only complete specification —
capturing both is the habit worth building. The seed corpus's OpenScholar
paper ships with one. Skip this step if you are working offline:
```

(The command block L81-85 is unchanged — it is self-contained and does not depend on step 1's corpus.)

Replace L87 (`**6. Compile a digest when a source is ready.**`) with:

```markdown
**6. Compile a digest when a source is ready.**

Use the `work_id` you checked in step 4:
```

(Step 5 added a second Work; the bare `<work-id>` placeholder must name which one.)

- [ ] **Step 3: 07-customize — correct the chapter credit, hand off specifically**

L26: replace `already trace to the tutorial project from Tutorial 04.` with `already trace to the tutorial project from Tutorial 01.` (the project is framed in 01-system-tour step 4; 02-first-source L30 also calls it "the framing step in Tutorial 01").

L126: replace `For optional setup, continue with [How-to guides](../how-to-guides/README.md).` with:

```markdown
Two how-to guides continue the loop you just closed:
[Return to work](../how-to-guides/inbox/return-to-work.md) picks up the
workspace after time away, and
[Run the weekly review](../how-to-guides/inbox/run-the-weekly-review.md) keeps
the queues this arc created moving. For everything else, the
[How-to guides](../how-to-guides/README.md) index routes by task.
```

- [ ] **Step 4: Verify and commit**

```bash
python3 scripts/checks/doc_claims_gate.py
pre-commit run --hook-stage manual --files docs/tutorials/01-system-tour.md docs/tutorials/02-first-source.md docs/tutorials/07-customize.md
git add docs/tutorials/01-system-tour.md docs/tutorials/02-first-source.md docs/tutorials/07-customize.md
git commit -m "docs: tutorial 02 keeps its offline promise; 01 drops the macOS stray and undemonstrated recap bullet; 07 credits the right chapter and hands off specifically"
```

---

### Task 8: how-to fixes — batch `--enrich`, index overpromise (MEDIUM + LOW)

**Files:**
- Modify: `docs/how-to-guides/library/capture-and-ingest.md`
- Modify: `docs/how-to-guides/library/run-a-systematic-review.md:39-44`
- Modify: `docs/how-to-guides/README.md:41`

- [ ] **Step 1: Verify the `--enrich` behavior in the code first**

The flag is defined at `src/memoria_vault/cli.py:329` (`import_cmd.add_argument("--enrich", action="store_true")`) and consumed near `cli.py:1668` (`if args.enrich and (enrichment := _queue_import_enrichment(...))` per admitted item). But system-actions-operations.md L91 says the BibTeX capture path queues a DOI enrichment request on its own ("and a DOI enrichment request when a DOI is present") while L92 documents `--enrich` only for CSL. Read `_cmd_work_import`, `_queue_import_enrichment`, and the bibtex/csl payload helpers and settle which of these is true:

- If `--enrich` queues enrichment for **both** formats, use: "Add `--enrich` to queue a DOI enrichment request for each newly admitted item that carries a DOI."
- If the BibTeX path **always** queues enrichment and `--enrich` matters only for CSL, use: "BibTeX imports queue a DOI enrichment request automatically for each entry with a DOI; for CSL imports add `--enrich` to get the same behavior."

Trust order: code over docs. If system-actions-operations.md L91/L92 turn out wrong, correct those cells in the same commit.

- [ ] **Step 2: Document the batch path in both guides**

In `capture-and-ingest.md`, after step 2's code block (L35), add the sentence chosen in Step 1, then:

```markdown
Reserve the per-Work enrichment in step 4 for rows import could not enrich —
no DOI, or a queued run that failed.
```

In `run-a-systematic-review.md`, append to step 3's paragraph (L41-44) the same chosen sentence adapted to context, ending with: `The capture guide's per-Work enrichment then covers only the leftovers.` (This guide exists specifically for the batch case; it must not route readers one-Work-at-a-time when a batch flag exists.)

- [ ] **Step 3: Stop advertising undelivered capabilities in the how-to index**

`docs/how-to-guides/README.md` L41 — replace:

```markdown
| [Knowledge](knowledge/) | Writing, linking, promoting, refactoring, querying, and pattern-running over knowledge notes |
```

with:

```markdown
| [Knowledge](knowledge/) | Writing, linking, promoting, and querying knowledge notes |
```

Then `grep -rn "pattern-running\|refactoring" docs/how-to-guides/` — if any other index or guide advertises either capability, apply the same removal (none of the five Knowledge guides covers them; prompt operations remain documented in reference).

- [ ] **Step 4: Add the knowledge-cycle crosslink to capture-and-ingest**

In `capture-and-ingest.md`'s `## Related` (L63-66), append:

```markdown
- Where captured sources go in the cycle: [The knowledge cycle](../../explanation/knowledge/knowledge-cycle.md)
```

- [ ] **Step 5: Verify and commit**

```bash
python3 scripts/checks/doc_claims_gate.py
pre-commit run --hook-stage manual --files docs/how-to-guides/library/capture-and-ingest.md docs/how-to-guides/library/run-a-systematic-review.md docs/how-to-guides/README.md
git add docs/how-to-guides/library/capture-and-ingest.md docs/how-to-guides/library/run-a-systematic-review.md docs/how-to-guides/README.md
git commit -m "docs: batch imports document --enrich; how-to index stops advertising pattern-running and refactoring no guide delivers"
```

---

### Task 9: explanation lows — voice drift, milestone link (LOW ×2)

**Files:**
- Modify: `docs/explanation/knowledge/common-pitfalls.md`
- Modify: `docs/explanation/rationale/deployment/distribution-model.md:36`

- [ ] **Step 1: Rewrite the five imperative "What prevents it" slots into the discussing voice**

The audit's only genuine quadrant drift: five of seven pitfalls answer in the imperative. Replace each (keeping links intact):

L41-42, from `**What prevents it:** pin citekeys in Better BibTeX so the key is treated as an identifier, not a metadata derivation. See [Set up Zotero](../../how-to-guides/setup/set-up-zotero.md).` to:

```markdown
**What prevents it:** pinned citekeys in Better BibTeX — the key treated as an
identifier, not a metadata derivation. [Set up Zotero](../../how-to-guides/setup/set-up-zotero.md)
covers the setting.
```

L53-55, from `**What prevents it:** maintain the controlled vocabulary and consolidate variants once the intended term is clear. The staged stabilization model is in [Vocabulary discipline](vocabulary-discipline.md).` to:

```markdown
**What prevents it:** a maintained controlled vocabulary that absorbs variants
once the intended term is clear. The staged stabilization model is in
[Vocabulary discipline](vocabulary-discipline.md).
```

L66-67, from `**What prevents it:** make every durable note earn its place through links, tensions, or a claim about current work.` to:

```markdown
**What prevents it:** a norm that every durable note earns its place through
links, tensions, or a claim about current work.
```

L78-81, from `**What prevents it:** confirm the source is checked before distilling, then set any `research_area` or `methodology` classification deliberately with `memoria work update`. Those classifications are PI-owned metadata, not an automated attention lifecycle.` to:

```markdown
**What prevents it:** distilling only from checked sources, with `research_area`
and `methodology` set deliberately through `memoria work update` — PI-owned
metadata, not an automated attention lifecycle.
```

L102-103, from `**What prevents it:** prune hard, annotate what remains, or create child hubs when a curated list grows past roughly 20-30 entries.` to:

```markdown
**What prevents it:** hard pruning, annotation of what remains, and child hubs
once a curated list grows past roughly 20-30 entries.
```

(The remaining two slots — L21-23 and L91-92 — are already declarative; leave them.)

- [ ] **Step 2: Link the alpha.20 milestone reference**

First confirm the target exists: `ls design-history/ | grep alpha.20` (expect `20-alpha.20.md`; if the filename differs, use the real one). Then in `distribution-model.md` L36, replace `The old `vault-template/` tree was removed in alpha.20.` with:

```markdown
The old `vault-template/` tree was removed in
[alpha.20](https://github.com/eranroseman/memoria-vault/blob/main/design-history/20-alpha.20.md).
```

(Blob URL per the link convention — `design-history/` is unpublished. This matches the cluster's house style, e.g. why-write-half-is-bounded.md L80.)

- [ ] **Step 3: Verify and commit**

```bash
python3 scripts/checks/checked_terminology_gate.py
pre-commit run --hook-stage manual --files docs/explanation/knowledge/common-pitfalls.md docs/explanation/rationale/deployment/distribution-model.md
git add docs/explanation/knowledge/common-pitfalls.md docs/explanation/rationale/deployment/distribution-model.md
git commit -m "docs: common-pitfalls discusses instead of instructs; alpha.20 milestone reference gets its design-history link"
```

---

### Task 10: reciprocal cross-quadrant links + duplicate-URL anchors (audit's highest-leverage link set)

**Files:**
- Modify: `docs/reference/data-model/frontmatter.md:210-216`
- Modify: `docs/reference/data-model/document-types.md:41-47`
- Modify: `docs/reference/control-and-policy/control-plane.md:88-93`
- Modify: `docs/reference/analysis-and-surfaces/linter.md:111-116`
- Modify: `docs/reference/analysis-and-surfaces/evidence-review.md:69-74`
- Modify: `docs/reference/pipelines-and-io/ingest.md:105-111`
- Modify: `docs/explanation/architecture/vault.md:95-99`
- Modify: `docs/explanation/execution/operation-postures/co-pi.md:51-54`
- Modify: `docs/explanation/execution/operation-postures/librarian.md:49-54`
- Modify: `docs/explanation/execution/operation-postures/writer.md:36-41`
- Modify: `docs/explanation/execution/operation-postures/peer-reviewer.md:37-42`

The most-trafficked reference pages carry zero cross-quadrant outbound links, and the five posture pages link only to each other. Every addition below appends to the file's existing `## Related` list in its existing style (plain `- lead phrase: [Link](path)` bullets). All link paths follow the Pages-route convention; the `../../..` depth on posture pages reflects their three-level nesting.

- [ ] **Step 1: Reference pages — add the return path**

`frontmatter.md` (Related at L210-216), append:

```markdown
- Why the type roster looks like this: [Document types (explanation)](../../explanation/knowledge/document-types.md)
- When validation fails on a note: [Fix broken frontmatter](../../how-to-guides/troubleshooting/fix-broken-frontmatter.md)
```

`document-types.md` (Related at L41-47), append:

```markdown
- The epistemic reasoning behind the roster: [Document types (explanation)](../../explanation/knowledge/document-types.md)
```

`control-plane.md` (Related at L88-93), append:

```markdown
- Working the queue day to day: [Work the action queue](../../how-to-guides/inbox/work-the-action-queue.md)
- When a request sticks: [Fix a stuck request](../../how-to-guides/troubleshooting/fix-stuck-card.md)
- Why the states are shaped this way: [Control-plane states](../../explanation/execution/control-plane/states.md)
```

`linter.md` (Related at L111-116), append:

```markdown
- Running it: [Run the linter](../../how-to-guides/operate/run-the-linter.md)
```

`evidence-review.md` (Related at L69-74), append:

```markdown
- The per-finding disposition flow: [Compose a draft](../../how-to-guides/project/compose-a-draft.md)
- The tutorial that teaches the queue's other front: [05: Verify evidence](../../tutorials/05-verify-evidence.md)
```

`ingest.md` (Related at L105-111), append:

```markdown
- The per-source how-to: [Capture and ingest a source](../../how-to-guides/library/capture-and-ingest.md)
```

- [ ] **Step 2: vault.md and the four posture pages — add the "now do it" link**

`vault.md` (Related at L95-99), append:

```markdown
- Working the write path day to day: [Work the action queue](../../how-to-guides/inbox/work-the-action-queue.md)
```

`co-pi.md` (Related at L51-54): fix the duplicate-URL bullet AND add the practice link. Replace L54:

```markdown
- Why one conversational front: [Why operation postures](../../rationale/boundaries/why-operation-postures.md)
```

with:

```markdown
- Why one conversational front: [Why one Co-PI fronts everything](../../rationale/boundaries/why-operation-postures.md#why-one-co-pi-fronts-everything)
- Practicing this posture: [Query the vault](../../../how-to-guides/knowledge/query-the-vault.md)
```

`librarian.md` (Related at L49-54): same duplicate-URL pattern. Replace L54:

```markdown
- Why intake is separated from verification: [Why operation postures](../../rationale/boundaries/why-operation-postures.md)
```

with:

```markdown
- Why intake is separated from verification: [The independence argument](../../rationale/boundaries/why-operation-postures.md#the-independence-argument)
- Practicing intake: [Capture and ingest a source](../../../how-to-guides/library/capture-and-ingest.md)
```

`writer.md` (Related at L36-41), append:

```markdown
- Practicing the draft loop: [Compose a draft](../../../how-to-guides/project/compose-a-draft.md)
```

`peer-reviewer.md` (Related at L37-42), append:

```markdown
- Practicing verification: [Analyze a project argument](../../../how-to-guides/project/analyze-a-project-argument.md)
```

(engineer.md gets no practice link — no how-to exists for the Engineer posture; the audit records that as an accepted LOW coverage gap, and a dead link would be worse.)

Anchor sanity: the two new anchors are kramdown auto-IDs of `## Why one Co-PI fronts everything` (L60) and `## The independence argument` (L77) in why-operation-postures.md. Verify with `grep -n "^## " docs/explanation/rationale/boundaries/why-operation-postures.md` before committing.

- [ ] **Step 3: Verify and commit**

```bash
python3 scripts/checks/checked_terminology_gate.py
pre-commit run --hook-stage manual --files docs/reference/data-model/frontmatter.md docs/reference/data-model/document-types.md docs/reference/control-and-policy/control-plane.md docs/reference/analysis-and-surfaces/linter.md docs/reference/analysis-and-surfaces/evidence-review.md docs/reference/pipelines-and-io/ingest.md docs/explanation/architecture/vault.md docs/explanation/execution/operation-postures/co-pi.md docs/explanation/execution/operation-postures/librarian.md docs/explanation/execution/operation-postures/writer.md docs/explanation/execution/operation-postures/peer-reviewer.md
git add docs/reference/data-model/frontmatter.md docs/reference/data-model/document-types.md docs/reference/control-and-policy/control-plane.md docs/reference/analysis-and-surfaces/linter.md docs/reference/analysis-and-surfaces/evidence-review.md docs/reference/pipelines-and-io/ingest.md docs/explanation/architecture/vault.md docs/explanation/execution/operation-postures/co-pi.md docs/explanation/execution/operation-postures/librarian.md docs/explanation/execution/operation-postures/writer.md docs/explanation/execution/operation-postures/peer-reviewer.md
git commit -m "docs: reciprocal cross-quadrant links for the highest-traffic reference pages; posture pages link their practice; duplicate Related URLs get their intended anchors"
```

---

### Task 11: full gate, PR, merge, cleanup

**Files:** none new (commits the plan document).

- [ ] **Step 1: Commit this plan**

Copy `docs/superpowers/plans/2026-08-03-diataxis-audit-fixes.md` from the main checkout into the worktree if not already present, then:

```bash
git add docs/superpowers/plans/2026-08-03-diataxis-audit-fixes.md
git commit -m "docs: track the Diátaxis-audit repair plan"
```

- [ ] **Step 2: Run the full gate**

Run `python scripts/verify` in the worktree (foreground or background with explicit exit capture — the log is the truth, never a piped exit code). Expected: `verify: OK`. If main has drifted, merge `origin/main` first and re-run; if the new roster gate fails after a merge, the roster pages and the shipped surface diverged in the merge — reconcile per trust order (code wins) before proceeding.

- [ ] **Step 3: Push and open the PR**

```bash
git push -u origin wip/docaudit
gh pr create --title "docs: Diátaxis-audit repairs — roster completeness gate, six-relation link table, reference accuracy, reciprocal links" --body "Lands every confirmed finding of the 2026-08-03 Diátaxis audit (169 published pages, 150 clean). HIGH: cli.md's roster gains the five commands the argparse tree ships; the link-conventions table carries all six frontmatter-legal relations (edges.py is the authority). Root cause: doc_claims_gate.py now checks the reverse direction — the two roster pages must list the whole shipped surface — so the reference README's 'Guarded mirror' labels are finally true (and control-plane.md's label upgraded to match its existing gate). MEDIUM: system-actions roster +2 ids and a seed-install catalog row; read-api.md documents its eight missing public functions; glossary disambiguates the two certainty senses; failure-modes re-sorted to match its own claim; tutorial 02 keeps its offline promise; batch imports document --enrich. LOW sweep: macOS stray, undemonstrated recap bullet, wrong chapter credit, imperative voice in common-pitfalls, alpha.20 milestone link, how-to index overpromise. Plus the audit's highest-value reciprocal links: six zero-outbound reference pages and four posture pages now link the how-to that runs them. Out of scope (recorded in the audit): new how-to guides for the review queue and MCP setup, and the Engineer-posture practice guide."
```

- [ ] **Step 4: Merge on green, clean up**

Squash-merge after the `verify` and `gitleaks` checks pass. Then remove the worktree and branch, and pull main:

```bash
git -C /home/eranr/memoria-vault worktree remove --force .claude/worktrees/docaudit
git -C /home/eranr/memoria-vault branch -D wip/docaudit
git -C /home/eranr/memoria-vault push origin --delete wip/docaudit
git -C /home/eranr/memoria-vault pull --ff-only origin main
```

(If the remote branch was already deleted by the merge, the `--delete` push fails harmlessly. Do not touch the `cov-*` or `docfix` worktrees — they belong to another session.)

---

## Explicitly out of scope (do not re-litigate mid-execution)

- **New how-to guides** for the evidence-set review queue, MCP transport setup, and prompt operations — content authoring with product-judgment weight; the audit records them as coverage gaps for a separate decision. The index overpromise they caused is fixed here (Task 8).
- **read-api completeness gate** — one observed drift, no printed completeness claim after Task 5; the checker bar (recurring failure) is not met.
- **`run-a-systematic-review.md` filename/title mismatch** — refuted in audit verification; the title is accurate about scope.
- **Demonstrating git in Tutorial 01** — the recap bullet is dropped instead (deletion > mechanism); Tutorial 07 already shows `git status`.
- **Engineer-posture practice link** — no how-to exists; recorded as an accepted LOW gap.
- **`extraction_confidence` glossary entry** — surfaced during research, not an audit finding; leave for a docs pass with product context.
