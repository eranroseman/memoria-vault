# V2 Evidence-Set Review UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the V2 review surface — the disposition seam with the reject flip, the evidence-review queue and view, the `memoria review` CLI cockpit with the pre-registered telemetry, the pane front, and the markdown export-target acceptance.

**Architecture:** One queue, two fronts: a pure queue-assembly module feeds both the `memoria review` CLI (engine-direct, keep-test) and a `view-spec.v1` view rendered by the U3 pane; all four actions drive one seam (`resolve_evidence_review`, corrected so only accept clears holds) emitting `disposition.v1`. Spec of record: `docs/superpowers/specs/2026-07-16-v2-evidence-review-design.md` (main @ a525a81a).

**Tech Stack:** Python 3 / SQLite / pytest; plain-JS plugin view on the surfaces plan's infrastructure; no new dependencies (bibtex round-trip uses the repo's own `parse_bibtex_entry`).

## Global Constraints

- Correctness gate: `python scripts/verify`; PR + `verify`/`gitleaks`; squash merge; explicit-path staging; disposable vaults only.
- Cross-plan execution order: **V2R-A and V2R-C run after Plan 22's S35.4 if it has landed (grep-first steps handle either state); V2R-B.4–.5 and all of V2R-D run after the surfaces plan's U3-ENG/U3-PLUG/SEAM.1.** All line refs at `a525a81a` — re-anchor by symbol after other plans land.
- Golden serialization: V2R-D.3 (plugin seed) and V2R-D.1 (floor entry) regenerate goldens — sequential with any other golden-touching task, cross-plan included.

## Cross-section contracts (BINDING — manifest seam resolutions)

1. **The queue row shape** (V2R-B produces, C and D consume): rows carry `evidence_id, claim_text, items, item_count, routing, routing_reason, reviewable, cure, project, age_days, latest_decision, warrant, analysis`. B's `evidence_review.assemble_evidence_review_queue(...)` (pure) is the single assembler; the CLI consumes it engine-direct (no HTTP — keep-test), the view via `engine_api.read_evidence_review_view(...)`.
2. **Age facet naming:** `min_age_days` everywhere — B's param, C's flag `--min-age-days`, the endpoint's query param. (C's drafted `--max-age-days` is superseded.)
3. **Disposition emission:** V2R-A's `emit_explicit_disposition_event(...)` is the one helper for the keep-test path (the context-bound `emit_disposition_event` requires a running request the CLI lacks). C's contract line naming `operations.py:146` is superseded by A's actual Produces.
4. **The reject flip is owned by V2R-A.1** (only accept clears; latest-event-wins; written against `_disposed_evidence_digests` with the ids-form variant). B's queue applies the same accept-only rule independently in its pure logic (consistent by contract, tested in both). D.5's xfail ordering note reads "pre-V2R-A", not pre-V2R-B.
5. **`resolve-evidence` worker operation** (V2R-D.1, resolving the declared SPEC GAP) is a thin wrapper over A's seam — one implementation, PI-protected, floor-listed as refused; the pane's four buttons enqueue it via SEAM.1's `actor="pi"` door; the CLI never uses it.
6. **View envelope:** B follows the surfaces plan's binding contract 3 (`{ok, view: {version, kind, blocks}}`); if U3-ENG shipped the flat form, B's noted one-line swap applies at execution.
7. **Telemetry rides `empirical_event.v1`** (C's schema decision): `workflow="evidence-review"`, `view.opened` + client `disposition.recorded` with `duration_s`; skip and reopen are journal-derived metrics, never synthesized events.
8. **Execution order:** V2R-A → V2R-B.1–.3 → V2R-C → V2R-B.4–.5 → V2R-D.

---
# V2R-A — The disposition seam: reject flip, defer/edit, warrant, disposition.v1

Section of the V2 evidence-review implementation plan. Repo:
`/home/eranr/memoria-vault` (main @ a525a81a). Governing spec:
`docs/superpowers/specs/2026-07-16-v2-evidence-review-design.md` — §4
(disposition mapping, the reject flip) and §1 item 3 (the warrant demand as
structured reason capture on accept); implementation slices 2 and 5 (this
section owns the *seam half* of slice 5 — journaling the warrant; row
re-render belongs to the view/queue sections).

## Cross-plan facts and execution order

1. **U3-ENG / U3-PLUG** (`docs/superpowers/plans/2026-07-15-surfaces-bootstrap-and-plugins.md`)
   produce the view-spec.v1 machinery this spec's §1 consumes: `GET
   /v1/views/attention`, the `{ok, api_version, spec: "view-spec.v1", blocks}`
   envelope, and `VIEW_BLOCK_KINDS = ("card", "text", "badge", "action-row",
   "evidence-list")` exported from `engine/api.py`. **V2R-A has no dependency
   on U3-ENG** — nothing here touches views. But the fields this section
   journals (`warrant`, `suppressed_until`, `edit_target`) are the inputs the
   evidence-review queue/view sections read, and those sections *do* consume
   U3-ENG's envelope and block catalog. Execution order: V2R-A may run before
   or after U3-ENG; the queue/view sections must run after **both**.
2. **Plan 22 S35.4** (`docs/superpowers/plans/2026-07-15-alpha22-substrate-trust.md`,
   Task S35.4) replaces `_disposed_evidence_ids(vault) -> set[str]` with
   `_disposed_evidence_digests(vault) -> dict[str, str]` (`items_sha256`-bound
   dispositions) and adds an evidence-record lookup + `items_sha256` key to
   `resolve_evidence_review`'s journaled event. This section is **written
   against the post-S35.4 digests form**; every task that touches those sites
   starts with a grep step and carries an explicit ids-form variant for the
   case where S35.4 has not yet executed. If V2R-A lands first, S35.4's step
   (d) record-lookup edit becomes a merge with Task V2R-A.2's identical
   lookup — reconcile at execution time, do not duplicate the lookup.
3. **No worker payload exists for this seam.** `memoria project
   resolve-evidence` calls `resolve_evidence_review` directly
   (`src/memoria_vault/cli.py:1120-1157`), not through
   `enqueue_operation`/`run_next_job`; there is no
   `product/capabilities/operations/resolve-evidence*.md` manifest. This is
   the spec's keep-test path (CLI front, no server, direct engine calls) —
   the tasks below change the engine seam and the argparse surface only.

## SPEC GAPs

- SPEC GAP: the spec says accept "may carry" the warrant but does not say what
  a warrant on reject/edit/defer does — this plan fails loud
  (`ValueError`), per the honesty doctrine; revisit if the PI wants silent drop.
- SPEC GAP: the spec derives *rendering* from "the latest disposition event"
  but does not state whether a later non-accept disposition voids an earlier
  accept for *hold-clearing*; this plan applies latest-event-wins to clearing
  too (a reject after an accept re-blocks), matching §8's voiding spirit.
- SPEC GAP: §1 says defer's clock is the disposition event's timestamp; the
  recorded `suppressed_until` field (next UTC midnight, `YYYY-MM-DDT00:00:00Z`)
  is a journaled convenience for readers, not a second clock — queue assembly
  may recompute from `timestamp` and must agree.

## Seam contract after this section (what other sections consume)

- `resolve_evidence_review(vault: Path, evidence_id: str, *, actor: str,
  machine: str, decision: str, reason: str = "", warrant: str = "") ->
  dict[str, Any]` — `decision ∈ {accept, reject, edit, defer}`; returns the
  journaled `resolve-evidence-review` event row, which now carries:
  `warrant` (accept only, present only when non-empty), `suppressed_until`
  (defer only), `edit_target = {"draft_path": str, "block_ref": str}` (edit
  only), plus S35.4's `items_sha256` when the digests form is in.
- Only `accept` clears verification holds: `_disposed_evidence_digests(vault:
  Path) -> dict[str, str]` maps evidence ids whose **latest** disposition is
  `accept` (with a non-null digest) to that bound digest; reject/edit/defer
  never suppress findings.
- Every disposition additionally lands one `disposition.v1` journal event
  (`event_type = "disposition"`) with `item_type="evidence-set"`,
  `item_id=<ev-id>`, `decision` mapped 1:1 — emitted through
  `emit_explicit_disposition_event(vault: Path, *, decision: str, item_type:
  str, item_id: str, actor: str, machine: str) -> dict[str, Any]`
  (new, `runtime/operations.py`).
- CLI: `memoria project resolve-evidence --decision
  {accept,reject,edit,defer} [--warrant TEXT]`.

Line references below were verified against main @ a525a81a; plan-22 S35 tasks
shift `knowledge.py` line numbers — always locate by symbol name first.

Test registration: both touched test files are already in `TEST_LEVELS`
(`tests/conftest.py:28` `test_cli_work_project.py: "contract"`, `:38`
`test_draft_verification.py: "runtime"`) — no conftest change in this section.

---

### Task V2R-A.1: The reject flip — only accept clears holds

Shipped behavior treats reject like accept: `_disposed_evidence_ids`
(`knowledge.py:3241-3251`) selects `decision IN ('accept', 'reject')` and the
verify loop skips the hold findings for any disposed id
(`knowledge.py:2224-2225`), so a rejected implicit synthesis currently
unblocks its export. This task proves that with a failing test, then fixes it:
latest disposition per id wins, and only `accept` clears.

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py` — the disposed-lookup
  function: post-S35.4 `_disposed_evidence_digests` (replaces
  `_disposed_evidence_ids` at `:3241-3251`; locate by name), consumed at the
  `disposed = ...` assignment (`:2187` pre-S35) and the skip site
  (`:2224-2225` pre-S35). The skip site itself needs **no** edit in either
  form — the flip lives entirely inside the lookup function.
- Modify: `tests/test_draft_verification.py` — new tests appended after
  `test_evidence_review_disposition_clears_draft_gate` (`:325-343`; if plan-22
  S35.4's tests already exist, append after
  `test_disposition_requires_matching_evidence_record`), plus one shared
  helper appended after `_compose_source_backed_draft` (`:968-992`).

**Interfaces:**
- Consumes: `state.connect(vault)` (`event_log` columns `event_id`,
  `payload_json`); test helpers `_project(vault)`, `_outline(vault, content)`,
  `write_checked_concept(...)`, and the module-level wrappers
  `compose_project_draft` / `verify_project_draft` /
  `resolve_evidence_review` already defined in `tests/test_draft_verification.py:27-51`.
- Produces: `_disposed_evidence_digests(vault: Path) -> dict[str, str]`
  (private to knowledge.py) — latest disposition per evidence id wins across
  **all** decisions; only ids whose latest decision is `accept` with a
  non-null `items_sha256` appear. (Ids form, if S35.4 has not run:
  `_disposed_evidence_ids(vault: Path) -> set[str]` — ids whose latest
  decision is `accept`.) Test helper
  `_compose_implicit_draft(vault: Path, *, body: str) -> str`.

**Steps:**

- [ ] Determine the S35.4 state — run:

  ```
  grep -n "_disposed_evidence_digests\|_disposed_evidence_ids" src/memoria_vault/runtime/knowledge.py
  ```

  Hits on `_disposed_evidence_digests` ⇒ digests form (expected; follow the
  main steps). Hits only on `_disposed_evidence_ids` ⇒ ids form: follow the
  main steps but use the ids-form implementation given at the end of this
  task, and expect no `items_sha256` in journaled events until S35.4 lands.

- [ ] Write the failing tests. In `tests/test_draft_verification.py`, append
  after `_compose_source_backed_draft` (end of file):

  ```python
  def _compose_implicit_draft(vault: Path, *, body: str) -> str:
      """Compose project-alpha around one checked note whose claim cites no items."""
      _project(vault)
      write_checked_concept(
          vault,
          "notes/thesis.md",
          "type: note\ncheck_status: checked\ntitle: Thesis\nid: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n",
          "note",
          body=body,
      )
      _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — Thesis\n")
      return compose_project_draft(vault, "project-alpha")["evidence_markers"][0]["id"]
  ```

  and append after `test_evidence_review_disposition_clears_draft_gate`:

  ```python
  def test_reject_disposition_keeps_export_hold(tmp_path: Path) -> None:
      vault = tmp_path
      evidence_id = _compose_implicit_draft(
          vault, body="This rejected implicit claim must stay blocked."
      )

      resolve_evidence_review(
          vault, evidence_id, decision="reject", reason="grounds do not support the claim"
      )
      verification = verify_project_draft(vault, "project-alpha")

      assert verification["ready"] is False
      assert "evidence-incomplete" in {f["kind"] for f in verification["findings"]}


  def test_reject_after_accept_reblocks_export(tmp_path: Path) -> None:
      vault = tmp_path
      evidence_id = _compose_implicit_draft(
          vault, body="This claim was accepted, then the PI reversed."
      )

      resolve_evidence_review(vault, evidence_id, decision="accept", reason="PI accepted")
      assert verify_project_draft(vault, "project-alpha")["ready"] is True

      resolve_evidence_review(vault, evidence_id, decision="reject", reason="PI reversed")
      verification = verify_project_draft(vault, "project-alpha")

      assert verification["ready"] is False
  ```

  (An empty-items marker derives `type=implicit`, `state=evidence-incomplete`,
  `review_required=True` — `state.py:_derived_evidence_row` — so the surviving
  hold finding is `evidence-incomplete`.)

- [ ] Run the tests to verify they fail against shipped behavior — this is the
  proof that reject currently unblocks:

  ```
  python -m pytest tests/test_draft_verification.py::test_reject_disposition_keeps_export_hold tests/test_draft_verification.py::test_reject_after_accept_reblocks_export -v
  ```

  Expected: both FAIL at `assert verification["ready"] is False` with
  `assert True is False` (the rejected id is suppressed and the draft reads
  export-ready).

- [ ] Write the minimal implementation. **Digests form** — replace the body of
  `_disposed_evidence_digests` in `src/memoria_vault/runtime/knowledge.py`
  (locate by name) with:

  ```python
  def _disposed_evidence_digests(vault: Path) -> dict[str, str]:
      """Evidence ids whose LATEST disposition is accept, mapped to the bound digest.

      Only accept clears holds (V2 spec §4): reject, edit, and defer never
      suppress findings, and a later non-accept disposition voids an earlier
      accept (latest event wins). Legacy accepts without items_sha256 stay
      inert (fail closed).
      """
      with state.connect(vault) as conn:
          rows = conn.execute(
              """
              SELECT json_extract(payload_json, '$.evidence_id') AS evidence_id,
                     json_extract(payload_json, '$.decision') AS decision,
                     json_extract(payload_json, '$.items_sha256') AS items_sha256
              FROM event_log
              WHERE json_extract(payload_json, '$.operation') = 'resolve-evidence-review'
              ORDER BY event_id
              """
          ).fetchall()
      latest: dict[str, tuple[str, Any]] = {
          str(row["evidence_id"]): (str(row["decision"] or ""), row["items_sha256"])
          for row in rows
          if row["evidence_id"]
      }
      return {
          evidence_id: str(digest)
          for evidence_id, (decision, digest) in latest.items()
          if decision == "accept" and digest
      }
  ```

  The consumer (`disposed.get(row["id"]) == _evidence_items_sha256(row["items"])`)
  is unchanged. Note the deliberate difference from S35.4's original: S35.4
  dropped NULL-digest rows *before* latest-wins (latest non-null won); the
  flip applies latest-wins over **all** events first, then filters — a later
  legacy or non-accept event fails closed instead of resurrecting an older
  accept.

  **Ids form** (only if the grep showed no digests function) — replace
  `_disposed_evidence_ids` (`knowledge.py:3241-3251`) with:

  ```python
  def _disposed_evidence_ids(vault: Path) -> set[str]:
      """Evidence ids whose LATEST disposition is accept (V2 spec §4: only accept clears)."""
      with state.connect(vault) as conn:
          rows = conn.execute(
              """
              SELECT json_extract(payload_json, '$.evidence_id') AS evidence_id,
                     json_extract(payload_json, '$.decision') AS decision
              FROM event_log
              WHERE json_extract(payload_json, '$.operation') = 'resolve-evidence-review'
              ORDER BY event_id
              """
          ).fetchall()
      latest = {
          str(row["evidence_id"]): str(row["decision"] or "")
          for row in rows
          if row["evidence_id"]
      }
      return {evidence_id for evidence_id, decision in latest.items() if decision == "accept"}
  ```

  The skip site `if row["id"] in disposed: continue` (`:2224-2225`) is
  unchanged. When S35.4 later executes, its replacement must preserve this
  task's accept-only + latest-wins semantics (the two new tests pin it).

- [ ] Run the tests to verify they pass, and that the existing disposition
  tests still hold (accept still clears; drift still overrides):

  ```
  python -m pytest tests/test_draft_verification.py -v
  ```

  Expected: all pass, including
  `test_evidence_review_disposition_clears_draft_gate` and
  `test_draft_text_drift_overrides_pi_disposition_and_refuses_export`.

- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/knowledge.py tests/test_draft_verification.py
  git commit -m "fix(evidence): only accept clears review holds; reject keeps the export block" -m "Shipped behavior suppressed hold findings for decision IN (accept, reject), so a rejected implicit synthesis unblocked its export. Latest disposition per evidence id now wins and only accept clears (V2 spec §4 reject flip), proven by tests that fail against the shipped semantics." -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task V2R-A.2: The seam gains `defer` and `edit`

Extends the decision guard, journals defer's UTC-day suppression and edit's
deep-link payload, and widens the CLI choices. Consumption of
`suppressed_until` (row suppression until the next UTC calendar day) and
`edit_target` (deep link into the draft) belongs to the queue/view sections —
this task only records them honestly.

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py` — imports (`:14`
  `from datetime import date`; the `memoria_vault.runtime.*` import block
  `:20-40`), `resolve_evidence_review` (`:2268-2297` pre-S35; guard at
  `:2284`), new private helper `_defer_suppressed_until` placed immediately
  before `_disposed_evidence_digests` (locate by name).
- Modify: `src/memoria_vault/cli.py:332` (`--decision` choices).
- Modify: `tests/test_draft_verification.py` (imports `:1-25`; tests appended
  after Task V2R-A.1's), `tests/test_cli_work_project.py` (new test appended
  after `test_cli_project_resolve_evidence_verifies_current_draft_before_disposition`,
  which ends at `:945`).
- Modify: `docs/how-to-guides/project/compose-a-draft.md:44-46`,
  `docs/tutorials/05-verify-evidence.md:47-48` (behavior sentences only; the
  doc-claims gate checks CLI paths/operation ids, both unchanged).

**Interfaces:**
- Consumes: `state.evidence_sets(vault: Path) -> list[dict[str, Any]]` (rows
  carry `id`, `block_ref` = `<rel>#^blk-<8hex>`, `items`, `type`, `state`,
  `review_required`); `runtime.time.now_iso() -> str` / `parse_iso(value) ->
  datetime | None`; `append_explicit_journal_event(vault, event, *, actor,
  machine) -> dict[str, Any]` (`trusted_writer.py:215-236`); post-S35.4 the
  in-function `record` lookup and `_evidence_items_sha256(items)`.
- Produces: `resolve_evidence_review(vault: Path, evidence_id: str, *, actor:
  str, machine: str, decision: str, reason: str = "") -> dict[str, Any]` now
  accepting `decision ∈ {accept, reject, edit, defer}`; journaled event gains
  `suppressed_until: str` (defer only; `YYYY-MM-DDT00:00:00Z`, next UTC
  midnight after the event `timestamp`) and `edit_target: {"draft_path": str,
  "block_ref": str}` (edit only); `_defer_suppressed_until(timestamp: str) ->
  str` (private); CLI `--decision {accept,reject,edit,defer}`.

**Steps:**

- [ ] Write the failing seam tests. In `tests/test_draft_verification.py`,
  extend the imports: after `from pathlib import Path` (`:4`) add

  ```python
  from datetime import timedelta
  ```

  and after the `from memoria_vault.runtime import knowledge, state` line add

  ```python
  from memoria_vault.runtime.time import parse_iso
  ```

  Then append after Task V2R-A.1's tests:

  ```python
  def test_defer_disposition_keeps_hold_and_records_utc_day_suppression(
      tmp_path: Path,
  ) -> None:
      vault = tmp_path
      evidence_id = _compose_implicit_draft(
          vault, body="This implicit claim is deferred until tomorrow."
      )

      event = resolve_evidence_review(vault, evidence_id, decision="defer", reason="revisit")
      verification = verify_project_draft(vault, "project-alpha")

      moment = parse_iso(event["timestamp"])
      assert moment is not None
      expected_day = (moment.date() + timedelta(days=1)).isoformat()
      assert event["suppressed_until"] == f"{expected_day}T00:00:00Z"
      assert verification["ready"] is False
      assert "evidence-incomplete" in {f["kind"] for f in verification["findings"]}


  def test_edit_disposition_records_deep_link_and_keeps_hold(tmp_path: Path) -> None:
      vault = tmp_path
      evidence_id = _compose_implicit_draft(
          vault, body="This implicit claim needs its marker fixed."
      )

      event = resolve_evidence_review(vault, evidence_id, decision="edit", reason="fix marker")
      verification = verify_project_draft(vault, "project-alpha")

      anchor = evidence_id.removeprefix("ev-")
      assert event["edit_target"] == {
          "draft_path": "projects/project-alpha/draft.md",
          "block_ref": f"projects/project-alpha/draft.md#^blk-{anchor}",
      }
      assert verification["ready"] is False


  def test_unknown_decision_names_all_four(tmp_path: Path) -> None:
      vault = tmp_path
      evidence_id = _compose_implicit_draft(vault, body="Guard message names the seam decisions.")

      with pytest.raises(ValueError, match="accept, reject, edit, or defer"):
          resolve_evidence_review(vault, evidence_id, decision="override", reason="nope")
  ```

- [ ] Run the tests to verify they fail:

  ```
  python -m pytest tests/test_draft_verification.py -v -k "defer_disposition or edit_disposition or unknown_decision"
  ```

  Expected: the defer and edit tests ERROR with
  `ValueError: evidence review decision must be accept or reject`; the guard
  test FAILS because the shipped message does not match
  `accept, reject, edit, or defer`.

- [ ] Write the minimal seam implementation in
  `src/memoria_vault/runtime/knowledge.py`:

  (a) Change line 14 from `from datetime import date` to:

  ```python
  from datetime import UTC, date, timedelta
  ```

  (b) Add to the `memoria_vault.runtime.*` import block (alphabetical, after
  the `subsystems.lib` import, before `trusted_writer`):

  ```python
  from memoria_vault.runtime.time import now_iso
  ```

  (Add `parse_iso` to that import too — `from memoria_vault.runtime.time
  import now_iso, parse_iso` — it is used by the helper below.)

  (c) In `resolve_evidence_review`, replace the guard (`:2284-2285`):

  ```python
      if decision not in {"accept", "reject"}:
          raise ValueError("evidence review decision must be accept or reject")
  ```

  with:

  ```python
      if decision not in {"accept", "reject", "edit", "defer"}:
          raise ValueError("evidence review decision must be accept, reject, edit, or defer")
  ```

  (d) Replace the tail `return append_explicit_journal_event(...)` call with a
  named event dict plus per-decision branches. **Digests form** (S35.4's
  `record` lookup and `items_sha256` already present — keep both):

  ```python
      event: dict[str, Any] = {
          "event": "resolved",
          "operation": "resolve-evidence-review",
          "evidence_id": evidence_id,
          "decision": decision,
          "reason": reason.strip(),
          "items_sha256": _evidence_items_sha256(record["items"]),
      }
      if decision == "defer":
          event["timestamp"] = now_iso()
          event["suppressed_until"] = _defer_suppressed_until(event["timestamp"])
      if decision == "edit":
          block_ref = str(record["block_ref"])
          event["edit_target"] = {
              "draft_path": block_ref.partition("#^")[0],
              "block_ref": block_ref,
          }
      return append_explicit_journal_event(Path(vault), event, actor=actor, machine=machine)
  ```

  **Ids form** (S35.4 not yet executed): the function has no `record` — insert
  the lookup after the decision guard, byte-identical to S35.4's step (d) so
  the later merge is a no-op:

  ```python
      record = next(
          (row for row in state.evidence_sets(Path(vault)) if row["id"] == evidence_id),
          None,
      )
      if record is None:
          raise ValueError(f"unknown evidence id: {evidence_id}")
  ```

  and omit the `"items_sha256"` line from the event dict (S35.4 adds it).

  (e) Add the helper immediately before `_disposed_evidence_digests` (or
  `_disposed_evidence_ids` in the ids form):

  ```python
  def _defer_suppressed_until(timestamp: str) -> str:
      """Next UTC midnight after the disposition timestamp (V2 spec §4 defer)."""
      moment = parse_iso(timestamp)
      if moment is None or moment.tzinfo is None:
          raise ValueError(f"defer timestamp must be timezone-aware ISO-8601: {timestamp}")
      next_day = moment.astimezone(UTC).date() + timedelta(days=1)
      return f"{next_day.isoformat()}T00:00:00Z"
  ```

