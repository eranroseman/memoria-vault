# Alpha.21 Hardening Implementation Plan (review repairs + coverage remediation)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden shipped alpha.21: repair the four adversarially-confirmed review findings, remove the Hermes-era Telegram push leftover (PI ruling 2026-07-15), and close the ten confirmed-real coverage gaps from the coverage-remediation review.

**Architecture:** Three independent sections at existing seams. Tasks 21.1–21.4: CS3 scan findings routed to the durable inbox and printed in human scan output; CS1 neutralization moved inside the VaultWriter seam (default-deny for machine actors); two PI CLI write paths switched to the durable-write helper; `_fsync_dir` made honest. Task 21.5: delete the Telegram transport, keep the loudness/blocker mechanics. Tasks COV.0–COV.11: per `docs/superpowers/specs/2026-07-15-coverage-remediation-design.md` — test-only proofs of enforcement/audit/safety-net branches (plus the CI `mcp` extra, one gate hardening, and two cleanups).

**Tech Stack:** Python 3 / SQLite / pytest (existing repo toolchain; no new dependencies — COV.1 installs an already-declared optional extra in CI).

## Global Constraints

- Correctness gate: `python scripts/verify` must pass before merge; `main` requires a PR + `verify` and `gitleaks` checks; squash merge.
- Stage explicit paths only — never `git add -A` (shared git index per checkout).
- Test only against disposable vaults (`tmp_path` / `test-vault/`).
- New test files must be registered in `tests/conftest.py` `TEST_LEVELS` (Task 21.4 adds `"test_vaultio.py": "unit"`).
- All line refs verified against main @ `d85d8799`; re-anchor by quoted context if drifted.
- **Ordering:** COV.3 executes AFTER 21.1 (its inbox-alert assertions are written against 21.1's changed `write_finding` signature: `dedupe_slug` param, `Path | None` return). 21.5 must not run concurrently with 21.1 in separate worktrees (both edit `inbox.py`). COV.0 (PI confirm-at-review for the coverage spec's design decisions) precedes COV.1–COV.11. Everything else is independent, any order, one PR-sized unit each.
- Sequencing vs Plan 22: if executing concurrently with Plan 22's S68.3 or COST.4 (journal-hashed floor goldens), land those sequentially.

---
# PLAN 21 — Repair the four adversarially-confirmed alpha.21 review findings

All line numbers verified against the working tree at commit `d85d8799`.
Repo rule honored throughout: the git index is shared per checkout — every
commit stages explicit paths, never `git add -A`. The correctness gate is
`python scripts/verify`.

---

### Task 21.1: Route CS3 scan findings to the durable inbox surface and human scan output

CS3 foreign-edit / restriction-key-removal findings are built into the transient
scan result only (`trusted_writer.py:482-500`, appended at `:544`, `:549`,
`:949-951`, returned at `:605`). No consumer besides tests; the default
(non-JSON) `memoria workspace scan` output never prints them. Fix: (a) give the
existing inbox finding writer (`write_finding` in
`src/memoria_vault/runtime/subsystems/lib/inbox.py:75-113`) a `dedupe_slug`
stable-filename mode mirroring `write_work_prompt`'s (`inbox.py:163-172`),
(b) route every finding through it from `_observe_pi_edits_from_status`, and
(c) print one human-readable line per finding in `_cmd_workspace_scan`
(`cli.py:1797-1798`).

**Files:**
- Modify: `src/memoria_vault/runtime/subsystems/lib/inbox.py:75-113` (`write_finding` — add `dedupe_slug`)
- Modify: `src/memoria_vault/runtime/trusted_writer.py:28` (import), new helper after `:500`, call before return at `:605`
- Modify: `src/memoria_vault/cli.py:1797-1798` (`_cmd_workspace_scan` + new `_print_scan_findings`)
- Test: `tests/test_inbox_cards.py` (contract), `tests/test_trusted_writer.py` (runtime), `tests/test_cli_workspace_requests.py` (contract) — all already registered in `tests/conftest.py` `TEST_LEVELS`

**Interfaces:**
- Consumes: `write_finding` (inbox.py:75), `markdown_code_span` (already imported in trusted_writer.py:20), `_foreign_edit_finding` / `_restriction_key_removed_finding` dicts (trusted_writer.py:482-500), scan payload shape `payload["result"]["findings"]` (worker.py:876).
- Produces:
  - `write_finding(vault: Path, card_type: str, title: str, finding: str, raised_by: str, agent_recommendation: str = "issues-found", target: str = "", citekey: str = "", loudness: str = "alert", evidence: str = "", dedupe_slug: str = "") -> Path | None` — with `dedupe_slug` the filename is stable (`inbox/<card_type>-<slug>.md`) and an already-present card returns `None`.
  - `_route_finding_to_inbox(vault: Path, finding: Mapping[str, str]) -> None` (private, trusted_writer.py) — durable card per CS3 finding; card filename scheme `inbox/flag-cs3-foreign-edit-<hash12>-<subject-slug>.md` and `inbox/flag-cs3-restriction-key-removed-<subject-slug>-<key>.md`.
  - `_print_scan_findings(payload: dict[str, Any], args: argparse.Namespace) -> None` (private, cli.py) — human line format: `finding: <kind> <subject_id>` plus ` (key: <key>)` for restriction-key removals; suppressed under `--json` / `--quiet`.

**Steps:**

- [ ] Write the failing test for the `write_finding` dedupe mode. Append to `tests/test_inbox_cards.py` (style mirrors `test_work_prompt_dedupe_slug_is_idempotent` at line 131):

```python
def test_finding_dedupe_slug_is_idempotent(tmp_path):
    a = inbox.write_finding(
        tmp_path,
        "flag",
        "Foreign edit: notes/w.md",
        "changed outside the trusted writer",
        "workspace-scan",
        target="notes/w.md",
        dedupe_slug="cs3-foreign-edit-abc123-notes/w.md",
    )
    b = inbox.write_finding(
        tmp_path,
        "flag",
        "Foreign edit: notes/w.md",
        "changed outside the trusted writer",
        "workspace-scan",
        target="notes/w.md",
        dedupe_slug="cs3-foreign-edit-abc123-notes/w.md",
    )
    assert a is not None and a.name == "flag-cs3-foreign-edit-abc123-notes-w-md.md"
    assert b is None  # second emit for the same card id writes nothing
    assert len(list((tmp_path / "inbox").glob("*.md"))) == 1
```

- [ ] Run it and verify it fails: `python -m pytest tests/test_inbox_cards.py::test_finding_dedupe_slug_is_idempotent -v` — expected failure: `TypeError: write_finding() got an unexpected keyword argument 'dedupe_slug'`.
- [ ] Implement the dedupe mode. In `src/memoria_vault/runtime/subsystems/lib/inbox.py`, change the `write_finding` signature (line 75-86) to add the trailing parameter and return type:

```python
def write_finding(
    vault: Path,
    card_type: str,
    title: str,
    finding: str,
    raised_by: str,
    agent_recommendation: str = "issues-found",
    target: str = "",
    citekey: str = "",
    loudness: str = "alert",
    evidence: str = "",
    dedupe_slug: str = "",
) -> Path | None:
```

and replace its tail (lines 110-113):

```python
    body = f"# Finding\n\n{finding}\n"
    if evidence:
        body += f"\n# Evidence\n\n{evidence}\n"
    content = frontmatter_doc(frontmatter, body)
    if dedupe_slug:
        inbox = vault / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        path = inbox / f"{card_type}-{_slug(dedupe_slug)}.md"
        if path.exists():
            return None
        write_text_durable(path, content)
        loudness_routing.push_card(
            vault, path, {"title": title, "loudness": loudness, "type": card_type}
        )
        return path
    return _write(vault, card_type, title, content, loudness=loudness)
```

Also extend the docstring (line 87): `"""Write a flag/alert card that leads with the finding.

    With ``dedupe_slug`` the filename is stable and an already-present card is
    left untouched — returns None instead of a path.
    """`
