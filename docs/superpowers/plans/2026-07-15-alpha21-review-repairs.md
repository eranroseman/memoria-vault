# Alpha.21 Review Repairs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the four adversarially-confirmed findings from the alpha.21 post-release implementation review so every shipped trust promise is actually kept.

**Architecture:** Four independent, small repairs at existing seams: CS3 scan findings routed to the durable inbox surface and printed in human scan output; CS1 neutralization moved inside the VaultWriter seam (default-deny for machine actors); two PI CLI write paths switched to the existing durable-write helper; `_fsync_dir` made honest and symmetric with backup's fatal treatment.

**Tech Stack:** Python 3 / SQLite / pytest (existing repo toolchain; no new dependencies).

## Global Constraints

- Correctness gate: `python scripts/verify` must pass before merge; `main` requires a PR + `verify` and `gitleaks` checks; squash merge.
- Stage explicit paths only — never `git add -A` (shared git index per checkout).
- Test only against disposable vaults (`tmp_path` / `test-vault/`).
- New test files must be registered in `tests/conftest.py` `TEST_LEVELS` (Task 21.4 adds `"test_vaultio.py": "unit"`).
- All line refs verified against main @ `d85d8799`; re-anchor by quoted context if drifted.
- Tasks are independent; any order; each is one PR-sized unit.
- Sequencing note vs Plan 22: nothing here conflicts, but if executing concurrently with Plan 22's S68.3 or COST.4 (both touch journal-hashed floor goldens), land those two sequentially.

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