- [ ] Run the seam tests to verify they pass:

  ```
  python -m pytest tests/test_draft_verification.py -v
  ```

  Expected: all pass (defer/edit journal their payloads and neither clears the
  hold — Task V2R-A.1's accept-only lookup already guarantees the latter).

- [ ] Write the failing CLI test. In `tests/test_cli_work_project.py`, append
  after `test_cli_project_resolve_evidence_verifies_current_draft_before_disposition`
  (ends `:945`):

  ```python
  def test_cli_project_resolve_evidence_supports_defer_and_edit(
      tmp_path: Path, capsys: pytest.CaptureFixture[str]
  ) -> None:
      workspace = tmp_path / "workspace"
      main(["init", "--workspace", str(workspace), "--yes", "--json"])
      capsys.readouterr()
      _write_project_argument_fixture(workspace)
      (workspace / "projects/project-alpha/outline.md").write_text(
          "- 01ARZ3NDEKTSV4RRFFQ69G5FA2 -- Support\n",
          encoding="utf-8",
      )
      assert (
          main(
              [
                  "project",
                  "compose",
                  "--workspace",
                  str(workspace),
                  "project-alpha",
                  "--json",
                  "--idempotency-key",
                  "compose-for-dispositions",
              ]
          )
          == 0
      )
      composed = json.loads(capsys.readouterr().out)
      evidence_id = composed["result"]["evidence_markers"][0]["id"]

      rc = main(
          [
              "project",
              "resolve-evidence",
              "--workspace",
              str(workspace),
              "project-alpha",
              "--evidence-id",
              evidence_id,
              "--decision",
              "defer",
              "--reason",
              "revisit tomorrow",
              "--json",
              "--idempotency-key",
              "verify-for-defer",
          ]
      )
      deferred = json.loads(capsys.readouterr().out)
      assert rc == 0
      assert deferred["ok"] is True
      assert deferred["decision"] == "defer"
      assert deferred["event"]["suppressed_until"].endswith("T00:00:00Z")

      rc = main(
          [
              "project",
              "resolve-evidence",
              "--workspace",
              str(workspace),
              "project-alpha",
              "--evidence-id",
              evidence_id,
              "--decision",
              "edit",
              "--json",
              "--idempotency-key",
              "verify-for-edit",
          ]
      )
      edited = json.loads(capsys.readouterr().out)
      assert rc == 0
      assert edited["event"]["edit_target"]["draft_path"] == "projects/project-alpha/draft.md"
  ```

- [ ] Run the CLI test to verify it fails:

  ```
  python -m pytest tests/test_cli_work_project.py::test_cli_project_resolve_evidence_supports_defer_and_edit -v
  ```

  Expected: ERROR with `SystemExit: 2` — argparse rejects
  `invalid choice: 'defer'`.

- [ ] Write the minimal CLI implementation. In `src/memoria_vault/cli.py:332`
  change:

  ```python
      resolve_evidence.add_argument("--decision", choices=("accept", "reject"), required=True)
  ```

  to:

  ```python
      resolve_evidence.add_argument(
          "--decision", choices=("accept", "reject", "edit", "defer"), required=True
      )
  ```

  (`_cmd_project_resolve_evidence` passes `decision` through unchanged — no
  handler edit.)

- [ ] Run the CLI test to verify it passes:

  ```
  python -m pytest tests/test_cli_work_project.py::test_cli_project_resolve_evidence_supports_defer_and_edit -v
  ```

  Expected: PASSED.

- [ ] Update the two behavior sentences in docs. In
  `docs/how-to-guides/project/compose-a-draft.md` replace:

  ```
  If verification reports an evidence item that you accept or reject after review,
  record the PI disposition:
  ```

  with:

  ```
  If verification reports an evidence item, record the PI disposition — `accept`,
  `reject`, `edit`, or `defer`. Only `accept` clears the export hold; `reject`
  keeps it blocking, `edit` records a fix-the-marker intent with a deep link to
  the draft block, and `defer` suppresses the review item until the next UTC
  calendar day:
  ```

  In `docs/tutorials/05-verify-evidence.md` replace:

  ```
  Reject records the PI disposition; it does not silently rewrite the draft or
  remove its durable evidence marker.
  ```

  with:

  ```
  Reject records the PI disposition and keeps the export hold blocking; it does
  not silently rewrite the draft or remove its durable evidence marker.
  ```

- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/knowledge.py src/memoria_vault/cli.py tests/test_draft_verification.py tests/test_cli_work_project.py docs/how-to-guides/project/compose-a-draft.md docs/tutorials/05-verify-evidence.md
  git commit -m "feat(evidence): resolve-evidence seam gains defer and edit decisions" -m "Defer journals suppressed_until (next UTC midnight, derived from the event timestamp - the spec's clock); edit journals an edit_target deep link (draft_path + block_ref). Neither clears the hold. CLI choices extend to the four V2 spec section 4 decisions; no worker payload exists for this seam (direct engine call, the keep-test path)." -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task V2R-A.3: Optional `warrant` on accept — journaled structured reason

Spec §1 item 3: evidence sets bind draft blocks, so "state the warrant" is
structured reason capture on the accept disposition — the optional `warrant`
text rides the disposition event as a named field (journaled provenance) and
is surfaced by later readers (the queue/view sections render it on the row;
W2 write-back later carries it as candidate material for a real `warrant`
edge — both out of scope here).

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py` (`resolve_evidence_review`
  signature + guard + event dict, as left by Task V2R-A.2).
- Modify: `src/memoria_vault/cli.py` (`:333` area — new `--warrant` argument
  next to `--reason`; handler `:1139-1146` passes it through).
- Modify: `tests/test_draft_verification.py`, `tests/test_cli_work_project.py`.

**Interfaces:**
- Consumes: Task V2R-A.2's event-dict form of `resolve_evidence_review`.
- Produces: `resolve_evidence_review(vault: Path, evidence_id: str, *, actor:
  str, machine: str, decision: str, reason: str = "", warrant: str = "") ->
  dict[str, Any]` — journals `warrant` only when non-empty; raises
  `ValueError("warrant text rides only the accept decision")` when a warrant
  accompanies reject/edit/defer. CLI: `memoria project resolve-evidence
  [--warrant TEXT]`.

**Steps:**

- [ ] Write the failing seam tests — append to `tests/test_draft_verification.py`:

  ```python
  def test_accept_disposition_journals_optional_warrant(tmp_path: Path) -> None:
      vault = tmp_path
      evidence_id = _compose_implicit_draft(
          vault, body="This accepted claim carries a stated warrant."
      )

      event = resolve_evidence_review(
          vault,
          evidence_id,
          decision="accept",
          reason="PI accepted",
          warrant="The cited spans jointly entail the claim.",
      )
      bare = resolve_evidence_review(vault, evidence_id, decision="accept", reason="again")

      assert event["warrant"] == "The cited spans jointly entail the claim."
      assert "warrant" not in bare


  def test_warrant_refused_on_non_accept_decisions(tmp_path: Path) -> None:
      vault = tmp_path
      evidence_id = _compose_implicit_draft(vault, body="A warrant cannot ride a rejection.")

      with pytest.raises(ValueError, match="warrant text rides only the accept decision"):
          resolve_evidence_review(
              vault,
              evidence_id,
              decision="reject",
              reason="no",
              warrant="This should be refused.",
          )
  ```

- [ ] Run the tests to verify they fail:

  ```
  python -m pytest tests/test_draft_verification.py -v -k "optional_warrant or warrant_refused"
  ```

  Expected: both ERROR with
  `TypeError: resolve_evidence_review() got an unexpected keyword argument 'warrant'`.

- [ ] Write the minimal seam implementation in
  `src/memoria_vault/runtime/knowledge.py`:

  (a) Add `warrant: str = ""` to the signature after `reason: str = ""`.

  (b) After the decision guard, add:

  ```python
      warrant = warrant.strip()
      if warrant and decision != "accept":
          raise ValueError("warrant text rides only the accept decision")
  ```

  (c) After the event dict from Task V2R-A.2 (before the defer branch), add:

  ```python
      if warrant:
          event["warrant"] = warrant
  ```

- [ ] Run the seam tests to verify they pass:

  ```
  python -m pytest tests/test_draft_verification.py -v
  ```

  Expected: all pass.

- [ ] Write the failing CLI test — append to `tests/test_cli_work_project.py`:

  ```python
  def test_cli_project_resolve_evidence_accept_carries_warrant(
      tmp_path: Path, capsys: pytest.CaptureFixture[str]
  ) -> None:
      workspace = tmp_path / "workspace"
      main(["init", "--workspace", str(workspace), "--yes", "--json"])
      capsys.readouterr()
      _write_project_argument_fixture(workspace)
      (workspace / "projects/project-alpha/outline.md").write_text(
          "- 01ARZ3NDEKTSV4RRFFQ69G5FA2 -- Support\n",
          encoding="utf-8",
      )
      assert (
          main(
              [
                  "project",
                  "compose",
                  "--workspace",
                  str(workspace),
                  "project-alpha",
                  "--json",
                  "--idempotency-key",
                  "compose-for-warrant",
              ]
          )
          == 0
      )
      composed = json.loads(capsys.readouterr().out)
      evidence_id = composed["result"]["evidence_markers"][0]["id"]

      rc = main(
          [
              "project",
              "resolve-evidence",
              "--workspace",
              str(workspace),
              "project-alpha",
              "--evidence-id",
              evidence_id,
              "--decision",
              "accept",
              "--reason",
              "reviewed",
              "--warrant",
              "Spans jointly entail the claim.",
              "--json",
              "--idempotency-key",
              "verify-for-warrant",
          ]
      )
      accepted = json.loads(capsys.readouterr().out)

      assert rc == 0
      assert accepted["ok"] is True
      assert accepted["event"]["warrant"] == "Spans jointly entail the claim."
  ```

- [ ] Run the CLI test to verify it fails:

  ```
  python -m pytest tests/test_cli_work_project.py::test_cli_project_resolve_evidence_accept_carries_warrant -v
  ```

  Expected: ERROR with `SystemExit: 2` — argparse:
  `unrecognized arguments: --warrant`.

- [ ] Write the minimal CLI implementation in `src/memoria_vault/cli.py`:

  (a) After `resolve_evidence.add_argument("--reason", default="")` (`:333`) add:

  ```python
      resolve_evidence.add_argument("--warrant", default="")
  ```

  (b) In `_cmd_project_resolve_evidence` (`:1139-1146`), pass it through —
  after `reason=args.reason,` add:

  ```python
          warrant=args.warrant,
  ```

- [ ] Run the CLI test to verify it passes:

  ```
  python -m pytest tests/test_cli_work_project.py::test_cli_project_resolve_evidence_accept_carries_warrant -v
  ```

  Expected: PASSED.

- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/knowledge.py src/memoria_vault/cli.py tests/test_draft_verification.py tests/test_cli_work_project.py
  git commit -m "feat(evidence): optional warrant journaled on the accept disposition" -m "V2 spec section 1.3: the warrant demand on an evidence-review row is structured reason capture on accept - a named field on the disposition event, present only when stated, refused on non-accept decisions. Later readers (queue/view sections, W2 write-back) surface it." -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task V2R-A.4: `disposition.v1` emission per action

Every seam action lands one `disposition.v1` journal event with
`item_type="evidence-set"`, `item_id=<ev-id>`, `decision` mapped 1:1 — the
same schema the resolve-attention seam already emits
(`runtime/integrity.py:1164-1173`). The existing helper
`emit_disposition_event` (`runtime/operations.py:146-164`) journals through
`append_journal_event`, whose `validate_operation_context` demands a bound
*running* request (`trusted_writer.py:139-155`) — the evidence seam is the
explicit-provenance keep-test path (direct engine call, no request envelope),
so this task adds the explicit-provenance twin that reuses the same validator
(`validate_disposition_event`, `engine/empirical_events.py:148-165`), schema
constant, and event shape. The closed `DECISIONS` enum
(`engine/empirical_events.py:32`) already contains all four decisions — the
validator is unchanged, exactly as the spec states.

**Files:**
- Modify: `src/memoria_vault/runtime/operations.py` — extend the
  `trusted_writer` import block (`:25-34`) with
  `append_explicit_journal_event`; add `emit_explicit_disposition_event`
  immediately after `emit_disposition_event` (`:146-164`).
- Modify: `src/memoria_vault/runtime/knowledge.py` — extend the existing
  module-level `from memoria_vault.runtime.operations import (...)` block
  (`:25-29`; no cycle — operations does not import knowledge); call site at
  the tail of `resolve_evidence_review`.
- Modify: `tests/test_draft_verification.py` (imports `:1-25`; one new test).

**Interfaces:**
- Consumes: `validate_disposition_event(payload) -> dict[str, Any]` and
  `DISPOSITION_EVENT_SCHEMA = "disposition.v1"`
  (`engine/empirical_events.py:13,148`);
  `append_explicit_journal_event(vault, event, *, actor, machine)`
  (`trusted_writer.py:215-236`).
- Produces: `emit_explicit_disposition_event(vault: Path, *, decision: str,
  item_type: str, item_id: str, actor: str, machine: str) -> dict[str, Any]`
  (`runtime/operations.py`, public); `resolve_evidence_review` emits one
  `disposition.v1` event (journal `event_type = "disposition"`) per action in
  addition to its `resolve-evidence-review` event, and returns the latter.

**Steps:**

- [ ] Write the failing test. In `tests/test_draft_verification.py`, add
  `import json` after `from datetime import timedelta`, then append:

  ```python
  def test_every_disposition_emits_disposition_v1_event(tmp_path: Path) -> None:
      vault = tmp_path
      evidence_id = _compose_implicit_draft(
          vault, body="Each seam action lands one disposition.v1 event."
      )

      for decision in ("defer", "edit", "reject", "accept"):
          resolve_evidence_review(
              vault, evidence_id, decision=decision, reason=f"PI chose {decision}"
          )

      with state.connect(vault) as conn:
          rows = conn.execute(
              "SELECT payload_json FROM event_log WHERE event_type = 'disposition' ORDER BY event_id"
          ).fetchall()
      payloads = [json.loads(row["payload_json"]) for row in rows]

      assert [payload["decision"] for payload in payloads] == [
          "defer",
          "edit",
          "reject",
          "accept",
      ]
      assert {payload["schema"] for payload in payloads} == {"disposition.v1"}
      assert {payload["item_type"] for payload in payloads} == {"evidence-set"}
      assert {payload["item_id"] for payload in payloads} == {evidence_id}
  ```

- [ ] Run the test to verify it fails:

  ```
  python -m pytest tests/test_draft_verification.py::test_every_disposition_emits_disposition_v1_event -v
  ```

  Expected: FAILS at the first assert with `[] == ['defer', 'edit', 'reject',
  'accept']` — no `disposition` events exist.

- [ ] Write the minimal implementation.

  (a) In `src/memoria_vault/runtime/operations.py`, add
  `append_explicit_journal_event,` to the `from
  memoria_vault.runtime.trusted_writer import (...)` block (alphabetical,
  before `append_journal_event`), then insert after `emit_disposition_event`:

  ```python
  def emit_explicit_disposition_event(
      vault: Path,
      *,
      decision: str,
      item_type: str,
      item_id: str,
      actor: str,
      machine: str,
  ) -> dict[str, Any]:
      """Append one disposition.v1 event created outside an operation envelope."""
      from memoria_vault.engine.empirical_events import (
          DISPOSITION_EVENT_SCHEMA,
          validate_disposition_event,
      )

      event = validate_disposition_event(
          {"decision": decision, "item_type": item_type, "item_id": item_id}
      )
      journal_event = {"event": "disposition", "schema": DISPOSITION_EVENT_SCHEMA, **event}
      return append_explicit_journal_event(vault, journal_event, actor=actor, machine=machine)
  ```

  (b) In `src/memoria_vault/runtime/knowledge.py`, add
  `emit_explicit_disposition_event,` to the module-level `from
  memoria_vault.runtime.operations import (...)` block (`:25-29`,
  alphabetical), and replace `resolve_evidence_review`'s tail

  ```python
      return append_explicit_journal_event(Path(vault), event, actor=actor, machine=machine)
  ```

  with:

  ```python
      row = append_explicit_journal_event(Path(vault), event, actor=actor, machine=machine)
      emit_explicit_disposition_event(
          Path(vault),
          decision=decision,
          item_type="evidence-set",
          item_id=evidence_id,
          actor=actor,
          machine=machine,
      )
      return row
  ```

  (The `_disposed_evidence_digests` query filters on
  `payload.operation = 'resolve-evidence-review'`, so the additional
  `disposition` events never pollute hold-clearing.)

- [ ] Run the full seam and CLI suites to verify everything passes:

  ```
  python -m pytest tests/test_draft_verification.py tests/test_cli_work_project.py -v
  ```

  Expected: all pass.

- [ ] Run the repo gate:

  ```
  python scripts/verify
  ```

  Expected: green. If a floor golden reports drift here, see the golden note
  below before touching anything.

- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/operations.py src/memoria_vault/runtime/knowledge.py tests/test_draft_verification.py
  git commit -m "feat(evidence): every resolve-evidence action emits disposition.v1" -m "Adds emit_explicit_disposition_event (explicit-provenance twin of the resolve-attention seam's helper - same validator, schema, and event shape; the context-bound writer requires a bound running request the keep-test CLI path does not have). item_type=evidence-set, item_id=ev-id, decision mapped 1:1; DECISIONS already holds all four, validator unchanged." -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

## Golden note — disposition events and floor regeneration

Floor goldens digest `journal_kinds` (every distinct `event_type` in
`event_log` — `tests/floor_lib.py:320-328`, goldens in
`tests/fixtures/floor/goldens/`, updated only via
`MEMORIA_FLOOR_UPDATE_GOLDENS=1`, refused in CI). `resolve-evidence-review`
is **not** floor-swept today (it is a direct engine call, not an
`OPERATION_REGISTRY` operation — `tests/test_floor_sweep_operations.py`), and
the seed vault records no evidence dispositions, so **V2R-A itself requires no
golden regeneration** — `verify-project-draft.json` and the rest stay
byte-identical. However: any later section (or floor-seed change) that
exercises this seam adds a new `"disposition"` kind to `journal_kinds` and
will drift every golden whose flow touches it. That drift is expected, not a
bug — regenerate deliberately with `MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m
pytest tests/test_floor_sweep_operations.py`, review the diff (the only
acceptable change is the added `disposition` kind and its hash consequences),
and commit the goldens with the change that caused them.
# V2R-B — Evidence-review queue assembly + payload + facets (`GET /v1/views/evidence-review`)

Section of the composite V2 evidence-review implementation plan. Repo:
`/home/eranr/memoria-vault` (main @ a525a81a; all line refs re-verified against the
checked-out tree at drafting time — re-anchor by quoted context if earlier sections
shift lines). Governing spec: §1 (queue union), §2 (honesty-card row schema), §3
(evidence-first/independence-first render rules), §6 (batch and filter) of
`docs/superpowers/specs/2026-07-16-v2-evidence-review-design.md`. This section is
**slice 1** of spec §9: queue assembly, the row payload, and the faceted endpoint.
It emits **no** journal events and changes **no** seam behavior — dispositions are
*read*, never written, here (slice 2 / V2R-C owns `defer`/`edit`/the reject flip and
`disposition.v1` emission via `emit_disposition_event`,
`src/memoria_vault/runtime/operations.py:146`, already exercised at the
resolve-attention seam, `src/memoria_vault/runtime/integrity.py:1165-1167`).

## Execution-order dependencies (cross-plan facts)

- **Hard: after U3-ENG** (`docs/superpowers/plans/2026-07-15-surfaces-bootstrap-and-plugins.md`).
  This section consumes U3-ENG's Produces: `engine_api.read_attention_view` and its
  private card-block helpers `_attention_view_card_block` / `_attention_created` /
  `_attention_age_days` (U3-ENG.1), `VIEW_BLOCK_KINDS = ("card", "text", "badge",
  "action-row", "evidence-list")` (U3-ENG.5), the `/v1/views/*` registration pattern
  — surface action + `_read` branch + floor ARG_TABLE entry (U3-ENG.4) — and the
  real-HTTP-server auth test pattern (U3-ENG.6). Do not start V2R-B until U3-ENG is
  merged.
- **View payload envelope** (surfaces plan, binding cross-section contract 3):
  `{ok: true, view: {version: "view-spec.v1", kind: <kind>, blocks: [...]}}`. This
  section adds `kind: "evidence-review"` on that machinery, wrapping via the shipped
  `_view(kind, blocks)` helper (`src/memoria_vault/engine/api.py:715-716`).
- **Soft: Plan 22 S35.4** (`docs/superpowers/plans/2026-07-15-alpha22-substrate-trust.md:2498`)
  replaces `_disposed_evidence_ids` with `_disposed_evidence_digests(vault) ->
  dict[str, str]` and journals `items_sha256` on every disposition. This section does
  **not** consume either function — the queue reads raw disposition events and owns
  its own accept-clearing rule, written against the **digests form** (fail-closed on
  a missing digest). Task V2R-B.2 opens with a grep step and carries the one-line
  relaxation for the ids form (pre-S35.4 checkouts).
- **Soft: Plan 22 S68.3** (`evidence-minted` journal events,
  `2026-07-15-alpha22-substrate-trust.md:3229`) supplies row age. Before S68.3
  lands, `age_days` is honestly `null` — no fabricated timestamps.
- **Independent of slice 2 (V2R-C, the reject flip):** the queue derives holds from
  stored evidence rows (`state`/`review_required`), not from `verify_project_draft`'s
  disposition-suppressed findings list, so rejected rows stay queued (rendered
  rejected) whether or not the verify-side flip has landed.

SPEC GAP: spec §6 names an "age" facet without defining buckets or the age source —
implemented as a `min_age_days` filter over first `evidence-minted` timestamps
(Plan 22 S68.3); rows with no minted event carry `age_days: null` and are treated as
age 0 by the filter; no per-age-bucket denominator is emitted.

SPEC GAP: spec §2 fields 4–6 have no producer (spec §7 bans model judgment in routing
and rendering) — the analysis block always carries the deterministic `what_tipped_it`
routing factor; `argument_for`/`argument_against` (both-or-neither enforced
structurally) and coarse `certainty` are present-only pass-throughs with no writer in
this plan.

SPEC GAP: a GET view cannot run `verify_project_draft` (an OperationContext-gated
writer seam that rebuilds evidence rows, `knowledge.py:2114-2137`) — the view derives
holds and the drift/unbound permanent blocks read-only from stored rows + current
draft text; `evidence-id-duplicate`, the planned `evidence-source-stale`,
`no-evidence-set`, and structural/number findings surface only through verify, whose
export-gate role is unchanged.

SPEC GAP: the surfaces plan's binding contract 3 (`{ok, view:{...}}`) contradicts the
U3-ENG task text's flat `{ok, spec, blocks}` payload — this section follows the
binding contract; if executed U3-ENG shipped the flat shape, swap the single
`_read_payload(view=_view(...))` call in Task V2R-B.4 to match the shipped envelope.

**Goldens:** every task here is a read or a hash-preserving refactor; no journal
event is written or reshaped → **no floor-golden regeneration** (floor goldens hash
journal output only, `tests/floor_lib.py`).

## Payload contract (what later sections — pane front, CLI front — consume)

`GET /v1/views/evidence-review` — authenticated (transport-wide bearer check,
`src/memoria_vault/runtime/http_transport.py:63`), optional `read_scope`/`scope`
narrowing, facet query params `routing_type` (`implicit|multi-hop|incomplete`),
`project`, `min_age_days` (positive int), `batch` (positive int, default 10).
Response:

```json
{
  "ok": true,
  "api_version": "engine-read-api.v1",
  "view": {
    "version": "view-spec.v1",
    "kind": "evidence-review",
    "blocks": [ <card>, <evidence-list>, <text>, <card collapsed>, ...,
                <srd-gap card>... ]
  },
  "facets": {
    "routing_type": {"implicit": 1, "multi-hop": 1, "incomplete": 1},
    "project": {"projects/project-alpha/project.md": 3},
    "kind": {"evidence-set": 3, "srd-gap": 0},
    "total": 3,
    "shown": 3,
    "batch": 10
  }
}
```

Facet counts are computed over the **whole scope-visible queue before filtering and
batching** (spec §6's honest denominators; `shown` is the post-filter, post-batch
block-row count). Deferred rows are outside both the blocks and the denominators
until the next UTC day; rejected rows are inside both.

**Per reviewable evidence row, exactly four blocks in fixed order** (spec §2 fields
1–3 = evidence, before fields 4–6 = analysis; structural, spec §3):

1. `card` — `id` = evidence id (`ev-<8hex>`), `ref` = block_ref, `review_kind:
   "evidence-set"`, `evidence_id`, `project`, `routing_type`, `reviewable: true`,
   `disposition: "open"|"rejected"`, `item_count`, `age_days` (int or null),
   `body_data: {kind: "untrusted_text", text: <claim block text verbatim>}` (field
   1). Present-only: `disposition_reason`, `warrant` (rides the latest disposition
   event when slice 5 records it).
2. `evidence-list` — `id` = `<ev>-grounds`, `items`: resolved previews (field 2):
   source-span `{ref, kind: "source-span", work_id, anchor, resolves,
   excerpt?}`; nested set `{ref, kind: "evidence-set", resolves, expansion?:
   {evidence_type, state, item_count}}` (one level, with state); code grounds
   `{ref, kind: "code-warrant", run_id, artifact_id, output_sha256, resolves,
   state}`.
3. `text` — `id` = `<ev>-routing`, `text` = the derivation rule verbatim
   (`implicit`, `multi-hop`, or `evidence-incomplete: <failing item> does not
   resolve`) (field 3).
4. `card` — `id` = `<ev>-analysis`, **`collapsed: true`** (spec §3
   independence-first), `what_tipped_it` (field 5, deterministic routing factor);
   present-only and both-or-neither `argument_for`/`argument_against` (field 4);
   present-only `certainty` (field 6). **No `verdict` key exists on any block and no
   `action-row` blocks are emitted by this slice** (field 7; actions arrive with the
   fronts after the slice-2 seam).

**Read-only cure rows** (permanent blocks `evidence-text-drift` /
`evidence-text-unbound`): three blocks — `card` (`reviewable: false`, `blocked_by:
[{kind, reason}]`, `cure`), `evidence-list`, `text` (the block reason verbatim) — and
**no analysis block**.

**srd-gap rows** (spec §1 union member 2, C1-gated): open attention cards with
`attention_kind: "srd-gap"` render as single trailing `card` blocks via U3-ENG's
`_attention_view_card_block`; the `facets.kind["srd-gap"]` key is always present
(reserved, 0 until C1 mints cards). srd-gap cards appear only on the unfiltered view
(they carry no routing type/project/evidence age).

All block kinds used (`card`, `evidence-list`, `text`) are members of U3-ENG.5's
closed `VIEW_BLOCK_KINDS` catalog — zero new block kinds (spec §1, "the same
five-block catalog U3 ships").

---

### Task V2R-B.1: expose canonical block text from the hash seam

`state._block_text_sha256_from_text` (`src/memoria_vault/runtime/state.py:2705-2754`)
already computes the canonical claim text (anchor and marker excised, stripped) and
then hashes it. The honesty card needs that text verbatim (spec §2 field 1). Split
the extractor out; the hash wrapper delegates — bindings and goldens unchanged.

**Files:**
- Create: `tests/test_evidence_review_queue.py`
- Modify: `src/memoria_vault/runtime/state.py:2705-2754`
  (`_block_text_sha256_from_text`)
- Modify: `tests/conftest.py:45` (TEST_LEVELS — nearest sibling
  `"test_evidence_markers.py": "unit"`, line 45; this file is pure-function tests →
  `"unit"`)

**Interfaces:**
- Consumes: `state._block_text_sha256_from_text(text: str, block_ref: str) -> str |
  None` (state.py:2705), `_evidence_id_for_block_anchor` (state.py:2757),
  `_direct_evidence_marker_matches` (state.py:3317), `_markdown_control_text`
  (referenced at state.py:2715).
- Produces: **`state._block_canonical_text_from_text(text: str, block_ref: str) ->
  str | None`** — the anchored block's text with the block anchor and the evidence
  marker excised, stripped; `None` under exactly the conditions the hash function
  returns `None` today. `_block_text_sha256_from_text` keeps its signature and
  becomes `"sha256:" + sha256(canonical)`.

**Steps:**

- [ ] Register the new test file. In `tests/conftest.py`, after the line
  `    "test_evidence_markers.py": "unit",` (line 45) insert:

  ```python
      "test_evidence_review_queue.py": "unit",
  ```

- [ ] Write the failing test — create `tests/test_evidence_review_queue.py`:

  ```python
  """Unit tests for evidence-review queue assembly and honesty-card blocks (V2 slice 1)."""

  from __future__ import annotations

  import datetime
  import hashlib

  from memoria_vault.runtime import state

  EV_OPEN = "ev-11111111"
  BLOCK_REF = "projects/project-alpha/draft.md#^blk-11111111"
  CONTENT = (
      "An implicit synthesis claim. ^blk-11111111 "
      "%%ev: ev-11111111 type=implicit state=evidence-incomplete review=true items=%%\n"
  )
  TODAY = datetime.date(2026, 7, 16)


  def test_block_canonical_text_excises_anchor_and_marker() -> None:
      canonical = state._block_canonical_text_from_text(CONTENT, BLOCK_REF)

      assert canonical == "An implicit synthesis claim."
      assert state._block_text_sha256_from_text(CONTENT, BLOCK_REF) == (
          "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
      )


  def test_block_canonical_text_returns_none_for_unresolvable_ref() -> None:
      assert state._block_canonical_text_from_text(CONTENT, "draft.md#^blk-99999999") is None
  ```

- [ ] Run to verify failure:
  `python -m pytest tests/test_evidence_review_queue.py -v`
  Expected: both tests fail with `AttributeError: module
  'memoria_vault.runtime.state' has no attribute '_block_canonical_text_from_text'`.

- [ ] Write the minimal implementation. In `src/memoria_vault/runtime/state.py`,
  rename `_block_text_sha256_from_text` (line 2705) to
  `_block_canonical_text_from_text` and change only its last two lines — from:

  ```python
      canonical = canonical.strip()
      return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
  ```

  to:

  ```python
      return canonical.strip()
  ```

  Then add directly below it:

  ```python
  def _block_text_sha256_from_text(text: str, block_ref: str) -> str | None:
      canonical = _block_canonical_text_from_text(text, block_ref)
      if canonical is None:
          return None
      return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
  ```

  (Callers — `_block_text_sha256` at state.py:2693 and
  `knowledge.py:2190` — are untouched; hashes are byte-identical.)

- [ ] Run to verify pass:

  ```bash
  python -m pytest tests/test_evidence_review_queue.py tests/test_evidence_sets.py tests/test_draft_verification.py -v
  ```

  Expected: all pass (the two new tests plus the untouched binding/verification
  suites — the refactor is behavior-preserving).

- [ ] Commit:

  ```bash
  git add src/memoria_vault/runtime/state.py tests/test_evidence_review_queue.py tests/conftest.py
  git commit -m "refactor(state): expose canonical block text beneath the block-hash seam

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task V2R-B.2: pure queue assembly over rows + disposition events

The queue function is pure (spec §1's union, one rule per test): PI-clearable holds
without a hold-clearing disposition; **only a digest-matching accept clears**
(spec §4 semantics, owned here independent of the slice-2 verify flip); rejected rows
stay, rendered rejected; deferred rows are suppressed until the next UTC calendar day
(the disposition event's timestamp is the clock); drift/unbound rows are read-only;
srd-gap cards union in behind a reserved facet.

**Files:**
- Create: `src/memoria_vault/runtime/evidence_review.py`
- Modify: `tests/test_evidence_review_queue.py`

**Interfaces:**
- Consumes: `state.read_event_log(vault, *, event_types=None) -> list[dict]`
  (state.py:930; `resolve-evidence-review` events have `event_type == "resolved"`
  and carry `operation`, `evidence_id`, `decision`, `reason`, `timestamp`, and —
  post-S35.4 — `items_sha256`; post-slice-5 optionally `warrant`); `state.db_path`
  (used at state.py:2336); `state._block_canonical_text_from_text` /
  `state._block_text_sha256_from_text` (V2R-B.1); evidence-set row shape from
  `state._evidence_set_row` (state.py:2478: `id`, `block_ref`, `items`, `type`,
  `state`, `review_required`, `run_id`, `block_text_sha256`); the verbatim
  drift/unbound reasons from `verify_project_draft` (knowledge.py:2194-2223).
- Produces (module `memoria_vault.runtime.evidence_review`):
  - `EVIDENCE_REVIEW_ROUTING_TYPES: tuple[str, ...] = ("implicit", "multi-hop",
    "incomplete")`
  - `PERMANENT_BLOCK_CURE: str`
  - `evidence_dispositions(vault: Path) -> list[dict[str, Any]]` — journal-ordered
    `resolve-evidence-review` payloads (latest last).
  - `evidence_minted_at(vault: Path) -> dict[str, str]` — evidence id → first
    `evidence-minted` timestamp (empty pre-S68.3).
  - `assemble_evidence_review_queue(drafts: Iterable[Mapping[str, Any]],
    dispositions: Iterable[Mapping[str, Any]], *, minted_at: Mapping[str, str] |
    None = None, srd_cards: Iterable[Mapping[str, Any]] = (), today:
    datetime.date) -> list[dict[str, Any]]` — **pure**; `drafts` are
    `read_project_draft`-shaped mappings (knowledge.py:2076-2111).
  - `queue_facets(queue: Iterable[Mapping[str, Any]]) -> dict[str, Any]` — honest
    denominators over the full queue (`routing_type`, `project`, reserved `kind`
    incl. `"srd-gap": 0`, `total`).
  - `filter_queue(queue, *, routing_type: str = "", project: str = "",
    min_age_days: int = 0) -> list[dict[str, Any]]` — composing facet filters;
    invalid `routing_type` raises `ValueError`.

**Steps:**

- [ ] **S35.4 coordination grep** (decides one branch below):

  ```bash
  grep -n "_disposed_evidence_digests\|_disposed_evidence_ids" src/memoria_vault/runtime/knowledge.py
  ```

  If `_disposed_evidence_digests` exists, S35.4 has landed: keep `_accept_clears`
  exactly as written below (missing digest = inert, fail closed). If only
  `_disposed_evidence_ids` exists (ids form, pre-S35.4), relax the missing-digest
  branch to `return True` (id-bound accepts, matching shipped verify) and leave the
  in-code NOTE so S35.4's landing restores fail-closed — and flip the expected value
  in `test_queue_accept_without_digest_is_inert` accordingly.

- [ ] Write the failing tests — append to `tests/test_evidence_review_queue.py`
  (extend the import block with `from memoria_vault.runtime import evidence_review`):

  ```python
  def _row(**overrides):
      row = {
          "id": EV_OPEN,
          "block_ref": BLOCK_REF,
          "items": [],
          "type": "implicit",
          "state": "evidence-incomplete",
          "review_required": True,
          "run_id": "",
          "block_text_sha256": state._block_text_sha256_from_text(CONTENT, BLOCK_REF),
      }
      row.update(overrides)
      return row


  def _draft(rows, content=CONTENT):
      return {
          "project_path": "projects/project-alpha/project.md",
          "draft_path": "projects/project-alpha/draft.md",
          "content": content,
          "evidence_sets": rows,
      }


  def _event(decision, *, evidence_id=EV_OPEN, timestamp="2026-07-15T09:00:00Z", **extra):
      return {
          "operation": "resolve-evidence-review",
          "evidence_id": evidence_id,
          "decision": decision,
          "reason": "PI decided",
          "timestamp": timestamp,
          **extra,
      }


  def _queue(rows=None, dispositions=(), *, content=CONTENT, srd_cards=(), minted_at=None):
      drafts = [_draft(rows if rows is not None else [_row()], content)]
      return evidence_review.assemble_evidence_review_queue(
          drafts, dispositions, minted_at=minted_at, srd_cards=srd_cards, today=TODAY
      )


  def test_queue_holds_open_hold_with_claim_text_and_routing() -> None:
      queue = _queue()

      assert len(queue) == 1
      entry = queue[0]
      assert entry["kind"] == "evidence-set"
      assert entry["evidence_id"] == EV_OPEN
      assert entry["claim_text"] == "An implicit synthesis claim."
      assert entry["routing_type"] == "implicit"
      assert entry["holds"] == ["evidence-incomplete", "review-required"]
      assert entry["reviewable"] is True
      assert entry["disposition"] == "open"
      assert entry["age_days"] is None


  def test_queue_clears_hold_on_digest_matching_accept() -> None:
      digest = hashlib.sha256(b"").hexdigest()

      assert _queue(dispositions=[_event("accept", items_sha256=digest)]) == []


  def test_queue_keeps_hold_when_accept_digest_is_stale() -> None:
      stale = hashlib.sha256(b"old-item#^p0001").hexdigest()

      queue = _queue(dispositions=[_event("accept", items_sha256=stale)])

      assert [entry["evidence_id"] for entry in queue] == [EV_OPEN]
      assert queue[0]["disposition"] == "open"


  def test_queue_accept_without_digest_is_inert() -> None:
      # Digests form (Plan 22 S35.4): a legacy accept with no items_sha256 fails
      # closed. Pre-S35.4 checkouts flip this expectation to [] per the grep step.
      queue = _queue(dispositions=[_event("accept")])

      assert [entry["evidence_id"] for entry in queue] == [EV_OPEN]


  def test_queue_keeps_rejected_row_rendered_rejected() -> None:
      queue = _queue(dispositions=[_event("reject")])

      assert len(queue) == 1
      assert queue[0]["disposition"] == "rejected"
      assert queue[0]["disposition_reason"] == "PI decided"
      assert queue[0]["reviewable"] is True


  def test_queue_suppresses_deferred_row_until_next_utc_day() -> None:
      deferred_today = _queue(dispositions=[_event("defer", timestamp="2026-07-16T02:00:00Z")])
      deferred_yesterday = _queue(dispositions=[_event("defer", timestamp="2026-07-15T23:59:59Z")])

      assert deferred_today == []
      assert [entry["evidence_id"] for entry in deferred_yesterday] == [EV_OPEN]
      assert deferred_yesterday[0]["disposition"] == "open"


  def test_queue_latest_disposition_wins() -> None:
      queue = _queue(
          dispositions=[
              _event("defer", timestamp="2026-07-16T01:00:00Z"),
              _event("reject", timestamp="2026-07-16T02:00:00Z"),
          ]
      )

      assert [entry["disposition"] for entry in queue] == ["rejected"]


  def test_queue_renders_drifted_row_read_only_with_reason() -> None:
      drifted = CONTENT.replace("An implicit synthesis claim.", "A silently edited claim.")

      queue = _queue(rows=[_row()], content=drifted)

      assert len(queue) == 1
      entry = queue[0]
      assert entry["reviewable"] is False
      assert entry["blocked_by"] == [
          {
              "kind": "evidence-text-drift",
              "reason": "anchored block text differs from its stored binding",
          }
      ]
      assert entry["holds"] == ["evidence-incomplete", "review-required"]


  def test_queue_renders_unbound_row_read_only() -> None:
      queue = _queue(rows=[_row(block_text_sha256=None)])

      assert queue[0]["reviewable"] is False
      assert queue[0]["blocked_by"] == [
          {"kind": "evidence-text-unbound", "reason": "stored block-text binding is missing"}
      ]


  def test_queue_skips_complete_unflagged_rows() -> None:
      row = _row(state="complete", review_required=False)

      assert _queue(rows=[row]) == []


  def test_queue_appends_srd_gap_cards_and_reserves_facet() -> None:
      card = {"id": "inbox_srd-gap.md", "kind": "card", "attention_kind": "srd-gap"}

      queue = _queue(srd_cards=[card])
      facets = evidence_review.queue_facets(queue)

      assert queue[-1] == {"kind": "srd-gap", "card_block": card}
      assert facets["kind"] == {"evidence-set": 1, "srd-gap": 1}
      assert evidence_review.queue_facets(_queue())["kind"] == {
          "evidence-set": 1,
          "srd-gap": 0,
      }


  def test_queue_age_days_from_minted_timestamp() -> None:
      queue = _queue(minted_at={EV_OPEN: "2026-07-13T10:00:00Z"})

      assert queue[0]["age_days"] == 3


  def test_queue_facets_count_the_full_queue() -> None:
      facets = evidence_review.queue_facets(_queue())

      assert facets == {
          "routing_type": {"implicit": 1},
          "project": {"projects/project-alpha/project.md": 1},
          "kind": {"evidence-set": 1, "srd-gap": 0},
          "total": 1,
      }


  def test_filter_queue_composes_and_validates() -> None:
      import pytest

      queue = _queue(minted_at={EV_OPEN: "2026-07-13T10:00:00Z"})

      assert evidence_review.filter_queue(queue, routing_type="implicit") == queue
      assert evidence_review.filter_queue(queue, routing_type="multi-hop") == []
      assert evidence_review.filter_queue(queue, project="project-alpha") == queue
      assert evidence_review.filter_queue(queue, project="projects/other/project.md") == []
      assert evidence_review.filter_queue(queue, min_age_days=3) == queue
      assert evidence_review.filter_queue(queue, min_age_days=4) == []
      with pytest.raises(ValueError, match="routing_type"):
          evidence_review.filter_queue(queue, routing_type="bogus")
  ```

  (Move `import pytest` to the file's import block when adding it.)

- [ ] Run to verify failure:
  `python -m pytest tests/test_evidence_review_queue.py -v`
  Expected: the two V2R-B.1 tests pass; every new test errors with `ImportError:
  cannot import name 'evidence_review'`.

- [ ] Write the minimal implementation — create
  `src/memoria_vault/runtime/evidence_review.py`:

  ```python
  """Evidence-review queue assembly, facets, and honesty-card blocks (V2 slice 1)."""

  from __future__ import annotations

  import datetime
  import hashlib
  import re
  from collections.abc import Iterable, Mapping
  from pathlib import Path
  from typing import Any

  from memoria_vault.runtime import state
  from memoria_vault.runtime.evidence import (
      evidence_ref_kind,
      parse_code_warrant_ref,
      parse_source_span_ref,
  )
  from memoria_vault.runtime.policy.paths import normalize_path

  EVIDENCE_REVIEW_ROUTING_TYPES = ("implicit", "multi-hop", "incomplete")
  PERMANENT_BLOCK_CURE = (
      "edit the draft or the grounds; no disposition clears a permanent block"
  )


  def evidence_dispositions(vault: Path) -> list[dict[str, Any]]:
      """Read resolve-evidence-review disposition events in journal order."""
      if not state.db_path(Path(vault)).is_file():
          return []
      return [
          event
          for event in state.read_event_log(Path(vault), event_types=["resolved"])
          if event.get("operation") == "resolve-evidence-review"
      ]


  def evidence_minted_at(vault: Path) -> dict[str, str]:
      """Map evidence ids to their first evidence-minted timestamp (plan 22 S68.3)."""
      if not state.db_path(Path(vault)).is_file():
          return {}
      minted: dict[str, str] = {}
      for event in state.read_event_log(Path(vault), event_types=["evidence-minted"]):
          evidence_id = str(event.get("evidence_id") or "")
          timestamp = str(event.get("timestamp") or "")
          if evidence_id and timestamp:
              minted.setdefault(evidence_id, timestamp)
      return minted


  def assemble_evidence_review_queue(
      drafts: Iterable[Mapping[str, Any]],
      dispositions: Iterable[Mapping[str, Any]],
      *,
      minted_at: Mapping[str, str] | None = None,
      srd_cards: Iterable[Mapping[str, Any]] = (),
      today: datetime.date,
  ) -> list[dict[str, Any]]:
      """Assemble the evidence-review queue (spec §1) — pure over its inputs."""
      latest = _latest_dispositions(dispositions)
      minted = dict(minted_at or {})
      queue: list[dict[str, Any]] = []
      for draft in drafts:
          content = str(draft.get("content") or "")
          for row in draft.get("evidence_sets") or []:
              entry = _queue_entry(
                  draft, row, content, latest.get(str(row["id"])), minted, today
              )
              if entry is not None:
                  queue.append(entry)
      queue.extend({"kind": "srd-gap", "card_block": dict(card)} for card in srd_cards)
      return queue


  def queue_facets(queue: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
      """Total counts per facet over the full queue (spec §6 honest denominators)."""
      routing: dict[str, int] = {}
      projects: dict[str, int] = {}
      kinds: dict[str, int] = {"evidence-set": 0, "srd-gap": 0}
      total = 0
      for entry in queue:
          total += 1
          kind = str(entry.get("kind") or "evidence-set")
          kinds[kind] = kinds.get(kind, 0) + 1
          if kind != "evidence-set":
              continue
          routing_type = str(entry.get("routing_type") or "")
          if routing_type:
              routing[routing_type] = routing.get(routing_type, 0) + 1
          project = str(entry.get("project_path") or "")
          if project:
              projects[project] = projects.get(project, 0) + 1
      return {"routing_type": routing, "project": projects, "kind": kinds, "total": total}


  def filter_queue(
      queue: Iterable[Mapping[str, Any]],
      *,
      routing_type: str = "",
      project: str = "",
      min_age_days: int = 0,
  ) -> list[dict[str, Any]]:
      """Apply composing facet filters (spec §6). srd-gap rows show unfiltered only."""
      if routing_type and routing_type not in EVIDENCE_REVIEW_ROUTING_TYPES:
          raise ValueError(
              f"routing_type must be one of {EVIDENCE_REVIEW_ROUTING_TYPES}"
          )
      filtered = bool(routing_type or project or min_age_days)
      selected: list[dict[str, Any]] = []
      for entry in queue:
          if entry.get("kind") != "evidence-set":
              if not filtered:
                  selected.append(dict(entry))
              continue
          if routing_type and entry.get("routing_type") != routing_type:
              continue
          project_path = str(entry.get("project_path") or "")
          if project and project not in {project_path, Path(project_path).parent.name}:
              continue
          if min_age_days and int(entry.get("age_days") or 0) < min_age_days:
              continue
          selected.append(dict(entry))
      return selected


  def _latest_dispositions(
      dispositions: Iterable[Mapping[str, Any]],
  ) -> dict[str, Mapping[str, Any]]:
      latest: dict[str, Mapping[str, Any]] = {}
      for event in dispositions:
          evidence_id = str(event.get("evidence_id") or "")
          if evidence_id:
              latest[evidence_id] = event
      return latest


  def _queue_entry(
      draft: Mapping[str, Any],
      row: Mapping[str, Any],
      content: str,
      disposition: Mapping[str, Any] | None,
      minted: Mapping[str, str],
      today: datetime.date,
  ) -> dict[str, Any] | None:
      blocked_by = _permanent_findings(row, content)
      holds = _hold_findings(row)
      if not blocked_by and not holds:
          return None
      decision = str((disposition or {}).get("decision") or "")
      if decision == "defer" and _defer_active(disposition or {}, today):
          return None
      if decision == "accept" and _accept_clears(row, disposition or {}):
          holds = []
          if not blocked_by:
              return None
      evidence_id = str(row["id"])
      entry: dict[str, Any] = {
          "kind": "evidence-set",
          "evidence_id": evidence_id,
          "project_path": str(draft.get("project_path") or ""),
          "draft_path": str(draft.get("draft_path") or ""),
          "block_ref": str(row["block_ref"]),
          "claim_text": state._block_canonical_text_from_text(
              content, str(row["block_ref"])
          )
          or "",
          "items": [str(item) for item in row.get("items") or []],
          "evidence_type": str(row.get("type") or ""),
          "routing_type": _routing_type(row),
          "holds": [finding["kind"] for finding in holds],
          "blocked_by": blocked_by,
          "reviewable": bool(holds) and not blocked_by,
          "disposition": "rejected" if decision == "reject" else "open",
          "age_days": _age_days(minted.get(evidence_id), today),
      }
      if decision == "reject":
          reason = str((disposition or {}).get("reason") or "").strip()
          if reason:
              entry["disposition_reason"] = reason
      warrant = str((disposition or {}).get("warrant") or "").strip()
      if warrant:
          entry["warrant"] = warrant
      return entry


  def _permanent_findings(row: Mapping[str, Any], content: str) -> list[dict[str, str]]:
      # Reason strings verbatim from verify_project_draft (knowledge.py:2194-2223).
      stored = row.get("block_text_sha256")
      if not stored:
          return [
              {
                  "kind": "evidence-text-unbound",
                  "reason": "stored block-text binding is missing",
              }
          ]
      current = state._block_text_sha256_from_text(content, str(row["block_ref"]))
      if current is None:
          return [
              {
                  "kind": "evidence-text-unbound",
                  "reason": "anchored block text cannot be resolved",
              }
          ]
      if current != stored:
          return [
              {
                  "kind": "evidence-text-drift",
                  "reason": "anchored block text differs from its stored binding",
              }
          ]
      return []


  def _hold_findings(row: Mapping[str, Any]) -> list[dict[str, str]]:
      holds: list[dict[str, str]] = []
      if str(row.get("state") or "") == "evidence-incomplete":
          holds.append({"kind": "evidence-incomplete"})
      if row.get("review_required"):
          holds.append({"kind": "review-required"})
      return holds


  def _routing_type(row: Mapping[str, Any]) -> str:
      evidence_type = str(row.get("type") or "")
      if evidence_type in {"implicit", "multi-hop"}:
          return evidence_type
      if str(row.get("state") or "") == "evidence-incomplete":
          return "incomplete"
      return ""


  def _accept_clears(row: Mapping[str, Any], disposition: Mapping[str, Any]) -> bool:
      # Digests form (Plan 22 S35.4): only an accept bound to the row's current
      # items digest clears; a missing digest (legacy event) is inert — fail
      # closed. NOTE (ids form): on a pre-S35.4 checkout, relax the missing-digest
      # case to `return True` (id-bound accepts, matching shipped verify) and
      # restore fail-closed when S35.4 merges.
      digest = str(disposition.get("items_sha256") or "")
      return bool(digest) and digest == _items_sha256(row.get("items") or [])


  def _items_sha256(items: Iterable[str]) -> str:
      # Same serialized form as the disposition binding (grounds contract §7).
      return hashlib.sha256("|".join(items).encode("utf-8")).hexdigest()


  def _defer_active(disposition: Mapping[str, Any], today: datetime.date) -> bool:
      deferred_on = _event_date(str(disposition.get("timestamp") or ""))
      return deferred_on is not None and today <= deferred_on


  def _age_days(timestamp: str | None, today: datetime.date) -> int | None:
      minted_on = _event_date(str(timestamp or ""))
      if minted_on is None:
          return None
      return max((today - minted_on).days, 0)


  def _event_date(timestamp: str) -> datetime.date | None:
      try:
          return datetime.date.fromisoformat(timestamp[:10])
      except ValueError:
          return None
  ```

  (`re`, `normalize_path`, `evidence_ref_kind`, `parse_code_warrant_ref`, and
  `parse_source_span_ref` are consumed by Task V2R-B.3's additions to this module —
  if the linter flags them as unused at this commit, add them in V2R-B.3 instead.)

- [ ] Run to verify pass: `python -m pytest tests/test_evidence_review_queue.py -v`
  Expected: all pass (2 from V2R-B.1 + 14 new).

- [ ] Commit:

  ```bash
  git add src/memoria_vault/runtime/evidence_review.py tests/test_evidence_review_queue.py
  git commit -m "feat(runtime): pure evidence-review queue assembly with disposition and facet rules

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task V2R-B.3: honesty-card row blocks and grounds-item previews

Spec §2's seven fields as view-spec.v1 blocks, present-only, evidence blocks (1–3)
strictly before the analysis block (4–6), analysis collapsed by default (spec §3),
no verdict and no pre-selected action (field 7).

**Files:**
- Modify: `src/memoria_vault/runtime/evidence_review.py` (append after
  `filter_queue`)
- Modify: `tests/test_evidence_review_queue.py`

**Interfaces:**
- Consumes: `evidence_ref_kind` / `parse_source_span_ref` / `parse_code_warrant_ref`
  (`src/memoria_vault/runtime/evidence.py:64,44,52`); `code_warrant_complete(vault,
  *, run_id, artifact_id, output_sha256) -> bool`
  (`src/memoria_vault/runtime/code/runs.py:26`); `state.catalog_sources(vault,
  checked_only=False)` (used at state.py:2678); the page-anchor scan pattern from
  `state._source_span_pages` (state.py:2676-2686).
- Produces:
  - `span_source_index(vault: Path) -> dict[str, tuple[set[str], str]]` — work_id →
    (resolvable pages, content text).
  - `resolve_item_previews(vault: Path, items: Iterable[str], *, rows_by_id:
    Mapping[str, Mapping[str, Any]], span_sources: Mapping[str, tuple[set[str],
    str]]) -> list[dict[str, Any]]` — the three preview shapes from the payload
    contract above.
  - `evidence_review_blocks(rows: Iterable[Mapping[str, Any]]) -> list[dict[str,
    Any]]` — **pure**; queue entries (optionally carrying `item_previews`) →
    view-spec.v1 blocks; srd-gap entries pass their `card_block` through, after all
    evidence rows.

**Steps:**

- [ ] Write the failing tests — append to `tests/test_evidence_review_queue.py`:

  ```python
  def test_row_blocks_fixed_order_no_verdict_no_action() -> None:
      blocks = evidence_review.evidence_review_blocks(_queue())

      assert [block["kind"] for block in blocks] == ["card", "evidence-list", "text", "card"]
      assert [block["id"] for block in blocks] == [
          EV_OPEN,
          f"{EV_OPEN}-grounds",
          f"{EV_OPEN}-routing",
          f"{EV_OPEN}-analysis",
      ]
      card, grounds, routing, analysis = blocks
      assert card["review_kind"] == "evidence-set"
      assert card["reviewable"] is True
      assert card["disposition"] == "open"
      assert card["item_count"] == 0
      assert card["body_data"] == {
          "kind": "untrusted_text",
          "text": "An implicit synthesis claim.",
      }
      assert grounds["items"] == []
      assert routing["text"] == "implicit"
      assert analysis["collapsed"] is True
      assert analysis["what_tipped_it"] == "type=implicit"
      assert "certainty" not in analysis
      assert all("verdict" not in block for block in blocks)
      assert all(block["kind"] != "action-row" for block in blocks)


  def test_row_blocks_drop_one_sided_arguments() -> None:
      row = dict(_queue()[0])
      row["argument_for"] = "the synthesis is well supported"

      analysis = evidence_review.evidence_review_blocks([row])[-1]

      assert "argument_for" not in analysis
      assert "argument_against" not in analysis

      row["argument_against"] = "the hop chain is long"
      analysis = evidence_review.evidence_review_blocks([row])[-1]
      assert analysis["argument_for"] == "the synthesis is well supported"
      assert analysis["argument_against"] == "the hop chain is long"


  def test_read_only_row_names_cure_and_omits_analysis() -> None:
      drifted = CONTENT.replace("An implicit synthesis claim.", "A silently edited claim.")
      blocks = evidence_review.evidence_review_blocks(_queue(content=drifted))

      assert [block["kind"] for block in blocks] == ["card", "evidence-list", "text"]
      card = blocks[0]
      assert card["reviewable"] is False
      assert card["blocked_by"][0]["kind"] == "evidence-text-drift"
      assert card["cure"] == evidence_review.PERMANENT_BLOCK_CURE
      assert blocks[2]["text"] == "anchored block text differs from its stored binding"


  def test_incomplete_routing_names_the_failing_item() -> None:
      row = dict(
          _queue(
              rows=[_row(type="single-span", items=["source-alpha#^p9999"], review_required=False)]
          )[0]
      )
      row["item_previews"] = [
          {
              "ref": "source-alpha#^p9999",
              "kind": "source-span",
              "work_id": "source-alpha",
              "anchor": "^p9999",
              "resolves": False,
          }
      ]

      blocks = evidence_review.evidence_review_blocks([row])

      assert blocks[2]["text"] == "evidence-incomplete: source-alpha#^p9999 does not resolve"
      assert blocks[3]["what_tipped_it"] == "source-alpha#^p9999"


  def test_srd_gap_card_renders_after_evidence_rows() -> None:
      card = {"id": "inbox_srd-gap.md", "kind": "card", "attention_kind": "srd-gap"}

      blocks = evidence_review.evidence_review_blocks(_queue(srd_cards=[card]))

      assert blocks[-1] == card
      assert blocks[-1]["attention_kind"] == "srd-gap"


  def test_item_previews_resolve_span_nested_and_code(tmp_path) -> None:
      rows_by_id = {
          "ev-22222222": {
              "id": "ev-22222222",
              "type": "implicit",
              "state": "evidence-incomplete",
              "items": [],
          }
      }
      span_sources = {"source-alpha": ({"p0001"}, "source-alpha source span. ^p0001\n")}
      code_ref = "code-warrant:run-1:artifact-1:sha256:" + "0" * 64

      previews = evidence_review.resolve_item_previews(
          tmp_path,
          ["source-alpha#^p0001", "source-alpha#^p9999", "ev-22222222", "ev-33333333", code_ref],
          rows_by_id=rows_by_id,
          span_sources=span_sources,
      )

      assert previews[0] == {
          "ref": "source-alpha#^p0001",
          "kind": "source-span",
          "work_id": "source-alpha",
          "anchor": "^p0001",
          "resolves": True,
          "excerpt": "source-alpha source span.",
      }
      assert previews[1]["resolves"] is False
      assert "excerpt" not in previews[1]
      assert previews[2]["expansion"] == {
          "evidence_type": "implicit",
          "state": "evidence-incomplete",
          "item_count": 0,
      }
      assert previews[3] == {"ref": "ev-33333333", "kind": "evidence-set", "resolves": False}
      assert previews[4]["kind"] == "code-warrant"
      assert previews[4]["run_id"] == "run-1"
      assert previews[4]["resolves"] is False
      assert previews[4]["state"] == "evidence-incomplete"
  ```

  (Add `from pathlib import Path` only if the annotation-free `tmp_path` fixture
  needs it — it does not.)

- [ ] Run to verify failure:
  `python -m pytest tests/test_evidence_review_queue.py -v -k "blocks or previews or routing_names or srd_gap_card"`
  Expected: each new test fails with `AttributeError: module
  'memoria_vault.runtime.evidence_review' has no attribute
  'evidence_review_blocks'` (or `resolve_item_previews`).

- [ ] Write the minimal implementation — append to
  `src/memoria_vault/runtime/evidence_review.py`:

  ```python
  def span_source_index(vault: Path) -> dict[str, tuple[set[str], str]]:
      """Index catalog source content: work_id -> (resolvable pages, text)."""
      index: dict[str, tuple[set[str], str]] = {}
      for source in state.catalog_sources(Path(vault), checked_only=False):
          work_id = str(source["work_id"])
          content_path = Path(vault) / normalize_path(str(source.get("content_path") or ""))
          if not content_path.is_file():
              index[work_id] = (set(), "")
              continue
          text = content_path.read_text(encoding="utf-8")
          pages = {page.removeprefix("^") for page in re.findall(r"\^p\d{4,}", text)}
          index[work_id] = (pages, text)
      return index


  def resolve_item_previews(
      vault: Path,
      items: Iterable[str],
      *,
      rows_by_id: Mapping[str, Mapping[str, Any]],
      span_sources: Mapping[str, tuple[set[str], str]],
  ) -> list[dict[str, Any]]:
      """Resolve grounds items to previews (spec §2 field 2), present-only."""
      previews: list[dict[str, Any]] = []
      for item in items:
          kind = evidence_ref_kind(item)
          if kind == "code-warrant":
              ref = parse_code_warrant_ref(item)
              resolves = _code_warrant_resolves(vault, ref)
              previews.append(
                  {
                      "ref": item,
                      "kind": kind,
                      "run_id": ref.run_id,
                      "artifact_id": ref.artifact_id,
                      "output_sha256": ref.output_sha256,
                      "resolves": resolves,
                      "state": "complete" if resolves else "evidence-incomplete",
                  }
              )
          elif kind == "evidence-set":
              nested = rows_by_id.get(item)
              preview: dict[str, Any] = {
                  "ref": item,
                  "kind": kind,
                  "resolves": nested is not None,
              }
              if nested is not None:
                  preview["expansion"] = {
                      "evidence_type": str(nested.get("type") or ""),
                      "state": str(nested.get("state") or ""),
                      "item_count": len(nested.get("items") or []),
                  }
              previews.append(preview)
          else:
              span = parse_source_span_ref(item)
              pages, text = span_sources.get(span.work_id, (set(), ""))
              preview = {
                  "ref": item,
                  "kind": kind,
                  "work_id": span.work_id,
                  "anchor": f"^{span.page}",
                  "resolves": span.page in pages,
              }
              excerpt = _span_excerpt(text, span.page)
              if excerpt:
                  preview["excerpt"] = excerpt
              previews.append(preview)
      return previews


  def evidence_review_blocks(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
      """Queue entries -> view-spec.v1 blocks; evidence rows first, srd-gap cards last."""
      blocks: list[dict[str, Any]] = []
      srd_blocks: list[dict[str, Any]] = []
      for row in rows:
          if row.get("kind") == "srd-gap":
              srd_blocks.append(dict(row["card_block"]))
              continue
          blocks.extend(_row_blocks(row))
      return blocks + srd_blocks


  def _row_blocks(row: Mapping[str, Any]) -> list[dict[str, Any]]:
      evidence_id = str(row["evidence_id"])
      previews = list(row.get("item_previews") or [])
      card: dict[str, Any] = {
          "id": evidence_id,
          "kind": "card",
          "ref": str(row["block_ref"]),
          "review_kind": "evidence-set",
          "evidence_id": evidence_id,
          "project": str(row["project_path"]),
          "routing_type": str(row["routing_type"]),
          "reviewable": bool(row["reviewable"]),
          "disposition": str(row["disposition"]),
          "item_count": len(row["items"]),
          "age_days": row["age_days"],
          "body_data": {"kind": "untrusted_text", "text": str(row["claim_text"])},
      }
      if row.get("blocked_by"):
          card["blocked_by"] = [dict(finding) for finding in row["blocked_by"]]
          card["cure"] = PERMANENT_BLOCK_CURE
      for field in ("disposition_reason", "warrant"):
          value = str(row.get(field) or "").strip()
          if value:
              card[field] = value
      grounds = {
          "id": f"{evidence_id}-grounds",
          "kind": "evidence-list",
          "ref": str(row["block_ref"]),
          "items": previews,
      }
      routing = {
          "id": f"{evidence_id}-routing",
          "kind": "text",
          "text": _routing_reason(row, previews),
      }
      blocks = [card, grounds, routing]
      if row.get("holds"):
          blocks.append(_analysis_block(row, previews))
      return blocks


  def _analysis_block(
      row: Mapping[str, Any], previews: list[dict[str, Any]]
  ) -> dict[str, Any]:
      # Spec §2 fields 4-6, collapsed by default (spec §3 independence-first).
      analysis: dict[str, Any] = {
          "id": f"{row['evidence_id']}-analysis",
          "kind": "card",
          "ref": str(row["block_ref"]),
          "collapsed": True,
          "what_tipped_it": _tipping_factor(row, previews),
      }
      arguments = {
          field: str(row.get(field) or "").strip()
          for field in ("argument_for", "argument_against")
      }
      if all(arguments.values()):  # never one-sided (spec §2 field 4)
          analysis.update(arguments)
      certainty = str(row.get("certainty") or "").strip()
      if certainty:
          analysis["certainty"] = certainty
      return analysis


  def _routing_reason(row: Mapping[str, Any], previews: list[dict[str, Any]]) -> str:
      routing_type = str(row.get("routing_type") or "")
      if routing_type in {"implicit", "multi-hop"}:
          return routing_type
      if routing_type == "incomplete":
          failing = _first_failing(previews)
          if failing is not None:
              return f"evidence-incomplete: {failing['ref']} does not resolve"
          return "evidence-incomplete"
      blocked = list(row.get("blocked_by") or [])
      return str(blocked[0]["reason"]) if blocked else ""


  def _tipping_factor(row: Mapping[str, Any], previews: list[dict[str, Any]]) -> str:
      routing_type = str(row.get("routing_type") or "")
      if routing_type in {"implicit", "multi-hop"}:
          return f"type={row['evidence_type']}"
      failing = _first_failing(previews)
      return str(failing["ref"]) if failing is not None else "state=evidence-incomplete"


  def _first_failing(previews: list[dict[str, Any]]) -> dict[str, Any] | None:
      return next((preview for preview in previews if not preview.get("resolves")), None)


  def _code_warrant_resolves(vault: Path, ref: Any) -> bool:
      from memoria_vault.runtime.code.runs import code_warrant_complete

      return code_warrant_complete(
          Path(vault),
          run_id=ref.run_id,
          artifact_id=ref.artifact_id,
          output_sha256=ref.output_sha256,
      )


  def _span_excerpt(text: str, page: str, *, limit: int = 240) -> str:
      for line in text.splitlines():
          if f"^{page}" in line:
              cleaned = re.sub(r"\s*\^p\d{4,}\s*", " ", line).strip()
              return cleaned[:limit]
      return ""
  ```

- [ ] Run to verify pass: `python -m pytest tests/test_evidence_review_queue.py -v`
  Expected: all pass.

- [ ] Commit:

  ```bash
  git add src/memoria_vault/runtime/evidence_review.py tests/test_evidence_review_queue.py
  git commit -m "feat(runtime): honesty-card row blocks with grounds previews and collapsed analysis

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task V2R-B.4: `read_evidence_review_view` — the engine collector

Wires the pure machinery to a workspace: enumerate checked projects, read drafts
(read-only — no rebuild, no context), load dispositions and minted timestamps, union
srd-gap attention cards, facet/filter/batch, resolve previews for the shown rows
only, and wrap in the binding view envelope.

**Files:**
- Create: `tests/test_evidence_review_view.py`
- Modify: `src/memoria_vault/engine/api.py` (imports lines 9-25; public function
  after `read_attention_view` — added by U3-ENG.1 after `read_attention_card`,
  api.py:155-164; private helpers after `_attention_in_scope`, api.py:709-712)
- Modify: `tests/conftest.py` (TEST_LEVELS — insert below the V2R-B.1 line; nearest
  siblings `test_attention_view.py` (U3-ENG.1) and `test_http_transport.py` (line
  62) are both `"contract"`)

**Interfaces:**
- Consumes: `evidence_review.*` (V2R-B.2/.3); `_read_project_draft` (api.py:13,
  aliasing knowledge.py:2076 — raises `ValueError` for unchecked project
  frontmatter); `_read_payload` (api.py:410); `_view` (api.py:715); `_scope_allows`
  (api.py:598); `_attention_cards` (api.py:679); `_attention_in_scope` (api.py:709);
  `_attention_view_card_block` (U3-ENG.1); `read_frontmatter` (api.py:21);
  `state.evidence_sets` (state.py:2335); `append_explicit_journal_event`
  (`src/memoria_vault/runtime/trusted_writer.py:215`, tests only);
  `compose_project_draft` / `verify_project_draft` via `tests/helpers.py`
  `call_with_context` (helpers.py:71), `write_checked_concept` (helpers.py:283).
- Produces: **`engine_api.read_evidence_review_view(workspace: Path, *,
  routing_type: str = "", project: str = "", min_age_days: int = 0, batch: int = 10,
  read_scope: list[str] | None = None) -> dict[str, Any]`** returning the payload
  contract above (`{ok, api_version, view: {version, kind: "evidence-review",
  blocks}, facets}`).

**Steps:**

- [ ] Register the new test file. In `tests/conftest.py`, directly below
  `    "test_evidence_review_queue.py": "unit",` insert:

  ```python
      "test_evidence_review_view.py": "contract",
  ```

- [ ] Write the failing tests — create `tests/test_evidence_review_view.py`:

  ```python
  """Contract tests for the /v1/views/evidence-review engine view (V2 slice 1)."""

  from __future__ import annotations

  import hashlib
  import json
  import threading
  import urllib.error
  import urllib.request
  from http import HTTPStatus
  from pathlib import Path

  import pytest

  from memoria_vault.engine import api
  from memoria_vault.runtime import state
  from memoria_vault.runtime.http_transport import _dispatch, make_http_server
  from memoria_vault.runtime.knowledge import compose_project_draft as _compose
  from memoria_vault.runtime.knowledge import verify_project_draft as _verify
  from memoria_vault.runtime.trusted_writer import append_explicit_journal_event
  from tests.helpers import call_with_context, write_checked_concept

  NOTE_IDS = {
      "thesis": "01ARZ3NDEKTSV4RRFFQ69G5FA1",
      "support": "01ARZ3NDEKTSV4RRFFQ69G5FA2",
      "grounded": "01ARZ3NDEKTSV4RRFFQ69G5FA3",
      "dangling": "01ARZ3NDEKTSV4RRFFQ69G5FA4",
  }


  def _project(vault: Path, name: str = "project-alpha") -> None:
      write_checked_concept(
          vault,
          f"projects/{name}/project.md",
          f"type: project\ncheck_status: checked\ntitle: {name}\n",
          "project",
      )


  def _note(vault: Path, stem: str, note_id: str, body: str) -> None:
      write_checked_concept(
          vault,
          f"notes/{stem}.md",
          f"type: note\ncheck_status: checked\ntitle: {stem}\nid: {note_id}\n",
          "note",
          body=body,
      )


  def _outline(vault: Path, content: str, name: str = "project-alpha") -> None:
      path = vault / f"projects/{name}/outline.md"
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text(content, encoding="utf-8")


  def _seed_implicit(vault: Path, name: str = "project-alpha") -> str:
      _project(vault, name)
      _note(vault, f"{name}-thesis", NOTE_IDS["thesis"], "An implicit synthesis claim.")
      _outline(vault, f"- {NOTE_IDS['thesis']} — Thesis\n", name)
      composed = call_with_context(_compose, vault, name)
      return composed["evidence_markers"][0]["id"]


  def _retarget_marker_items(vault: Path, evidence_id: str, items: str) -> None:
      draft = vault / "projects/project-alpha/draft.md"
      tail = f"%%ev: {evidence_id} type=implicit state=evidence-incomplete review=true items=%%"
      replacement = (
          f"%%ev: {evidence_id} type=implicit state=evidence-incomplete "
          f"review=true items={items}%%"
      )
      text = draft.read_text(encoding="utf-8")
      assert tail in text
      draft.write_text(text.replace(tail, replacement), encoding="utf-8")


  def _seed_matrix(vault: Path) -> dict[str, str]:
      """One implicit, one multi-hop, one drifted (read-only), one incomplete row."""
      state.upsert_catalog_record(
          vault,
          work_id="source-alpha",
          title="Alpha Source",
          check_status="checked",
          content_path=".memoria/blobs/source-content/source-alpha.md",
      )
      content = vault / ".memoria/blobs/source-content/source-alpha.md"
      content.parent.mkdir(parents=True, exist_ok=True)
      content.write_text("source-alpha source span. ^p0001\n", encoding="utf-8")
      _project(vault)
      _note(vault, "thesis", NOTE_IDS["thesis"], "An implicit synthesis claim.")
      _note(vault, "support", NOTE_IDS["support"], "A dependent multi-hop claim.")
      _note(vault, "grounded", NOTE_IDS["grounded"], "A complete source-backed claim.")
      _note(vault, "dangling", NOTE_IDS["dangling"], "A claim over a missing span.")
      _outline(
          vault,
          "".join(f"- {note_id} — block\n" for note_id in NOTE_IDS.values()),
      )
      composed = call_with_context(_compose, vault, "project-alpha")
      by_ref = {
          marker["id"]: marker for marker in composed["evidence_markers"]
      }
      draft_text = (vault / "projects/project-alpha/draft.md").read_text(encoding="utf-8")
      ordered = sorted(by_ref, key=draft_text.index)
      ids = dict(zip(("implicit", "multi_hop", "drift", "incomplete"), ordered, strict=True))
      _retarget_marker_items(vault, ids["multi_hop"], ids["implicit"])
      _retarget_marker_items(vault, ids["drift"], "source-alpha#^p0001")
      _retarget_marker_items(vault, ids["incomplete"], "source-alpha#^p9999")
      call_with_context(_verify, vault, "project-alpha")  # rebuild rows from markers
      draft = vault / "projects/project-alpha/draft.md"
      draft.write_text(
          draft.read_text(encoding="utf-8").replace(
              "A complete source-backed claim.",
              "A complete source-backed claim, silently edited.",
          ),
          encoding="utf-8",
      )
      return ids


  def _disposition(vault: Path, evidence_id: str, decision: str, **extra) -> None:
      append_explicit_journal_event(
          vault,
          {
              "event": "resolved",
              "operation": "resolve-evidence-review",
              "evidence_id": evidence_id,
              "decision": decision,
              "reason": "PI decided",
              **extra,
          },
          actor="pi",
          machine="test-machine",
      )


  def _accept_digest(items: tuple[str, ...] = ()) -> str:
      return hashlib.sha256("|".join(items).encode("utf-8")).hexdigest()


  def _cards(payload: dict) -> dict[str, dict]:
      return {
          block["evidence_id"]: block
          for block in payload["view"]["blocks"]
          if block["kind"] == "card" and "evidence_id" in block
      }


  def test_view_serves_implicit_hold_with_honesty_blocks(tmp_path: Path) -> None:
      _seed_implicit(tmp_path)

      payload = api.read_evidence_review_view(tmp_path)

      assert payload["ok"] is True
      assert payload["api_version"] == api.READ_API_VERSION
      view = payload["view"]
      assert view["version"] == "view-spec.v1"
      assert view["kind"] == "evidence-review"
      assert [block["kind"] for block in view["blocks"]] == [
          "card",
          "evidence-list",
          "text",
          "card",
      ]
      card, _grounds, routing, analysis = view["blocks"]
      assert card["reviewable"] is True
      assert card["routing_type"] == "implicit"
      assert card["disposition"] == "open"
      assert card["age_days"] is None
      assert card["body_data"]["kind"] == "untrusted_text"
      assert "An implicit synthesis claim." in card["body_data"]["text"]
      assert routing["text"] == "implicit"
      assert analysis["collapsed"] is True
      assert all("verdict" not in block for block in view["blocks"])
      assert all(block["kind"] != "action-row" for block in view["blocks"])
      assert {block["kind"] for block in view["blocks"]} <= set(api.VIEW_BLOCK_KINDS)
      assert payload["facets"] == {
          "routing_type": {"implicit": 1},
          "project": {"projects/project-alpha/project.md": 1},
          "kind": {"evidence-set": 1, "srd-gap": 0},
          "total": 1,
          "shown": 1,
          "batch": 10,
      }


  def test_view_routes_matrix_and_renders_drift_read_only(tmp_path: Path) -> None:
      ids = _seed_matrix(tmp_path)

      payload = api.read_evidence_review_view(tmp_path)

      cards = _cards(payload)
      assert set(cards) == set(ids.values())
      assert cards[ids["implicit"]]["routing_type"] == "implicit"
      assert cards[ids["multi_hop"]]["routing_type"] == "multi-hop"
      assert cards[ids["incomplete"]]["routing_type"] == "incomplete"
      drift = cards[ids["drift"]]
      assert drift["reviewable"] is False
      assert drift["blocked_by"][0]["kind"] == "evidence-text-drift"
      assert "cure" in drift
      blocks_by_id = {block["id"]: block for block in payload["view"]["blocks"]}
      assert f"{ids['drift']}-analysis" not in blocks_by_id
      hop_items = blocks_by_id[f"{ids['multi_hop']}-grounds"]["items"]
      assert hop_items[0]["kind"] == "evidence-set"
      assert hop_items[0]["resolves"] is True
      assert hop_items[0]["expansion"]["evidence_type"] == "implicit"
      drift_items = blocks_by_id[f"{ids['drift']}-grounds"]["items"]
      assert drift_items[0]["excerpt"] == "source-alpha source span."
      assert blocks_by_id[f"{ids['incomplete']}-routing"]["text"] == (
          "evidence-incomplete: source-alpha#^p9999 does not resolve"
      )
      assert payload["facets"]["routing_type"] == {
          "implicit": 1,
          "multi-hop": 1,
          "incomplete": 1,
      }
      assert payload["facets"]["total"] == 4


  def test_view_applies_disposition_rules(tmp_path: Path) -> None:
      evidence_id = _seed_implicit(tmp_path)

      _disposition(tmp_path, evidence_id, "reject")
      rejected = api.read_evidence_review_view(tmp_path)
      assert _cards(rejected)[evidence_id]["disposition"] == "rejected"
      assert _cards(rejected)[evidence_id]["disposition_reason"] == "PI decided"

      _disposition(tmp_path, evidence_id, "accept", items_sha256=_accept_digest())
      accepted = api.read_evidence_review_view(tmp_path)
      assert accepted["view"]["blocks"] == []
      assert accepted["facets"]["total"] == 0

      _disposition(
          tmp_path,
          evidence_id,
          "accept",
          items_sha256=_accept_digest(("source-alpha#^p0001",)),
      )
      voided = api.read_evidence_review_view(tmp_path)
      assert evidence_id in _cards(voided)

      _disposition(tmp_path, evidence_id, "defer")
      deferred = api.read_evidence_review_view(tmp_path)
      assert deferred["view"]["blocks"] == []
      assert deferred["facets"]["total"] == 0


  def test_view_filters_compose_with_honest_denominators(tmp_path: Path) -> None:
      _seed_matrix(tmp_path)

      hops = api.read_evidence_review_view(tmp_path, routing_type="multi-hop")
      assert hops["facets"]["total"] == 4  # denominators stay whole-queue
      assert hops["facets"]["shown"] == 1
      assert [card["routing_type"] for card in _cards(hops).values()] == ["multi-hop"]

      other = api.read_evidence_review_view(tmp_path, project="project-beta")
      assert other["facets"]["shown"] == 0
      assert other["facets"]["total"] == 4

      batched = api.read_evidence_review_view(tmp_path, batch=1)
      assert batched["facets"]["shown"] == 1
      assert batched["facets"]["batch"] == 1

      with pytest.raises(ValueError, match="routing_type"):
          api.read_evidence_review_view(tmp_path, routing_type="bogus")


  def test_view_reserves_and_renders_srd_gap_cards(tmp_path: Path) -> None:
      _seed_implicit(tmp_path)
      card_path = tmp_path / "inbox" / "srd-gap-check.md"
      card_path.parent.mkdir(parents=True, exist_ok=True)
      card_path.write_text(
          "---\n"
          "projection: attention\n"
          "title: SRD gap on thesis\n"
          "attention_kind: srd-gap\n"
          "attention_status: open\n"
          "routing_class: ask\n"
          "---\n"
          "C1 found a systematic-review-discipline gap.\n",
          encoding="utf-8",
      )

      payload = api.read_evidence_review_view(tmp_path)

      last = payload["view"]["blocks"][-1]
      assert last["kind"] == "card"
      assert last["attention_kind"] == "srd-gap"
      assert payload["facets"]["kind"] == {"evidence-set": 1, "srd-gap": 1}


  def test_view_respects_read_scope(tmp_path: Path) -> None:
      _seed_implicit(tmp_path)

      scoped = api.read_evidence_review_view(tmp_path, read_scope=["notes/other.md"])

      assert scoped["view"]["blocks"] == []
      assert scoped["facets"]["total"] == 0
  ```

- [ ] Run to verify failure:
  `python -m pytest tests/test_evidence_review_view.py -v`
  Expected: all tests fail with `AttributeError: module 'memoria_vault.engine.api'
  has no attribute 'read_evidence_review_view'`.

- [ ] Write the minimal implementation in `src/memoria_vault/engine/api.py`.

  Add to the imports (after `from memoria_vault.runtime import state`, line 10;
  `import datetime` already exists via U3-ENG.1):

  ```python
  from memoria_vault.runtime import evidence_review
  ```

  After `read_attention_view`'s return (U3-ENG.1, following `read_attention_card`
  at api.py:155-164) add:

  ```python
  def read_evidence_review_view(
      workspace: Path,
      *,
      routing_type: str = "",
      project: str = "",
      min_age_days: int = 0,
      batch: int = 10,
      read_scope: list[str] | None = None,
  ) -> dict[str, Any]:
      workspace = Path(workspace)
      drafts = [
          draft
          for draft in _evidence_review_drafts(workspace)
          if _scope_allows(draft["draft_path"], read_scope)
      ]
      srd_cards = [
          _attention_view_card_block(card)
          for card in _attention_cards(workspace)
          if card["kind"] == "srd-gap"
          and card["status"] == "open"
          and _attention_in_scope(card, read_scope)
      ]
      queue = evidence_review.assemble_evidence_review_queue(
          drafts,
          evidence_review.evidence_dispositions(workspace),
          minted_at=evidence_review.evidence_minted_at(workspace),
          srd_cards=srd_cards,
          today=datetime.datetime.now(datetime.timezone.utc).date(),
      )
      facets = evidence_review.queue_facets(queue)
      selected = evidence_review.filter_queue(
          queue, routing_type=routing_type, project=project, min_age_days=min_age_days
      )
      batch = max(1, int(batch))
      shown = selected[:batch]
      _attach_item_previews(workspace, shown)
      facets.update({"shown": len(shown), "batch": batch})
      return _read_payload(
          view=_view("evidence-review", evidence_review.evidence_review_blocks(shown)),
          facets=facets,
      )
  ```

  After `_attention_in_scope` (api.py:709-712; below the U3-ENG.1 helper block) add:

  ```python
  def _evidence_review_drafts(workspace: Path) -> list[dict[str, Any]]:
      drafts = []
      for rel in sorted(_evidence_review_project_rels(workspace)):
          try:
              drafts.append(_read_project_draft(workspace, rel))
          except ValueError:
              continue  # unchecked project frontmatter is not consumable by reads
      return drafts


  def _evidence_review_project_rels(workspace: Path) -> set[str]:
      projects_dir = workspace / "projects"
      if not projects_dir.is_dir():
          return set()
      return {
          path.relative_to(workspace).as_posix()
          for path in [*projects_dir.glob("*.md"), *projects_dir.glob("*/project.md")]
          if read_frontmatter(path).get("type") == "project"
      }


  def _attach_item_previews(workspace: Path, rows: list[dict[str, Any]]) -> None:
      evidence_rows = [row for row in rows if row.get("kind") == "evidence-set"]
      if not evidence_rows:
          return
      rows_by_id = {str(row["id"]): row for row in state.evidence_sets(workspace)}
      span_sources = evidence_review.span_source_index(workspace)
      for row in evidence_rows:
          row["item_previews"] = evidence_review.resolve_item_previews(
              workspace,
              row["items"],
              rows_by_id=rows_by_id,
              span_sources=span_sources,
          )
  ```

- [ ] Run to verify pass: `python -m pytest tests/test_evidence_review_view.py -v`
  Expected: 7 passed.

- [ ] Commit:

  ```bash
  git add src/memoria_vault/engine/api.py tests/test_evidence_review_view.py tests/conftest.py
  git commit -m "feat(engine): read_evidence_review_view with faceted queue and honesty-card blocks

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task V2R-B.5: register `GET /v1/views/evidence-review` and prove it through the real HTTP server