- [ ] Run it and verify it passes: `python -m pytest tests/test_inbox_cards.py -v`.
- [ ] Write the failing runtime test for durable routing + rescan idempotence. Append to `tests/test_trusted_writer.py` (uses the file's existing `workspace`, `note_text`, `init_git`, `git`, `observe_pi_edits_from_status`, `read_frontmatter` helpers):

```python
def cs3_inbox_cards(vault: Path) -> list[Path]:
    inbox = vault / "inbox"
    return sorted(inbox.glob("flag-cs3-*.md")) if inbox.is_dir() else []


def test_observe_sweep_routes_findings_to_durable_inbox_cards(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    init_git(vault, "writer@example.invalid", "Trusted Writer")
    target = vault / "notes/witnessed.md"
    target.parent.mkdir(parents=True)
    original = note_text(title="Witnessed note").replace(
        "tags: []\n", "superseded: true\ntags: []\n"
    )
    target.write_text(original, encoding="utf-8")
    git(vault, "add", "--", "notes/witnessed.md")
    git(vault, "commit", "-m", "seed witnessed note")
    observe_pi_edits_from_status(vault, machine="test-machine")
    assert cs3_inbox_cards(vault) == []

    target.write_text(
        note_text(title="Witnessed note") + "\nChanged out of band.\n", encoding="utf-8"
    )
    git(vault, "add", "--", "notes/witnessed.md")
    git(vault, "commit", "-m", "foreign edit removing restriction key")
    result = observe_pi_edits_from_status(vault, machine="test-machine")

    assert sorted(finding["kind"] for finding in result["findings"]) == [
        "foreign-edit",
        "restriction-key-removed",
    ]
    cards = cs3_inbox_cards(vault)
    assert len(cards) == 2
    for card in cards:
        frontmatter = read_frontmatter(card)
        assert frontmatter["projection"] == "attention"
        assert frontmatter["attention_kind"] == "flag"
        assert frontmatter["target"] == "notes/witnessed.md"
        assert frontmatter["raised_by"] == "workspace-scan"
        assert frontmatter["loudness"] == "alert"

    rescan = observe_pi_edits_from_status(vault, machine="test-machine")
    assert sorted(finding["kind"] for finding in rescan["findings"]) == [
        "foreign-edit",
        "restriction-key-removed",
    ]
    assert cs3_inbox_cards(vault) == cards  # rescan mints no duplicate cards
```

- [ ] Run it and verify it fails: `python -m pytest tests/test_trusted_writer.py::test_observe_sweep_routes_findings_to_durable_inbox_cards -v` — expected failure: `AssertionError` at `assert len(cards) == 2` (cards is `[]`; nothing routes findings to the inbox yet).
- [ ] Implement the routing. In `src/memoria_vault/runtime/trusted_writer.py`, change line 28 to:

```python
from memoria_vault.runtime.subsystems.lib.inbox import write_finding, write_work_prompt
```

Insert after `_restriction_key_removed_finding` (after line 500):

```python
def _route_finding_to_inbox(vault: Path, finding: Mapping[str, str]) -> None:
    """Land one CS3 scan finding on the durable Inbox attention surface."""
    subject = str(finding["subject_id"])
    if finding["kind"] == "restriction-key-removed":
        key = str(finding["key"])
        title = f"Restriction key removed: {subject}"
        detail = (
            f"Restriction key {markdown_code_span(key)} was removed from "
            f"{markdown_code_span(subject)} outside the trusted writer; until "
            "reviewed the file can re-enter Ask and pass the export gate."
        )
        slug = f"cs3-restriction-key-removed-{subject}-{key}"
    else:
        current = str(finding["current_human_sha256"])
        title = f"Foreign edit: {subject}"
        detail = (
            f"{markdown_code_span(subject)} changed outside the trusted writer: "
            f"expected {markdown_code_span(str(finding['prior_human_sha256']))}, "
            f"found {markdown_code_span(current)}."
        )
        slug = f"cs3-foreign-edit-{current.removeprefix('sha256:')[:12]}-{subject}"
    write_finding(
        vault,
        "flag",
        title,
        detail,
        raised_by="workspace-scan",
        agent_recommendation="issues-found",
        target=subject,
        loudness="alert",
        dedupe_slug=slug,
    )
```

(The hash prefix leads the foreign-edit slug so `_slug`'s 60-char truncation can
never cut it off for long subject paths.) Then in `_observe_pi_edits_from_status`,
replace the return at line 605:

```python
    for finding in findings:
        _route_finding_to_inbox(vault, finding)
    return {"paths": targets, "observed": observed, "findings": findings, "commit": commit}
```

- [ ] Run it and verify it passes: `python -m pytest tests/test_trusted_writer.py::test_observe_sweep_routes_findings_to_durable_inbox_cards -v`.
- [ ] Write the failing CLI test for the human scan output. Append to `tests/test_cli_workspace_requests.py` (file already imports `main`, `json`, `Path`, `pytest`):

```python
def test_workspace_scan_prints_and_persists_cs3_findings(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    note = workspace / "notes/witness.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text(
        "---\n"
        "type: note\n"
        "id: 01KBN6V6KX0000000000000001\n"
        "title: Witness note\n"
        "tags: []\n"
        "links: {}\n"
        "---\n"
        "Witness body.\n",
        encoding="utf-8",
    )
    assert main(["workspace", "scan", "--workspace", str(workspace), "--json"]) == 0
    capsys.readouterr()  # first scan observes + baselines the note

    text = note.read_text(encoding="utf-8")
    note.write_text(text + "\nForeign out-of-band edit.\n", encoding="utf-8")

    assert main(["workspace", "scan", "--workspace", str(workspace)]) == 0
    out = capsys.readouterr().out
    assert "finding: foreign-edit notes/witness.md" in out
    cards = sorted((workspace / "inbox").glob("flag-cs3-foreign-edit-*notes-witness-md.md"))
    assert len(cards) == 1

    assert main(["workspace", "scan", "--workspace", str(workspace)]) == 0
    capsys.readouterr()
    rescanned = sorted((workspace / "inbox").glob("flag-cs3-foreign-edit-*notes-witness-md.md"))
    assert rescanned == cards  # rescan is idempotent on the durable surface
```

- [ ] Run it and verify it fails: `python -m pytest tests/test_cli_workspace_requests.py::test_workspace_scan_prints_and_persists_cs3_findings -v` — expected failure: `AssertionError` at `assert "finding: foreign-edit notes/witness.md" in out` (the human path prints only the `_success_detail` summary line).
- [ ] Implement the human output. In `src/memoria_vault/cli.py`, replace `_cmd_workspace_scan` (lines 1797-1798) with:

```python
def _cmd_workspace_scan(args: argparse.Namespace) -> int:
    payload = _workspace_scan_payload(args)
    _print_scan_findings(payload, args)
    return _emit(payload, args)


def _print_scan_findings(payload: dict[str, Any], args: argparse.Namespace) -> None:
    if args.json or args.quiet:
        return
    result = payload.get("result")
    findings = result.get("findings") if isinstance(result, dict) else None
    for finding in findings or []:
        kind = str(finding.get("kind") or "finding")
        subject = str(finding.get("subject_id") or "")
        key = str(finding.get("key") or "")
        suffix = f" (key: {key})" if key else ""
        print(f"finding: {kind} {subject}{suffix}")
```

- [ ] Run it and verify it passes: `python -m pytest tests/test_cli_workspace_requests.py::test_workspace_scan_prints_and_persists_cs3_findings -v`.
- [ ] Run the neighboring suites for fallout: `python -m pytest tests/test_trusted_writer.py tests/test_inbox_cards.py tests/test_cli_workspace_requests.py tests/test_journal_trust.py -q`.
- [ ] Run the gate: `python scripts/verify`.
- [ ] Commit:

```
git add src/memoria_vault/runtime/subsystems/lib/inbox.py src/memoria_vault/runtime/trusted_writer.py src/memoria_vault/cli.py tests/test_inbox_cards.py tests/test_trusted_writer.py tests/test_cli_workspace_requests.py
git commit -m "fix(scan): land CS3 findings on the durable inbox surface and human scan output

Foreign-edit and restriction-key-removal findings previously lived only in
the transient scan result. Route each through the inbox finding writer with
a stable dedupe slug, and print a summary line per finding in the default
(non-JSON) workspace scan output.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 21.2: Make CS1 neutralization VaultWriter-owned default-deny for machine actors

Spec `docs/superpowers/specs/2026-07-12-beta.1-content-security.md:38-42`
requires content-layer neutralization to run *inside* VaultWriter, default-deny,
before the write lands. Today the writer entry points `stage_concept`
(trusted_writer.py:663), `promote_checked` (:707), and `materialize_unchecked`
(:743) write bodies untouched; neutralization is caller-owned (knowledge.py).
Design decision already ratified in the review: neutralize inside the seam for
machine actors (`context.actor != "pi"`), PI-authored content exempt per the
spec's carve-outs. Existing per-caller neutralization calls stay (the transform
is documented idempotent, content_security.py:362-369); the seam becomes the
guarantee.

**Files:**
- Modify: `src/memoria_vault/runtime/trusted_writer.py:19-22` (import), `:679-680` (stage_concept), `:727` (promote_checked), `:753` (materialize_unchecked)
- Test: `tests/test_trusted_writer.py` (runtime, already registered)

**Interfaces:**
- Consumes: `neutralize_untrusted_markdown(body: str) -> str` (content_security.py:362, idempotent), `OperationContext.actor` (trusted_writer.py:54; `"pi"` is the sole exempt actor of `state.ACTORS = {"pi", "agent", "operation", "integrity"}`).
- Produces: no signature changes. Behavioral guarantee other sections may rely on: **any body written through `stage_concept`, `promote_checked`, or `materialize_unchecked` under a non-`pi` actor is `neutralize_untrusted_markdown`-clean on disk**; `pi`-actor bodies pass through byte-identical.

**Steps:**

- [ ] Write the failing tests. Append to `tests/test_trusted_writer.py` (uses existing `workspace`, `note_text`, `stage_concept`, `promote_checked` wrappers; add a module-level wrapper for `materialize_unchecked` beside the others at lines 42-68):

```python
from memoria_vault.runtime.trusted_writer import (
    materialize_unchecked as _materialize_unchecked,
)


def materialize_unchecked(vault: Path, *args, **kwargs):
    return call_with_context(_materialize_unchecked, vault, *args, **kwargs)


HOSTILE_BODY = (
    "Alpha body.\n\n"
    "![beacon](https://evil.test/pixel.png)\n"
    "<script>alert(1)</script>\n"
    "Visit https://evil.test/exfil now.\n"
)


def hostile_note_text() -> str:
    return note_text().replace("Alpha body.\n", HOSTILE_BODY)


def assert_neutralized(text: str) -> None:
    assert "![beacon]" not in text  # image embed made inert
    assert "<script>" not in text and "&lt;script" in text  # raw HTML escaped
    assert "](https://evil.test/pixel.png)" not in text  # no live link destination
    assert "`https://evil.test/exfil`" in text  # external URL is a code span


def test_stage_concept_neutralizes_machine_actor_bodies(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    stage_concept(vault, "notes/alpha.md", hostile_note_text(), machine="test-machine")

    staged = (vault / ".memoria/staging/notes/alpha.md").read_text(encoding="utf-8")
    assert_neutralized(staged)


def test_stage_concept_preserves_pi_authored_body(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    stage_concept(
        vault, "notes/alpha.md", hostile_note_text(), actor="pi", machine="test-machine"
    )

    staged = (vault / ".memoria/staging/notes/alpha.md").read_text(encoding="utf-8")
    assert "![beacon](https://evil.test/pixel.png)" in staged  # PI content not mangled


def test_promote_checked_neutralizes_even_when_the_stager_forgot(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    stage_concept(vault, "notes/alpha.md", note_text(), machine="test-machine")
    staged_path = vault / ".memoria/staging/notes/alpha.md"
    staged_path.write_text(hostile_note_text(), encoding="utf-8")  # bypassed neutralization

    promote_checked(vault, "notes/alpha.md", machine="test-machine")

    assert_neutralized((vault / "notes/alpha.md").read_text(encoding="utf-8"))


def test_materialize_unchecked_neutralizes_even_when_the_stager_forgot(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    stage_concept(vault, "notes/alpha.md", note_text(), machine="test-machine")
    staged_path = vault / ".memoria/staging/notes/alpha.md"
    staged_path.write_text(hostile_note_text(), encoding="utf-8")  # bypassed neutralization

    materialize_unchecked(vault, "notes/alpha.md", machine="test-machine")

    assert_neutralized((vault / "notes/alpha.md").read_text(encoding="utf-8"))
```

(Place the import beside the existing aliased imports at lines 12-37 and the wrapper beside the others; `call_with_context` defaults `actor="operation"`, a machine actor.)
- [ ] Run them and verify they fail: `python -m pytest tests/test_trusted_writer.py::test_stage_concept_neutralizes_machine_actor_bodies tests/test_trusted_writer.py::test_promote_checked_neutralizes_even_when_the_stager_forgot tests/test_trusted_writer.py::test_materialize_unchecked_neutralizes_even_when_the_stager_forgot -v` — expected failure: `AssertionError` in `assert_neutralized` at `assert "![beacon]" not in text` for all three (bodies land untouched). `test_stage_concept_preserves_pi_authored_body` passes vacuously today; keep it — it pins the carve-out.
- [ ] Implement the seam. In `src/memoria_vault/runtime/trusted_writer.py`, extend the import at lines 19-22:

```python
from memoria_vault.runtime.content_security import (
    markdown_code_span,
    neutralize_untrusted_markdown,
    neutralize_untrusted_markdown_fragment,
)
```

In `stage_concept`, after `frontmatter, body = split_frontmatter(content)` (line 679):

```python
    frontmatter, body = split_frontmatter(content)
    if context.actor != "pi":
        body = neutralize_untrusted_markdown(body)
    _validate_concept(contract, target, frontmatter)
```

In `promote_checked`, after the staged read (line 727):

```python
    frontmatter, body = split_frontmatter(staged_path.read_text(encoding="utf-8"))
    if context.actor != "pi":
        body = neutralize_untrusted_markdown(body)
```

In `materialize_unchecked`, after the staged read (line 753):

```python
    frontmatter, body = split_frontmatter(staged_path.read_text(encoding="utf-8"))
    if context.actor != "pi":
        body = neutralize_untrusted_markdown(body)
    output_path = vault / target
```

(Deliberately NOT in `_write_checked`: `mark_checked` re-checks live files whose
bodies may be PI-authored observed edits — neutralizing there would mangle
human content, violating the spec's carve-out. Double application across
stage→promote is safe: the transform is idempotent.)
- [ ] Run the new tests and verify they pass: `python -m pytest tests/test_trusted_writer.py -v -k "neutraliz or preserves_pi"`.
- [ ] Run the seam's consumer suites for mangling regressions (callers that already neutralize must be unaffected by the idempotent second pass): `python -m pytest tests/test_trusted_writer.py tests/test_knowledge.py tests/test_content_security.py tests/test_worker_knowledge_cycle.py -q`.
- [ ] Run the gate: `python scripts/verify`.
- [ ] Commit:

```
git add src/memoria_vault/runtime/trusted_writer.py tests/test_trusted_writer.py
git commit -m "fix(writer): own CS1 neutralization inside the VaultWriter seam

stage_concept, promote_checked, and materialize_unchecked now neutralize
machine-actor bodies default-deny per the content-security spec; PI-authored
content is exempt. Caller-side neutralization stays (idempotent) but the
seam is the guarantee.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 21.3: Make the steering and vocabulary PI write paths durable

`_cmd_steering_edit` (`src/memoria_vault/cli.py:2020`) and `_update_vocabulary`
(`cli.py:2891`) write PI-owned files with raw `Path.write_text`, bypassing the
crash-safe temp-file/fsync/rename path every other vault write uses. Switch
both to the existing `write_text_durable(path: Path, text: str, *, create_parent: bool = False) -> None`
(`src/memoria_vault/runtime/vaultio.py:170-171`, delegating to
`write_bytes_durable` at `:174-191`).

**Files:**
- Modify: `src/memoria_vault/cli.py:2010-2020` (`_cmd_steering_edit`), `:2862-2891` (`_update_vocabulary`)
- Test: `tests/test_cli_workspace_requests.py` (contract, already registered)

**Interfaces:**
- Consumes: `write_text_durable(path: Path, text: str, *, create_parent: bool = False) -> None` (vaultio.py:170). Both targets (`steering.md`, `system/vocabulary.md`) already exist when written (guarded at cli.py:2003/2876), so no `create_parent`.
- Produces: no new interfaces; behavioral guarantee: a failed replace during `memoria steering edit` / `memoria vocab add|rename|merge` leaves the original file byte-identical.

**Steps:**

- [ ] Write the failing test. Append to `tests/test_cli_workspace_requests.py`:

```python
def test_steering_and_vocabulary_writes_survive_a_failed_replace(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    steering = workspace / "steering.md"
    vocabulary = workspace / "system/vocabulary.md"
    steering_before = steering.read_text(encoding="utf-8")
    vocabulary_before = vocabulary.read_text(encoding="utf-8")

    import os

    def broken_replace(src, dst, *args, **kwargs):
        raise OSError("injected replace failure")

    monkeypatch.setattr(os, "replace", broken_replace)

    assert (
        main(
            [
                "steering",
                "edit",
                "--workspace",
                str(workspace),
                "--body",
                "Steering with [link](https://example.org).",
                "--json",
            ]
        )
        == 2
    )
    steering_error = json.loads(capsys.readouterr().out)
    assert "injected replace failure" in steering_error["error"]
    assert steering.read_text(encoding="utf-8") == steering_before

    assert (
        main(
            [
                "vocab",
                "add",
                "--workspace",
                str(workspace),
                "research_area",
                "alpha-topic",
                "--json",
            ]
        )
        == 2
    )
    vocabulary_error = json.loads(capsys.readouterr().out)
    assert "injected replace failure" in vocabulary_error["error"]
    assert vocabulary.read_text(encoding="utf-8") == vocabulary_before

    monkeypatch.undo()
    assert (
        main(
            [
                "steering",
                "edit",
                "--workspace",
                str(workspace),
                "--body",
                "Steering with [link](https://example.org).",
                "--json",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert steering.read_text(encoding="utf-8") == (
        "Steering with [link](https://example.org).\n"
    )  # PI steering content lands byte-exact, never neutralized
```

- [ ] Run it and verify it fails: `python -m pytest tests/test_cli_workspace_requests.py::test_steering_and_vocabulary_writes_survive_a_failed_replace -v` — expected failure: `AssertionError` at `assert steering.read_text(encoding="utf-8") == steering_before` (raw `write_text` mutated the file before the journal write raised; today the file is clobbered even though `main` exits 2).
- [ ] Implement the fix. In `src/memoria_vault/cli.py`, `_cmd_steering_edit` (lines 2010-2020) — extend the lazy import block and replace the write:

```python
def _cmd_steering_edit(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.trusted_writer import (
        append_explicit_journal_event,
        commit_explicit_writer_changes,
    )
    from memoria_vault.runtime.vaultio import write_text_durable

    _require_pi_actor(args, "steering edit")
    workspace = _workspace(args)
    body = args.body if args.body is not None else Path(args.file).read_text(encoding="utf-8")
    path = workspace / "steering.md"
    write_text_durable(path, body if body.endswith("\n") else f"{body}\n")
```

In `_update_vocabulary` (lines 2862-2891) — extend the lazy import block the same way and replace line 2891:

```python
    from memoria_vault.runtime.vaultio import write_text_durable
```

```python
    write_text_durable(path, text)
```

- [ ] Run it and verify it passes: `python -m pytest tests/test_cli_workspace_requests.py::test_steering_and_vocabulary_writes_survive_a_failed_replace -v`.
- [ ] Run the neighboring steering/vocab tests for fallout: `python -m pytest tests/test_cli_workspace_requests.py -q -k "steering or vocab"`.
- [ ] Run the gate: `python scripts/verify`.
- [ ] Commit:

```
git add src/memoria_vault/cli.py tests/test_cli_workspace_requests.py
git commit -m "fix(cli): write steering.md and vocabulary.md through write_text_durable

Raw Path.write_text on the two PI-owned write paths could clobber the file
on a mid-write failure. Route both through the crash-safe temp/fsync/rename
helper the rest of the vault already uses.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 21.4: Make `vaultio._fsync_dir` raise on failure, matching backup semantics

`vaultio._fsync_dir` (`src/memoria_vault/runtime/vaultio.py:204-214`) silently
swallows every directory-fsync `OSError` (and every `os.open` failure), while
`backup._fsync_directory` (`src/memoria_vault/runtime/backup.py:1390-1403`)
treats both as fatal on POSIX and tolerates them only on Windows
(`os.name == "nt"`) — verified: backup tolerates *only* the Windows case; there
is no EINVAL/ENOTSUP carve-out anywhere in the repo (`grep -rn "EINVAL\|ENOTSUP"`
→ 0 hits), so the honest mirror is backup's exact posture. Make `_fsync_dir`
identical to backup's semantics and pin it with the deterministic
fsync-injection pattern from `tests/test_backup_restore.py:926-975`.

**Files:**
- Create: `tests/test_vaultio.py`
- Modify: `src/memoria_vault/runtime/vaultio.py:204-214` (`_fsync_dir`)
- Modify: `tests/conftest.py:111` (register `test_vaultio.py` in `TEST_LEVELS`, level `unit` — same level as the neighboring pure-helper suite `test_runtime_helpers.py`)
- Test: `tests/test_vaultio.py`

**Interfaces:**
- Consumes: `os.fsync`, `os.open`; callers `write_bytes_durable` (vaultio.py:185) and `append_text_durable` (vaultio.py:201).
- Produces: `_fsync_dir(path: Path) -> None` (private) — raises `OSError` on directory open/fsync failure on POSIX; returns silently only on Windows (`os.name == "nt"`), byte-for-byte the semantics of `backup._fsync_directory`. Downstream guarantee: `write_bytes_durable` / `write_text_durable` / `append_text_durable` surface directory-durability failures instead of reporting silent success.

**Steps:**

- [ ] Register the new test file. In `tests/conftest.py`, after `"test_trusted_writer.py": "runtime",` (line 111) insert:

```python
    "test_vaultio.py": "unit",
```

- [ ] Write the failing tests. Create `tests/test_vaultio.py`:

```python
"""Durability contract for vaultio's atomic write helpers."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from memoria_vault.runtime import vaultio


def _fail_directory_fsync(real_fsync):
    """Deterministic injection: fail fsync only for directory fds.

    Mirrors the injected-fsync pattern of
    tests/test_backup_restore.py::test_restore_first_move_fsync_failure_preserves_original_wal.
    """

    def fsync(fd: int) -> None:
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError("injected directory fsync failure")
        real_fsync(fd)

    return fsync


def test_write_bytes_durable_surfaces_directory_fsync_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "note.md"
    monkeypatch.setattr(vaultio.os, "fsync", _fail_directory_fsync(os.fsync))

    with pytest.raises(OSError, match="injected directory fsync failure"):
        vaultio.write_bytes_durable(target, b"body\n")


def test_append_text_durable_surfaces_directory_fsync_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "journal.jsonl"
    monkeypatch.setattr(vaultio.os, "fsync", _fail_directory_fsync(os.fsync))

    with pytest.raises(OSError, match="injected directory fsync failure"):
        vaultio.append_text_durable(target, "{}\n", create_parent=True)

    assert target.read_text(encoding="utf-8") == "{}\n"  # data landed; durability failed loudly


def test_fsync_dir_raises_when_directory_cannot_be_opened(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_open = os.open

    def broken_open(path, flags, *args, **kwargs):
        if Path(path) == tmp_path:
            raise OSError("injected directory open failure")
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(vaultio.os, "open", broken_open)

    with pytest.raises(OSError, match="injected directory open failure"):
        vaultio._fsync_dir(tmp_path)
```

- [ ] Run them and verify they fail: `python -m pytest tests/test_vaultio.py -v` — expected failure: all three fail with `Failed: DID NOT RAISE <class 'OSError'>` (the current `_fsync_dir` swallows both the open error and the fsync error).
- [ ] Write the implementation. In `src/memoria_vault/runtime/vaultio.py`, replace `_fsync_dir` (lines 204-214) with the exact semantics of `backup._fsync_directory`:

```python
def _fsync_dir(path: Path) -> None:
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        if os.name == "nt":
            return
        raise
    try:
        os.fsync(fd)
    except OSError:
        if os.name != "nt":
            raise
    finally:
        os.close(fd)
```

- [ ] Run them and verify they pass: `python -m pytest tests/test_vaultio.py -v`.
- [ ] Run the write-path consumers for fallout (every durable write now inherits the raise): `python -m pytest tests/test_backup_restore.py tests/test_trusted_writer.py tests/test_journal_trust.py tests/test_inbox_cards.py -q`.
- [ ] Run the gate: `python scripts/verify`.
- [ ] Commit:

```
git add src/memoria_vault/runtime/vaultio.py tests/test_vaultio.py tests/conftest.py
git commit -m "fix(vaultio): raise on directory-fsync failure like backup does

_fsync_dir silently swallowed directory open/fsync errors while
backup._fsync_directory treats them as fatal on POSIX. Mirror backup's
exact posture (Windows-only tolerance) so durable writes stop reporting
silent success.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```
### Task 21.5: Remove the Hermes-era Telegram push transport (PI ruling 2026-07-15)

**Provenance:** PI ruling during the 2026-07-15 planning session: "We don't have
telegram. It sounds like a Hermes leftover." Verified: the transport landed with
PR #549 (2026-06-15, Hermes generation, pre-alpha.11-reset); the docs' planned
inbound path (#382, "Telegram inbound mobile-capture gateway") is CLOSED. The
loudness/blocker mechanics in the same module are current architecture (the
policy engine's `loudness.block.active` gate consumes `open_blockers`) and are
KEPT. Only the push transport goes. `design-history/` mentions are the frozen
record — do not touch.

**Files:**
- Modify: `src/memoria_vault/runtime/subsystems/lib/loudness.py` (delete
  `TELEGRAM_TOKEN_ENV`/`TELEGRAM_CHAT_ENV`/`TELEGRAM_API_BASE_ENV` at :26-28,
  `should_push` at :62, `_first_env` at :66, `_append_push_log` at :74,
  `push_card` at :78 through its end, and the `PUSH_LOG_RELPATH` constant;
  keep `is_open_blocker`, `open_blockers`, `blocker_message`; drop imports that
  become unused — check `json`/`urllib`/`os` usage after the cut)
- Modify: `src/memoria_vault/runtime/subsystems/lib/inbox.py:170` and
  `:185-187` (delete the two `loudness_routing.push_card(...)` calls; cards
  keep their `loudness` frontmatter) and `:15` (delete the now-unused
  `from memoria_vault.runtime.subsystems.lib import loudness as loudness_routing`)
- Modify: `tests/test_loudness.py` (rewrite; see steps)
- Modify: `docs/README.md:135`,
  `docs/explanation/architecture/README.md:45`,
  `docs/reference/evidence-and-integrations/integrations.md:84`,
  `docs/reference/system/failure-modes.md:26`
- Test: `tests/test_loudness.py`

**Interfaces:**
- Consumes: nothing from other tasks. Ordering vs 21.1: both edit files in the
  inbox/loudness family; either order works, but do not run concurrently in
  separate worktrees (same-file merge risk with `inbox.py`).
- Produces: `loudness.py` public surface shrinks to
  `is_open_blocker(frontmatter: dict[str, Any]) -> bool`,
  `open_blockers(vault: Path) -> list[dict[str, str]]`,
  `blocker_message(blockers: list[dict[str, str]]) -> str`. Removed symbols no
  task may reference: `push_card`, `should_push`, `PUSH_LOG_RELPATH`,
  `TELEGRAM_TOKEN_ENV`, `TELEGRAM_CHAT_ENV`, `TELEGRAM_API_BASE_ENV`.

- [ ] **Step 1: Rewrite the two push tests as no-push-log assertions (failing)**

Replace `tests/test_loudness.py` lines 1-39 (the module docstring, `json`
import, and the two push tests) with:

```python
"""Graded-loudness routing helpers."""

from memoria_vault.runtime.subsystems.lib import inbox, loudness


def test_alert_card_writes_no_push_log(tmp_path):
    inbox.write_finding(
        tmp_path, "alert", "Critical drift", "system is stopped", "linter", loudness="alert"
    )

    assert not (tmp_path / "system/push-log.jsonl").exists()
    assert not (tmp_path / ".memoria").exists() or not list(
        (tmp_path / ".memoria").rglob("push-log*")
    )


def test_notice_card_writes_no_push_log(tmp_path):
    inbox.write_proposal(
        tmp_path,
        "candidate",
        "Maybe",
        "read it",
        "useful",
        "weak",
        "gap",
        "likely",
        "librarian",
        loudness="notice",
    )

    assert not list(tmp_path.rglob("push-log*"))
```

Note: the first test's path assertions are written against wherever
`PUSH_LOG_RELPATH` currently points — read the constant before editing and use
`tmp_path.rglob("push-log*")` if the relpath differs; the intent is "no push
log anywhere". Keep `test_open_blockers_only_reads_open_block_attention_projections`
(lines 42-80) unchanged.

- [ ] **Step 2: Run tests to verify the alert-card test fails**

Run: `python -m pytest tests/test_loudness.py -v`
Expected: `test_alert_card_writes_no_push_log` FAILS (the transport still
writes a `not-configured` push-log row); the blocker test still passes.

- [ ] **Step 3: Delete the transport**

In `src/memoria_vault/runtime/subsystems/lib/loudness.py`: delete the three
`TELEGRAM_*` constants, `PUSH_LOG_RELPATH`, `should_push`, `_first_env`,
`_append_push_log`, and `push_card` (whole function). Remove imports that are
now unused (run `python -m ruff check src/memoria_vault/runtime/subsystems/lib/loudness.py`
to catch them). In `src/memoria_vault/runtime/subsystems/lib/inbox.py`: delete
line 170 (`loudness_routing.push_card(vault, path, {...})`), lines 185-187 (the
second `push_card` call), and the `:15` import alias.

- [ ] **Step 4: Run the module tests to verify green**

Run: `python -m pytest tests/test_loudness.py tests/test_inbox.py -v`
(if `tests/test_inbox.py` does not exist, run the inbox tests' actual home:
`grep -rln "write_finding\|write_proposal" tests/ | head` and run those files)
Expected: PASS across the board.

- [ ] **Step 5: Fix the four docs claims**

- `docs/README.md:135`: replace the bullet with:
  `- **Mobile capture is not available** — no push channel ships; inbound capture from a phone is out of scope for beta.1. See [Architecture](explanation/architecture/README.md#interaction-channels).`
  (drops the "urgent push (via Telegram) ships today" claim and the dead
  closed-issue #382 reference)
- `docs/explanation/architecture/README.md:45`: end the sentence at
  "remain pull-only." — delete ", while alert and block prompts may push to
  Telegram when configured".
- `docs/reference/evidence-and-integrations/integrations.md:84`: delete the
  entire `**Telegram Bot API**` table row.
- `docs/reference/system/failure-modes.md:26`: read the surrounding paragraph
  and delete the sentence fragment "alert/block prompts attempt a Telegram push
  only when that adapter is configured", rewording the remainder so the
  paragraph still reads (alert/block cards are pull-only inbox projections).

- [ ] **Step 6: Repo-wide leftover sweep**

Run: `grep -rni "telegram" src/ tests/ docs/ scripts/ .github/ --include="*" | grep -v design-history`
Expected: zero hits. (`design-history/` keeps its mentions — frozen record.)

- [ ] **Step 7: Full gate + commit**

Run: `python scripts/verify`
Expected: PASS.

```bash
git add src/memoria_vault/runtime/subsystems/lib/loudness.py \
        src/memoria_vault/runtime/subsystems/lib/inbox.py \
        tests/test_loudness.py \
        docs/README.md \
        docs/explanation/architecture/README.md \
        docs/reference/evidence-and-integrations/integrations.md \
        docs/reference/system/failure-modes.md
git commit -m "refactor: remove Hermes-era Telegram push transport (PI ruling; loudness/blocker mechanics kept)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```
# Plan 21 — Coverage remediation (COV)

Governing spec: `docs/superpowers/specs/2026-07-15-coverage-remediation-design.md`.
All line refs below were re-verified against the current checkout (origin/main,
clean); where the spec's refs drifted, the real lines are cited and the drift
noted.

**Ordering and independence.** Every COV task is independent of every other COV
task and of the rest of Plan 21, with exactly two exceptions: COV.1 goes first
and stands alone (spec decision — highest value-to-effort), and **COV.3 executes
AFTER Task 21.1** (Task 21.1 changes the `write_finding` signature that COV.3's
inbox-alert assertion is written against). Tasks may otherwise be picked off in
any order or split across PRs.

**TDD shape for test-only tasks.** Items 2–6 and 8–10 add tests to existing,
correct production code, so a freshly written test passes immediately. The red
step for those tasks is therefore a *bite proof*: a named one-line temporary
mutation of the production code, the exact command, the exact expected failure,
then restore. COV.7's hardening half and COV.11 are the only production-code
changes, and COV.7's hardening test runs true red-green.

**No new test files anywhere in this section** — every test extends an existing
file already registered in `tests/conftest.py` `TEST_LEVELS`, so no conftest
change is needed by any COV task.

**Execution-time discovery (feeds COV.0 and COV.7).** The `.agents` search root
listed in `scripts/checks/removed_surfaces.json` does not exist in the repo
(`ls -d .agents` → no such directory), yet `python
scripts/checks/removed_surface_gate.py` prints `removed-surface-gate: clean` —
the silent skip at `removed_surface_gate.py:97-98` is masking a stale root
*right now*. COV.7's hardening therefore must also drop the stale `.agents`
entry from the contract, or the hardened gate fails on the real repo.

## Out of scope (ruled acceptable — do not re-litigate)

- `scripts/verify` — `main()`/`run()` never fire under pytest by design (would recursively re-run the whole `GATES` roster); CI runs it directly as a real integration check on every PR.
- `scripts/test_vault/e2e_smoke.py` — the literal e2e smoke test, run wholesale and unmocked as its own `GATES` entry; mocking it to gain coverage credit would defeat its purpose.
- `tests/test_live_runner.py` — correctly, doubly gated (marker + runtime live-endpoint check); the one intentional opt-in real-network proof.
- `scripts/test_vault/test_env_harness.py` — missing branches are unhappy-path shapes the one golden cassette never triggers; ordinary passing-test shadow, not a real gap.
- `scripts/checks/plugin_provenance_doctor.py` — its actual violation-detecting logic is well covered; remaining misses are an argparse/print shim and a TOCTOU-only defensive branch.
- `src/memoria_vault/runtime/state.py` — bulk of its misses is Windows-only code that cannot run on Linux CI (see COV.11a for the pragma fix); the rest is defense-in-depth re-checks and a `supersede_request_id` path unreachable through any current caller.
- `src/memoria_vault/runtime/backup.py` — 134 misses scattered across a module already carrying 90 dedicated tests; remaining gaps mostly require forging on-disk transaction files or injecting real `OSError`s mid-copy.
- `src/memoria_vault/runtime/subsystems/integrity/linter/hub_handoff.py` — the uncovered parse-failure branch guards two already-implicitly-synced strings; `main()` is thin CLI wiring with no independent policy logic.
- `src/memoria_vault/runtime/paths.py`'s `resolve_vault()` — no caller anywhere in `src/`/`tests/` beyond its own definition; a deletion candidate per the repo's "prefer deletion > mechanism" bias — flagged for a follow-up decision, not resolved by this spec.
- `src/memoria_vault/runtime/code/runner.py`'s `bwrap` sandbox path (lines 30-38, 68-89, 100-143, 167-182 per spec) — correctly fail-closed on an absent `bwrap` binary; deferred until wired to a live operation.

---

### Task COV.0: PI confirm-at-review checkpoint (no code)

**Files:** none (review gate only).
**Interfaces:** none.

- [ ] Confirm with the PI, at plan review, the spec's "Design decisions (made here; confirm at review)" plus two execution-time additions:
  1. Scope is exactly the ten items (2–10 test-only, 1 CI-config) plus cleanups 11a/11b; the out-of-scope list above stands as ruled-acceptable and is not re-litigated.
  2. Item 1 (CI `mcp` extra) goes first and stands alone; the chosen mechanism is the `verify.yml` install step, not `requirements-dev.txt` (reason stated in COV.1).
  3. Items 2–10 are mutually independent; any order, any PR split — except COV.3's ordering after Task 21.1 (post-21.1 `write_finding` signature).
  4. No production behavior changes anywhere **except**: (a) the COV.7 missing-search-root hard failure, which the spec itself names as a design hardening, and (b) the newly discovered removal of the stale `.agents` search root from `scripts/checks/removed_surfaces.json` that the hardening forces (evidence: the root does not exist today and the gate still reports clean). 11a/11b remain a pragma and a dead-code deletion.
  5. The `code/runner.py` bwrap-sandbox path stays deferred until the runtime primitive is wired to a live operation.

---

### Task COV.1: CI installs the `mcp` optional extra (CI-config, not TDD)

**Files:**
- Modify: `/home/eranr/memoria-vault/.github/workflows/verify.yml` (install step, lines 41-44)
- Read-only context: `/home/eranr/memoria-vault/pyproject.toml:18-19` (`[project.optional-dependencies] mcp = ["mcp>=1.27"]`), `/home/eranr/memoria-vault/requirements-dev.txt` (header scopes it to contributor tooling), `/home/eranr/memoria-vault/tests/test_mcp_transport.py` (8 of 11 tests open with `pytest.importorskip("mcp")`)
- Test: `tests/test_mcp_transport.py` (already written; no new test code)

**Interfaces:**
- Consumes: `verify.yml` "Install runtime + dev tooling" step: `python -m pip install --quiet -r requirements-dev.txt` / `python -m pip install --quiet -e .`
- Produces: CI installs `-e ".[mcp]"`; the 8 previously-skipped tests in `tests/test_mcp_transport.py` run in the required `verify` check.

**Decision (per the spec's own two options): change `verify.yml`, not `requirements-dev.txt`.**
Reason: `requirements-dev.txt`'s own header says "Runtime package dependencies
live in pyproject.toml", and `mcp` is a declared runtime optional extra whose
version constraint (`mcp>=1.27`) is already owned by `pyproject.toml`. Adding a
second pin in requirements-dev would create a drift-prone duplicate; installing
the extra keeps a single source of truth. Known trade-off, acceptable: the pip
cache key (`cache-dependency-path: requirements-dev.txt`) will not track the
extra, so `mcp` installs uncached — it is a small offline pure-pip wheel with no
live service or secret behind it.

- [ ] Record the red state: run `python -m pytest tests/test_mcp_transport.py -v -rs` and confirm 3 passed, 8 skipped with reason `could not import 'mcp'` (every test from `test_mcp_app_requires_non_root_read_scope` at line 89 onward).
- [ ] Edit `.github/workflows/verify.yml` line 44: change `python -m pip install --quiet -e .` to `python -m pip install --quiet -e ".[mcp]"`.
- [ ] Prove it locally exactly as CI will see it: run `python -m pip install -e ".[mcp]"`, then `python -m pytest tests/test_mcp_transport.py -v -rs` — expect 11 passed, 0 skipped.
- [ ] Run `python scripts/verify` to confirm the full gate stays green with the extra installed.
- [ ] Commit:
  ```
  git add .github/workflows/verify.yml
  git commit -m "ci: install the mcp extra so mcp transport tests run in verify

  mcp>=1.27 is a declared optional runtime extra in pyproject.toml;
  installing -e \".[mcp]\" (not a requirements-dev pin) keeps the version
  constraint single-sourced. Unskips the 8 gated tests in
  tests/test_mcp_transport.py in the required CI gate.

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task COV.2: `policy/hook.py` — audit deny-path and completion-failure handler

**Files:**
- Modify (tests only): `/home/eranr/memoria-vault/tests/test_policy_hook.py` (append after `test_evaluate_pre_prunes_stale_pending_stashes_but_keeps_fresh_stashes`, line 311)
- Read-only production: `/home/eranr/memoria-vault/src/memoria_vault/runtime/policy/hook.py` — `_audit_tool_policy_block` at 232-261 (body past the `action is None` check: 238-261; `append_audit` deny row 247-259), call site in `evaluate_pre` at 322; `evaluate_post` at 380-440 (exception handler 413-434; `record_event(..., code="audit_completion_failed")` at 422-432). Spec refs verified — no drift.
- Test: `tests/test_policy_hook.py` (registered `contract` in `TEST_LEVELS` — no conftest change)

**Interfaces:**
- Consumes: `evaluate_pre(payload: dict, actor: str, workspace: Path) -> dict`; `evaluate_post(payload: dict, actor: str, workspace: Path) -> dict`; `append_audit(vault: Path, entry: dict) -> None` (writes `system/logs/audit.jsonl`); `record_event(*, component, level, code, payload=None, details=None, vault_path=None, state_dir=None, now=None) -> dict | None` (honors `MEMORIA_DIAGNOSTICS_DIR`); `PolicyEngine.complete_write(actor, action, path, request_id, before_hash)`.
- Produces: tests `test_denied_write_tool_lands_a_deny_row_in_the_audit_log`, `test_evaluate_post_records_completion_failure_and_still_unlinks_stash`.

- [ ] Write the failing test (deny-path audit) at the end of `tests/test_policy_hook.py`, mirroring the file's `_m`-alias style (no new imports needed):

  ```python
  def test_denied_write_tool_lands_a_deny_row_in_the_audit_log(tmp_path):
      vault = _vault_with_policy(tmp_path)

      blocked = evaluate_pre(
          {
              "tool_name": "obsidian_patch_content",
              "tool_input": {"filepath": "inbox/a.md"},
              "extra": {"request_id": "REQ-DENY-1"},
          },
          "readonly",
          vault,
      )

      audit_log = vault / "system" / "logs" / "audit.jsonl"
      rows = (
          [json.loads(line) for line in audit_log.read_text(encoding="utf-8").splitlines()]
          if audit_log.is_file()
          else []
      )
      denies = [row for row in rows if row.get("decision") == "deny"]

      assert blocked.get("decision") == "block"
      assert "tool allowlist" in blocked["reason"]
      assert len(denies) == 1
      assert denies[0]["actor"] == "readonly"
      assert denies[0]["action"] == "write"
      assert denies[0]["path"] == "inbox/a.md"
      assert denies[0]["request_id"] == "REQ-DENY-1"
      assert denies[0]["policy_rule"] == "tool-policy.allowlist"
      assert "tool allowlist" in denies[0]["message"]
  ```

  (The `readonly` actor in the file's `POLICY_CONFIG` allows only read tools, so
  `obsidian_patch_content` is denied by the allowlist with a valid
  path+request_id — exactly the branch at `hook.py:238-259`.)
- [ ] Prove the test bites: temporarily comment out the `_audit_tool_policy_block(...)` call at `hook.py:322`, run `python -m pytest tests/test_policy_hook.py::test_denied_write_tool_lands_a_deny_row_in_the_audit_log -v` — expect `AssertionError` at `assert len(denies) == 1` (0 rows). Restore the line, rerun, expect PASS.
- [ ] Write the failing test (completion-failure handler) below it:

  ```python
  def test_evaluate_post_records_completion_failure_and_still_unlinks_stash(
      tmp_path, monkeypatch, capsys
  ):
      vault = _vault_with_policy(tmp_path / "vault")
      diag = tmp_path / "diagnostics"
      monkeypatch.setenv("MEMORIA_DIAGNOSTICS_DIR", str(diag))
      monkeypatch.setenv("MEMORIA_DIAGNOSTIC_LEVEL", "warn")
      (vault / "inbox").mkdir(parents=True, exist_ok=True)
      from memoria_vault.runtime.policy import EMPTY_SHA256, PolicyEngine

      def boom(self, *args, **kwargs):
          raise RuntimeError("simulated completion failure")

      monkeypatch.setattr(PolicyEngine, "complete_write", boom)
      payload = {
          "tool_name": "obsidian_put_content",
          "tool_input": {"filepath": "inbox/round.md"},
          "extra": {"request_id": "REQ-FAIL-1", "tool_call_id": "call-fail"},
      }
      stash = _pending_file(vault, _stash_key(payload))
      stash.parent.mkdir(parents=True, exist_ok=True)
      stash.write_text(
          json.dumps({"before_hash": EMPTY_SHA256, "path": "inbox/round.md"}),
          encoding="utf-8",
      )
      (vault / "inbox" / "round.md").write_text("answer body", encoding="utf-8")

      post = evaluate_post(payload, "adapter", vault)

      events = [
          json.loads(line)
          for log in sorted(diag.glob("diagnostics-*.jsonl"))
          for line in log.read_text(encoding="utf-8").splitlines()
          if line.strip()
      ]
      assert post == {}
      assert not stash.exists()
      assert "audit completion failed" in capsys.readouterr().err
      assert [event["code"] for event in events] == ["audit_completion_failed"]
      assert events[0]["component"] == "adapter.policy_hook"
      assert events[0]["level"] == "error"
      assert set(events[0]["details"]) == {"actor", "path", "exception_type"}
      assert not (vault / "system" / "logs" / "audit.jsonl").exists()
  ```

  (Diagnostics dir is a tmp sibling of the vault: `assert_outside_vault` rejects
  paths inside the vault or the repo worktree, and `record_event` honors
  `MEMORIA_DIAGNOSTICS_DIR`. `evaluate_post` re-imports `PolicyEngine` inside
  the function, but patching the class attribute reaches it.)
- [ ] Prove the test bites: temporarily replace the `record_event(...)` call at `hook.py:422-432` with `pass`, run `python -m pytest tests/test_policy_hook.py::test_evaluate_post_records_completion_failure_and_still_unlinks_stash -v` — expect `AssertionError` at the `["audit_completion_failed"]` comparison (got `[]`). Restore, rerun, expect PASS.
- [ ] Run the whole file: `python -m pytest tests/test_policy_hook.py -v` — all pass.
- [ ] Commit:
  ```
  git add tests/test_policy_hook.py
  git commit -m "test(policy): cover hook deny-path auditing and completion-failure recording

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task COV.3: `retraction.py` — `sweep()`, `check_doi()` offline warning, severity tie-break

**ORDERING: execute AFTER Task 21.1.** Task 21.1 changes `write_finding`; this
task's inbox-alert assertions are written against the **post-21.1** signature
(see Consumes). `retraction.py:321-333` passes no `dedupe_slug` today, so the
first-write behavior this test observes (one alert card written) is identical
under both signatures; the assertions below are deliberately filename-agnostic
(glob + frontmatter) so they also hold if 21.1 wires a `dedupe_slug` into this
call site.

**Files:**
- Modify (tests only): `/home/eranr/memoria-vault/tests/test_sweeps_retraction.py` (extend aliases at lines 5-11; append tests after line 127)
- Read-only production: `/home/eranr/memoria-vault/src/memoria_vault/runtime/subsystems/integrity/retraction/retraction.py` — `build_rw_index` at 97-115 (tie-break at 112-114), `check_doi` at 255-300 (one-time offline no-CSV stderr warning at 273-283, `_warned_no_csv` flag at 47), `sweep` at 303-334 (`write_finding` call at 321-333, no `dedupe_slug` passed), `rw_csv_path` honoring `MEMORIA_RW_CSV` at 71-76, module cache `_RW_INDEX` at 46. Spec refs verified — no drift. NOTE: the spec/prompt shorthand "retraction.py" resolves to this subsystems path, not `runtime/retraction.py`.
- Test: `tests/test_sweeps_retraction.py` (registered `contract` — no conftest change)

**Interfaces:**
- Consumes: `sweep(vault: Path, offline: bool = True) -> dict` (returns `{"checked": int, "retracted": int}`); `check_doi(doi: str, offline: bool = False) -> dict`; `build_rw_index(rows) -> dict[str, dict]`; and — post-Task-21.1 — `write_finding(vault, card_type, title, finding, raised_by, agent_recommendation="issues-found", target="", citekey="", loudness="alert", evidence="", dedupe_slug="") -> Path | None` (Task 21.1 of this plan changes it; COV.3 runs after 21.1).
- Produces: tests `test_build_rw_index_severity_tie_break_keeps_retraction_over_concern`, `test_sweep_flags_a_retracted_cited_source_with_an_inbox_alert`, `test_check_doi_offline_warns_once_when_rw_csv_is_missing`.

- [ ] Extend the alias block at the top of `tests/test_sweeps_retraction.py` (after line 11, matching the existing `_m` style):

  ```python
  check_doi = _m.check_doi
  read_frontmatter = _m.read_frontmatter
  sweep = _m.sweep
  ```
- [ ] Write the failing test (severity tie-break) at the end of the file:

  ```python
  def test_build_rw_index_severity_tie_break_keeps_retraction_over_concern():
      rows = [
          {
              "OriginalPaperDOI": "10.1/Twice",
              "RetractionNature": "Expression of Concern",
              "RetractionDate": "2020-02-02",
              "RetractionDOI": "10.1/rw-eoc2",
          },
          {
              "OriginalPaperDOI": "10.1/Twice",
              "RetractionNature": "Retraction",
              "RetractionDate": "2021-05-03",
              "RetractionDOI": "10.1/rw-ret2",
          },
      ]

      idx = build_rw_index(rows)
      idx_reversed = build_rw_index(list(reversed(rows)))

      assert idx["10.1/twice"]["retracted"] is True
      assert idx["10.1/twice"]["nature"] == "Retraction"
      assert idx["10.1/twice"]["retraction_doi"] == "10.1/rw-ret2"
      assert idx_reversed["10.1/twice"]["nature"] == "Retraction"
  ```
- [ ] Prove the test bites: temporarily change `retraction.py:113` from `if prev is None or (rec["retracted"] and not prev["retracted"]):` to `if prev is None:`, run `python -m pytest tests/test_sweeps_retraction.py::test_build_rw_index_severity_tie_break_keeps_retraction_over_concern -v` — expect `AssertionError` at `nature == "Retraction"` (got `'Expression of Concern'`). Restore, rerun, expect PASS.
- [ ] Write the failing test (offline sweep writes the Inbox alert) below it:

  ```python
  def test_sweep_flags_a_retracted_cited_source_with_an_inbox_alert(tmp_path, monkeypatch):
      vault = tmp_path / "vault"
      retracted_note = vault / "catalog" / "sources" / "smith2020" / "source.md"
      retracted_note.parent.mkdir(parents=True)
      retracted_note.write_text(
          "---\ntype: source\ncitekey: smith2020\ndoi: 10.1/Retracted\n---\nBody.\n",
          encoding="utf-8",
      )
      clean_note = vault / "catalog" / "sources" / "jones2021" / "source.md"
      clean_note.parent.mkdir(parents=True)
      clean_note.write_text(
          "---\ntype: source\ncitekey: jones2021\ndoi: 10.1/Clean\n---\nBody.\n",
          encoding="utf-8",
      )
      rw_csv = tmp_path / "rw.csv"
      with rw_csv.open("w", newline="", encoding="utf-8") as f:
          w = csv.DictWriter(
              f,
              fieldnames=["OriginalPaperDOI", "RetractionNature", "RetractionDate", "RetractionDOI"],
          )
          w.writeheader()
          w.writerows(RW_ROWS)
      monkeypatch.setenv("MEMORIA_RW_CSV", str(rw_csv))
      for var in (
          "MEMORIA_TELEGRAM_BOT_TOKEN",
          "TELEGRAM_BOT_TOKEN",
          "MEMORIA_TELEGRAM_CHAT_ID",
          "TELEGRAM_CHAT_ID",
      ):
          monkeypatch.delenv(var, raising=False)

      _m._RW_INDEX = None
      try:
          result = sweep(vault, offline=True)
      finally:
          _m._RW_INDEX = None

      cards = sorted((vault / "inbox").glob("alert-*.md"))
      assert result == {"checked": 2, "retracted": 1}
      assert len(cards) == 1
      fm = read_frontmatter(cards[0])
      assert fm["attention_kind"] == "alert"
      assert fm["target"] == "catalog/sources/smith2020/source.md"
      assert fm["citekey"] == "smith2020"
      assert fm["raised_by"] == "sweep"
      assert fm["loudness"] == "alert"
      assert "10.1/Retracted is retracted" in str(fm["finding"])
  ```

  Step notes: (1) written against the post-21.1 `write_finding` signature — no
  `dedupe_slug` is passed by `retraction.py:321-333`, so a card is written and
  the assertions are card-content-based, not filename-based; (2) `RW_ROWS`
  (file lines 13-26) already carries `10.1/Retracted` as a real Retraction, and
  `10.1/Clean` is absent from the CSV so the second source counts as checked
  but not retracted; (3) the Telegram env vars are cleared because an `alert`
  card is push-loudness and a developer's real token would otherwise trigger a
  live push; (4) `_RW_INDEX` reset mirrors the file's existing cache hygiene.
- [ ] Prove the test bites: temporarily change `retraction.py:318` from `if result.get("retracted"):` to `if False:`, run `python -m pytest tests/test_sweeps_retraction.py::test_sweep_flags_a_retracted_cited_source_with_an_inbox_alert -v` — expect `AssertionError` at `result == {"checked": 2, "retracted": 1}` (got `retracted: 0`). Restore, rerun, expect PASS.
- [ ] Write the failing test (one-time offline no-CSV warning) below it:

  ```python
  def test_check_doi_offline_warns_once_when_rw_csv_is_missing(tmp_path, monkeypatch, capsys):
      monkeypatch.setenv("MEMORIA_RW_CSV", str(tmp_path / "missing.csv"))
      _m._RW_INDEX = None
      _m._warned_no_csv = False
      try:
          first = check_doi("10.1/x", offline=True)
          second = check_doi("10.1/y", offline=True)
      finally:
          _m._RW_INDEX = None
          _m._warned_no_csv = False

      err = capsys.readouterr().err
      assert err.count("Retraction Watch CSV not found") == 1
      assert first["retracted"] is None
      assert "UNKNOWN" in first["note"]
      assert second["retracted"] is None
  ```
- [ ] Prove the test bites: temporarily comment out the `print(...)` warning block at `retraction.py:277-283`, run `python -m pytest tests/test_sweeps_retraction.py::test_check_doi_offline_warns_once_when_rw_csv_is_missing -v` — expect `AssertionError` at `err.count(...) == 1` (got 0). Restore, rerun, expect PASS.
- [ ] Run the whole file: `python -m pytest tests/test_sweeps_retraction.py -v` — all pass.
- [ ] Commit:
  ```
  git add tests/test_sweeps_retraction.py
  git commit -m "test(retraction): cover sweep, offline no-CSV warning, and severity tie-break

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task COV.4: `diagnostics.py` — content-light sequences/objects and raw-bundle re-redaction

**Files:**
- Modify (tests only): `/home/eranr/memoria-vault/tests/test_diagnostics.py` (append after `test_redaction_self_test_blocks_known_sensitive_strings`, line 151)
- Read-only production: `/home/eranr/memoria-vault/src/memoria_vault/runtime/diagnostics.py` — `_content_light` at 81-91 (list/tuple/set branch 89-90, `str(value)` fallback 91), `create_redacted_bundle` re-redaction of `payload_redacted` at 237-238. Spec refs verified — no drift.
- Test: `tests/test_diagnostics.py` (registered `unit` — no conftest change)

**Interfaces:**
- Consumes: `record_event(*, component, level, code, payload=None, details=None, vault_path=None, state_dir=None, now=None) -> dict | None`; `create_redacted_bundle(output: Path, *, state_dir=None, include_raw: bool = False) -> Path`; `RAW_ONCE_ENV = "MEMORIA_DIAGNOSTIC_RAW_ONCE"`.
- Produces: tests `test_content_light_hashes_sequence_items_and_arbitrary_objects`, `test_redacted_bundle_include_raw_re_redacts_captured_payloads`.

- [ ] Write the failing test (content-light sequences and object fallback), mirroring the file's fixture style:

  ```python
  def test_content_light_hashes_sequence_items_and_arbitrary_objects(tmp_path, monkeypatch):
      state = tmp_path / "state"
      monkeypatch.setenv("MEMORIA_DIAGNOSTIC_LEVEL", "warn")

      class Opaque:
          def __str__(self) -> str:
              return "opaque-secret-body"

      event = diagnostics.record_event(
          component="ingest",
          level="error",
          code="sequence_details",
          details={
              "titles": ["Secret Draft", "Second Secret"],
              "pair": ("left-secret", 2),
              "opaque": Opaque(),
          },
          state_dir=state,
          now=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
      )

      text = (state / "diagnostics-2026-06-19.jsonl").read_text(encoding="utf-8")
      assert event["details"]["titles"][0]["sha256"]
      assert event["details"]["titles"][1]["length"] > 0
      assert event["details"]["pair"][0]["sha256"]
      assert event["details"]["pair"][1] == 2
      assert event["details"]["opaque"]["sha256"]
      for secret in ("Secret Draft", "Second Secret", "left-secret", "opaque-secret-body"):
          assert secret not in text
  ```
- [ ] Prove the test bites: temporarily change `diagnostics.py:89-90` (the `list | tuple | set` branch) to `return value`, run `python -m pytest tests/test_diagnostics.py::test_content_light_hashes_sequence_items_and_arbitrary_objects -v` — expect failure (either `AssertionError: assert 'Secret Draft' not in text` or a `TypeError` on the dict subscript — both prove the branch is load-bearing). Restore, rerun, expect PASS.
- [ ] Write the failing test (include_raw re-redaction) below it. It follows the spec's prescribed shape (raw-once env var, secret payload, `include_raw=True`) and additionally seeds one forged log row whose `payload_redacted` still holds a raw secret — the exact input the defensive re-redaction at 237-238 exists for:

  ```python
  def test_redacted_bundle_include_raw_re_redacts_captured_payloads(tmp_path, monkeypatch):
      state = tmp_path / "state"
      state.mkdir(parents=True)
      forged = {
          "timestamp": "2026-06-19T12:00:00Z",
          "component": "bundle",
          "level": "error",
          "code": "imported_row",
          "raw_capture": "ephemeral-redacted",
          "payload_redacted": "Bearer forgedtokenabcdefghijklmn body text",
      }
      (state / "diagnostics-2026-06-19.jsonl").write_text(
          json.dumps(forged) + "\n", encoding="utf-8"
      )
      monkeypatch.setenv(diagnostics.RAW_ONCE_ENV, "1")
      diagnostics.record_event(
          component="bundle",
          level="error",
          code="raw_once_bundle",
          payload="api_key=0123456789abcdef",
          state_dir=state,
          now=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
      )

      bundle = diagnostics.create_redacted_bundle(
          tmp_path / "bundle.tgz", state_dir=state, include_raw=True
      )

      with tarfile.open(bundle, "r:gz") as tar:
          payload = tar.extractfile("diagnostics-2026-06-19.redacted.jsonl")
          text = payload.read().decode("utf-8") if payload else ""

      assert "payload_redacted" in text
      assert "raw_capture" in text
      assert "forgedtokenabcdefghijklmn" not in text
      assert "0123456789abcdef" not in text
      assert "[REDACTED]" in text
      assert "body text" in text
  ```
- [ ] Prove the test bites: temporarily change `diagnostics.py:237-238` (`elif "payload_redacted" in clean: ... redact_text(...)`) to `elif "payload_redacted" in clean:` + `pass`, run `python -m pytest tests/test_diagnostics.py::test_redacted_bundle_include_raw_re_redacts_captured_payloads -v` — expect `AssertionError: assert 'forgedtokenabcdefghijklmn' not in text`. Restore, rerun, expect PASS.
- [ ] Run the whole file: `python -m pytest tests/test_diagnostics.py -v` — all pass.
- [ ] Commit:
  ```
  git add tests/test_diagnostics.py
  git commit -m "test(diagnostics): cover content-light sequences and raw-bundle re-redaction

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task COV.5: `http_transport.py` — real end-to-end auth/size gate + scope-intersection narrowing

**Files:**
- Modify (tests only): `/home/eranr/memoria-vault/tests/test_http_transport.py` (extend imports at lines 3-17; append tests before the module-tail helpers at line 609)
- Read-only production: `/home/eranr/memoria-vault/src/memoria_vault/runtime/http_transport.py` — `make_http_server` at 29-97 with the inner `Handler` at 41-95 (`_handle` auth gate 62-76, `_json_body` Content-Length guard 78-87, `MAX_BODY_BYTES = 1_000_000` at 20), `is_authorized` at 100-101, `_scope_intersection` at 287-295 (spec's line 292 = `narrowed.add(request_scope)` — verified). Spec's "lines 41-97" verified (Handler body ends 95; `make_http_server` returns at 97).
- Test: `tests/test_http_transport.py` (registered `contract` — no conftest change)

**Interfaces:**
- Consumes: `make_http_server(workspace: Path, *, host: str, port: int, token: str, read_scope: list[str] | None = None) -> ThreadingHTTPServer`; `_scope_intersection(maximum: list[str], requested: list[str]) -> list[str]`; `_dispatch(workspace, method, raw_path, body, *, read_scope=None) -> tuple[dict, HTTPStatus]`; existing fixtures `workspace` (via `tests.helpers.init_cli_workspace`) and `write_checked_note`.
- Produces: tests `test_http_server_handler_enforces_bearer_auth_and_body_size`, `test_http_transport_scope_intersection_narrows_to_requested_subscope`; module helper `_http_request`.

- [ ] Extend the imports: add `import http.client` and `import threading` to the stdlib import block, and change line 15 to
  `from memoria_vault.runtime.http_transport import MAX_BODY_BYTES, PayloadTooLarge, _dispatch, _scope_intersection, is_authorized, make_http_server`.
- [ ] Write the failing test (real server, real HTTP requests) plus its request helper (helper goes next to `_raise` at the bottom of the file):

  ```python
  def test_http_server_handler_enforces_bearer_auth_and_body_size(workspace: Path) -> None:
      server = make_http_server(workspace, host="127.0.0.1", port=0, token="test-token")
      thread = threading.Thread(target=server.serve_forever, daemon=True)
      thread.start()
      host, port = server.server_address[0], server.server_address[1]
      try:
          no_auth = _http_request(host, port, "GET", "/status", {})
          wrong_auth = _http_request(
              host, port, "GET", "/status", {"Authorization": "Bearer wrong"}
          )
          authorized = _http_request(
              host, port, "GET", "/status", {"Authorization": "Bearer test-token"}
          )
          oversized = _http_request(
              host,
              port,
              "POST",
              "/operation/run",
              {
                  "Authorization": "Bearer test-token",
                  "Content-Length": str(MAX_BODY_BYTES + 1),
              },
          )
      finally:
          server.shutdown()
          thread.join(timeout=5)
          server.server_close()

      assert no_auth == (HTTPStatus.UNAUTHORIZED, {"ok": False, "error": "unauthorized"})
      assert wrong_auth == (HTTPStatus.UNAUTHORIZED, {"ok": False, "error": "unauthorized"})
      assert authorized[0] == HTTPStatus.OK
      assert authorized[1]["ok"] is True
      assert authorized[1]["api_version"] == "engine-read-api.v1"
      assert oversized == (
          HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
          {"ok": False, "error": "request body too large"},
      )
  ```

  ```python
  def _http_request(
      host: str, port: int, method: str, path: str, headers: dict[str, str]
  ) -> tuple[HTTPStatus, dict]:
      conn = http.client.HTTPConnection(host, port, timeout=10)
      try:
          conn.putrequest(method, path)
          for name, value in headers.items():
              conn.putheader(name, value)
          conn.endheaders()
          response = conn.getresponse()
          return HTTPStatus(response.status), json.loads(response.read().decode("utf-8"))
      finally:
          conn.close()
  ```

  Step notes: (1) `port=0` binds an ephemeral port read back from
  `server_address` — no fixed-port flake; (2) the oversized case sends only the
  `Content-Length` header, never a body — `_json_body` rejects on the header
  *before* reading `rfile`, so the client never blocks on a 1MB send while the
  server has already responded 413; (3) the `"request body too large"` body
  string is produced only by `PayloadTooLarge`, pinning the 413 to the
  `_json_body` guard rather than any generic 400.
- [ ] Prove the test bites: temporarily comment out the auth guard at `http_transport.py:63-65` (the `if not is_authorized(...)` block in `_handle`), run `python -m pytest tests/test_http_transport.py::test_http_server_handler_enforces_bearer_auth_and_body_size -v` — expect `AssertionError` on `no_auth == (HTTPStatus.UNAUTHORIZED, ...)` (got 200). Restore, rerun, expect PASS.
- [ ] Write the failing test (scope-intersection: requested scope strictly inside the granted scope) after `test_http_transport_startup_read_scope_cannot_be_widened` (line 229):

  ```python
  def test_http_transport_scope_intersection_narrows_to_requested_subscope(
      workspace: Path,
  ) -> None:
      write_checked_note(workspace, "notes/alpha.md", "Alpha")
      write_checked_note(workspace, "notes/beta.md", "Beta")

      assert _scope_intersection(["notes"], ["notes/alpha.md"]) == ["notes/alpha.md"]

      narrowed, status = _dispatch(
          workspace,
          "GET",
          "/concepts?read_scope=notes/alpha.md",
          dict,
          read_scope=["notes"],
      )

      assert status == HTTPStatus.OK
      assert [row["path"] for row in narrowed["concepts"]] == ["notes/alpha.md"]
  ```

  (The existing tests cover widen-and-clamp and disjoint; this is the third
  case at line 291-292 — the request lies inside the startup maximum and the
  *requested* scope must win, hiding `notes/beta.md`.)
- [ ] Prove the test bites: temporarily change `http_transport.py:292` from `narrowed.add(request_scope)` to `narrowed.add(max_scope)`, run `python -m pytest tests/test_http_transport.py::test_http_transport_scope_intersection_narrows_to_requested_subscope -v` — expect `AssertionError` at the `_scope_intersection` equality (got `['notes']`). Restore, rerun, expect PASS.
- [ ] Run the whole file: `python -m pytest tests/test_http_transport.py -v` — all pass.
- [ ] Commit:
  ```
  git add tests/test_http_transport.py
  git commit -m "test(http): end-to-end Handler auth and body-size gate plus scope narrowing

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task COV.6: `schema_doc_drift.py` — seeded-mismatch fixtures for three unproven dimensions

**Files:**
- Modify (tests only): `/home/eranr/memoria-vault/tests/test_schema_doc_drift.py` (append after `test_schema_doc_lint_fails_on_seeded_type_roster_mismatch`, line 74)
- Read-only production: `/home/eranr/memoria-vault/scripts/checks/schema_doc_drift.py` — `_schema_claim_errors` at 108-121 (category/gated scalar check at 110-114; spec's line 112 verified), `_map_section_errors` at 124-146 (`"documented {label} is not live"` at 141 — verified), `_required_when_errors` at 159-160, `_list_subset_errors` at 163-175 (spec's 168-175 verified).
- Test: `tests/test_schema_doc_drift.py` (registered `static` — no conftest change)

**Interfaces:**
- Consumes: `check_schema_docs(schemas_dir: Path, docs_dir: Path) -> list[str]`; local fixture helper `_write_fixture(root: Path, *, enum_values: str = "claim, question") -> tuple[Path, Path]` (live schema: `type: note`, `category: notes`, no `required_when`/`required_any`/`forbidden`).
- Produces: tests `test_schema_doc_lint_fails_on_seeded_category_mismatch`, `test_schema_doc_lint_fails_on_required_when_rule_not_live`, `test_schema_doc_lint_fails_on_seeded_list_subset_mismatch`.

- [ ] Write the failing test (documented `category` mismatch), reusing `_write_fixture` and overwriting only the frontmatter doc, matching the file's style:

  ```python
  def test_schema_doc_lint_fails_on_seeded_category_mismatch(tmp_path: Path) -> None:
      schemas, docs = _write_fixture(tmp_path)
      (docs / "frontmatter.md").write_text(
          "```yaml\ntype: note\ncategory: cards\n```\n",
          encoding="utf-8",
      )

      errors = check_schema_docs(schemas, docs)

      assert any(
          "note.category: documented 'cards' != live 'notes'" in error for error in errors
      )
  ```
- [ ] Prove the test bites: temporarily comment out the scalar loop at `schema_doc_drift.py:110-114` (replace with `pass`), run `python -m pytest tests/test_schema_doc_drift.py::test_schema_doc_lint_fails_on_seeded_category_mismatch -v` — expect `AssertionError` (empty errors). Restore, rerun, expect PASS.
- [ ] Write the failing test (`required_when` entry absent from the live schema):

  ```python
  def test_schema_doc_lint_fails_on_required_when_rule_not_live(tmp_path: Path) -> None:
      schemas, docs = _write_fixture(tmp_path)
      (docs / "frontmatter.md").write_text(
          "```yaml\ntype: note\nrequired_when:\n  citekey: mode == claim\n```\n",
          encoding="utf-8",
      )

      errors = check_schema_docs(schemas, docs)

      assert any(
          "note.required_when.citekey: documented rule is not live" in error
          for error in errors
      )
  ```
- [ ] Prove the test bites: temporarily change `schema_doc_drift.py:140-141` (the `if key not in live_map:` append) to `continue`, run `python -m pytest tests/test_schema_doc_drift.py::test_schema_doc_lint_fails_on_required_when_rule_not_live -v` — expect `AssertionError` (empty errors). Restore, rerun, expect PASS. (Note this mutation also breaks the two existing `_field_map_errors` paths — confirmation the shared helper is what fires here.)
- [ ] Write the failing test (`required_any`/`forbidden` list-subset mismatch, seeded via `required_any`):

  ```python
  def test_schema_doc_lint_fails_on_seeded_list_subset_mismatch(tmp_path: Path) -> None:
      schemas, docs = _write_fixture(tmp_path)
      (docs / "frontmatter.md").write_text(
          "```yaml\ntype: note\nrequired_any: [citekey, url]\n```\n",
          encoding="utf-8",
      )

      errors = check_schema_docs(schemas, docs)

      assert any(
          "note.required_any: documented ['citekey', 'url'] not in live []" in error
          for error in errors
      )
  ```
- [ ] Prove the test bites: temporarily add `return []` as the first line of `_list_subset_errors` (`schema_doc_drift.py:166`), run `python -m pytest tests/test_schema_doc_drift.py::test_schema_doc_lint_fails_on_seeded_list_subset_mismatch -v` — expect `AssertionError` (empty errors). Restore, rerun, expect PASS.
- [ ] Run the whole file: `python -m pytest tests/test_schema_doc_drift.py -v` — all pass.
- [ ] Commit:
  ```
  git add tests/test_schema_doc_drift.py
  git commit -m "test(checks): seed mismatch fixtures for three schema-doc drift dimensions

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task COV.7: `removed_surface_gate.py` — file-type search root test + missing-root hard failure

This task has a production-code half: the spec names the missing-root hard
failure as a design hardening, and the execution-time discovery above proves it
fires today (`.agents` is a listed search root that no longer exists, silently
skipped). The hardening therefore ships with the stale-root removal from the
contract file.

**Files:**
- Modify: `/home/eranr/memoria-vault/scripts/checks/removed_surface_gate.py` (silent skip at lines 96-98 inside `find_violations`)
- Modify: `/home/eranr/memoria-vault/scripts/checks/removed_surfaces.json` (drop the stale `".agents"` entry from `search_roots`, currently the first entry)
- Modify (tests): `/home/eranr/memoria-vault/tests/test_removed_surface_gate.py` (append after line 48)
- Read-only production: `iter_files` file-root branch at `removed_surface_gate.py:66-70` (spec said 67-70 — off by one, `if root.is_file():` is line 66).
- Test: `tests/test_removed_surface_gate.py` (registered `static` — no conftest change)

**Interfaces:**
- Consumes: `find_violations(repo: Path = ROOT, contract_path: Path = CONTRACT) -> list[str]`; `iter_files(repo: Path, root: Path, allow_text_files: frozenset[str])`; test-local `write_contract(path: Path) -> None` (contract with `search_roots: ["docs"]`).
- Produces: behavior change — a missing search root now appends `"missing search root: <rel>"` to the violations list (gate fails loudly instead of silently skipping); tests `test_scans_file_type_search_roots`, `test_missing_search_root_is_a_hard_failure`.

- [ ] Write the failing test (file-type search root — the real production shape: the live contract lists `.pre-commit-config.yaml`, `AGENTS.md`, `CONTRIBUTING.md`, `SECURITY.md` as file roots):

  ```python
  def test_scans_file_type_search_roots(tmp_path: Path) -> None:
      contract = tmp_path / "removed_surfaces.json"
      contract.write_text(
          json.dumps(
              {
                  "search_roots": ["NOTES.md"],
                  "allow_text_files": [],
                  "rules": [
                      {
                          "kind": "text",
                          "needle": "OldSurface",
                          "owner": "tests",
                          "reason": "retired prose reference",
                      }
                  ],
              }
          ),
          encoding="utf-8",
      )
      (tmp_path / "NOTES.md").write_text("intro\nOldSurface\n", encoding="utf-8")

      assert gate.find_violations(tmp_path, contract) == ["NOTES.md: contains OldSurface"]
  ```
- [ ] Prove the test bites: temporarily change `removed_surface_gate.py:66` from `if root.is_file():` to `if False:` — the file root then falls into `rglob` (yielding nothing for a file), run `python -m pytest tests/test_removed_surface_gate.py::test_scans_file_type_search_roots -v` — expect `AssertionError` (got `[]`). Restore, rerun, expect PASS.
- [ ] Write the failing test (missing search root is a hard failure — true red: fails against current code):

  ```python
  def test_missing_search_root_is_a_hard_failure(tmp_path: Path) -> None:
      contract = tmp_path / "removed_surfaces.json"
      write_contract(contract)  # search root "docs" — deliberately not created

      assert gate.find_violations(tmp_path, contract) == ["missing search root: docs"]
  ```
- [ ] Run test to verify it fails: `python -m pytest tests/test_removed_surface_gate.py::test_missing_search_root_is_a_hard_failure -v` — expect `AssertionError: assert [] == ['missing search root: docs']` (current code silently `continue`s at lines 97-98).
- [ ] Write minimal implementation — in `find_violations` (`removed_surface_gate.py:95-98`) replace the silent skip:

  ```python
      for rel in contract.search_roots:
          root = repo / rel
          if not root.exists():
              errors.append(f"missing search root: {rel}")
              continue
  ```
- [ ] Run test to verify it passes: `python -m pytest tests/test_removed_surface_gate.py -v` — all pass.
- [ ] Run the hardened gate against the real repo to watch it catch the live stale root: `python scripts/checks/removed_surface_gate.py` — expect `removed-surface-gate: FAIL` / `missing search root: .agents` (exit 1). This is the hardening doing its job, not a regression.
- [ ] Remove the `".agents",` entry from `search_roots` in `scripts/checks/removed_surfaces.json` (the directory was removed/renamed out of the repo; the silent skip hid it until now).
- [ ] Rerun `python scripts/checks/removed_surface_gate.py` — expect `removed-surface-gate: clean` (exit 0), then `python scripts/verify` to confirm the full gate.
- [ ] Commit:
  ```
  git add scripts/checks/removed_surface_gate.py scripts/checks/removed_surfaces.json tests/test_removed_surface_gate.py
  git commit -m "fix(checks): fail hard on a missing removed-surface search root

  A typo'd or renamed search root silently stopped being scanned
  (line 98 skipped it); the hardened gate immediately caught the stale
  .agents root in the live contract, removed here. Also pins the
  file-type search-root branch the real contract relies on.

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task COV.8: `worker.py` — `main()` subcommand dispatch wiring

**Files:**
- Modify (tests only): `/home/eranr/memoria-vault/tests/test_worker_queue.py` (append after `test_worker_cli_enqueues_operation_payload`, line 517)
- Read-only production: `/home/eranr/memoria-vault/src/memoria_vault/runtime/worker.py` — `main()` at **1387-1484** (spec said 1436-1484 — drifted; the dispatcher body is 1413-1484: `scan` 1436-1445, `run-scheduled` 1446-1462, `integrity-sweep` 1463-1470, `observe-pi-edits` 1471-1479 with an in-function import from `trusted_writer`, `recover` 1480-1482, `run-pending` fallthrough 1483). Only `enqueue-operation` has a wiring test today.
- Test: `tests/test_worker_queue.py` (registered `runtime` — no conftest change)

**Interfaces:**
- Consumes: `main(argv: list[str] | None = None) -> int` (as the file's existing `worker_main` alias); patch points `memoria_vault.runtime.worker.enqueue_operation`, `memoria_vault.runtime.worker.run_pending_jobs`, `memoria_vault.runtime.worker.run_integrity_sweep`, `memoria_vault.runtime.trusted_writer.observe_pi_edits_explicit_from_status`, `memoria_vault.runtime.state.recover_pending_materializations`.
- Produces: test `test_worker_cli_dispatches_each_subcommand_to_its_handler` (parametrized over the six remaining subcommands) plus module helper `_dispatch_recorder`.

- [ ] Write the failing test — one parametrized test, one param row per remaining subcommand, mirroring the enqueue-operation test's argv shape. Handlers are recorded, not run, so a bare `tmp_path` suffices as the vault:

  ```python
  def _dispatch_recorder(calls: list, name: str):
      def record(*args, **kwargs):
          calls.append((name, args, kwargs))
          return {"recorded": name}

      return record


  @pytest.mark.parametrize(
      ("argv_tail", "targets", "expected", "expect_stdout"),
      [
          pytest.param(
              ["scan", "--idempotency-key", "scan-key"],
              {
                  "enqueue_operation": "memoria_vault.runtime.worker.enqueue_operation",
                  "run_pending_jobs": "memoria_vault.runtime.worker.run_pending_jobs",
              },
              [
                  (
                      "enqueue_operation",
                      ("observe-pi-edits",),
                      {
                          "idempotency_key": "scan-key",
                          "actor": "integrity",
                          "provenance": {"surface": "worker-scan"},
                      },
                  ),
                  ("run_pending_jobs", (), {"machine": "memoria-scheduled-checks", "limit": 1}),
              ],
              None,
              id="scan",
          ),
          pytest.param(
              [
                  "run-scheduled",
                  "--operation-id",
                  "answer-query",
                  "--payload",
                  '{"k": 1}',
                  "--schedule-id",
                  "sched-1",
              ],
              {
                  "enqueue_operation": "memoria_vault.runtime.worker.enqueue_operation",
                  "run_pending_jobs": "memoria_vault.runtime.worker.run_pending_jobs",
              },
              [
                  (
                      "enqueue_operation",
                      ("answer-query",),
                      {
                          "payload": {"k": 1},
                          "idempotency_key": "answer-query-sched-1",
                          "schedule_id": "sched-1",
                          "actor": "operation",
                          "provenance": {"surface": "worker-schedule"},
                      },
                  ),
                  ("run_pending_jobs", (), {"machine": "memoria-scheduled-checks", "limit": 1}),
              ],
              None,
              id="run-scheduled",
          ),
          pytest.param(
              ["integrity-sweep", "--sweep-id", "sweep-7"],
              {"run_integrity_sweep": "memoria_vault.runtime.worker.run_integrity_sweep"},
              [
                  (
                      "run_integrity_sweep",
                      (),
                      {
                          "shadow": True,
                          "sweep_id": "sweep-7",
                          "machine": "memoria-scheduled-checks",
                      },
                  ),
              ],
              None,
              id="integrity-sweep",
          ),
          pytest.param(
              ["integrity-sweep", "--active"],
              {"run_integrity_sweep": "memoria_vault.runtime.worker.run_integrity_sweep"},
              [("run_integrity_sweep", (), {"shadow": False, "sweep_id": None})],
              None,
              id="integrity-sweep-active",
          ),
          pytest.param(
              ["observe-pi-edits"],
              {
                  "observe_pi_edits": (
                      "memoria_vault.runtime.trusted_writer."
                      "observe_pi_edits_explicit_from_status"
                  ),
              },
              [
                  (
                      "observe_pi_edits",
                      (),
                      {"actor": "integrity", "machine": "memoria-scheduled-checks"},
                  ),
              ],
              None,
              id="observe-pi-edits",
          ),
          pytest.param(
              ["recover"],
              {
                  "recover_pending_materializations": (
                      "memoria_vault.runtime.state.recover_pending_materializations"
                  ),
              },
              [("recover_pending_materializations", (), {})],
              {"recorded": "recover_pending_materializations"},
              id="recover",
          ),
          pytest.param(
              ["run-pending", "--limit", "3", "--machine", "custom-machine"],
              {"run_pending_jobs": "memoria_vault.runtime.worker.run_pending_jobs"},
              [("run_pending_jobs", (), {"machine": "custom-machine", "limit": 3})],
              None,
              id="run-pending",
          ),
      ],
  )
  def test_worker_cli_dispatches_each_subcommand_to_its_handler(
      tmp_path: Path,
      capsys,
      monkeypatch: pytest.MonkeyPatch,
      argv_tail: list[str],
      targets: dict[str, str],
      expected: list[tuple[str, tuple, dict]],
      expect_stdout: dict | None,
  ) -> None:
      calls: list[tuple[str, tuple, dict]] = []
      for name, target in targets.items():
          monkeypatch.setattr(target, _dispatch_recorder(calls, name))

      rc = worker_main([argv_tail[0], "--vault", str(tmp_path), *argv_tail[1:]])

      assert rc == 0
      out = capsys.readouterr().out
      if expect_stdout is not None:
          assert json.loads(out) == expect_stdout
      for name, arg_tail, kwargs_subset in expected:
          matching = [call for call in calls if call[0] == name]
          assert len(matching) == 1, f"{name} called {len(matching)} times: {calls}"
          _, args, kwargs = matching[0]
          assert args[0] == tmp_path
          assert args[1:] == arg_tail
          for key, value in kwargs_subset.items():
              assert kwargs.get(key) == value, f"{name} kwarg {key}: {kwargs.get(key)!r}"
  ```

  (`worker_main`, `pytest`, `json`, `Path` are already imported at the top of
  this file. `observe-pi-edits` is patched at its `trusted_writer` home because
  `main()` imports it inside the branch; `recover` is patched on the `state`
  module `main()` calls through.)
- [ ] Prove the test bites: temporarily change `worker.py:1463` from `if args.command == "integrity-sweep":` to `if args.command == "never":`, run `python -m pytest "tests/test_worker_queue.py::test_worker_cli_dispatches_each_subcommand_to_its_handler[integrity-sweep]" -v` — expect `AssertionError: run_integrity_sweep called 0 times` (the argv falls through to `run_pending_jobs`, which is unpatched here and irrelevant to the recorded-call assertion). Restore, rerun, expect PASS.
- [ ] Run all seven param rows: `python -m pytest tests/test_worker_queue.py::test_worker_cli_dispatches_each_subcommand_to_its_handler -v` — 7 passed.
- [ ] Commit:
  ```
  git add tests/test_worker_queue.py
  git commit -m "test(worker): pin main() subcommand dispatch wiring for every subcommand

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task COV.9: `code/runner.py` — `run_artifact` ValueError guards

**Files:**
- Modify (tests only): `/home/eranr/memoria-vault/tests/test_code_artifacts.py` (append after line 76)
- Read-only production: `/home/eranr/memoria-vault/src/memoria_vault/runtime/code/runner.py` — unknown-artifact guard at 49-51, malformed/empty `approved_command` guard at 52-54. Spec refs (51, 54) verified — no drift. `create_code_artifact` (`code/records.py:14`) performs no `approved_command` validation, confirming these guards are the only backstop.
- Test: `tests/test_code_artifacts.py` (registered `runtime` — no conftest change)

**Interfaces:**
- Consumes: `run_artifact(vault: Path, artifact_id: str, *, run_id: str | None = None, timeout_s: int = 30, max_output_bytes: int = 1_000_000) -> dict[str, Any]`; `create_code_artifact(vault, project_path, artifact_id, *, title="", purpose="warrant", approved_command, declared_inputs=None, declared_outputs=None, dependency_notes="") -> dict[str, Any]`.
- Produces: test `test_run_artifact_rejects_unknown_artifact_and_malformed_command`.

- [ ] Write the failing test. This file deliberately does not import pytest, so use the repo's pytest-independent try/except/else idiom (see the PT011 waiver comment in `pyproject.toml`). Pure Python — no `bwrap` needed; both guards raise before any availability check:

  ```python
  def test_run_artifact_rejects_unknown_artifact_and_malformed_command(tmp_path: Path) -> None:
      try:
          run_artifact(tmp_path, "missing")
      except ValueError as exc:
          assert "unknown code artifact: missing" in str(exc)
      else:
          raise AssertionError("run_artifact accepted an unknown artifact_id")

      create_code_artifact(
          tmp_path,
          "project-alpha",
          "empty-argv",
          approved_command=[],
      )
      create_code_artifact(
          tmp_path,
          "project-alpha",
          "blank-part",
          approved_command=["python3", ""],
      )
      for artifact_id in ("empty-argv", "blank-part"):
          try:
              run_artifact(tmp_path, artifact_id)
          except ValueError as exc:
              assert "approved_command must be a non-empty argv list" in str(exc)
          else:
              raise AssertionError(f"run_artifact executed malformed command {artifact_id!r}")
  ```
- [ ] Prove the test bites: temporarily change `runner.py:53` from `if not command or not all(isinstance(part, str) and part for part in command):` to `if False:`, run `python -m pytest tests/test_code_artifacts.py::test_run_artifact_rejects_unknown_artifact_and_malformed_command -v` — expect `AssertionError: run_artifact executed malformed command 'empty-argv'` (the malformed command reaches the availability check and comes back as an `unavailable` run record instead of raising). Restore, rerun, expect PASS.
- [ ] Run the whole file: `python -m pytest tests/test_code_artifacts.py -v` — all pass.
- [ ] Commit:
  ```
  git add tests/test_code_artifacts.py
  git commit -m "test(code): pin run_artifact ValueError guards for garbage artifact input

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task COV.10: workspace-seed wikilink detectors — synthetic violation fixture

**Files:**
- Modify (tests only): `/home/eranr/memoria-vault/tests/test_workspace_seed_links.py` (append after `test_workspace_seed_links_are_clean`, line 149)
- Read-only (same file, module under test): `_check_wikilink_aliases` at **98-108** and `_check_broken_wikilinks` at **111-120** (spec said 101-108 / 114-120 — drifted by 3 lines; verified). Their substantive logic has never run: no packaged seed markdown contains `[[wikilink]]` syntax.
- Test: `tests/test_workspace_seed_links.py` (registered `static` — no conftest change)

**Interfaces:**
- Consumes: `_check_wikilink_aliases(md: Path, errors: list[str]) -> None`; `_check_broken_wikilinks(md: Path, errors: list[str], vault_stems: set[str]) -> None` (both are module-level functions in this same test file — called directly).
- Produces: test `test_wikilink_detectors_flag_bare_and_broken_links`.

- [ ] Write the failing test — a tmp markdown fixture carrying one bare wikilink (also broken), one aliased-but-broken wikilink, and one aliased link that resolves:

  ```python
  def test_wikilink_detectors_flag_bare_and_broken_links(tmp_path: Path) -> None:
      md = tmp_path / "note.md"
      md.write_text(
          "\n".join(
              [
                  "A [[Missing Note]] here.",
                  "An [[absent-note|Absent Note]] there.",
                  "A [[real-note|Real Note]] link that resolves.",
              ]
          )
          + "\n",
          encoding="utf-8",
      )

      alias_errors: list[str] = []
      _check_wikilink_aliases(md, alias_errors)
      broken_errors: list[str] = []
      _check_broken_wikilinks(md, broken_errors, {"real-note"})

      assert alias_errors == [
          f"{md}: bare wikilink [[Missing Note]] — alias it with the page title"
      ]
      assert broken_errors == [
          f"{md}: wikilink [[Missing Note]] resolves to no vault note",
          f"{md}: wikilink [[absent-note|Absent Note]] resolves to no vault note",
      ]
  ```
- [ ] Prove the test bites: temporarily comment out the `errors.append(...)` at line 108 in `_check_wikilink_aliases`, run `python -m pytest tests/test_workspace_seed_links.py::test_wikilink_detectors_flag_bare_and_broken_links -v` — expect `AssertionError` at the `alias_errors` equality (got `[]`). Restore, rerun, expect PASS.
- [ ] Run the whole file: `python -m pytest tests/test_workspace_seed_links.py -v` — both tests pass.
- [ ] Commit:
  ```
  git add tests/test_workspace_seed_links.py
  git commit -m "test(seed): exercise the wikilink detectors on a synthetic violation fixture

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task COV.11: cleanups — 11a Windows-lock pragma + 11b dead template-frontmatter code

No test writing; two small, low-risk fixes in one task/commit. If COV.10 runs
first, 11b's deletion lands in the same file COV.10 extended — both touch
disjoint regions, so either order is safe.

**Files:**
- Modify: `/home/eranr/memoria-vault/src/memoria_vault/runtime/state.py` — `_open_workspace_lock_file_windows` `def` at line **115** (~71% of the file's missed lines; its sibling Windows-only branches at lines 40 and 45 already carry `# pragma: no cover`; sole caller is the `os.name == "nt"` branch at line 359, unreachable on Linux CI)
- Modify: `/home/eranr/memoria-vault/tests/test_workspace_seed_links.py` — dead block: `YAML_FENCE_RE` at line 23, `DROPPED_KEYS` at line 24, `_check_template_frontmatter` at lines 75-79, the `tmpl_dir` block in `_collect_errors` at lines 127-130, plus the "the vault note templates' fenced frontmatter, and" phrase in the module docstring (line 5-6). Targets `system/templates`, retired from the shipped seed in commit `cf6fcdae` before this file existed (PR #1349); `tmpl_dir.is_dir()` is always false.
- Test: existing suites only (`tests/test_runtime_state.py`, `tests/test_workspace_seed_links.py`)

**Interfaces:**
- Consumes: coverage.py's default `# pragma: no cover` exclusion (a pragma on a `def` line excludes the whole function body).
- Produces: no runtime behavior change; `state.py` coverage stops inflating on Windows-only code; `test_workspace_seed_links.py` sheds its dead check.

- [ ] 11a — edit `state.py:115` to carry the pragma on the `def` line, wording matched to its siblings at lines 40/45:

  ```python
  def _open_workspace_lock_file_windows(_vault: Path, lock_path: Path):  # pragma: no cover - runs only on Windows.
  ```

  (E501 is deliberately not enforced in this repo — width is owned by `ruff
  format`, which does not wrap comments.)
- [ ] Run `python -m pytest tests/test_runtime_state.py tests/test_worker_queue.py -q` — all pass (comment-only change; the Windows lock still works, per the multiprocess lock test).
- [ ] 11b — in `tests/test_workspace_seed_links.py` delete: line 23 (`YAML_FENCE_RE = ...`), line 24 (`DROPPED_KEYS = ...`), lines 75-79 (`def _check_template_frontmatter(...)` and body), lines 127-130 in `_collect_errors` (`tmpl_dir = SEED / "system/templates"` through the `_check_template_frontmatter(md, errors)` call), and trim the docstring phrase "the vault note templates' fenced frontmatter, and" (lines 5-6) so the module description matches what it still checks. Leave the `"templates" in md.parts` skip at line 139 untouched (it guards the wikilink checks generally, not the retired check).
- [ ] Run `python -m pytest tests/test_workspace_seed_links.py -v` — passes; then `grep -n "YAML_FENCE_RE\|DROPPED_KEYS\|_check_template_frontmatter\|tmpl_dir" tests/test_workspace_seed_links.py` — no output.
- [ ] Run `python scripts/verify` — full gate green.
- [ ] Commit:
  ```
  git add src/memoria_vault/runtime/state.py tests/test_workspace_seed_links.py
  git commit -m "chore: pragma the Windows-only lock opener; delete retired template check

  11a: _open_workspace_lock_file_windows cannot run on Linux CI and its
  sibling Windows-only branches already carry the pragma. 11b: the
  system/templates seed dir was retired in cf6fcdae before this test
  file existed; the check was dead on arrival.

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Section close-out

- [ ] Run `python scripts/verify` once over the assembled branch state (whatever subset of COV tasks landed together) before any PR — it is the one merge gate, alongside `gitleaks`.