Mirrors U3-ENG.4's registration (surface action → `_read` branch → floor ARG_TABLE)
and U3-ENG.6's real-server auth proof.

**Files:**
- Modify: `src/memoria_vault/engine/surface_contract.py` (insert after the
  `views.attention` action added by U3-ENG.4, which sits after `attention.get`,
  lines 104-115)
- Modify: `src/memoria_vault/runtime/http_transport.py` (`_read`, after the
  `/v1/views/attention` branch added by U3-ENG.4 following `/attention/card`,
  lines 161-164)
- Modify: `tests/test_surface_contract.py` (expected-id set lines 16-34; http_routes
  set lines 43-60 — both shifted by one U3-ENG.4 entry)
- Modify: `tests/floor_lib.py` (ARG_TABLE, after the `views.attention` entry added
  by U3-ENG.4 following `attention.get` at lines 1187-1191)
- Modify: `tests/test_evidence_review_view.py`

**Interfaces:**
- Consumes: `HTTP_ROUTES = http_routes()` route gate (`http_transport.py:21,115`);
  `_one` / `_int_query` (`http_transport.py:224,240` — `_int_query` returns the
  default when the param is absent and rejects non-positive explicit values, so
  `min_age_days=0` means "no age filter, omit the param"); `make_http_server`
  (`http_transport.py:29`); `is_authorized` (`http_transport.py:100`).
- Produces: surface action id **`views.evidence_review`** (engine
  `read_evidence_review_view`, kind `read`, scope `optional-read-scope`, params
  `routing_type`/`project` (string, default "") + `min_age_days` (integer, default
  0) + `batch` (integer, default 10), http `GET /v1/views/evidence-review`,
  response_version `engine-read-api.v1`, **no cli/mcp bindings** — the CLI front is
  slice 4); HTTP route `("GET", "/v1/views/evidence-review")`; floor ARG_TABLE entry
  `"views.evidence_review": {"cli": None, "http": ("GET",
  "/v1/views/evidence-review"), "mcp": None}`.

**Steps:**

- [ ] Write the failing tests — append to `tests/test_evidence_review_view.py`:

  ```python
  def test_http_dispatch_serves_evidence_review_view(tmp_path: Path) -> None:
      _seed_matrix(tmp_path)

      full, full_status = _dispatch(tmp_path, "GET", "/v1/views/evidence-review", dict)
      filtered, filtered_status = _dispatch(
          tmp_path,
          "GET",
          "/v1/views/evidence-review?routing_type=multi-hop&batch=5",
          dict,
      )
      invalid, invalid_status = _dispatch(
          tmp_path, "GET", "/v1/views/evidence-review?routing_type=bogus", dict
      )

      assert full_status == HTTPStatus.OK
      assert full["view"]["kind"] == "evidence-review"
      assert full["view"]["version"] == "view-spec.v1"
      assert full["facets"]["total"] == 4
      assert filtered_status == HTTPStatus.OK
      assert filtered["facets"]["shown"] == 1
      assert filtered["facets"]["total"] == 4
      assert invalid_status == HTTPStatus.BAD_REQUEST
      assert invalid["ok"] is False


  def test_http_dispatch_rejects_wrong_method_for_evidence_review(tmp_path: Path) -> None:
      response, status = _dispatch(tmp_path, "POST", "/v1/views/evidence-review", dict)

      assert status == HTTPStatus.METHOD_NOT_ALLOWED
      assert response == {"ok": False, "error": "method not allowed"}


  def test_evidence_review_view_requires_bearer_token(tmp_path: Path) -> None:
      _seed_implicit(tmp_path)
      server = make_http_server(tmp_path, host="127.0.0.1", port=0, token="test-token")
      thread = threading.Thread(target=server.serve_forever, daemon=True)
      thread.start()
      try:
          url = f"http://127.0.0.1:{server.server_address[1]}/v1/views/evidence-review"
          with pytest.raises(urllib.error.HTTPError) as denied:
              urllib.request.urlopen(url)
          assert denied.value.code == HTTPStatus.UNAUTHORIZED
          request = urllib.request.Request(
              url, headers={"Authorization": "Bearer test-token"}
          )
          with urllib.request.urlopen(request) as response:
              payload = json.loads(response.read().decode("utf-8"))
          assert payload["ok"] is True
          assert payload["view"]["kind"] == "evidence-review"
          assert [block["kind"] for block in payload["view"]["blocks"]] == [
              "card",
              "evidence-list",
              "text",
              "card",
          ]
      finally:
          server.shutdown()
          server.server_close()
          thread.join(timeout=5)
  ```

  Also update `tests/test_surface_contract.py`: add `"views.evidence_review",` to
  the `expected` set (after the `"views.attention",` line U3-ENG.4 added below
  `"attention.get",`) and `("GET", "/v1/views/evidence-review"),` to the
  `http_routes()` set (after U3-ENG.4's `("GET", "/v1/views/attention"),`).

- [ ] Run to verify failure:

  ```bash
  python -m pytest tests/test_evidence_review_view.py::test_http_dispatch_serves_evidence_review_view tests/test_evidence_review_view.py::test_http_dispatch_rejects_wrong_method_for_evidence_review tests/test_evidence_review_view.py::test_evidence_review_view_requires_bearer_token tests/test_surface_contract.py -v
  ```

  Expected: the dispatch tests fail with status `HTTPStatus.NOT_FOUND` (route not
  registered); the bearer test fails on the authorized request (404 body);
  `test_surface_contract` fails on the added registry entries.

- [ ] Write the minimal implementation.

  In `src/memoria_vault/engine/surface_contract.py`, insert after the
  `views.attention` action dict (U3-ENG.4):

  ```python
      {
          "id": "views.evidence_review",
          "summary": "Render the evidence-review queue view.",
          "engine": "read_evidence_review_view",
          "kind": "read",
          "scope": "optional-read-scope",
          "params": {
              "routing_type": {"type": "string", "default": ""},
              "project": {"type": "string", "default": ""},
              "min_age_days": {"type": "integer", "default": 0},
              "batch": {"type": "integer", "default": 10},
          },
          "http": {"method": "GET", "path": "/v1/views/evidence-review"},
          "response_version": ENGINE_READ_API_VERSION,
      },
  ```

  In `src/memoria_vault/runtime/http_transport.py` `_read`, after the
  `/v1/views/attention` branch (U3-ENG.4):

  ```python
      if path == "/v1/views/evidence-review":
          return engine_api.read_evidence_review_view(
              workspace,
              routing_type=_one(query, "routing_type"),
              project=_one(query, "project"),
              min_age_days=_int_query(query, "min_age_days", 0),
              batch=_int_query(query, "batch", 10),
              read_scope=read_scope,
          )
  ```

  In `tests/floor_lib.py` ARG_TABLE, after the `views.attention` entry (U3-ENG.4):

  ```python
      # No cli/mcp binding: views.evidence_review is HTTP-only in slice 1; the
      # CLI front (memoria review) is V2 slice 4 and registers its own binding.
      "views.evidence_review": {
          "cli": None,
          "http": ("GET", "/v1/views/evidence-review"),
          "mcp": None,
      },
  ```

- [ ] Run to verify pass:

  ```bash
  python -m pytest tests/test_evidence_review_view.py tests/test_evidence_review_queue.py \
      tests/test_surface_contract.py tests/test_http_transport.py tests/test_floor_coverage.py -v
  python -m pytest tests/test_floor_sweep_reads.py -k "views" -v
  ```

  Expected: all pass — `test_http_transport_openapi_covers_registry_http_routes`
  picks the new route up from the registry (its four params plus
  `read_scope`/`scope` appear in the OpenAPI doc automatically), and the floor read
  sweep exercises the action over http only (cli/mcp skip as undeclared, the
  ARG_TABLE None convention).

- [ ] Run the full gate and confirm clean before finishing the section:

  ```bash
  python scripts/verify
  ```

  Expected: pass — no journal events were added or reshaped, so floor goldens are
  untouched (no regeneration step exists in this section by design).

- [ ] Commit:

  ```bash
  git add src/memoria_vault/engine/surface_contract.py \
      src/memoria_vault/runtime/http_transport.py \
      tests/test_surface_contract.py tests/floor_lib.py tests/test_evidence_review_view.py
  git commit -m "feat(http): serve GET /v1/views/evidence-review with facets and honest denominators

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```
# V2R-C — `memoria review` CLI cockpit + telemetry

Section of the V2 evidence-review implementation plan. Repo: `/home/eranr/memoria-vault`
(main @ a525a81a). Governing spec: §1 (CLI front), §3 (evidence-first/independence-first),
§4 instrumentation paragraph, §6 (batch and filter), §8 (keep-test acceptance) of
`docs/superpowers/specs/2026-07-16-v2-evidence-review-design.md` — slices 4 and 6.

## SPEC GAPs (one-liners; decided minimally here, flag at review)

- SPEC GAP: no paging beyond `--batch` — the spec names batch 10 and facets only, so facet
  narrowing *is* the paging mechanism; `--batch 0` (all rows) exists for internal row lookup.
- SPEC GAP: `disposition.recorded` requires a `reason_code` from the closed `REASON_CODES`
  enum (`empirical_events.py:46-60`) whose vocabulary was written for suggestion triage;
  the CLI defaults to `"other"` with an optional `--reason-code` choice — no enum change.
- SPEC GAP: no session concept exists (I1 skeleton, out-of-scope list); `session_id` here is
  one CLI process invocation (`uuid4().hex`), so `items_per_session` ≈ 1 until a real session
  concept lands — the stats payload reports it anyway because the empirical plan pre-registered it.
- SPEC GAP: the spec's slice 6 names the metrics but no reading surface; `memoria review stats`
  is added as the minimal honest reader (drop to function-only if the PI objects).

## Named event schema — decision (task instruction: "pick honestly")

**Ride `empirical_event.v1` + the existing journal events. No `review-telemetry.v1`.**
The I1 vocabulary already contains everything this slice needs: `workflow="evidence-review"`
is in `WORKFLOWS` (`engine/empirical_events.py:17-31`), event types `view.opened` and
`disposition.recorded` exist (`:65-74`), `DECISIONS` already holds all four actions (`:32`),
and `duration_s`/`item_type`/`item_id` are allowed fields (`:75-90`). The I1 skeleton design
(`docs/superpowers/specs/2026-07-14-i1-skeleton-design.md`) deliberately splits **client**
telemetry (`empirical_event.v1`, honest `session_id`/`surface`) from **server** truth
(`disposition.v1`, emitted at the seam) and reconciles them by `request_id` — the CLI *is* a
client (`surface="cli"` is in `SURFACES`), so it emits the client events; the seam (V2R-A)
emits the server event. A new schema would duplicate three enum tables to say nothing new.
Skip rate and reopen rate are **derived** metrics (a skip is the *absence* of an event; a
reopen is a *pattern* over the stream) — they are computed deterministically from the
journal by `review_telemetry_summary`, never synthesized as fake point-in-time events.

## Cross-section interface contract (MUST reconcile at plan assembly)

V2R-C consumes these exact signatures. **Execution order: V2R-A → V2R-B → V2R-C**
(and Plan 22 S35.4 before V2R-A — see the grep gate in V2R-C.5).

1. **From V2R-B (slice 1), consumed directly — engine call, no HTTP (spec §8 keep-test):**

   ```python
   engine_api.evidence_review_queue(
       workspace: Path,
       *,
       routing_type: str = "",      # "" | "implicit" | "multi-hop" | "incomplete"
       project: str = "",           # project rel-path filter, e.g. "projects/project-alpha"
       max_age_days: int | None = None,
       batch: int = 10,             # batch <= 0 returns all rows
   ) -> dict[str, Any]
   ```

   returning `{"ok": True, "rows": [...], "total": <int, pre-batch row count>,
   "facet_totals": {"routing_type": {<value>: <count>}, "project": {<rel>: <count>}}}`,
   each row carrying at least: `evidence_id` (`ev-<8hex>`), `claim_text` (bound block,
   verbatim), `items` (list of `{"ref": str, "preview": str, ...}`), `item_count`,
   `routing` (`implicit|multi-hop|incomplete`), `routing_reason` (derivation rule /
   failing-item reason, verbatim), `reviewable` (bool; `False` = permanent-block cure row),
   `cure` (str, `""` when reviewable), `project`, `age_days` (`int | None`),
   `latest_decision` (`"" | accept|reject|edit|defer` — rejected rows render rejected,
   spec §4), `warrant` (str, from the latest accept disposition, spec §1.3), and
   `analysis` (`None`, or `{"argument_for","argument_against","tipped_by","certainty"}`
   both-or-neither, spec §2 fields 4–6).

2. **From V2R-A (slice 2):** `resolve_evidence_review(vault: Path, evidence_id: str, *,
   actor: str, machine: str, decision: str, reason: str = "", warrant: str = "") ->
   dict[str, Any]` (`runtime/knowledge.py:2268-2297` today, accept/reject only —
   V2R-A extends the `knowledge.py:2284` guard to the four decisions and `cli.py:332`
   choices with it) — journals `operation="resolve-evidence-review"` events carrying
   `evidence_id`, `decision`, `reason`, `items_sha256` (S35.4), `warrant` (accept only;
   raises `ValueError` when warrant text rides a non-accept decision), raises
   `ValueError("unknown evidence id: …")` for ids with no evidence-set record (S35.4),
   and emits one `disposition.v1` event per action via `emit_disposition_event`
   (`runtime/operations.py:146` — the resolve-attention helper, reused for this seam)
   with `item_type="evidence-set"`, `item_id=ev-<8hex>`.

3. **From Plan 22 S35.4** (`docs/superpowers/plans/2026-07-15-alpha22-substrate-trust.md`):
   `_disposed_evidence_ids` (`knowledge.py:3241-3251` on main) is REPLACED by
   `_disposed_evidence_digests(vault: Path) -> dict[str, str]` plus
   `_evidence_items_sha256(items: Iterable[str]) -> str`. V2R-C.5 (accept-voided reopens)
   is written against the **digests** form and gates on a grep (step 1 there).

4. **U3 view machinery is NOT consumed.** `GET /v1/views/evidence-review`,
   `VIEW_BLOCK_KINDS`, and the pane are U3-ENG/U3-PLUG products
   (`docs/superpowers/plans/2026-07-15-surfaces-bootstrap-and-plugins.md:6421-7226`) plus
   V2R-B's endpoint slice; the CLI front reads the queue rows directly, which is exactly
   the spec §8 keep-test ("no server, direct engine calls"). No ordering dependency on U3.

## Produces (what later sections may consume)

- CLI verbs: `memoria review list|show|accept|reject|edit|defer|stats` (all `_common`-flagged:
  `--workspace/--json/--quiet/--idempotency-key/--schedule-id/--actor`).
- `knowledge.review_dwell_seconds(vault: Path, evidence_id: str) -> float | None`
- `knowledge.review_telemetry_summary(vault: Path) -> dict[str, Any]` with keys
  `sessions, shows, items_shown, items_per_session, actions{accept,reject,edit,defer},
  disposed_items, dwell_s{count,mean,median}, skip_rate,
  reopens{defer_then_disposed,accept_voided}, reopen_rate`.
- Journal facts: `memoria review show` appends one `empirical_event.v1` `view.opened`
  (workflow `evidence-review`, item_type `evidence-set`); each action appends one
  `disposition.recorded` client event (decision, `reason_code`, `duration_s` when dwell ≥ 1 s)
  **in addition to** the seam's `resolved` + `disposition.v1` events.

## Golden-regeneration note

**No floor-golden regeneration.** No new operation id is introduced (telemetry rides the
existing `empirical-event-record` operation, `runtime/worker.py:340-355`); no recorded
floor flow changes; all new journal events come from new CLI verbs the floor does not
exercise. The only pinned-surface change is the exact CLI-command set
(`tests/test_cli.py:73-146`), updated explicitly per task below.

---

### Task V2R-C.1: `memoria review list` — faceted evidence-summary rows (batch 10)

**Files:**
- Create: `tests/test_cli_review.py`
- Modify: `src/memoria_vault/cli.py` (registration block lines 131–143: insert
  `_review_commands(sub)` after `_operation_commands(sub)` line 138; new
  `_review_commands` after `_attention_commands` which ends at line 421; handlers after
  `_cmd_attention_worklist` which ends at line 1647)
- Modify: `tests/conftest.py` (TEST_LEVELS dict starting line 18; nearest siblings
  `test_cli*.py` are all `"contract"`)
- Modify: `tests/test_cli.py` (exact command-surface set, lines 73–146)

**Interfaces:**
- Consumes: `engine_api.evidence_review_queue(workspace, *, routing_type="", project="",
  max_age_days=None, batch=10) -> dict[str, Any]` (V2R-B, contract item 1);
  `_common(parser)` (`cli.py:560`), `_workspace(args) -> Path` (`cli.py:2130`),
  `_emit(payload, args) -> int` (`cli.py:3092`); test fixtures
  `write_checked_concept`/`call_with_context`/`init_git` (`tests/helpers.py:283,71`,
  import pattern per `tests/test_empirical_events.py:18-23`) and
  `knowledge.compose_project_draft` (`runtime/knowledge.py:1965`).
- Produces: `memoria review list --workspace W [--type implicit|multi-hop|incomplete]
  [--project P] [--max-age-days N] [--batch N] [--json|--quiet]`; handler
  `_cmd_review_list(args) -> int`; helpers `_review_summary_row(row) -> dict`,
  `_truncate(text, width=60) -> str`. JSON payload:
  `{"ok": True, "rows": [<summary rows>], "total": int, "batch": int, "facet_totals": {...}}`
  where summary rows carry ONLY `evidence_id, claim_text, item_count, routing,
  routing_reason, reviewable, cure, project, age_days, latest_decision, warrant` —
  `analysis` is stripped (spec §3: "analysis never appears in list rows").

**Steps:**

- [ ] Register the test file. In `tests/conftest.py`, below the line
  `    "test_cli_workspace_requests.py": "contract",` (line 29) insert:

  ```python
      "test_cli_review.py": "contract",
  ```

- [ ] Write the failing tests. Create `tests/test_cli_review.py`:

  ```python
  from __future__ import annotations

  import json
  from pathlib import Path

  import pytest

  from memoria_vault.cli import main
  from memoria_vault.runtime import state
  from memoria_vault.runtime.knowledge import compose_project_draft as _compose_project_draft
  from tests.helpers import call_with_context, init_git, write_checked_concept

  NOTE_IDS = ("01ARZ3NDEKTSV4RRFFQ69G5FA1", "01ARZ3NDEKTSV4RRFFQ69G5FA2")


  def _vault(tmp_path: Path) -> Path:
      init_git(tmp_path, "review@example.invalid", "Review CLI")
      return tmp_path


  def _implicit_project(vault: Path, *, notes: int = 1) -> list[str]:
      """Compose a draft with ``notes`` implicit (reviewable) evidence sets."""
      write_checked_concept(
          vault,
          "projects/project-alpha/project.md",
          "type: project\ncheck_status: checked\ntitle: Alpha project\n",
          "project",
      )
      outline_lines = []
      for index in range(notes):
          note_id = NOTE_IDS[index]
          write_checked_concept(
              vault,
              f"notes/claim-{index}.md",
              f"type: note\ncheck_status: checked\ntitle: Claim {index}\nid: {note_id}\n",
              "note",
              body=f"Implicit claim {index} needs review.",
          )
          outline_lines.append(f"- {note_id} — Claim {index}\n")
      outline = vault / "projects/project-alpha/outline.md"
      outline.parent.mkdir(parents=True, exist_ok=True)
      outline.write_text("".join(outline_lines), encoding="utf-8")
      result = call_with_context(_compose_project_draft, vault, "project-alpha")
      return [str(marker["id"]) for marker in result["evidence_markers"]]


  def test_review_list_renders_evidence_summary_rows_only(
      tmp_path: Path, capsys: pytest.CaptureFixture[str]
  ) -> None:
      vault = _vault(tmp_path)
      (evidence_id,) = _implicit_project(vault)

      rc = main(["review", "list", "--workspace", str(vault), "--json"])
      payload = json.loads(capsys.readouterr().out)

      assert rc == 0
      assert payload["ok"] is True
      assert payload["batch"] == 10
      assert payload["total"] == 1
      (row,) = payload["rows"]
      assert row["evidence_id"] == evidence_id
      assert row["routing"] == "implicit"
      assert row["item_count"] == 0
      assert "Implicit claim 0" in row["claim_text"]
      assert row["routing_reason"]
      assert "analysis" not in row  # spec §3: never in list rows
      assert "items" not in row  # summary rows: claim + item count + routing reason


  def test_review_list_type_facet_mirrors_queue_params(
      tmp_path: Path, capsys: pytest.CaptureFixture[str]
  ) -> None:
      vault = _vault(tmp_path)
      _implicit_project(vault)

      rc = main(
          ["review", "list", "--workspace", str(vault), "--type", "multi-hop", "--json"]
      )
      payload = json.loads(capsys.readouterr().out)

      assert rc == 0
      assert payload["rows"] == []
      assert payload["total"] == 0
      assert payload["facet_totals"]["routing_type"].get("implicit") == 1


  def test_review_list_batch_caps_rows_with_honest_total(
      tmp_path: Path, capsys: pytest.CaptureFixture[str]
  ) -> None:
      vault = _vault(tmp_path)
      _implicit_project(vault, notes=2)

      rc = main(["review", "list", "--workspace", str(vault), "--batch", "1", "--json"])
      payload = json.loads(capsys.readouterr().out)

      assert rc == 0
      assert len(payload["rows"]) == 1
      assert payload["total"] == 2
      assert payload["batch"] == 1


  def test_review_list_human_rows_are_one_line_summaries(
      tmp_path: Path, capsys: pytest.CaptureFixture[str]
  ) -> None:
      vault = _vault(tmp_path)
      (evidence_id,) = _implicit_project(vault)

      rc = main(["review", "list", "--workspace", str(vault)])
      out = capsys.readouterr().out

      assert rc == 0
      assert evidence_id in out
      assert "implicit" in out
      assert "1 of 1 row(s) shown (batch 10)" in out
      assert "argument" not in out.lower()  # no machine analysis in list mode
  ```

- [ ] Run to verify failure:

  ```
  python -m pytest tests/test_cli_review.py -v
  ```

  Expected: all 4 tests error with `SystemExit: 2` (argparse: `invalid choice: 'review'`).

- [ ] Minimal implementation in `src/memoria_vault/cli.py`.

  (a) In `_build_parser`, after `    _operation_commands(sub)` (line 138) insert:

  ```python
      _review_commands(sub)
  ```

  (b) After `_attention_commands` (ends line 421; before `_operation_commands`, line 424)
  add:

  ```python
  def _review_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
      review = sub.add_parser("review")
      review_sub = review.add_subparsers(dest="review_command", required=True)
      list_cmd = review_sub.add_parser("list")
      _common(list_cmd)
      list_cmd.add_argument(
          "--type", choices=("implicit", "multi-hop", "incomplete"), default=""
      )
      list_cmd.add_argument("--project", default="")
      list_cmd.add_argument("--max-age-days", type=int, default=None)
      list_cmd.add_argument("--batch", type=int, default=10)
      list_cmd.set_defaults(handler=_cmd_review_list)
  ```

  (c) After `_cmd_attention_worklist` (ends line 1647) add:

  ```python
  _REVIEW_SUMMARY_FIELDS = (
      "evidence_id",
      "claim_text",
      "item_count",
      "routing",
      "routing_reason",
      "reviewable",
      "cure",
      "project",
      "age_days",
      "latest_decision",
      "warrant",
  )


  def _review_summary_row(row: dict[str, Any]) -> dict[str, Any]:
      """Evidence-summary projection: claim + item count + routing reason (spec §3)."""
      return {key: row[key] for key in _REVIEW_SUMMARY_FIELDS if key in row}


  def _truncate(text: str, width: int = 60) -> str:
      text = " ".join(str(text).split())
      return text if len(text) <= width else text[: width - 1] + "…"


  def _cmd_review_list(args: argparse.Namespace) -> int:
      queue = engine_api.evidence_review_queue(
          _workspace(args),
          routing_type=args.type,
          project=args.project,
          max_age_days=args.max_age_days,
          batch=args.batch,
      )
      rows = [_review_summary_row(row) for row in queue["rows"]]
      payload = {
          "ok": True,
          "rows": rows,
          "total": queue["total"],
          "batch": args.batch,
          "facet_totals": queue["facet_totals"],
      }
      if args.json or args.quiet:
          return _emit(payload, args)
      for row in rows:
          marker = ""
          if not row.get("reviewable", True):
              marker = f"  [read-only: {row.get('cure', '')}]"
          elif row.get("latest_decision"):
              marker = f"  [{row['latest_decision']}]"
          print(
              f"{row['evidence_id']}  {row['routing']:<9}  "
              f"{row['item_count']} item(s)  {_truncate(row['claim_text'])}"
              f"  — {row['routing_reason']}{marker}"
          )
      print(f"{len(rows)} of {queue['total']} row(s) shown (batch {args.batch})")
      return 0
  ```

- [ ] In `tests/test_cli.py` `test_cli_command_surface_is_exact` (line 73), add to the set
  (after `"memoria attention worklist",` line 122):

  ```python
          "memoria review list",
  ```

- [ ] Run to verify pass:

  ```
  python -m pytest tests/test_cli_review.py tests/test_cli.py -v
  ```

  Expected: all pass.

- [ ] Commit:

  ```
  git add src/memoria_vault/cli.py tests/test_cli_review.py tests/conftest.py tests/test_cli.py
  git commit -m "feat(cli): memoria review list — faceted evidence-summary rows (V2R-C.1)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task V2R-C.2: `memoria review show <ev-id>` — evidence-first detail, `--show-analysis` fold, `view.opened` emission

**Files:**
- Modify: `src/memoria_vault/cli.py` (`_review_commands` from V2R-C.1; handlers block
  after `_cmd_review_list`)
- Modify: `tests/test_cli_review.py` (append), `tests/test_cli.py` (surface set)

**Interfaces:**
- Consumes: `engine_api.evidence_review_queue(..., batch=0)` (all rows, contract item 1);
  `engine_api.run_operation(workspace, operation_id, payload, *, actor, idempotency_key=…,
  command=…) -> dict` (`engine/api.py:414-426`) driving the `empirical-event-record`
  operation (`runtime/worker.py:340-355` — requires
  `idempotency_key == f"empirical-event:{event_id}"`; `runtime/operations.py:111`
  validates via `validate_empirical_event`, `engine/empirical_events.py:104`);
  `now_iso()` (`runtime/time.py:17`); `state.read_event_log(vault, event_types=…)`
  (`runtime/state.py:930`) in tests; `_fail(message, *, json_output)` (`cli.py:3234`).
- Produces: `memoria review show <evidence_id> --workspace W [--show-analysis]
  [--json|--quiet]`; handler `_cmd_review_show(args) -> int`; helpers
  `_review_queue_row(workspace, evidence_id) -> dict | None`,
  `_emit_review_view_opened(args, workspace, evidence_id) -> dict`. Render order is
  structural (spec §3): claim → grounds items → routing, THEN (only under
  `--show-analysis`) the machine analysis; without the flag the `analysis` key is absent
  from the JSON row and the human output prints the fold hint. One `view.opened`
  `empirical_event.v1` event per show (`surface="cli"`, `workflow="evidence-review"`,
  `item_type="evidence-set"`, `item_id=<ev-id>`, per-invocation `session_id`).

**Steps:**

- [ ] Write the failing tests. Append to `tests/test_cli_review.py`:

  ```python
  def test_review_show_is_evidence_first_with_analysis_folded(
      tmp_path: Path, capsys: pytest.CaptureFixture[str]
  ) -> None:
      vault = _vault(tmp_path)
      (evidence_id,) = _implicit_project(vault)

      rc = main(["review", "show", evidence_id, "--workspace", str(vault), "--json"])
      payload = json.loads(capsys.readouterr().out)

      assert rc == 0
      assert payload["ok"] is True
      assert payload["row"]["evidence_id"] == evidence_id
      assert "analysis" not in payload["row"]  # folded by default (spec §3)

      rc = main(
          [
              "review",
              "show",
              evidence_id,
              "--workspace",
              str(vault),
              "--show-analysis",
              "--json",
          ]
      )
      payload = json.loads(capsys.readouterr().out)
      assert rc == 0
      assert "analysis" in payload["row"]  # key present; None until analysis exists


  def test_review_show_human_output_orders_evidence_before_analysis(
      tmp_path: Path, capsys: pytest.CaptureFixture[str]
  ) -> None:
      vault = _vault(tmp_path)
      (evidence_id,) = _implicit_project(vault)

      rc = main(
          ["review", "show", evidence_id, "--workspace", str(vault), "--show-analysis"]
      )
      out = capsys.readouterr().out

      assert rc == 0
      assert out.index("Claim") < out.index("Grounds items")
      assert out.index("Grounds items") < out.index("Why routed")
      assert out.index("Why routed") < out.index("Machine analysis")

      rc = main(["review", "show", evidence_id, "--workspace", str(vault)])
      out = capsys.readouterr().out
      assert rc == 0
      assert "Machine analysis folded" in out


  def test_review_show_emits_view_opened_event(
      tmp_path: Path, capsys: pytest.CaptureFixture[str]
  ) -> None:
      vault = _vault(tmp_path)
      (evidence_id,) = _implicit_project(vault)

      rc = main(["review", "show", evidence_id, "--workspace", str(vault), "--json"])
      capsys.readouterr()

      assert rc == 0
      opened = [
          event
          for event in state.read_event_log(vault, event_types=["empirical-event"])
          if event.get("event_type") == "view.opened"
      ]
      assert len(opened) == 1
      assert opened[0]["workflow"] == "evidence-review"
      assert opened[0]["surface"] == "cli"
      assert opened[0]["item_type"] == "evidence-set"
      assert opened[0]["item_id"] == evidence_id
      assert opened[0]["session_id"]


  def test_review_show_unknown_id_fails_without_telemetry(
      tmp_path: Path, capsys: pytest.CaptureFixture[str]
  ) -> None:
      vault = _vault(tmp_path)
      _implicit_project(vault)

      rc = main(["review", "show", "ev-deadbeef", "--workspace", str(vault), "--json"])
      payload = json.loads(capsys.readouterr().out)

      assert rc == 2
      assert payload["ok"] is False
      assert "ev-deadbeef" in payload["error"]
      assert state.read_event_log(vault, event_types=["empirical-event"]) == []
  ```

- [ ] Run to verify failure:

  ```
  python -m pytest tests/test_cli_review.py -v -k review_show
  ```

  Expected: 4 errors with `SystemExit: 2` (argparse: `invalid choice: 'show'`).

- [ ] Minimal implementation in `src/memoria_vault/cli.py`.

  (a) In `_review_commands`, after the `list_cmd.set_defaults(...)` line add:

  ```python
      show = review_sub.add_parser("show")
      _common(show)
      show.add_argument("evidence_id")
      show.add_argument("--show-analysis", action="store_true")
      show.set_defaults(handler=_cmd_review_show)
  ```

  (b) After `_cmd_review_list` add:

  ```python
  def _review_queue_row(workspace: Path, evidence_id: str) -> dict[str, Any] | None:
      queue = engine_api.evidence_review_queue(workspace, batch=0)
      return next(
          (row for row in queue["rows"] if row["evidence_id"] == evidence_id), None
      )


  def _emit_review_view_opened(
      args: argparse.Namespace, workspace: Path, evidence_id: str
  ) -> dict[str, Any]:
      from memoria_vault.runtime.time import now_iso

      event = {
          "event_id": str(uuid.uuid4()),
          "event_type": "view.opened",
          "timestamp": now_iso(),
          "session_id": uuid.uuid4().hex,
          "surface": "cli",
          "workflow": "evidence-review",
          "item_type": "evidence-set",
          "item_id": evidence_id,
      }
      result = engine_api.run_operation(
          workspace,
          "empirical-event-record",
          event,
          idempotency_key=f"empirical-event:{event['event_id']}",
          actor=args.actor,
          command="review-show",
      )
      return {"ok": bool(result.get("ok")), "event_id": event["event_id"]}


  def _cmd_review_show(args: argparse.Namespace) -> int:
      workspace = _workspace(args)
      row = _review_queue_row(workspace, args.evidence_id)
      if row is None:
          return _fail(
              f"evidence id is not in the review queue: {args.evidence_id}",
              json_output=args.json,
          )
      telemetry = _emit_review_view_opened(args, workspace, args.evidence_id)
      shown = dict(row)
      analysis = shown.pop("analysis", None)
      if args.show_analysis:
          shown["analysis"] = analysis
      payload = {"ok": True, "row": shown, "telemetry": telemetry}
      if args.json or args.quiet:
          return _emit(payload, args)
      print(f"Claim ({shown['evidence_id']}, {shown['routing']}):")
      print(f"  {shown['claim_text']}")
      print(f"Grounds items ({shown['item_count']}):")
      for item in shown.get("items", []):
          print(f"  - {item.get('ref', '')}  {item.get('preview', '')}".rstrip())
      print(f"Why routed: {shown['routing_reason']}")
      if shown.get("latest_decision"):
          print(f"Latest decision: {shown['latest_decision']}")
      if shown.get("warrant"):
          print(f"Warrant: {shown['warrant']}")
      if args.show_analysis:
          print("Machine analysis:")
          if analysis:
              for key in ("argument_for", "argument_against", "tipped_by", "certainty"):
                  print(f"  {key.replace('_', ' ')}: {analysis.get(key, '')}")
          else:
              print("  (none recorded)")
      else:
          print("Machine analysis folded — pass --show-analysis to expand.")
      return 0
  ```

  (`uuid` is already imported at `cli.py:14`; `engine_api` at `cli.py:24`.)

- [ ] In `tests/test_cli.py`, add `"memoria review show",` to the exact set beside
  `"memoria review list",`.

- [ ] Run to verify pass:

  ```
  python -m pytest tests/test_cli_review.py tests/test_cli.py -v
  ```

  Expected: all pass.

- [ ] Commit:

  ```
  git add src/memoria_vault/cli.py tests/test_cli_review.py tests/test_cli.py
  git commit -m "feat(cli): memoria review show — evidence-first detail with --show-analysis fold (V2R-C.2)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task V2R-C.3: action subcommands accept/reject/edit/defer — V2R-A seam + dwell-carrying `disposition.recorded`

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py` (imports lines 5–18; new
  `review_dwell_seconds` immediately after `_disposed_evidence_digests` — the S35.4
  replacement of `_disposed_evidence_ids`, lines 3241–3251 on main; locate by name)
- Modify: `src/memoria_vault/cli.py` (`_review_commands`; handlers after
  `_cmd_review_show`)
- Modify: `tests/test_cli_review.py` (append), `tests/test_cli.py` (surface set)

**Interfaces:**
- Consumes: `resolve_evidence_review(vault, evidence_id, *, actor, machine, decision,
  reason="", warrant="") -> dict` (V2R-A, contract item 2); `_require_pi_actor(args,
  action)` (`cli.py:1298-1300`); `REASON_CODES` (`engine/empirical_events.py:46-60`);
  `state.connect`/`state.db_path` (`runtime/state.py:472`, used as in
  `state.evidence_sets`, `:2335-2347`); `parse_iso` (`runtime/time.py:22`);
  `engine_api.run_operation` + `empirical-event-record` as in V2R-C.2. The existing
  `memoria project resolve-evidence` (`cli.py:1120-1157`, choices at `cli.py:332`) stays
  untouched here — V2R-A extends its choices; `memoria review <action>` is the cockpit
  front on the same seam.
- Produces: `memoria review accept <ev-id> [--warrant TEXT] [--reason R]
  [--reason-code C]`, `memoria review reject|edit|defer <ev-id> [--reason R]
  [--reason-code C]`; handler `_cmd_review_action(args) -> int` (shared, dispatched via
  `args.review_decision`); helper `_emit_review_disposition_recorded(args, workspace,
  dwell) -> dict`; **`knowledge.review_dwell_seconds(vault: Path, evidence_id: str) ->
  float | None`** — seconds from the latest journaled `view.opened` for that item to now,
  `None` when never shown or dwell ≤ 0 (journal timestamps are whole-second,
  `runtime/time.py:8-14`). Each action journals the seam event (V2R-A emits
  `disposition.v1` inside it) plus one client `disposition.recorded` with `duration_s`
  only when dwell ≥ 1 s — never a fabricated zero.

**Steps:**

- [ ] Write the failing tests. Append to `tests/test_cli_review.py` (extend the
  imports at top of file with `import uuid`, `from datetime import UTC, datetime,
  timedelta`, `from memoria_vault.engine import api as engine_api`, and
  `from memoria_vault.runtime.time import utc_z`):

  ```python
  def _seam_events(vault: Path) -> list[dict]:
      return [
          event
          for event in state.read_event_log(vault, event_types=["resolved"])
          if event.get("operation") == "resolve-evidence-review"
      ]


  def _client_dispositions(vault: Path) -> list[dict]:
      return [
          event
          for event in state.read_event_log(vault, event_types=["empirical-event"])
          if event.get("event_type") == "disposition.recorded"
      ]


  def _emit_backdated_view_opened(vault: Path, item_id: str, *, seconds_ago: int) -> None:
      event = {
          "event_id": str(uuid.uuid4()),
          "event_type": "view.opened",
          "timestamp": utc_z(datetime.now(UTC) - timedelta(seconds=seconds_ago)),
          "session_id": "session-backdated",
          "surface": "cli",
          "workflow": "evidence-review",
          "item_type": "evidence-set",
          "item_id": item_id,
      }
      result = engine_api.run_operation(
          vault,
          "empirical-event-record",
          event,
          idempotency_key=f"empirical-event:{event['event_id']}",
          actor="pi",
          machine="test-machine",
      )
      assert result["ok"] is True


  @pytest.mark.parametrize("decision", ["accept", "reject", "edit", "defer"])
  def test_review_action_drives_seam_and_emits_client_disposition(
      tmp_path: Path, capsys: pytest.CaptureFixture[str], decision: str
  ) -> None:
      vault = _vault(tmp_path)
      (evidence_id,) = _implicit_project(vault)

      rc = main(["review", decision, evidence_id, "--workspace", str(vault), "--json"])
      payload = json.loads(capsys.readouterr().out)

      assert rc == 0
      assert payload["ok"] is True
      assert payload["decision"] == decision
      (seam,) = _seam_events(vault)
      assert seam["evidence_id"] == evidence_id
      assert seam["decision"] == decision
      (client,) = _client_dispositions(vault)
      assert client["decision"] == decision
      assert client["workflow"] == "evidence-review"
      assert client["item_id"] == evidence_id
      assert client["reason_code"] == "other"
      assert "duration_s" not in client  # never shown — no fabricated dwell


  def test_review_accept_records_warrant_on_disposition(
      tmp_path: Path, capsys: pytest.CaptureFixture[str]
  ) -> None:
      vault = _vault(tmp_path)
      (evidence_id,) = _implicit_project(vault)
      warrant = "Institutional cost data warrants this synthesis."

      rc = main(
          [
              "review",
              "accept",
              evidence_id,
              "--workspace",
              str(vault),
              "--warrant",
              warrant,
              "--reason",
              "PI accepted",
              "--json",
          ]
      )
      payload = json.loads(capsys.readouterr().out)

      assert rc == 0
      assert payload["ok"] is True
      (seam,) = _seam_events(vault)
      assert seam["decision"] == "accept"
      assert seam["warrant"] == warrant


  def test_review_action_dwell_rides_disposition_recorded(
      tmp_path: Path, capsys: pytest.CaptureFixture[str]
  ) -> None:
      vault = _vault(tmp_path)
      (evidence_id,) = _implicit_project(vault)
      _emit_backdated_view_opened(vault, evidence_id, seconds_ago=90)

      rc = main(["review", "defer", evidence_id, "--workspace", str(vault), "--json"])
      payload = json.loads(capsys.readouterr().out)

      assert rc == 0
      (client,) = _client_dispositions(vault)
      assert 89 <= client["duration_s"] <= 180
      assert payload["telemetry"]["duration_s"] == client["duration_s"]


  def test_review_action_requires_pi_actor(
      tmp_path: Path, capsys: pytest.CaptureFixture[str]
  ) -> None:
      vault = _vault(tmp_path)
      (evidence_id,) = _implicit_project(vault)

      rc = main(
          [
              "review",
              "accept",
              evidence_id,
              "--workspace",
              str(vault),
              "--actor",
              "agent",
              "--json",
          ]
      )
      payload = json.loads(capsys.readouterr().out)

      assert rc == 2
      assert payload["ok"] is False
      assert _seam_events(vault) == []
  ```

- [ ] Run to verify failure:

  ```
  python -m pytest tests/test_cli_review.py -v -k "review_action or records_warrant"
  ```

  Expected: 7 errors with `SystemExit: 2` (argparse: `invalid choice: 'accept'` etc.).

- [ ] Minimal implementation, part 1 — `src/memoria_vault/runtime/knowledge.py`.

  (a) Change the datetime import (line 14 area, currently `from datetime import date`) to:

  ```python
  from datetime import UTC, date, datetime
  ```

  and add beneath the runtime imports (after
  `from memoria_vault.runtime.read_barrier import is_consumable_checked_file`):

  ```python
  from memoria_vault.runtime.time import parse_iso
  ```

  (b) Immediately after `_disposed_evidence_digests` (S35.4's replacement of
  `_disposed_evidence_ids`, `knowledge.py:3241-3251` on main; locate by name) add:

  ```python
  def review_dwell_seconds(vault: Path, evidence_id: str) -> float | None:
      """Seconds from the latest evidence-review detail-open to now (spec §4)."""
      if not state.db_path(vault).is_file():
          return None
      with state.connect(vault) as conn:
          row = conn.execute(
              """
              SELECT json_extract(payload_json, '$.timestamp') AS opened_at
              FROM event_log
              WHERE event_type = 'empirical-event'
                AND json_extract(payload_json, '$.event_type') = 'view.opened'
                AND json_extract(payload_json, '$.workflow') = 'evidence-review'
                AND json_extract(payload_json, '$.item_id') = ?
              ORDER BY event_id DESC
              LIMIT 1
              """,
              (evidence_id,),
          ).fetchone()
      if row is None or not row["opened_at"]:
          return None
      opened = parse_iso(str(row["opened_at"]))
      if opened is None or opened.tzinfo is None:
          return None
      dwell = (datetime.now(UTC) - opened).total_seconds()
      return dwell if dwell > 0 else None
  ```

- [ ] Minimal implementation, part 2 — `src/memoria_vault/cli.py`.

  (a) In `_review_commands`, after the `show.set_defaults(...)` line add:

  ```python
      from memoria_vault.engine.empirical_events import REASON_CODES

      for decision in ("accept", "reject", "edit", "defer"):
          action = review_sub.add_parser(decision)
          _common(action)
          action.add_argument("evidence_id")
          action.add_argument("--reason", default="")
          action.add_argument("--reason-code", choices=sorted(REASON_CODES), default="other")
          if decision == "accept":
              action.add_argument("--warrant", default="")
          action.set_defaults(handler=_cmd_review_action, review_decision=decision)
  ```

  (b) After `_cmd_review_show` add:

  ```python
  def _emit_review_disposition_recorded(
      args: argparse.Namespace, workspace: Path, dwell: float | None
  ) -> dict[str, Any]:
      from memoria_vault.runtime.time import now_iso

      event: dict[str, Any] = {
          "event_id": str(uuid.uuid4()),
          "event_type": "disposition.recorded",
          "timestamp": now_iso(),
          "session_id": uuid.uuid4().hex,
          "surface": "cli",
          "workflow": "evidence-review",
          "decision": args.review_decision,
          "reason_code": args.reason_code,
          "item_type": "evidence-set",
          "item_id": args.evidence_id,
      }
      if dwell is not None and dwell >= 1.0:
          event["duration_s"] = round(dwell, 1)
      result = engine_api.run_operation(
          workspace,
          "empirical-event-record",
          event,
          idempotency_key=f"empirical-event:{event['event_id']}",
          actor=args.actor,
          command=f"review-{args.review_decision}",
      )
      return {
          "ok": bool(result.get("ok")),
          "event_id": event["event_id"],
          "duration_s": event.get("duration_s"),
      }


  def _cmd_review_action(args: argparse.Namespace) -> int:
      from memoria_vault.runtime.knowledge import (
          resolve_evidence_review,
          review_dwell_seconds,
      )

      _require_pi_actor(args, f"review-{args.review_decision}")
      workspace = _workspace(args)
      dwell = review_dwell_seconds(workspace, args.evidence_id)
      event = resolve_evidence_review(
          workspace,
          args.evidence_id,
          decision=args.review_decision,
          reason=args.reason,
          warrant=getattr(args, "warrant", ""),
          actor=args.actor,
          machine="memoria-cli",
      )
      telemetry = _emit_review_disposition_recorded(args, workspace, dwell)
      return _emit(
          {
              "ok": True,
              "evidence_id": args.evidence_id,
              "decision": args.review_decision,
              "event": event,
              "telemetry": telemetry,
          },
          args,
      )
  ```

- [ ] In `tests/test_cli.py`, add to the exact set beside `"memoria review show",`:

  ```python
          "memoria review accept",
          "memoria review reject",
          "memoria review edit",
          "memoria review defer",
  ```

- [ ] Run to verify pass:

  ```
  python -m pytest tests/test_cli_review.py tests/test_cli.py tests/test_draft_verification.py -v
  ```

  Expected: all pass (`test_draft_verification.py` proves the seam contract is untouched).

- [ ] Commit:

  ```
  git add src/memoria_vault/cli.py src/memoria_vault/runtime/knowledge.py tests/test_cli_review.py tests/test_cli.py
  git commit -m "feat(cli): review accept/reject/edit/defer drive the evidence seam with dwell telemetry (V2R-C.3)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task V2R-C.4: `review_telemetry_summary` — items/session, per-action counts, dwell, skip rate (+ `memoria review stats`)

**Files:**
- Create: `tests/test_review_telemetry.py`
- Modify: `src/memoria_vault/runtime/knowledge.py` (imports; new function after
  `review_dwell_seconds` from V2R-C.3)
- Modify: `src/memoria_vault/cli.py` (`_review_commands`; one handler)
- Modify: `tests/conftest.py` (TEST_LEVELS), `tests/test_cli.py` (surface set)

**Interfaces:**
- Consumes: journaled `empirical-event` rows (`view.opened`, `disposition.recorded`) and
  `resolved` rows with `operation="resolve-evidence-review"` (`state.py` event_log,
  insert path `:808`); `statistics.mean`/`median` (stdlib); `defaultdict`
  (`knowledge.py:12`, already imported); test emitters from V2R-C.3's test file pattern.
- Produces: **`knowledge.review_telemetry_summary(vault: Path) -> dict[str, Any]`** with
  keys `sessions` (int), `shows` (int), `items_shown` (int), `items_per_session` (float),
  `actions` (`{"accept": int, "reject": int, "edit": int, "defer": int}`),
  `disposed_items` (int), `dwell_s` (`{"count": int, "mean": float, "median": float}` —
  over journaled `duration_s` samples), `skip_rate` (float — shown-undisposed items /
  shown items; 0.0 when nothing shown). Reopen keys arrive in V2R-C.5. CLI verb
  `memoria review stats --workspace W [--json]` → `{"ok": True, "telemetry": {...}}`.

**Steps:**

- [ ] Register the test file. In `tests/conftest.py`, below the line
  `    "test_empirical_events.py": "contract",` (line 42) insert:

  ```python
      "test_review_telemetry.py": "contract",
  ```

- [ ] Write the failing tests. Create `tests/test_review_telemetry.py`:

  ```python
  from __future__ import annotations

  import json
  import uuid
  from pathlib import Path

  import pytest

  from memoria_vault.cli import main
  from memoria_vault.engine import api as engine_api
  from memoria_vault.runtime.knowledge import (
      compose_project_draft as _compose_project_draft,
  )
  from memoria_vault.runtime.knowledge import (
      resolve_evidence_review as _resolve_evidence_review,
  )
  from memoria_vault.runtime.knowledge import review_telemetry_summary
  from memoria_vault.runtime.time import now_iso
  from tests.helpers import call_with_context, init_git, write_checked_concept

  NOTE_IDS = ("01ARZ3NDEKTSV4RRFFQ69G5FA1", "01ARZ3NDEKTSV4RRFFQ69G5FA2")


  def _vault(tmp_path: Path) -> Path:
      init_git(tmp_path, "telemetry@example.invalid", "Review Telemetry")
      return tmp_path


  def _implicit_project(vault: Path, *, notes: int = 1) -> list[str]:
      write_checked_concept(
          vault,
          "projects/project-alpha/project.md",
          "type: project\ncheck_status: checked\ntitle: Alpha project\n",
          "project",
      )
      outline_lines = []
      for index in range(notes):
          note_id = NOTE_IDS[index]
          write_checked_concept(
              vault,
              f"notes/claim-{index}.md",
              f"type: note\ncheck_status: checked\ntitle: Claim {index}\nid: {note_id}\n",
              "note",
              body=f"Implicit claim {index} needs review.",
          )
          outline_lines.append(f"- {note_id} — Claim {index}\n")
      outline = vault / "projects/project-alpha/outline.md"
      outline.parent.mkdir(parents=True, exist_ok=True)
      outline.write_text("".join(outline_lines), encoding="utf-8")
      result = call_with_context(_compose_project_draft, vault, "project-alpha")
      return [str(marker["id"]) for marker in result["evidence_markers"]]


  def resolve(vault: Path, evidence_id: str, decision: str) -> dict:
      return _resolve_evidence_review(
          vault,
          evidence_id,
          decision=decision,
          reason="test",
          actor="pi",
          machine="test-machine",
      )


  def _record(vault: Path, event: dict) -> None:
      result = engine_api.run_operation(
          vault,
          "empirical-event-record",
          event,
          idempotency_key=f"empirical-event:{event['event_id']}",
          actor="pi",
          machine="test-machine",
      )
      assert result["ok"] is True


  def _view_opened(vault: Path, item_id: str, *, session_id: str = "session-a") -> None:
      _record(
          vault,
          {
              "event_id": str(uuid.uuid4()),
              "event_type": "view.opened",
              "timestamp": now_iso(),
              "session_id": session_id,
              "surface": "cli",
              "workflow": "evidence-review",
              "item_type": "evidence-set",
              "item_id": item_id,
          },
      )


  def _disposition_recorded(vault: Path, item_id: str, *, duration_s: float) -> None:
      _record(
          vault,
          {
              "event_id": str(uuid.uuid4()),
              "event_type": "disposition.recorded",
              "timestamp": now_iso(),
              "session_id": "session-a",
              "surface": "cli",
              "workflow": "evidence-review",
              "decision": "accept",
              "reason_code": "other",
              "item_type": "evidence-set",
              "item_id": item_id,
              "duration_s": duration_s,
          },
      )


  def test_summary_counts_actions_per_decision(tmp_path: Path) -> None:
      vault = _vault(tmp_path)
      first, second = _implicit_project(vault, notes=2)
      resolve(vault, first, "accept")
      resolve(vault, second, "defer")

      summary = review_telemetry_summary(vault)

      assert summary["actions"] == {"accept": 1, "reject": 0, "edit": 0, "defer": 1}
      assert summary["disposed_items"] == 2


  def test_summary_aggregates_dwell_from_journaled_durations(tmp_path: Path) -> None:
      vault = _vault(tmp_path)
      (evidence_id,) = _implicit_project(vault)
      _disposition_recorded(vault, evidence_id, duration_s=30.0)
      _disposition_recorded(vault, evidence_id, duration_s=90.0)

      summary = review_telemetry_summary(vault)

      assert summary["dwell_s"] == {"count": 2, "mean": 60.0, "median": 60.0}


  def test_summary_computes_skip_rate_from_shown_undisposed(tmp_path: Path) -> None:
      vault = _vault(tmp_path)
      first, second = _implicit_project(vault, notes=2)
      _view_opened(vault, first)
      _view_opened(vault, second)
      resolve(vault, first, "accept")

      summary = review_telemetry_summary(vault)

      assert summary["items_shown"] == 2
      assert summary["skip_rate"] == 0.5


  def test_summary_groups_items_per_session(tmp_path: Path) -> None:
      vault = _vault(tmp_path)
      first, second = _implicit_project(vault, notes=2)
      _view_opened(vault, first, session_id="session-a")
      _view_opened(vault, second, session_id="session-a")
      _view_opened(vault, first, session_id="session-b")

      summary = review_telemetry_summary(vault)

      assert summary["sessions"] == 2
      assert summary["shows"] == 3
      assert summary["items_per_session"] == 1.5


  def test_summary_is_all_zero_on_untouched_vault(tmp_path: Path) -> None:
      vault = _vault(tmp_path)

      summary = review_telemetry_summary(vault)

      assert summary["sessions"] == 0
      assert summary["actions"] == {"accept": 0, "reject": 0, "edit": 0, "defer": 0}
      assert summary["skip_rate"] == 0.0
      assert summary["dwell_s"]["count"] == 0


  def test_review_stats_cli_surfaces_summary(
      tmp_path: Path, capsys: pytest.CaptureFixture[str]
  ) -> None:
      vault = _vault(tmp_path)
      (evidence_id,) = _implicit_project(vault)
      _view_opened(vault, evidence_id)
      resolve(vault, evidence_id, "accept")

      rc = main(["review", "stats", "--workspace", str(vault), "--json"])
      payload = json.loads(capsys.readouterr().out)

      assert rc == 0
      assert payload["ok"] is True
      assert payload["telemetry"]["actions"]["accept"] == 1
      assert payload["telemetry"]["skip_rate"] == 0.0
  ```

- [ ] Run to verify failure:

  ```
  python -m pytest tests/test_review_telemetry.py -v
  ```

  Expected: collection error — `ImportError: cannot import name 'review_telemetry_summary'`.

- [ ] Minimal implementation, part 1 — `src/memoria_vault/runtime/knowledge.py`.

  (a) Add to the stdlib imports (after `import subprocess`, line 11):

  ```python
  from statistics import mean, median
  ```

  (b) After `review_dwell_seconds` add (action counting reads the seam's own
  `resolve-evidence-review` journal events — the server truth — not the client copies):

  ```python
  _REVIEW_DECISIONS = ("accept", "reject", "edit", "defer")


  def _review_show_rows(vault: Path) -> list[tuple[str, str]]:
      with state.connect(vault) as conn:
          rows = conn.execute(
              """
              SELECT json_extract(payload_json, '$.session_id') AS session_id,
                     json_extract(payload_json, '$.item_id') AS item_id
              FROM event_log
              WHERE event_type = 'empirical-event'
                AND json_extract(payload_json, '$.event_type') = 'view.opened'
                AND json_extract(payload_json, '$.workflow') = 'evidence-review'
                AND json_extract(payload_json, '$.item_id') IS NOT NULL
              ORDER BY event_id
              """
          ).fetchall()
      return [(str(row["session_id"]), str(row["item_id"])) for row in rows]


  def _review_dwell_samples(vault: Path) -> list[float]:
      with state.connect(vault) as conn:
          rows = conn.execute(
              """
              SELECT json_extract(payload_json, '$.duration_s') AS duration_s
              FROM event_log
              WHERE event_type = 'empirical-event'
                AND json_extract(payload_json, '$.event_type') = 'disposition.recorded'
                AND json_extract(payload_json, '$.workflow') = 'evidence-review'
                AND json_extract(payload_json, '$.duration_s') IS NOT NULL
              ORDER BY event_id
              """
          ).fetchall()
      return [float(row["duration_s"]) for row in rows]


  def _review_disposition_rows(vault: Path) -> list[tuple[str, str, str]]:
      with state.connect(vault) as conn:
          rows = conn.execute(
              """
              SELECT json_extract(payload_json, '$.evidence_id') AS evidence_id,
                     json_extract(payload_json, '$.decision') AS decision,
                     json_extract(payload_json, '$.items_sha256') AS items_sha256
              FROM event_log
              WHERE json_extract(payload_json, '$.operation') = 'resolve-evidence-review'
              ORDER BY event_id
              """
          ).fetchall()
      return [
          (str(row["evidence_id"]), str(row["decision"]), str(row["items_sha256"] or ""))
          for row in rows
          if row["evidence_id"] and row["decision"]
      ]


  def review_telemetry_summary(vault: Path) -> dict[str, Any]:
      """Deterministic evidence-review telemetry over journaled I1 events (spec §4)."""
      if state.db_path(vault).is_file():
          shows = _review_show_rows(vault)
          dwell_samples = _review_dwell_samples(vault)
          dispositions = _review_disposition_rows(vault)
      else:
          shows, dwell_samples, dispositions = [], [], []
      actions = {decision: 0 for decision in _REVIEW_DECISIONS}
      for _evidence_id, decision, _digest in dispositions:
          if decision in actions:
              actions[decision] += 1
      shown_items = {item for _session, item in shows}
      disposed_items = {evidence_id for evidence_id, _decision, _digest in dispositions}
      per_session: dict[str, set[str]] = defaultdict(set)
      for session, item in shows:
          per_session[session].add(item)
      return {
          "sessions": len(per_session),
          "shows": len(shows),
          "items_shown": len(shown_items),
          "items_per_session": (
              mean(len(items) for items in per_session.values()) if per_session else 0.0
          ),
          "actions": actions,
          "disposed_items": len(disposed_items),
          "dwell_s": {
              "count": len(dwell_samples),
              "mean": mean(dwell_samples) if dwell_samples else 0.0,
              "median": median(dwell_samples) if dwell_samples else 0.0,
          },
          "skip_rate": (
              len(shown_items - disposed_items) / len(shown_items) if shown_items else 0.0
          ),
      }
  ```

- [ ] Minimal implementation, part 2 — `src/memoria_vault/cli.py`.

  (a) In `_review_commands`, after the action-subcommand loop add:

  ```python
      stats = review_sub.add_parser("stats")
      _common(stats)
      stats.set_defaults(handler=_cmd_review_stats)
  ```

  (b) After `_cmd_review_action` add:

  ```python
  def _cmd_review_stats(args: argparse.Namespace) -> int:
      from memoria_vault.runtime.knowledge import review_telemetry_summary

      return _emit(
          {"ok": True, "telemetry": review_telemetry_summary(_workspace(args))}, args
      )
  ```

- [ ] In `tests/test_cli.py`, add `"memoria review stats",` to the exact set beside the
  other review verbs.

- [ ] Run to verify pass:

  ```
  python -m pytest tests/test_review_telemetry.py tests/test_cli_review.py tests/test_cli.py -v
  ```

  Expected: all pass.

- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/knowledge.py src/memoria_vault/cli.py tests/test_review_telemetry.py tests/conftest.py tests/test_cli.py
  git commit -m "feat(telemetry): review_telemetry_summary — sessions, action counts, dwell, skip rate (V2R-C.4)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task V2R-C.5: reopen metrics — deferred-then-disposed and accept-voided (digests-aware)

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py` (`review_telemetry_summary` from
  V2R-C.4)
- Modify: `tests/test_review_telemetry.py` (append)

**Interfaces:**
- Consumes: `_evidence_items_sha256(items: Iterable[str]) -> str` and the
  `items_sha256` key on `resolve-evidence-review` journal events (Plan 22 S35.4,
  contract item 3); `state.evidence_sets(vault) -> list[dict]`
  (`runtime/state.py:2335-2347`); `state.rebuild_evidence_sets_from_markers(vault, *,
  run_id="")` (`runtime/state.py:2350-2356`) in tests.
- Produces: `review_telemetry_summary` gains
  `"reopens": {"defer_then_disposed": int, "accept_voided": int}` and
  `"reopen_rate": float` (reopens / disposed items; 0.0 when nothing disposed).
  Definitions (spec §4): a **defer-then-disposed** reopen is an evidence id with a
  `defer` disposition followed by a later `accept`/`reject`/`edit` disposition (counted
  once per id); an **accept-voided** reopen is an id whose *latest* disposition is
  `accept` but whose accept-time `items_sha256` no longer matches the current items
  digest (the row re-routes on the next verify — S35.4 semantics). Ids that vanished
  from `evidence_sets` are not counted (fail closed, matching S35.4's inert-legacy rule).

**Steps:**

- [ ] **Grep gate — both repo states (reject-flip coordination).** Run:

  ```
  grep -n "_disposed_evidence_digests\|_disposed_evidence_ids\|_evidence_items_sha256" src/memoria_vault/runtime/knowledge.py
  ```

  Expected: hits for `_disposed_evidence_digests` and `_evidence_items_sha256`, and NO
  hit for `_disposed_evidence_ids`. **If `_disposed_evidence_ids` (`knowledge.py:3241`
  on main) still exists, STOP: Plan 22 S35.4 has not executed — run it (and V2R-A)
  first.** This task is written against the digests form; under the ids form there is no
  `items_sha256` on disposition events, accept-voiding does not exist as a detectable
  state, and `accept_voided` would be silently zero — a dishonest metric.

- [ ] Write the failing tests. Append to `tests/test_review_telemetry.py` (add
  `from memoria_vault.runtime import state` to its imports):

  ```python
  def test_reopen_counts_deferred_row_disposed_later(tmp_path: Path) -> None:
      vault = _vault(tmp_path)
      (evidence_id,) = _implicit_project(vault)
      resolve(vault, evidence_id, "defer")
      resolve(vault, evidence_id, "accept")

      summary = review_telemetry_summary(vault)

      assert summary["reopens"] == {"defer_then_disposed": 1, "accept_voided": 0}
      assert summary["reopen_rate"] == 1.0


  def test_reopen_counts_accept_voided_by_item_edit(tmp_path: Path) -> None:
      vault = _vault(tmp_path)
      (evidence_id,) = _implicit_project(vault)
      resolve(vault, evidence_id, "accept")

      draft = vault / "projects/project-alpha/draft.md"
      draft.write_text(
          draft.read_text(encoding="utf-8").replace(
              "items=%%",
              "items=source-missing#^p0001%%",
          ),
          encoding="utf-8",
      )
      state.rebuild_evidence_sets_from_markers(vault)

      summary = review_telemetry_summary(vault)

      assert summary["reopens"] == {"defer_then_disposed": 0, "accept_voided": 1}
      assert summary["reopen_rate"] == 1.0


  def test_intact_accept_is_not_a_reopen(tmp_path: Path) -> None:
      vault = _vault(tmp_path)
      (evidence_id,) = _implicit_project(vault)
      resolve(vault, evidence_id, "accept")

      summary = review_telemetry_summary(vault)

      assert summary["reopens"] == {"defer_then_disposed": 0, "accept_voided": 0}
      assert summary["reopen_rate"] == 0.0
  ```

  (The `"items=%%"` replace target is the tail of the composed implicit marker — the
  same stable anchor S35.4's void test uses, plan 22 lines 2570–2600.)

- [ ] Run to verify failure:

  ```
  python -m pytest tests/test_review_telemetry.py -v -k reopen
  ```

  Expected: 3 failures with `KeyError: 'reopens'`.

- [ ] Minimal implementation in `src/memoria_vault/runtime/knowledge.py`, inside
  `review_telemetry_summary`. After the `per_session` loop insert:

  ```python
      deferred: set[str] = set()
      reopened_after_defer: set[str] = set()
      latest_decision: dict[str, str] = {}
      latest_accept_digest: dict[str, str] = {}
      for evidence_id, decision, digest in dispositions:
          if decision in {"accept", "reject", "edit"} and evidence_id in deferred:
              reopened_after_defer.add(evidence_id)
          if decision == "defer":
              deferred.add(evidence_id)
          latest_decision[evidence_id] = decision
          if decision == "accept":
              latest_accept_digest[evidence_id] = digest
      current_digests = {
          str(row["id"]): _evidence_items_sha256(row["items"])
          for row in state.evidence_sets(vault)
      }
      accept_voided = {
          evidence_id
          for evidence_id, digest in latest_accept_digest.items()
          if latest_decision.get(evidence_id) == "accept"
          and digest
          and current_digests.get(evidence_id) not in (None, digest)
      }
      reopens = len(reopened_after_defer) + len(accept_voided)
  ```

  and extend the returned dict (after the `"skip_rate"` entry):

  ```python
          "reopens": {
              "defer_then_disposed": len(reopened_after_defer),
              "accept_voided": len(accept_voided),
          },
          "reopen_rate": (reopens / len(disposed_items)) if disposed_items else 0.0,
  ```

- [ ] Run to verify pass, then the full gate:

  ```
  python -m pytest tests/test_review_telemetry.py tests/test_cli_review.py tests/test_draft_verification.py -v
  python scripts/verify
  ```

  Expected: all pass; verify green.

- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/knowledge.py tests/test_review_telemetry.py
  git commit -m "feat(telemetry): reopen metrics — defer-then-disposed and accept-voided reopens (V2R-C.5)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```
# V2R-D — Pane front + export-target acceptance (spec §1 pane front, §5; slices 3 and 7)

Governing spec: `docs/superpowers/specs/2026-07-16-v2-evidence-review-design.md`.
Base: `main @ a525a81a`. Gate: `python scripts/verify`.

## Execution-order dependencies

1. **After U3-PLUG / U3-ENG** (`docs/superpowers/plans/2026-07-15-surfaces-bootstrap-and-plugins.md`).
   The pane front is a **second view** on infrastructure that plan produces and this
   section consumes verbatim:
   - `packages/memoria-obsidian/viewspec.js` (U3-PLUG.4 Produces): `renderView(view) -> Tree[]`,
     `renderBlock(block) -> Tree` (`Tree = {tag, cls, text, attrs, children}`),
     `sortCards(cards) -> cards`, `moveSelection(count, index, key) -> number`,
     `materialize(tree, parentEl) -> el`, `VIEW_SPEC_VERSION = "view-spec.v1"`,
     `KNOWN_BLOCK_KINDS = ["card", "text", "badge", "action-row", "evidence-list"]`.
   - `packages/memoria-obsidian/main.js` (U3-PLUG.6/7 Produces):
     `plugin.authedJson(path) -> Promise<object>`,
     `plugin.enqueueNamedOperation(operationId, payload) -> Promise<object|null>`,
     the `AttentionView` ItemView pattern, `formatAsOf`/`skewBanner` (U3-PLUG.3),
     the `node --test scripts/` harness with its `plugin.views`/`plugin.commands`/
     `requests` mocks, and the seed-parity + floor-golden sync discipline
     (byte-identical copies under
     `src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/`,
     goldens regenerated with `MEMORIA_FLOOR_UPDATE_GOLDENS=1`).
   - SEAM.1 Produces: HTTP `POST /operation/run` enqueues with `actor="pi"` — the
     pane's only mutation door carries PI authority.
2. **After V2R-A (slice 1)** — this section consumes `GET /v1/views/evidence-review`:
   envelope `{ok: true, view: {version: "view-spec.v1", kind: "evidence-review",
   blocks: [...]}}` (cross-section payload contract #3 of the surfaces plan); card
   blocks (`kind: "card"`, `kind_line` = routing, honesty fields `argument_for`/
   `argument_against`/`tipped_by`/`certainty` present-only, `ref` = draft-block
   deep link) with child `evidence-list` and, on reviewable rows only, an
   `action-row` whose four actions carry `operation_id: "resolve-evidence"` and
   payloads `{evidence_id, decision}`; facet query params `routing`/`project`/`age`;
   read-only cure rows carry no `action-row`.
3. **After V2R-B (slice 2)** — the extended seam
   `resolve_evidence_review(vault, evidence_id, *, actor, machine, decision, reason="", warrant="")`
   with the four decisions (`accept`/`reject`/`edit`/`defer`), the **reject flip**
   (only `accept` clears holds), and per-action `disposition.v1` emission (V2R-B
   reuses `emit_disposition_event`, `src/memoria_vault/runtime/operations.py:146` —
   the existing resolve-attention-seam helper, per `runtime/integrity.py:1165-1167`).
   Task V2R-D.1 is written order-tolerantly against the **shipped** signature
   (`knowledge.py:2268-2297`, accept/reject only) and passes `warrant` through only
   when present, so it runs before or after V2R-B; V2R-D.5's reject test requires
   V2R-B.

## SPEC GAPs (decisions made here, one line each)

- SPEC GAP (resolved here): **no `resolve-evidence` worker operation exists** —
  verified by grep: `worker.py` dispatches only `{"acknowledge-attention",
  "resolve-attention"}` (`worker.py:813`) and `resolve_evidence_review` is
  engine/CLI-only (`cli.py:1120`, `knowledge.py:2268`) — so pane action buttons
  would have nothing to enqueue; V2R-D.1 adds the small operation manifest +
  worker branch + PI-actor protection, mirroring `resolve-attention` exactly.
- SPEC GAP: the exact evidence-review card field mapping is owned by V2R-A
  (slice 1); this section writes against the shapes in dependency #2 above —
  reconcile at plan assembly.
- SPEC GAP: the pane surfaces only the `routing` facet control; `project`/`age`
  ride the shared query params and are exercised by the CLI front (slice 4,
  V2R-C) — full facet UI is deferred to the U2 cockpit.
- SPEC GAP: warrant capture on Accept is slice 5's affordance (V2R-E); the pane's
  Accept here enqueues without `warrant`; V2R-D.1's worker branch already passes
  `warrant` through when a later payload carries it.
- SPEC GAP (resolved here): shipped draft export **silently drops** citations for
  DOI-bearing works (`state.compact_citation` prefers `doi` over `citekey`,
  `state.py:2397-2402`) and never inlines the references fence (only the
  non-draft export does, `knowledge.py:2693-2700`) — spec §5 acceptance is
  unsatisfiable against that; V2R-D.4 makes the minimal semantic fix at the
  export seam.
- Plan 22 S35.4 replaces `_disposed_evidence_ids` (`knowledge.py:3241-3251`) with
  `_disposed_evidence_digests(vault) -> dict[str, str]`; V2R-D.5's reject test is
  **behavior-level** (export stays refused after reject) so it is selector-agnostic
  — its grep step records which form is shipped, and no test text changes either way.

## Golden-regeneration note (declared up front)

Three tasks disturb floor goldens (`tests/fixtures/floor/goldens/`): V2R-D.1
(new manifest changes the `regenerate-capability-index` digest), V2R-D.3 (seeded
plugin file hashes), V2R-D.4 (possible `export-project.json` drift if the floor
sweep exercises the draft-export path). Each ends with
`MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest tests/test_floor_sweep_operations.py tests/test_floor_coverage.py -q`,
a `git diff --stat tests/fixtures/floor/goldens/` review, and an explicit-path commit.

---

### Task V2R-D.1: `resolve-evidence` worker operation — the pane's enqueue target

**Files:**
- Create: `src/memoria_vault/product/capabilities/operations/resolve-evidence.md`
- Modify: `src/memoria_vault/runtime/worker.py` (`PROTECTED_OPERATION_ACTORS`,
  lines 53–66; dispatch branch after the attention branch that ends at line 831)
- Modify: `tests/test_operation_context.py` (`PI_AUTHORITY_OPERATIONS`, lines
  974–985; one new happy-path test)
- Modify: `tests/floor_lib.py` (OPERATION_REGISTRY, after the `resolve-attention`
  entry at lines 1029–1038)
- Modify: `tests/fixtures/floor/goldens/regenerate-capability-index.json`
  (regenerated, not hand-edited)

**Interfaces:**
- Consumes: `resolve_evidence_review(vault, evidence_id, *, actor, machine,
  decision, reason="") -> dict` (`src/memoria_vault/runtime/knowledge.py:2268`;
  gains `warrant=""` and two decisions in V2R-B — this branch is tolerant of both
  states); actor gate `PROTECTED_OPERATION_ACTORS.get(context.operation_id)`
  (`worker.py:1094`); runner-policy defaults injected by `_manifest_frontmatter`
  (`runtime/capabilities.py:157-163`, so the manifest needs no `runner` key —
  same shape as `resolve-attention.md`).
- Produces: worker operation id **`resolve-evidence`** (PI-only), payload
  `{evidence_id: str, decision: str, reason?: str, warrant?: str}`, result
  `{"commit": "", "resolution": <journal event>}`. **Every pane action button
  (V2R-D.3) and any future MCP/HTTP caller enqueues this id.**

**Steps:**

- [ ] Write the failing tests — in `tests/test_operation_context.py`, add
  `"resolve-evidence",` to the `PI_AUTHORITY_OPERATIONS` tuple (after
  `"resolve-attention",` at line 976), and append after
  `test_attention_resolution_accepts_pi_and_records_pi` (ends line 1071):

  ```python
  def test_resolve_evidence_operation_records_pi_disposition(
      tmp_path: Path,
      capsys: pytest.CaptureFixture[str],
  ) -> None:
      workspace = init_cli_workspace(tmp_path, capsys)
      request = worker.enqueue_operation(
          workspace,
          "resolve-evidence",
          actor="pi",
          idempotency_key="pi-resolve-evidence",
          payload={
              "evidence_id": "ev-0011aabb",
              "decision": "accept",
              "reason": "grounds hold",
          },
      )

      result = worker.run_request(workspace, request["job_id"], machine="PI laptop")

      assert result["status"] == "done"
      events = [
          row
          for row in _event_log_payloads(workspace)
          if row.get("operation") == "resolve-evidence-review"
      ]
      assert len(events) == 1
      assert events[0]["evidence_id"] == "ev-0011aabb"
      assert events[0]["decision"] == "accept"


  def test_resolve_evidence_operation_requires_evidence_id(
      tmp_path: Path,
      capsys: pytest.CaptureFixture[str],
  ) -> None:
      workspace = init_cli_workspace(tmp_path, capsys)
      request = worker.enqueue_operation(
          workspace,
          "resolve-evidence",
          actor="pi",
          idempotency_key="pi-resolve-evidence-missing-id",
          payload={"decision": "accept"},
      )

      result = worker.run_request(workspace, request["job_id"], machine="PI laptop")

      assert result["status"] == "failed"
      assert "resolve-evidence requires evidence_id" in result["error"]
  ```

- [ ] Run to verify failure:
  `python -m pytest tests/test_operation_context.py -k "resolve_evidence or (protected_operation_rejects and resolve-evidence)" -v`
  Expected: the two new tests fail (`FileNotFoundError:
  product/capabilities/operations/resolve-evidence.md` surfaces as a failed job,
  status/error assertions miss), and the three new
  `test_protected_operation_rejects_wrong_actor_before_payload_validation[resolve-evidence-*]`
  params fail the same way.

- [ ] Write the minimal implementation.

  Create `src/memoria_vault/product/capabilities/operations/resolve-evidence.md`:

  ```markdown
  ---
  title: Resolve evidence review
  type: operation
  description: Record a PI disposition (accept, reject, edit, defer) for one evidence-set review item.
  operation_id: resolve-evidence
  allowed_tools:
  - trusted_writer
  allowed_paths:
  - .memoria/journal/
  - .memoria/index/
  allowed_network: []
  prompt_version: resolve-evidence.v1
  io_schema:
    input: evidence_review_target
    output: resolved_event
  risk_class: low
  required_checks: []
  tags:
  - v2
  - evidence-review
  id: operations/resolve-evidence
  links: {}
  ---

  # Operation

  Record the PI's disposition for one evidence-set review item through the
  worker journal. The disposition drives the grounds-contract holds: only
  accept clears them.
  ```

  In `src/memoria_vault/runtime/worker.py`, add to `PROTECTED_OPERATION_ACTORS`
  (after the `"resolve-attention": "pi",` line 55):

  ```python
      "resolve-evidence": "pi",
  ```

  and insert a dispatch branch directly after the attention branch's
  `return {"commit": result["commit"], "resolution": result["event"]}` (line 831):

  ```python
      if operation_id == "resolve-evidence":
          from memoria_vault.runtime.knowledge import resolve_evidence_review

          evidence_id = str(payload.get("evidence_id") or "").strip()
          if not evidence_id:
              raise ValueError("resolve-evidence requires evidence_id")
          kwargs: dict[str, Any] = {
              "actor": context.actor,
              "machine": context.machine,
              "decision": str(payload.get("decision") or ""),
              "reason": str(payload.get("reason") or ""),
          }
          # Present only post-V2R-B (slice 5 sends it); omitting keeps this
          # branch valid against the shipped two-decision seam signature.
          warrant = str(payload.get("warrant") or "").strip()
          if warrant:
              kwargs["warrant"] = warrant
          event = resolve_evidence_review(vault, evidence_id, **kwargs)
          return {"commit": "", "resolution": event}
  ```

  In `tests/floor_lib.py`, insert after the `resolve-attention` OPERATION_REGISTRY
  entry (closing brace of the dict entry at line 1038):

  ```python
      # worker.py resolve-evidence branch (added by V2R-D.1) delegates to
      # knowledge.py:resolve_evidence_review. PROTECTED_OPERATION_ACTORS
      # "pi"-only — same actor-check-fires-first shape as resolve-attention.
      "resolve-evidence": {
          "payload": {"evidence_id": "ev-00000000", "decision": "accept"},
          "expect": "refused",
          "reason": "requires PI actor authority",
      },
  ```

- [ ] Run to verify pass:

  ```bash
  python -m pytest tests/test_operation_context.py -v
  python -m pytest tests/test_capabilities.py tests/test_floor_coverage.py tests/test_floor_sweep_operations.py -q
  ```

  Expected: `test_worker_operations_are_cataloged_and_policy_shaped` picks the new
  branch up from the worker source regex and loads the manifest;
  `test_every_operation_has_a_floor_entry` sees the new floor entry; the floor
  sweep confirms the refusal live. If `regenerate-capability-index`'s golden
  drifts (the index now lists one more manifest):
  `MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest tests/test_floor_sweep_operations.py tests/test_floor_coverage.py -q`
  then `git diff tests/fixtures/floor/goldens/` — only
  `regenerate-capability-index.json` (and no other golden) may change.

- [ ] Commit:

  ```bash
  git add src/memoria_vault/product/capabilities/operations/resolve-evidence.md \
      src/memoria_vault/runtime/worker.py tests/test_operation_context.py \
      tests/floor_lib.py tests/fixtures/floor/goldens/regenerate-capability-index.json
  git commit -m "feat(worker): resolve-evidence operation — PI-only disposition door for the review surfaces

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task V2R-D.2: `collapseAnalysis` — independence-first as a pure tree transform

**Files:**
- Modify: `packages/memoria-obsidian/viewspec.js` (one exported function; no
  changes to existing exports)
- Modify: `packages/memoria-obsidian/scripts/test-viewspec.mjs`
- Modify (parity): `src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/viewspec.js`
  (synced in V2R-D.3's sync step together with `main.js`/`styles.css`)

**Interfaces:**
- Consumes: the card `Tree` anatomy `renderBlock` produces (U3-PLUG.4): children
  with classes `memoria-card-kind`, `memoria-card-title`, `memoria-evidence`,
  `memoria-card-arguments`, `memoria-card-tipped`, `memoria-action-row`,
  `memoria-card-meta`; honesty fields are **present-only**, so cure rows without
  `argument_for`/`argument_against` have no analysis children.
- Produces (CommonJS export of `viewspec.js`):
  - `collapseAnalysis(tree, open) -> Tree` — pure; moves the
    `memoria-card-arguments` and `memoria-card-tipped` children (spec §2 fields
    4–6) into a `div.memoria-analysis` container preceded by a
    `button.memoria-analysis-toggle` (`attrs: {"data-toggle-analysis": "1"}`,
    text `"Show analysis (machine)"` collapsed / `"Hide analysis"` open); when
    `open` is falsy the container class is `"memoria-analysis is-collapsed"`;
    returns the input tree unchanged when the card has no analysis children
    (read-only cure rows get no toggle). Evidence order is untouched — blocks
    1–3 still precede the disclosure (spec §3, structural not stylistic).

**Steps:**

- [ ] Write the failing tests — append to
  `packages/memoria-obsidian/scripts/test-viewspec.mjs` (add `collapseAnalysis`
  to the destructured require at the top):

  ```js
  test("collapseAnalysis hides machine analysis by default; evidence stays first", () => {
    const card = renderBlock({
      kind: "card",
      id: "ev1",
      ref: "projects/project-alpha/draft.md#^blk-a1b2",
      title: "Implicit synthesis claim",
      kind_line: "evidence-review",
      certainty: "possible",
      argument_for: "Both grounds items support the claim text.",
      argument_against: "The set is implicit; no span was cited.",
      tipped_by: "implicit derivation",
      blocks: [
        { kind: "evidence-list", id: "e1", items: [{ label: "span", ref: "notes/a.md" }] },
        {
          kind: "action-row",
          id: "a1",
          actions: [
            { label: "Accept", operation_id: "resolve-evidence", payload: { evidence_id: "ev-0011aabb", decision: "accept" }, primary: true },
            { label: "Reject", operation_id: "resolve-evidence", payload: { evidence_id: "ev-0011aabb", decision: "reject" } },
            { label: "Edit", operation_id: "resolve-evidence", payload: { evidence_id: "ev-0011aabb", decision: "edit" } },
            { label: "Defer", operation_id: "resolve-evidence", payload: { evidence_id: "ev-0011aabb", decision: "defer" } },
          ],
        },
      ],
    });

    const collapsed = collapseAnalysis(card, false);
    const classes = collapsed.children.map((child) => child.cls);
    assert.ok(!classes.includes("memoria-card-arguments"), "analysis moved out of the card body");
    assert.ok(!classes.includes("memoria-card-tipped"), "tipped/certainty moved too");
    const toggleAt = classes.indexOf("memoria-analysis-toggle");
    const analysisAt = classes.indexOf("memoria-analysis is-collapsed");
    assert.ok(toggleAt !== -1, "disclosure toggle rendered");
    assert.equal(analysisAt, toggleAt + 1);
    assert.ok(classes.indexOf("memoria-evidence") < toggleAt, "evidence precedes the disclosure");
    assert.equal(collapsed.children[toggleAt].text, "Show analysis (machine)");
    assert.equal(collapsed.children[toggleAt].attrs["data-toggle-analysis"], "1");
    const inner = collapsed.children[analysisAt].children.map((child) => child.cls);
    assert.deepEqual(inner, ["memoria-card-arguments", "memoria-card-tipped"]);

    const open = collapseAnalysis(card, true);
    const openClasses = open.children.map((child) => child.cls);
    assert.ok(openClasses.includes("memoria-analysis"), "open container is not collapsed");
    assert.equal(open.children[openClasses.indexOf("memoria-analysis-toggle")].text, "Hide analysis");
  });

  test("collapseAnalysis is a no-op for cards without analysis (read-only cure rows)", () => {
    const card = renderBlock({
      kind: "card",
      id: "cure1",
      ref: "projects/project-alpha/draft.md#^blk-c3d4",
      title: "evidence-text-drift — repair the marker, then re-verify",
      kind_line: "evidence-text-drift",
      blocks: [],
    });
    assert.equal(collapseAnalysis(card, false), card);
  });
  ```

- [ ] Run to verify failure:
  `cd /home/eranr/memoria-vault/packages/memoria-obsidian && node --test scripts/`
  — expected: `TypeError: collapseAnalysis is not a function`.

- [ ] Write the minimal implementation — in `packages/memoria-obsidian/viewspec.js`,
  before the `module.exports` block:

  ```js
  const ANALYSIS_CLASSES = ["memoria-card-arguments", "memoria-card-tipped"];

  function collapseAnalysis(tree, open) {
    const isAnalysis = (child) => Boolean(child) && ANALYSIS_CLASSES.includes(child.cls);
    const moved = (tree.children || []).filter(isAnalysis);
    if (!moved.length) {
      return tree;
    }
    const children = [];
    let inserted = false;
    for (const child of tree.children) {
      if (!isAnalysis(child)) {
        children.push(child);
        continue;
      }
      if (inserted) {
        continue;
      }
      inserted = true;
      children.push({
        tag: "button",
        cls: "memoria-analysis-toggle",
        text: open ? "Hide analysis" : "Show analysis (machine)",
        attrs: { "data-toggle-analysis": "1" },
        children: [],
      });
      children.push({
        tag: "div",
        cls: open ? "memoria-analysis" : "memoria-analysis is-collapsed",
        text: "",
        attrs: {},
        children: moved,
      });
    }
    return { ...tree, children };
  }
  ```

  Add `collapseAnalysis,` to `module.exports`.

- [ ] Run to verify pass:
  `cd /home/eranr/memoria-vault/packages/memoria-obsidian && node --test scripts/` — all green.

- [ ] Commit (seed copy travels with V2R-D.3's sync; the shipped module alone here):

  ```bash
  git add packages/memoria-obsidian/viewspec.js packages/memoria-obsidian/scripts/test-viewspec.mjs
  git commit -m "feat(obsidian): collapseAnalysis — machine analysis collapsed by default as a pure tree transform

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task V2R-D.3: Evidence-review pane — second ItemView on the U3 infrastructure

**Files:**
- Modify: `packages/memoria-obsidian/main.js` (constants next to
  `VIEW_TYPE_ATTENTION`; `onload` — `registerView` + `open-evidence-review`
  command; `activateEvidenceReviewView` method next to `activateAttentionView`;
  `poll()` refresh loop extended; `EvidenceReviewView` class appended after
  `AttentionView`)
- Modify: `packages/memoria-obsidian/styles.css` (analysis-disclosure styles,
  theme vars only — U3-PLUG.9's hardcoded-color lint gate applies)
- Modify: `packages/memoria-obsidian/scripts/test.mjs` (registration + enqueue
  assertions; mock route for the evidence-review payload)
- Modify: `tests/test_memoria_obsidian_package.py` (command roster in
  `test_memoria_obsidian_registers_minimal_proof_commands`, the tuple U3-PLUG.7
  extended with `"open-attention"` — currently lines 70–82 pre-U3; locate by content)
- Modify (parity): seed copies of `main.js`/`styles.css`/`viewspec.js` under
  `src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/`
  + regenerated `tests/fixtures/floor/goldens/`

**Interfaces:**
- Consumes: `renderBlock`/`renderView`/`moveSelection`/`materialize`/
  `collapseAnalysis` (viewspec.js; V2R-D.2), `formatAsOf` (U3-PLUG.3),
  `authedJson`/`enqueueNamedOperation` (U3-PLUG.6/7); `GET
  /v1/views/evidence-review` (V2R-A; dependency #2 above); worker operation
  `resolve-evidence` (V2R-D.1).
- Produces:
  - `VIEW_TYPE_EVIDENCE_REVIEW = "memoria-evidence-review"`,
    `EVIDENCE_REVIEW_VIEW_PATH = "/v1/views/evidence-review"`,
    `EVIDENCE_ROUTING_FACETS = ["", "implicit", "multi-hop", "incomplete"]`.
  - `class EvidenceReviewView extends ItemView` with `getViewType()`,
    `getDisplayText() -> "Memoria Evidence Review"`, `refresh()`, `render()`,
    `onKey(event)`, `onClick(event)`; **server queue order preserved** (no
    `sortCards` — spec §6's batch order is the review order); expanded cards
    render through `collapseAnalysis` (analysis collapsed by default,
    re-collapses on every expand — independence-first by construction); the four
    action buttons enqueue `resolve-evidence` via `enqueueNamedOperation`; the
    Edit action additionally deep-links the draft block (`openLinkText` on the
    card `ref`); a routing-facet cycle button re-fetches with `?routing=<facet>`.
  - Command id `"open-evidence-review"`; `poll()` refreshes open evidence-review
    leaves alongside attention leaves.

**Steps:**

- [ ] Write the failing test — append to the `try` block of
  `packages/memoria-obsidian/scripts/test.mjs` (after U3-PLUG.7's block 6),
  and extend the mock `requestUrl` router: when `options.url` ends with
  `/v1/views/evidence-review` (with or without query), return
  `{ ok: true, view: { version: "view-spec.v1", kind: "evidence-review", blocks: [] } }`
  in its `json`:

  ```js
    // 7) Evidence-review pane: second view registered; actions enqueue resolve-evidence.
    assert.ok(plugin.views["memoria-evidence-review"], "evidence review view registered");
    const evidenceView = plugin.views["memoria-evidence-review"]({});
    assert.equal(evidenceView.getViewType(), "memoria-evidence-review");
    assert.equal(evidenceView.getDisplayText(), "Memoria Evidence Review");
    assert.ok(plugin.commands.includes("open-evidence-review"));
    const rejected = await plugin.enqueueNamedOperation("resolve-evidence", {
      evidence_id: "ev-0011aabb",
      decision: "reject",
      reason: "grounds do not support the claim",
    });
    assert.equal(JSON.parse(requests.at(-1).body).operation_id, "resolve-evidence");
    assert.ok(rejected);
  ```

- [ ] Run to verify failure:
  `cd /home/eranr/memoria-vault/packages/memoria-obsidian && node --test scripts/`
  — expected: `evidence review view registered` assertion failure.

- [ ] Write the minimal implementation — in `packages/memoria-obsidian/main.js`:

  1. Constants next to `VIEW_TYPE_ATTENTION`:

  ```js
  const VIEW_TYPE_EVIDENCE_REVIEW = "memoria-evidence-review";
  const EVIDENCE_REVIEW_VIEW_PATH = "/v1/views/evidence-review";
  const EVIDENCE_ROUTING_FACETS = ["", "implicit", "multi-hop", "incomplete"];
  ```

  2. In `onload`, directly after the attention `registerView`/command lines:

  ```js
    this.registerView(
      VIEW_TYPE_EVIDENCE_REVIEW,
      (leaf) => new EvidenceReviewView(leaf, this),
    );
    this.addCommand({
      id: "open-evidence-review",
      name: "Memoria: Open evidence review",
      callback: () => this.activateEvidenceReviewView(),
    });
  ```

  3. Add `activateEvidenceReviewView` next to `activateAttentionView` — copy its
  body verbatim, substituting `VIEW_TYPE_EVIDENCE_REVIEW`.

  4. In `poll()`, generalize U3-PLUG.7's refresh loop to both view types:

  ```js
        for (const viewType of [VIEW_TYPE_ATTENTION, VIEW_TYPE_EVIDENCE_REVIEW]) {
          for (const leaf of this.app.workspace.getLeavesOfType
            ? this.app.workspace.getLeavesOfType(viewType)
            : []) {
            if (leaf.view && typeof leaf.view.refresh === "function") {
              leaf.view.refresh();
            }
          }
        }
  ```

  5. Append the class after `AttentionView` (requires block already imports the
  viewspec helpers; add `collapseAnalysis` to that destructuring):

  ```js
  class EvidenceReviewView extends ItemView {
    constructor(leaf, plugin) {
      super(leaf);
      this.plugin = plugin;
      this.view = null;
      this.cards = [];
      this.extras = [];
      this.selected = 0;
      this.expandedRef = "";
      this.analysisOpenRef = "";
      this.facetRouting = "";
    }

    getViewType() {
      return VIEW_TYPE_EVIDENCE_REVIEW;
    }

    getDisplayText() {
      return "Memoria Evidence Review";
    }

    getIcon() {
      return "scale";
    }

    async onOpen() {
      this.contentEl.addClass("memoria-evidence-review");
      this.contentEl.tabIndex = 0;
      this.registerDomEvent(this.contentEl, "keydown", (event) => this.onKey(event));
      this.registerDomEvent(this.contentEl, "click", (event) => this.onClick(event));
      await this.refresh();
    }

    viewPath() {
      return this.facetRouting
        ? `${EVIDENCE_REVIEW_VIEW_PATH}?routing=${encodeURIComponent(this.facetRouting)}`
        : EVIDENCE_REVIEW_VIEW_PATH;
    }

    async refresh() {
      try {
        const payload = await this.plugin.authedJson(this.viewPath());
        this.view = payload.view || null;
      } catch (error) {
        this.contentEl.empty();
        this.contentEl.createDiv({
          cls: "memoria-block-unknown",
          text: `Memoria evidence review unavailable: ${String(error.message || error)}`,
        });
        return;
      }
      const blocks =
        this.view && this.view.version === "view-spec.v1" ? this.view.blocks || [] : [];
      // Server queue order is the review order (spec section 6) — never re-sorted.
      this.cards = blocks.filter((block) => block && block.kind === "card");
      this.extras = blocks.filter((block) => !block || block.kind !== "card");
      this.selected = Math.max(0, Math.min(this.selected, this.cards.length - 1));
      this.render();
    }

    render() {
      const root = this.contentEl;
      root.empty();
      const header = root.createDiv({ cls: "memoria-attention-header" });
      header.createSpan({ text: "EVIDENCE REVIEW" });
      const facet = header.createEl("button", {
        cls: "memoria-action",
        text: this.facetRouting ? `routing: ${this.facetRouting}` : "routing: all",
      });
      facet.setAttribute("data-cycle-routing", "1");
      header.createSpan({
        cls: "memoria-attention-age",
        text: `as of ${formatAsOf(this.plugin.lastPollAt)}`,
      });
      if (!this.view || this.view.version !== "view-spec.v1") {
        for (const tree of renderView(this.view)) {
          materialize(tree, root);
        }
        return;
      }
      for (const extra of this.extras) {
        materialize(renderBlock(extra), root);
      }
      this.cards.forEach((card, index) => {
        const row = root.createDiv({
          cls: index === this.selected ? "memoria-row is-selected" : "memoria-row",
        });
        const loudness = String(card.loudness || "");
        row.createSpan({
          cls: loudness
            ? `memoria-loudness-dot memoria-loudness-${loudness}`
            : "memoria-loudness-dot",
        });
        row.createSpan({ cls: "memoria-row-title", text: String(card.title || "") });
        row.createSpan({ cls: "memoria-row-age", text: String(card.age_label || "") });
        row.setAttribute("data-row-index", String(index));
        const ref = String(card.ref || "");
        if (ref && ref === this.expandedRef) {
          materialize(
            collapseAnalysis(renderBlock(card), this.analysisOpenRef === ref),
            root,
          );
        }
      });
    }

    toggleExpand(index) {
      this.selected = index;
      const ref = String((this.cards[index] || {}).ref || "");
      this.expandedRef = this.expandedRef === ref ? "" : ref;
      // Independence-first: analysis re-collapses on every expand (spec section 3).
      this.analysisOpenRef = "";
      this.render();
    }

    onKey(event) {
      if (event.key === "j" || event.key === "k") {
        this.selected = moveSelection(this.cards.length, this.selected, event.key);
        event.preventDefault();
        this.render();
        return;
      }
      if (event.key === "Enter" && this.cards.length) {
        event.preventDefault();
        this.toggleExpand(this.selected);
      }
    }

    async onClick(event) {
      const facetEl = event.target.closest("button[data-cycle-routing]");
      if (facetEl) {
        const at = EVIDENCE_ROUTING_FACETS.indexOf(this.facetRouting);
        this.facetRouting =
          EVIDENCE_ROUTING_FACETS[(at + 1) % EVIDENCE_ROUTING_FACETS.length];
        await this.refresh();
        return;
      }
      const toggleEl = event.target.closest("button[data-toggle-analysis]");
      if (toggleEl) {
        this.analysisOpenRef =
          this.analysisOpenRef === this.expandedRef ? "" : this.expandedRef;
        this.render();
        return;
      }
      const actionEl = event.target.closest("button[data-operation-id]");
      if (actionEl) {
        const payload = JSON.parse(actionEl.getAttribute("data-payload") || "{}");
        await this.plugin.enqueueNamedOperation(
          actionEl.getAttribute("data-operation-id"),
          payload,
        );
        if (payload.decision === "edit" && this.expandedRef) {
          this.plugin.app.workspace.openLinkText(this.expandedRef, "", false);
        }
        await this.refresh();
        return;
      }
      const linkEl = event.target.closest("a[data-ref]");
      if (linkEl) {
        this.plugin.app.workspace.openLinkText(linkEl.getAttribute("data-ref"), "", false);
        return;
      }
      const rowEl = event.target.closest(".memoria-row");
      if (rowEl) {
        this.toggleExpand(Number(rowEl.getAttribute("data-row-index")));
      }
    }
  }
  ```

  6. Append to `packages/memoria-obsidian/styles.css`:

  ```css
  /* Evidence-review pane (V2 spec section 3): evidence first, machine analysis
     collapsed by default behind an explicit disclosure. Theme vars only. */
  .memoria-evidence-review { font-size: 13px; }
  .memoria-analysis-toggle {
    margin-top: 6px;
    padding: 2px 8px;
    border: 1px solid var(--background-modifier-border);
    border-radius: 4px;
    background-color: transparent;
    color: var(--text-muted);
    cursor: pointer;
    font-size: 11px;
  }
  .memoria-analysis.is-collapsed { display: none; }
  ```

  7. In `tests/test_memoria_obsidian_package.py::test_memoria_obsidian_registers_minimal_proof_commands`,
  add `"open-evidence-review",` to the command tuple (after U3-PLUG.7's
  `"open-attention",`).

- [ ] Run tests:
  `cd /home/eranr/memoria-vault/packages/memoria-obsidian && node --test scripts/`
  (all pass) then `python -m pytest tests/test_memoria_obsidian_package.py -v`
  — expected: green except `test_memoria_obsidian_seed_matches_release_artifacts`
  (seed stale) — fixed next step.

- [ ] Sync the seed and regenerate goldens (U3-PLUG.6's discipline; `viewspec.js`
  from V2R-D.2 rides along):

  ```bash
  cp packages/memoria-obsidian/main.js packages/memoria-obsidian/styles.css \
     packages/memoria-obsidian/viewspec.js \
     src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/
  MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest tests/test_floor_sweep_operations.py tests/test_floor_coverage.py -q
  git diff --stat tests/fixtures/floor/goldens/
  ```

  Review the diff: only `files` hash entries under
  `.obsidian/plugins/memoria-obsidian/` may change.

- [ ] Run `python -m pytest tests/test_memoria_obsidian_package.py -v` — all green.

- [ ] Commit:

  ```bash
  git add packages/memoria-obsidian/main.js packages/memoria-obsidian/styles.css \
      packages/memoria-obsidian/scripts/test.mjs tests/test_memoria_obsidian_package.py \
      src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian \
      tests/fixtures/floor/goldens
  git commit -m "feat(obsidian): evidence-review pane — second view, collapsed analysis, four disposition actions

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task V2R-D.4: Draft export — inlined references fence + unresolved-citation refusal

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py`
  (`render_project_draft_export_markdown`, lines 2584–2606;
  `_render_draft_export_body`, lines 3328–3345; two new helpers next to
  `_append_project_export_references`, lines 2693–2700)
- Modify: `tests/test_draft_verification.py` (add `citekey="source-alpha",` to
  every `state.upsert_catalog_record(` call — six sites: lines 101, 141, 202,
  246, 969, and the remaining one located by grep)
- Modify: `tests/test_content_security.py` (same one-line `citekey=` addition to
  its `upsert_catalog_record` fixture — one site, locate by grep; its two
  `draft=True` exports at lines 960 and 1042 must keep passing)
- Create: `tests/test_export_acceptance.py`
- Modify: `tests/conftest.py` (TEST_LEVELS dict, insert
  `"test_export_acceptance.py": "runtime",` after
  `"test_exploration_trace.py": "contract",` at line 48 — nearest sibling level
  is `test_draft_verification.py`: `"runtime"`)

**Interfaces:**
- Consumes: `parse_evidence_marker`/`parse_source_span_ref`
  (`runtime/evidence.py`, already imported inside `_render_draft_export_body`);
  `state.catalog_sources(vault)` (`state.py:1615`, checked-only rows carrying
  `work_id`/`citekey`/`csl_json`); `render_references_bib(vault) -> str`
  (`capture.py:558` — the bibliography projection's definition, entries joined
  by blank lines).
- Produces (module-private, `knowledge.py`):
  - `_draft_citekeys(vault: Path) -> dict[str, str]` — work_id → citekey
    (`citekey` frontmatter else `csl_json["id"]`), i.e. exactly the works
    `render_references_bib` emits — map membership **is** fence membership.
  - `_draft_unresolved_citations(vault: Path, content: str) -> list[str]` —
    sorted work_ids of marker items that parse to a source-span ref but have no
    fence entry.
  - `_render_draft_export_body` now cites via `_draft_citekeys` (DOI-bearing
    works cite their citekey instead of being silently dropped —
    `state.compact_citation` is no longer used here).
  - `render_project_draft_export_markdown` refuses unresolved citations
    (`ValueError("project draft is not export-ready: unresolved-citation:<work_id>, …")`)
    and appends the `## References` bibtex fence rendered **from the projection
    definition** (`render_references_bib`, never a possibly-stale tracked file —
    `check_references_bib` guards the file elsewhere).

**Steps:**

- [ ] Write the failing tests — create `tests/test_export_acceptance.py`:

  ```python
  """Export-target acceptance: markdown + bibliography.bib (V2 spec section 5)."""

  from __future__ import annotations

  import re
  from pathlib import Path

  import pytest

  from memoria_vault.runtime import state
  from memoria_vault.runtime.capture import parse_bibtex_entry, write_references_bib_explicit
  from memoria_vault.runtime.knowledge import compose_project_draft as _compose_project_draft
  from memoria_vault.runtime.knowledge import resolve_evidence_review as _resolve_evidence_review
  from memoria_vault.runtime.knowledge import verify_project_draft as _verify_project_draft
  from memoria_vault.runtime.knowledge import write_project_export as _write_project_export
  from tests.helpers import call_with_context, write_checked_concept


  def compose_project_draft(vault: Path, *args, **kwargs):
      return call_with_context(_compose_project_draft, vault, *args, **kwargs)


  def verify_project_draft(vault: Path, *args, **kwargs):
      return call_with_context(_verify_project_draft, vault, *args, **kwargs)


  def write_project_export(vault: Path, *args, **kwargs):
      return call_with_context(_write_project_export, vault, *args, **kwargs)


  def resolve_evidence_review(vault: Path, *args, **kwargs):
      kwargs.setdefault("actor", "pi")
      kwargs.setdefault("machine", "test-machine")
      return _resolve_evidence_review(vault, *args, **kwargs)


  def _project(vault: Path) -> None:
      write_checked_concept(
          vault,
          "projects/project-alpha/project.md",
          "type: project\ncheck_status: checked\ntitle: Alpha project\n",
          "project",
      )


  def _outline(vault: Path, content: str) -> None:
      path = vault / "projects/project-alpha/outline.md"
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text(content, encoding="utf-8")


  def _source_span(vault: Path, work_id: str) -> None:
      path = vault / f".memoria/blobs/source-content/{work_id}.md"
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text(f"{work_id} source span. ^p0001\n", encoding="utf-8")


  def _catalog_source(vault: Path, work_id: str, **kwargs) -> None:
      state.upsert_catalog_record(
          vault,
          work_id=work_id,
          title=kwargs.pop("title", f"{work_id} source"),
          check_status="checked",
          content_path=f".memoria/blobs/source-content/{work_id}.md",
          **kwargs,
      )
      _source_span(vault, work_id)


  def _source_backed_draft(vault: Path) -> None:
      _project(vault)
      write_checked_concept(
          vault,
          "notes/support.md",
          "type: note\ncheck_status: checked\ntitle: Support\n"
          "id: 01ARZ3NDEKTSV4RRFFQ69G5FA2\nwork_id: catalog/sources/source-alpha\n",
          "note",
          body="This source-backed claim can be exported.",
      )
      _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA2 — Support\n")
      compose_project_draft(vault, "project-alpha")


  def _fence(content: str) -> str:
      match = re.search(r"```bibtex\n(?P<bib>.*?)\n```", content, re.S)
      assert match is not None, "exported artifact carries no inlined bibtex fence"
      return match.group("bib")


  def test_markdown_draft_export_citations_resolve_against_inlined_fence(
      tmp_path: Path,
  ) -> None:
      vault = tmp_path
      _catalog_source(vault, "source-alpha", citekey="smith2020")
      _source_backed_draft(vault)
      verify_project_draft(vault, "project-alpha")

      exported = write_project_export(vault, "project-alpha", draft=True)

      content = exported["content"]
      body, _, references = content.partition("## References")
      assert references, "draft export must inline the References fence"
      used = set(re.findall(r"\[@([^;\]\s]+)", body))
      fence_keys = {
          match.group(1).strip()
          for match in re.finditer(r"(?m)^@\w+\{([^,]+),", _fence(content))
      }
      assert used == {"smith2020"}
      assert used <= fence_keys


  def test_draft_export_refuses_unresolved_citation_naming_the_finding(
      tmp_path: Path,
  ) -> None:
      vault = tmp_path
      # DOI-bearing, citekey-less: in the catalog but absent from the
      # bibliography projection — shipped behavior silently drops its citation.
      _catalog_source(vault, "source-alpha", doi="10.1000/alpha")
      _source_backed_draft(vault)
      verify_project_draft(vault, "project-alpha")

      with pytest.raises(ValueError, match="unresolved-citation:source-alpha"):
          write_project_export(vault, "project-alpha", draft=True)
  ```

- [ ] Run to verify failure:
  `python -m pytest tests/test_export_acceptance.py -v`
  Expected: the resolution test fails at `"exported artifact carries no inlined
  bibtex fence"`; the refusal test fails with `DID NOT RAISE` (the citation is
  silently dropped today). Register the file first (TEST_LEVELS edit above) or
  `tests/test_testing_levels.py` fails the whole run.

- [ ] Write the minimal implementation — in `src/memoria_vault/runtime/knowledge.py`:

  1. Insert after `_append_project_export_references` (line 2700):

  ```python
  def _append_draft_export_references(lines: list[str], vault: Path) -> None:
      from memoria_vault.runtime.capture import render_references_bib

      text = render_references_bib(vault).strip()
      if not text:
          return
      lines.extend(["## References", "", "```bibtex", text, "```", ""])


  def _draft_citekeys(vault: Path) -> dict[str, str]:
      citekeys: dict[str, str] = {}
      for source in state.catalog_sources(vault):
          csl = source.get("csl_json") if isinstance(source.get("csl_json"), dict) else {}
          citekey = str(source.get("citekey") or csl.get("id") or "").strip()
          if citekey:
              citekeys[str(source.get("work_id") or "")] = citekey
      return citekeys


  def _draft_unresolved_citations(vault: Path, content: str) -> list[str]:
      from memoria_vault.runtime.evidence import parse_evidence_marker, parse_source_span_ref

      citekeys = _draft_citekeys(vault)
      unresolved = set()
      for match in re.finditer(r"%%ev:\s*.*?%%", content):
          marker = parse_evidence_marker(match.group(0).strip())
          for item in marker.items:
              try:
                  source = parse_source_span_ref(item)
              except ValueError:
                  continue
              if source.work_id not in citekeys:
                  unresolved.add(source.work_id)
      return sorted(unresolved)
  ```

  2. In `render_project_draft_export_markdown` (line 2584), after the
  `if draft is None:` guard and before rendering, add the refusal and switch the
  content assembly to append the fence:

  ```python
      unresolved = _draft_unresolved_citations(vault, draft["content"])
      if unresolved:
          labels = ", ".join(f"unresolved-citation:{work_id}" for work_id in unresolved)
          raise ValueError(f"project draft is not export-ready: {labels}")
      _frontmatter, body = split_frontmatter(draft["content"])
      lines = [_render_draft_export_body(vault, body).strip(), ""]
      _append_draft_export_references(lines, vault)
      content = neutralize_untrusted_markdown("\n".join(lines).rstrip() + "\n")
  ```

  (replacing the current single-line `content = ...` at line 2596).

  3. In `_render_draft_export_body` (line 3328), replace the
  `state.compact_citation` lookup with the fence-membership map:

  ```python
  def _render_draft_export_body(vault: Path, content: str) -> str:
      from memoria_vault.runtime.evidence import parse_evidence_marker, parse_source_span_ref

      citekeys_by_work = _draft_citekeys(vault)

      def citation(match: re.Match[str]) -> str:
          marker = parse_evidence_marker(match.group(0).strip())
          citekeys = []
          for item in marker.items:
              try:
                  source = parse_source_span_ref(item)
              except ValueError:
                  continue
              if citekey := citekeys_by_work.get(source.work_id):
                  citekeys.append(f"@{citekey}")
          return f" [{'; '.join(citekeys)}]" if citekeys else ""

      text = re.sub(r"\s*%%ev:\s*.*?%%", citation, content)
      return re.sub(r"\s+\^blk-[A-Za-z0-9_-]+", "", text)
  ```

  4. Update fixtures: add `citekey="source-alpha",` to every
  `state.upsert_catalog_record(` call in `tests/test_draft_verification.py`
  (six sites — `grep -n "upsert_catalog_record" tests/test_draft_verification.py`)
  and the one in `tests/test_content_security.py`. Rendering is unchanged for
  them (`[@source-alpha]` before and after — the explicit citekey equals the
  old work_id fallback), and the sources now genuinely appear in the fence.

- [ ] Run to verify pass:

  ```bash
  python -m pytest tests/test_export_acceptance.py tests/test_draft_verification.py \
      tests/test_content_security.py tests/test_testing_levels.py -v
  python -m pytest tests/test_floor_sweep_operations.py -k export-project -v
  ```

  Expected: all green. If the `export-project` floor golden drifts (only if that
  sweep exercises the draft path):
  `MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest tests/test_floor_sweep_operations.py tests/test_floor_coverage.py -q`,
  review `git diff tests/fixtures/floor/goldens/export-project.json`, include it
  in the commit.

- [ ] Commit:

  ```bash
  git add src/memoria_vault/runtime/knowledge.py tests/test_export_acceptance.py \
      tests/test_draft_verification.py tests/test_content_security.py tests/conftest.py
  git commit -m "feat(export): draft export inlines the bibliography fence and refuses unresolved citations

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task V2R-D.5: Refusal-honesty acceptance — blocked exports name findings; reject stays blocking

Requires V2R-B (reject flip) for the second test; the first passes against
shipped refusal plumbing and pins it as acceptance.

**Files:**
- Modify: `tests/test_export_acceptance.py` (append two tests)

**Interfaces:**
- Consumes: `render_project_draft_export_markdown`'s refusal message
  (`ValueError(f"project draft is not export-ready: {reasons}")`,
  `knowledge.py:2590-2592`) built from `_verification_finding_labels`
  (`knowledge.py:3232-3238`, `kind:evidence_id` labels);
  `resolve_evidence_review` (V2R-B's four-decision form; `reject` leaves the
  hold); `compose_project_draft`'s returned `evidence_markers[0]["id"]`.
- Produces: nothing new — acceptance pins for spec §5/§8.

**Steps:**

- [ ] Grep the disposition-selector state (records, does not change, which form
  is shipped — the tests below are behavior-level and selector-agnostic):
  `grep -n "_disposed_evidence_digests\|_disposed_evidence_ids" src/memoria_vault/runtime/knowledge.py`
  Expected post-Plan-22-S35.4: only `_disposed_evidence_digests(vault) ->
  dict[str, str]`. If the ids form is still shipped, V2R-B (which owns the flip)
  decides which selector it edits; these tests are unaffected either way.

- [ ] Write the tests — append to `tests/test_export_acceptance.py`:

  ```python
  def _implicit_draft(vault: Path) -> str:
      _project(vault)
      write_checked_concept(
          vault,
          "notes/thesis.md",
          "type: note\ncheck_status: checked\ntitle: Thesis\n"
          "id: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n",
          "note",
          body="This implicit claim needs review.",
      )
      _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — Thesis\n")
      composed = compose_project_draft(vault, "project-alpha")
      return composed["evidence_markers"][0]["id"]


  def test_blocked_export_names_its_findings(tmp_path: Path) -> None:
      vault = tmp_path
      evidence_id = _implicit_draft(vault)
      verification = verify_project_draft(vault, "project-alpha")

      assert verification["ready"] is False
      with pytest.raises(ValueError) as refusal:
          write_project_export(vault, "project-alpha", draft=True)

      message = str(refusal.value)
      assert "project draft is not export-ready" in message
      assert f"evidence-incomplete:{evidence_id}" in message
      assert f"review-required:{evidence_id}" in message


  def test_rejected_disposition_leaves_export_blocked(tmp_path: Path) -> None:
      """Spec section 4: only accept clears holds — a reject must keep refusing.

      Behavior-level on purpose: passes against both the S35.4 digests
      selector and the pre-S35.4 ids selector once V2R-B lands the flip;
      fails against shipped pre-V2R-B semantics (reject clears the hold).
      """
      vault = tmp_path
      evidence_id = _implicit_draft(vault)
      verify_project_draft(vault, "project-alpha")

      resolve_evidence_review(vault, evidence_id, decision="reject", reason="unsupported")
      reverified = verify_project_draft(vault, "project-alpha")

      assert reverified["ready"] is False
      with pytest.raises(ValueError, match="project draft is not export-ready"):
          write_project_export(vault, "project-alpha", draft=True)
  ```

- [ ] Run to verify the expected split:
  `python -m pytest tests/test_export_acceptance.py::test_blocked_export_names_its_findings tests/test_export_acceptance.py::test_rejected_disposition_leaves_export_blocked -v`
  Expected: the first **passes immediately** (a deliberate acceptance pin of
  shipped refusal naming — keep it); the second **fails against shipped
  behavior** (reject currently clears the hold and the export succeeds) and
  passes once V2R-B's flip is merged. If executing before V2R-B, mark it
  `@pytest.mark.xfail(strict=True, reason="V2R-B reject flip not yet merged")`
  and remove the mark in the same PR that merges V2R-B.

- [ ] Run the file green (post-V2R-B): `python -m pytest tests/test_export_acceptance.py -v`

- [ ] Commit:

  ```bash
  git add tests/test_export_acceptance.py
  git commit -m "test(export): refusal honesty — blocked exports name findings; reject leaves the hold blocking

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task V2R-D.6: `bibliography.bib` round-trip — structural bibtex parse (Zotero-import proxy)

No `pybtex`/`bibtexparser` dependency exists (verified: `pyproject.toml`
dependencies are `pydantic-ai-slim[openai]` and `PyYAML` only) and none is
added — the repo's own structural parser `parse_bibtex_entry`
(`capture.py:540-555`, the same machinery `capture-bibtex-source` trusts on
inbound entries) is the round-trip check: what it parses cleanly, Zotero's
BibTeX importer accepts (balanced containers, `@type{key, field = {value}}`).
The live Zotero import stays a manual acceptance step, named in V2R-D.7's docs.

**Files:**
- Modify: `tests/test_export_acceptance.py` (append one test)

**Interfaces:**
- Consumes: `write_references_bib_explicit(vault, *, actor, machine,
  output_path="bibliography.bib", commit=False) -> dict` (`capture.py:590-610`);
  `parse_bibtex_entry(text) -> {"entry_type", "citekey", "fields"}`
  (`capture.py:540`); entries joined by blank lines, ordered by `work_id`
  (`render_references_bib`, `capture.py:558-568`; `catalog_sources` ORDER BY,
  `state.py:1615-1627`).
- Produces: nothing new — the projection acceptance pin for spec §5/§8.

**Steps:**

- [ ] Write the test — append to `tests/test_export_acceptance.py`:

  ```python
  def test_bibliography_projection_round_trips_through_structural_bibtex_parse(
      tmp_path: Path,
  ) -> None:
      vault = tmp_path
      state.upsert_catalog_record(
          vault,
          work_id="work-alpha",
          title="Alpha & the {Braced} Title",
          check_status="checked",
          citekey="alpha2020",
          identifiers={"doi": "10.1000/alpha"},
          csl_json={
              "author": [{"family": "Müller", "given": "A."}],
              "issued": {"date-parts": [[2020]]},
              "container-title": "Journal of Tests",
          },
      )
      state.upsert_catalog_record(
          vault,
          work_id="work-beta",
          title="Beta",
          check_status="checked",
          citekey="beta2021",
      )

      write_references_bib_explicit(vault, actor="pi", machine="test-machine")

      text = (vault / "bibliography.bib").read_text(encoding="utf-8")
      chunks = [f"@{chunk}" for chunk in re.split(r"(?m)^@", text) if chunk.strip()]
      entries = [parse_bibtex_entry(chunk) for chunk in chunks]

      citekeys = [entry["citekey"] for entry in entries]
      assert citekeys == ["alpha2020", "beta2021"]
      assert len(set(citekeys)) == len(citekeys), "duplicate citekeys break Zotero import"
      for entry in entries:
          assert entry["entry_type"], "typeless entries break Zotero import"
          assert entry["fields"].get("title"), "titleless entries import as blanks"
      alpha = entries[0]["fields"]
      assert alpha.get("doi") == "10.1000/alpha"
      assert "Müller" in alpha.get("author", "")
      assert alpha.get("year") == "2020"
  ```

- [ ] Run: `python -m pytest tests/test_export_acceptance.py::test_bibliography_projection_round_trips_through_structural_bibtex_parse -v`
  Expected: **passes immediately** — a deliberate acceptance pin (like
  U3-ENG.5's forward-compat pin): it freezes the structural properties Zotero
  import depends on, so a future renderer change that emits duplicate keys,
  typeless entries, or unbalanced braces fails here first. Keep it. If any
  assertion fails, that is a real projection bug — stop and fix
  `_render_source_bibtex` (`capture.py:1056`) before proceeding.

- [ ] Commit:

  ```bash
  git add tests/test_export_acceptance.py
  git commit -m "test(export): bibliography.bib structural round-trip pin (Zotero-import proxy)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task V2R-D.7: Docs — best-effort export marking + evidence-review reference page

**Files:**
- Modify: `docs/reference/pipelines-and-io/export.md` (intro, lines 14–26)
- Modify: `docs/how-to-guides/project/export-a-draft.md` (step 2, lines 47–53;
  Verify list, lines 97–104)
- Create: `docs/reference/analysis-and-surfaces/evidence-review.md`
  (`nav_order: 6` — 1–5 are taken in that section)

**Interfaces:**
- Consumes: the doc-claims gate (`scripts/checks/doc_claims_gate.py`, wired in
  `scripts/verify:44`) — every `` `memoria <verb>` `` and every
  ``operation `<id>` `` citation must exist in the shipped surface. `memoria
  project export` and `memoria project resolve-evidence` exist today
  (`cli.py:328-334`); operation `resolve-evidence` exists after V2R-D.1;
  **`memoria review` exists only after slice 4 (V2R-C)** — until then the
  reference page names the CLI cockpit in prose without backticks.
- Produces: docs stating the PI ruling — markdown + `bibliography.bib` is the
  acceptance-tested target; `docx`/`pdf`/`odt` are best-effort — plus the review
  UI reference page.

**Steps:**

- [ ] Edit `docs/reference/pipelines-and-io/export.md` — replace the sentence at
  line 22 (`` `.docx`, `.pdf`, and `.odt` remain available when Pandoc is
  installed. ``) with:

  ```markdown
  Markdown plus the vault-wide `bibliography.bib` projection is the
  **acceptance-tested** export target: the verify gate proves every exported
  citation resolves against the inlined bibtex fence, that refused exports name
  their blocking findings, and that the projection parses cleanly for reference
  managers. `.docx`, `.pdf`, and `.odt` remain available when Pandoc is
  installed, as **best-effort** routes — exercised, not gate-tested.
  ```

- [ ] Edit `docs/how-to-guides/project/export-a-draft.md` — in step 2 (line 47),
  after "change `--format` and `--output`;" insert:

  ```markdown
  these Pandoc formats are best-effort (Markdown plus `bibliography.bib` is the
  acceptance-tested target);
  ```

  and add one Verify bullet (after line 100's citation bullet):

  ```markdown
  - For a reference-manager round-trip, import `bibliography.bib` into Zotero
    (File → Import) — every entry lands with type, title, and citekey intact
  ```

- [ ] Create `docs/reference/analysis-and-surfaces/evidence-review.md`:

  ```markdown
  ---
  title: Evidence-set review
  parent: Analysis and surfaces
  nav_order: 6
  grand_parent: Reference
  ---

  # Evidence-set review

  The evidence-set review surface routes the grounds contract's PI-clearable
  holds to one queue with two fronts: the Obsidian evidence-review pane
  (command: `Memoria: Open evidence review`) and the CLI review cockpit. Both
  read the same `view-spec.v1` payload from `GET /v1/views/evidence-review` and
  drive the same seam through the PI-only worker operation `resolve-evidence`.

  ## Queue

  Rows are evidence sets whose findings are `evidence-incomplete` or
  `review-required` and that carry no hold-clearing disposition. Rejected rows
  stay queued, rendered rejected; deferred rows are suppressed until the next
  UTC calendar day. Permanent blocks (`evidence-text-drift`,
  `evidence-text-unbound`, duplicates) are not reviewable: they render
  read-only, naming their cure (repair the draft marker, then re-verify).

  ## Row schema (fixed order)

  1. Claim text (the bound draft block, verbatim)
  2. Grounds items with resolved previews
  3. Why routed (the derivation rule, verbatim)
  4. Machine's argument-for / argument-against (both or neither)
  5. Tipped-by (the single routing factor)
  6. Coarse certainty (three levels)
  7. No verdict line; no pre-selected action

  Fields 1–3 (evidence) always render before fields 4–6 (machine analysis),
  and the analysis is collapsed by default behind a disclosure control — the
  PI reads the grounds before the machine's opinion, by construction.

  ## Dispositions

  | Action | Effect | Event |
  | --- | --- | --- |
  | Accept | clears the hold; bound to the items content — voided if items later change | `disposition.v1`, `decision=accept` |
  | Reject | the hold **stays blocking**; the row renders rejected | `disposition.v1`, `decision=reject` |
  | Edit | records fix-the-marker intent and deep-links the draft block; the hold clears only when the edit lands | `disposition.v1`, `decision=edit` |
  | Defer | the hold stays; the row is suppressed until the next UTC day | `disposition.v1`, `decision=defer` |

  Only accept clears holds. A rejected evidence set keeps blocking its
  project's draft export, which refuses naming the finding.

  ## Related

  - Export gates and refusal states: [Export routes and formats](../../reference/pipelines-and-io/export.md)
  - The works-cited projection behind the fence: [Bibliography](../../reference/evidence-and-integrations/bibliography.md)
  ```

  If slice 4 (V2R-C, `memoria review`) has already merged when this task
  executes, replace "the CLI review cockpit" with `` `memoria review` `` — the
  doc-claims gate confirms which form is legal.

- [ ] Run to verify: `python3 scripts/checks/doc_claims_gate.py` — expected
  `doc-claims-gate: clean` (it walks the real argparse tree and the manifest
  roster, so a premature `memoria review` citation fails here).

- [ ] Run the full gate: `python scripts/verify` — green.

- [ ] Commit:

  ```bash
  git add docs/reference/pipelines-and-io/export.md \
      docs/how-to-guides/project/export-a-draft.md \
      docs/reference/analysis-and-surfaces/evidence-review.md
  git commit -m "docs(export,review): mark docx/pdf/odt best-effort; add evidence-review reference page

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```
