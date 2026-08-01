"""Attention-card lifecycle: journaling unattributed dispositions, monthly compaction."""

from __future__ import annotations

import contextlib
import datetime
import json
import threading
from pathlib import Path
from typing import Any

import pytest

from memoria_vault.engine import api as engine_api
from memoria_vault.runtime import state, worker
from memoria_vault.runtime.subsystems.lib import inbox as inbox_lib
from memoria_vault.runtime.subsystems.lib import lifecycle, loudness
from memoria_vault.runtime.trusted_writer import append_explicit_journal_event
from memoria_vault.runtime.vaultio import read_frontmatter
from tests.helpers import git, init_cli_workspace, init_git


def _write_card(
    vault: Path,
    name: str,
    status: str,
    extra: str = "",
    *,
    projection: str = "attention",
    loudness: str = "block",
) -> Path:
    path = vault / "inbox" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        "title: Stop\n"
        f"projection: {projection}\n"
        "attention_kind: alert\n"
        f"attention_status: {status}\n"
        f"loudness: {loudness}\n"
        f"{extra}"
        "---\n\n# Finding\n\nBody.\n",
        encoding="utf-8",
    )
    return path


def _dispositions(vault: Path) -> list[dict[str, Any]]:
    return state.read_event_log(vault, event_types=("resolved",))


def _run(workspace: Path, operation_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Drive one real attention operation end to end, the way the PI's pane does."""
    request = worker.enqueue_operation(
        workspace,
        operation_id,
        actor="pi",
        idempotency_key=f"pi-{operation_id}-{payload['target_id']}",
        payload=payload,
    )
    result = worker.run_request(workspace, request["job_id"], machine="PI laptop")
    assert result["status"] == "done", result
    return result


def test_a_closed_card_is_journaled_without_naming_an_author(tmp_path: Path) -> None:
    """The row records the disposition and claims nothing about who made it.

    `platform.node()` is identical for the PI's hand and for a machine, and
    `inbox/**` is the one write target the reference actor policy grants a non-PI
    actor -- so a perimeter write lands on exactly the cards this scan reads. The
    journal forbids UPDATE and DELETE, so `actor: "pi"` here would be a permanent
    false attestation that inspection could never correct.
    """
    _write_card(tmp_path, "alert-stop.md", "resolved")

    journaled = lifecycle.journal_unattributed_dispositions(tmp_path, machine="test-machine")

    assert [event["target_id"] for event in journaled] == ["inbox/alert-stop.md"]
    events = _dispositions(tmp_path)
    assert len(events) == 1
    assert events[0]["via"] == "unattributed-edit"
    assert events[0]["actor"] != "pi"
    assert events[0]["actor"] == "integrity"
    assert events[0]["outcome"] == "apply"
    assert events[0]["resolution"] == "resolved"


def test_every_closed_card_is_journaled_not_just_the_first(tmp_path: Path) -> None:
    """One batch, N rows -- a truncated batch clears the rest silently.

    The rows go out through a single `append_explicit_event_batch`, so nothing
    downstream would notice a comprehension that dropped cards after the first;
    the dispositions would just never be recorded, which is the silent clear this
    journaling exists to remove.
    """
    _write_card(tmp_path, "alert-one.md", "resolved")
    _write_card(tmp_path, "alert-two.md", "resolved", "resolution_outcome: reject\n")
    _write_card(tmp_path, "alert-three.md", "deferred")

    journaled = lifecycle.journal_unattributed_dispositions(tmp_path, machine="test-machine")

    assert {event["target_id"] for event in journaled} == {
        "inbox/alert-one.md",
        "inbox/alert-two.md",
        "inbox/alert-three.md",
    }
    assert {event["target_id"] for event in _dispositions(tmp_path)} == {
        "inbox/alert-one.md",
        "inbox/alert-two.md",
        "inbox/alert-three.md",
    }


def test_a_vault_with_no_closed_card_never_takes_the_workspace_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The deciding read moved inside the lock; the frontmatter scan stayed outside.

    This runs on every gated write, so if the scan moved in too, every such write
    would contend on the workspace lock to discover there was nothing to do.
    """
    _write_card(tmp_path, "alert-open.md", "open")
    taken = []
    real_lock = state.workspace_lock
    monkeypatch.setattr(
        state, "workspace_lock", lambda vault: (taken.append(vault), real_lock(vault))[1]
    )

    assert lifecycle.journal_unattributed_dispositions(tmp_path, machine="test-machine") == []

    assert taken == []


def test_journaling_is_idempotent(tmp_path: Path) -> None:
    _write_card(tmp_path, "alert-stop.md", "resolved")
    lifecycle.journal_unattributed_dispositions(tmp_path, machine="test-machine")

    again = lifecycle.journal_unattributed_dispositions(tmp_path, machine="test-machine")

    assert again == []
    assert len(_dispositions(tmp_path)) == 1


def test_open_cards_are_not_journaled(tmp_path: Path) -> None:
    _write_card(tmp_path, "alert-open.md", "open")

    journaled = lifecycle.journal_unattributed_dispositions(tmp_path, machine="test-machine")

    assert journaled == []
    assert _dispositions(tmp_path) == []


def test_a_deferred_notice_card_journals_a_defer_outcome(tmp_path: Path) -> None:
    """`loudness` is not the trigger -- the closed status is.

    Only a `block` card can gate anything, but every closed card the gate walks past
    is a disposition the journal is missing, so a `notice` card is journaled too.
    """
    _write_card(tmp_path, "alert-later.md", "deferred", loudness="notice")

    journaled = lifecycle.journal_unattributed_dispositions(tmp_path, machine="test-machine")

    assert journaled[0]["outcome"] == "defer"
    assert (tmp_path / "inbox/alert-later.md").exists()  # journaling never moves files


def test_projection_matching_is_case_folded(tmp_path: Path) -> None:
    """`loudness.is_open_blocker` case-folds `projection`, so `Attention` can block.

    Journaling has to fold the same way, or such a card blocks the gate while it is
    open and then clears it silently once closed -- the exact hole this closes.
    """
    _write_card(tmp_path, "alert-stop.md", "resolved", projection="Attention")

    journaled = lifecycle.journal_unattributed_dispositions(tmp_path, machine="test-machine")

    assert [event["target_id"] for event in journaled] == ["inbox/alert-stop.md"]


@pytest.mark.parametrize(
    ("status", "written_outcome", "expected"),
    [
        ("resolved", "reject", "reject"),
        ("resolved", "defer", "apply"),
        ("deferred", "apply", "defer"),
    ],
)
def test_journaled_outcome_keeps_status_and_outcome_consistent(
    tmp_path: Path, status: str, written_outcome: str, expected: str
) -> None:
    _write_card(tmp_path, "alert-stop.md", status, extra=f"resolution_outcome: {written_outcome}\n")

    journaled = lifecycle.journal_unattributed_dispositions(tmp_path, machine="test-machine")

    assert journaled[0]["outcome"] == expected
    assert journaled[0]["resolution_outcome"] == expected


def test_journaled_event_carries_no_card_body_text(tmp_path: Path) -> None:
    unbounded = "x" * 50_000
    _write_card(
        tmp_path,
        "alert-stop.md",
        "resolved",
        extra=f"resolution_outcome: {unbounded}\nrouting_class: {unbounded}\n",
    )

    journaled = lifecycle.journal_unattributed_dispositions(tmp_path, machine="test-machine")

    # The journal forbids UPDATE and DELETE: card text that lands here is permanent.
    assert unbounded not in json.dumps(_dispositions(tmp_path))
    assert journaled[0]["outcome"] == "apply"
    assert journaled[0]["routing_class"] == "ask"


def test_a_foreign_resolved_event_does_not_speak_for_a_card(tmp_path: Path) -> None:
    """`resolved` is a shared event type: note curation, moves, and rollbacks emit it too.

    Only an attention row that resolved the card records its disposition. Matching a
    foreign row would suppress the write and hand the gate back its silent clear.
    """
    _write_card(tmp_path, "alert-stop.md", "resolved")
    append_explicit_journal_event(
        tmp_path,
        {
            "event": "resolved",
            "resolution": "resolved",
            "target_id": "inbox/alert-stop.md",
            "source": "note-curation",
        },
        actor="pi",
        machine="test-machine",
    )

    journaled = lifecycle.journal_unattributed_dispositions(tmp_path, machine="test-machine")

    assert [event["via"] for event in journaled] == ["unattributed-edit"]


def test_non_attention_projections_are_not_journaled(tmp_path: Path) -> None:
    path = tmp_path / "inbox/digest.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\ntitle: Weekly\nprojection: digest\nattention_status: resolved\n---\n",
        encoding="utf-8",
    )

    journaled = lifecycle.journal_unattributed_dispositions(tmp_path, machine="test-machine")

    assert journaled == []


def test_nested_inbox_files_are_not_journaled(tmp_path: Path) -> None:
    nested = tmp_path / "inbox/archive/alert-stop.md"
    nested.parent.mkdir(parents=True, exist_ok=True)
    nested.write_text(
        "---\ntitle: Stop\nprojection: attention\nattention_status: resolved\n---\n",
        encoding="utf-8",
    )

    journaled = lifecycle.journal_unattributed_dispositions(tmp_path, machine="test-machine")

    assert journaled == []


def test_operation_resolved_card_is_not_journaled_again(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    _write_card(workspace, "alert-done.md", "open")
    _run(workspace, "resolve-attention", {"target_id": "inbox/alert-done.md", "outcome": "apply"})
    before = _dispositions(workspace)
    # The operation left behind exactly what the scan looks for: a closed card.
    assert "attention_status: resolved" in (workspace / "inbox/alert-done.md").read_text()
    assert [event["resolution"] for event in before] == ["resolved"]

    journaled = lifecycle.journal_unattributed_dispositions(workspace, machine="test-machine")

    assert journaled == []
    assert _dispositions(workspace) == before


def test_acknowledged_card_closed_outside_the_writer_is_journaled(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    _write_card(workspace, "alert-ack.md", "open")
    _run(workspace, "acknowledge-attention", {"target_id": "inbox/alert-ack.md"})
    # An acknowledgement is a `resolved` event that closed nothing: same event type,
    # same target, card still open. Matching on the target alone would skip it.
    assert [event["resolution"] for event in _dispositions(workspace)] == ["acknowledged"]
    _write_card(workspace, "alert-ack.md", "resolved")  # closed outside the trusted writer

    journaled = lifecycle.journal_unattributed_dispositions(workspace, machine="test-machine")

    assert [event["target_id"] for event in journaled] == ["inbox/alert-ack.md"]
    assert journaled[0]["via"] == "unattributed-edit"


def test_a_rival_session_cannot_read_the_journal_mid_decision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two sessions racing one closed card leave one permanent row, not two.

    AGENTS.md documents several sessions per checkout and the caller is a per-write
    policy hook, so the read that decides which rows are missing and the append that
    writes them have to sit in one critical section. A rival is launched from inside
    the first session's read and given time to finish: if it can get through, both
    sessions see an empty journal and the append-only log keeps both rows.
    """
    _write_card(tmp_path, "alert-stop.md", "resolved")
    with state.connect(tmp_path):  # build the schema before the race, not during it
        pass
    real_read = state.read_event_log
    rival: list[threading.Thread] = []
    rival_errors: list[BaseException] = []

    def rival_session() -> None:
        try:
            lifecycle.journal_unattributed_dispositions(tmp_path, machine="rival")
        except BaseException as exc:  # noqa: BLE001 - reported on the main thread
            rival_errors.append(exc)

    def racing_read(vault: Path, **kwargs: Any) -> list[dict[str, Any]]:
        rows = real_read(vault, **kwargs)
        if not rival:  # the rival's own read must not start a third session
            thread = threading.Thread(target=rival_session)
            rival.append(thread)
            thread.start()
            thread.join(timeout=0.5)  # finishes only if nothing held it out
        return rows

    monkeypatch.setattr(state, "read_event_log", racing_read)
    lifecycle.journal_unattributed_dispositions(tmp_path, machine="test-machine")
    rival[0].join(timeout=30)
    monkeypatch.undo()

    assert rival_errors == []
    assert [event["target_id"] for event in _dispositions(tmp_path)] == ["inbox/alert-stop.md"]


def _this_months_digest() -> str:
    return f"inbox/archive/{datetime.date.today():%Y-%m}.md"


def test_compact_moves_resolved_cards_to_monthly_archive(tmp_path: Path) -> None:
    init_git(tmp_path, "pi@example.invalid", "PI")
    _write_card(tmp_path, "alert-done.md", "resolved", extra="resolved_at: 2026-06-30T10:00:00Z\n")
    _write_card(tmp_path, "alert-open.md", "open")
    _write_card(tmp_path, "alert-later.md", "deferred")

    result = lifecycle.compact_resolved_cards(tmp_path, machine="test-machine")

    assert result["archived"] == ["inbox/alert-done.md"]
    assert result["digests"] == ["inbox/archive/2026-06.md"]
    assert result["commit"]
    assert not (tmp_path / "inbox/alert-done.md").exists()
    assert (tmp_path / "inbox/alert-open.md").exists()
    assert (tmp_path / "inbox/alert-later.md").exists()  # deferred is not archived
    digest = (tmp_path / "inbox/archive/2026-06.md").read_text(encoding="utf-8")
    assert "## Stop (alert-done.md)" in digest
    assert "- attention_kind: alert" in digest
    assert "Body." in digest


def test_compact_appends_and_stays_invisible_to_attention_globs(tmp_path: Path) -> None:
    init_git(tmp_path, "pi@example.invalid", "PI")
    _write_card(tmp_path, "alert-one.md", "resolved", extra="resolved_at: 2026-07-01T00:00:00Z\n")
    lifecycle.compact_resolved_cards(tmp_path, machine="test-machine")
    _write_card(tmp_path, "alert-two.md", "resolved", extra="resolved_at: 2026-07-02T00:00:00Z\n")

    lifecycle.compact_resolved_cards(tmp_path, machine="test-machine")

    digest_path = tmp_path / "inbox/archive/2026-07.md"
    digest = digest_path.read_text(encoding="utf-8")
    assert "(alert-one.md)" in digest and "(alert-two.md)" in digest  # append-only
    assert digest.count("# Inbox archive 2026-07") == 1  # one header per month, not per run
    assert read_frontmatter(digest_path) == {}  # no frontmatter: never an attention card
    assert loudness.open_blockers(tmp_path) == []


def test_compact_journals_hand_edit_before_archiving(tmp_path: Path) -> None:
    init_git(tmp_path, "pi@example.invalid", "PI")
    _write_card(tmp_path, "alert-done.md", "resolved")

    result = lifecycle.compact_resolved_cards(tmp_path, machine="test-machine")

    assert [e["target_id"] for e in result["adopted"]] == ["inbox/alert-done.md"]
    events = state.read_event_log(tmp_path, event_types=("resolved",))
    assert [e["target_id"] for e in events] == ["inbox/alert-done.md"]


def test_compact_commits_deletion_of_tracked_cards(tmp_path: Path) -> None:
    init_git(tmp_path, "pi@example.invalid", "PI")
    _write_card(tmp_path, "alert-done.md", "resolved")
    git(tmp_path, "add", "inbox/alert-done.md")
    git(tmp_path, "commit", "-m", "seed card")

    result = lifecycle.compact_resolved_cards(tmp_path, machine="test-machine")

    assert result["commit"]
    assert "inbox/alert-done.md" not in git(tmp_path, "ls-files")


def test_every_resolved_month_gets_its_own_digest(tmp_path: Path) -> None:
    """N cards over two months: one digest per month, every card in exactly one.

    Compaction is a multi-card, multi-month operation by nature -- a loop that
    archives the first card, or one that files a whole run under a single month
    key, passes any one-card fixture and silently loses the rest of the tail.
    """
    init_git(tmp_path, "pi@example.invalid", "PI")
    _write_card(tmp_path, "alert-may-1.md", "resolved", extra="resolved_at: 2026-05-02\n")
    _write_card(tmp_path, "alert-may-2.md", "resolved", extra="resolved_at: 2026-05-30\n")
    _write_card(tmp_path, "alert-jun-1.md", "resolved", extra="resolved_at: 2026-06-01\n")
    _write_card(tmp_path, "alert-open.md", "open")

    result = lifecycle.compact_resolved_cards(tmp_path, machine="test-machine")

    assert result["archived"] == [
        "inbox/alert-jun-1.md",
        "inbox/alert-may-1.md",
        "inbox/alert-may-2.md",
    ]
    assert sorted(result["digests"]) == ["inbox/archive/2026-05.md", "inbox/archive/2026-06.md"]
    may = (tmp_path / "inbox/archive/2026-05.md").read_text(encoding="utf-8")
    june = (tmp_path / "inbox/archive/2026-06.md").read_text(encoding="utf-8")
    assert "(alert-may-1.md)" in may and "(alert-may-2.md)" in may
    assert "(alert-jun-1.md)" in june
    assert "(alert-jun-1.md)" not in may and "(alert-may-1.md)" not in june
    assert (may.count("\n## "), june.count("\n## ")) == (2, 1)
    assert [p.name for p in (tmp_path / "inbox").glob("*.md")] == ["alert-open.md"]


@pytest.mark.parametrize(
    "written_resolved_at",
    ["", "resolved_at: ''\n", "resolved_at: yesterday\n", "resolved_at: 2026\n"],
)
def test_a_card_that_stamps_no_month_lands_in_the_compaction_months_digest(
    tmp_path: Path, written_resolved_at: str
) -> None:
    """The month-key fallback's producer states, not its rendered value.

    Nothing writes `resolved_at` when a card is closed by hand, YAML hands back an
    `int` for a bare year, and the field is card text besides. Only a `YYYY-MM`
    prefix may name a digest; everything else files under the month the compaction
    ran in, so no card is dropped for want of a stamp.
    """
    init_git(tmp_path, "pi@example.invalid", "PI")
    _write_card(tmp_path, "alert-done.md", "resolved", extra=written_resolved_at)

    result = lifecycle.compact_resolved_cards(tmp_path, machine="test-machine")

    assert result["digests"] == [_this_months_digest()]
    assert (tmp_path / _this_months_digest()).is_file()


def test_a_hostile_resolved_at_cannot_steer_the_digest_out_of_the_archive(
    tmp_path: Path,
) -> None:
    """`resolved_at` is card text: a hand-written or adapter-written card sets it.

    The month key is a matched prefix slice, so it is always `\\d{4}-\\d{2}` -- a
    traversal or an absolute path in that field can never name the file compaction
    creates.
    """
    init_git(tmp_path, "pi@example.invalid", "PI")
    _write_card(tmp_path, "alert-a.md", "resolved", extra="resolved_at: ../../../../tmp/pwn\n")
    _write_card(tmp_path, "alert-b.md", "resolved", extra="resolved_at: /etc/passwd\n")

    result = lifecycle.compact_resolved_cards(tmp_path, machine="test-machine")

    assert result["digests"] == [_this_months_digest()]
    written = sorted(
        path.relative_to(tmp_path).as_posix()
        for path in tmp_path.rglob("*.md")
        if ".git" not in path.parts and ".memoria" not in path.parts
    )
    assert written == [_this_months_digest()]


def test_a_card_with_no_title_is_headed_by_its_file_name(tmp_path: Path) -> None:
    """The title fallback's producer state: a card frontmatter with no `title`.

    Only `write_finding` and friends guarantee one; a hand-written card need not
    carry it, and a section headed `## None` would lose the only handle the digest
    keeps on what was archived.
    """
    init_git(tmp_path, "pi@example.invalid", "PI")
    path = tmp_path / "inbox/alert-untitled.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\nprojection: attention\nattention_status: resolved\n---\n\nBody.\n",
        encoding="utf-8",
    )

    lifecycle.compact_resolved_cards(tmp_path, machine="test-machine")

    digest = (tmp_path / _this_months_digest()).read_text(encoding="utf-8")
    assert "## alert-untitled (alert-untitled.md)" in digest
    assert "None" not in digest  # absent fields are omitted, never rendered as None


def test_case_variant_projection_and_status_are_compacted(tmp_path: Path) -> None:
    """`loudness.is_open_blocker` case-folds both keys, so a `Resolved` card is real.

    Such a card blocks the gate while it is open and is journaled when it closes
    (both fold), so a compaction that matched only the lower-case spelling would
    pin exactly those cards in the hot scan forever.
    """
    init_git(tmp_path, "pi@example.invalid", "PI")
    path = tmp_path / "inbox/alert-shouty.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\ntitle: Stop\nprojection: Attention\nattention_status: Resolved\n---\n\nBody.\n",
        encoding="utf-8",
    )

    result = lifecycle.compact_resolved_cards(tmp_path, machine="test-machine")

    assert result["archived"] == ["inbox/alert-shouty.md"]


def test_a_second_compaction_writes_nothing_and_commits_nothing(tmp_path: Path) -> None:
    """Compaction runs on every scan, including the file-watch tick.

    A commit taken whether or not a card moved would add an empty commit to the
    vault's history on every tick.
    """
    init_git(tmp_path, "pi@example.invalid", "PI")
    _write_card(tmp_path, "alert-done.md", "resolved", extra="resolved_at: 2026-06-30\n")
    first = lifecycle.compact_resolved_cards(tmp_path, machine="test-machine")
    digest_before = (tmp_path / "inbox/archive/2026-06.md").read_text(encoding="utf-8")

    again = lifecycle.compact_resolved_cards(tmp_path, machine="test-machine")

    assert (again["archived"], again["digests"], again["commit"]) == ([], [], "")
    assert (tmp_path / "inbox/archive/2026-06.md").read_text(encoding="utf-8") == digest_before
    assert git(tmp_path, "rev-parse", "HEAD") == first["commit"]


def test_a_vault_with_nothing_to_archive_needs_no_git_repo(tmp_path: Path) -> None:
    """Compaction runs on every `workspace scan`; only archiving needs a commit.

    The journaling half still runs -- a deferred card is a disposition -- so the
    two halves have to be separable without a repo to commit to.
    """
    _write_card(tmp_path, "alert-open.md", "open")
    _write_card(tmp_path, "alert-later.md", "deferred")

    result = lifecycle.compact_resolved_cards(tmp_path, machine="test-machine")

    assert [e["target_id"] for e in result["adopted"]] == ["inbox/alert-later.md"]
    assert (result["archived"], result["digests"], result["commit"]) == ([], [], "")
    assert not (tmp_path / "inbox/archive").exists()


def test_a_vault_with_no_git_repo_refuses_before_touching_a_card(tmp_path: Path) -> None:
    """The digest is only durable once committed, so the repo check precedes the move.

    Appending and unlinking first and discovering the missing repo at the commit
    would leave the tail archived into an uncommitted file and the cards gone from
    a vault whose history cannot record either.
    """
    _write_card(tmp_path, "alert-done.md", "resolved")

    with pytest.raises(RuntimeError, match="git"):
        lifecycle.compact_resolved_cards(tmp_path, machine="test-machine")

    assert (tmp_path / "inbox/alert-done.md").exists()
    assert not (tmp_path / "inbox/archive").exists()


def test_the_archive_is_invisible_to_every_attention_consumer(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The untouched-by-construction argument in the module docstring, pinned.

    Each consumer is named there: two non-recursive `inbox/*.md` globs, the
    work-prompt dedupe's one direct path, and -- for readers that do descend, like
    the seeded `inbox.base` folder view -- the digest's absent frontmatter.
    """
    workspace = init_cli_workspace(tmp_path, capsys)
    prompt = inbox_lib.write_work_prompt(
        workspace,
        "Drift",
        "Look",
        "It drifted",
        "integrity",
        target="notes/n.md",
        dedupe_slug="drift",
    )
    assert prompt is not None
    prompt.write_text(
        prompt.read_text(encoding="utf-8").replace(
            "attention_status: open", "attention_status: resolved"
        ),
        encoding="utf-8",
    )

    lifecycle.compact_resolved_cards(workspace, machine="test-machine")

    digest = workspace / _this_months_digest()
    # Reachable, and invisible only because of the shape of the globs that read it.
    assert digest in set((workspace / "inbox").rglob("*.md"))
    assert digest not in set((workspace / "inbox").glob("*.md"))
    assert read_frontmatter(digest) == {}
    assert 'projection == "attention"' in (workspace / "inbox.base").read_text(encoding="utf-8")
    assert loudness.open_blockers(workspace) == []
    assert engine_api.read_attention(workspace)["attention"] == []
    # The dedupe slot is free again, so a live finding can be re-raised.
    assert (
        inbox_lib.write_work_prompt(
            workspace,
            "Drift",
            "Look",
            "It drifted again",
            "integrity",
            target="notes/n.md",
            dedupe_slug="drift",
        )
        is not None
    )


def test_inbox_files_that_are_not_attention_cards_are_left_alone(tmp_path: Path) -> None:
    """`inbox/` is a folder the PI writes in, not a table this owns.

    Compaction deletes what it archives, so the projection test is the only thing
    between a hand-written note that happens to say `attention_status: resolved`
    and a file the PI never gets back.
    """
    init_git(tmp_path, "pi@example.invalid", "PI")
    plain = tmp_path / "inbox/scratch.md"
    plain.parent.mkdir(parents=True, exist_ok=True)
    plain.write_text("# Scratch\n\nattention_status: resolved\n", encoding="utf-8")
    other = _write_card(tmp_path, "digest-week.md", "resolved", projection="digest")

    result = lifecycle.compact_resolved_cards(tmp_path, machine="test-machine")

    assert result["archived"] == []
    assert plain.is_file() and other.is_file()
    assert not (tmp_path / "inbox/archive").exists()


def test_a_tail_archived_between_the_probe_and_the_lock_is_not_archived_twice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The read inside the lock is the authoritative one; the probe only decides to try.

    Acting on the probe's list instead would append a second digest section for a
    card the winner already archived, then unlink a file that is gone -- and commit
    a tail that moved nowhere.
    """
    init_git(tmp_path, "pi@example.invalid", "PI")
    git(tmp_path, "commit", "--allow-empty", "-m", "seed history")
    head = git(tmp_path, "rev-parse", "HEAD")
    card = _write_card(tmp_path, "alert-done.md", "resolved", extra="resolved_at: 2026-06-30\n")
    real_lock = state.workspace_lock
    fired: list[bool] = []

    @contextlib.contextmanager
    def rival_wins_the_race(vault: Path) -> Any:
        # The disposition row is written under the journaling half's own lock, so
        # its presence marks this acquisition as compaction's, not journaling's.
        if not fired and _dispositions(vault):
            fired.append(True)
            card.unlink()  # the winner archived it while this call waited
        with real_lock(vault):
            yield

    monkeypatch.setattr(state, "workspace_lock", rival_wins_the_race)
    result = lifecycle.compact_resolved_cards(tmp_path, machine="test-machine")
    monkeypatch.undo()

    assert fired == [True]  # the state under test was produced, not assumed
    assert (result["archived"], result["digests"], result["commit"]) == ([], [], "")
    assert not (tmp_path / "inbox/archive").exists()
    assert git(tmp_path, "rev-parse", "HEAD") == head  # nothing moved, so nothing committed


def test_a_rival_scan_cannot_enter_the_archive_mid_compaction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two scans racing one resolved card leave one digest section, not two.

    `workspace scan` is both the file-watch tick and a command the PI runs, so two
    of them overlap on a live vault. Outside one critical section both read the
    same card, both append it to the digest, and the second `unlink` raises on a
    file the first already removed -- a duplicated archive entry and an error out
    of a hygiene pass.
    """
    init_git(tmp_path, "pi@example.invalid", "PI")
    _write_card(tmp_path, "alert-done.md", "resolved", extra="resolved_at: 2026-06-30\n")
    with state.connect(tmp_path):  # build the schema before the race, not during it
        pass
    real_append = lifecycle.append_text_durable
    rival: list[threading.Thread] = []
    rival_errors: list[BaseException] = []

    def rival_session() -> None:
        try:
            lifecycle.compact_resolved_cards(tmp_path, machine="rival")
        except BaseException as exc:  # noqa: BLE001 - reported on the main thread
            rival_errors.append(exc)

    def racing_append(*args: Any, **kwargs: Any) -> None:
        if not rival:  # the rival's own append must not start a third session
            thread = threading.Thread(target=rival_session)
            rival.append(thread)
            thread.start()
            thread.join(timeout=0.5)  # finishes only if nothing held it out
        real_append(*args, **kwargs)

    monkeypatch.setattr(lifecycle, "append_text_durable", racing_append)
    lifecycle.compact_resolved_cards(tmp_path, machine="test-machine")
    rival[0].join(timeout=30)
    monkeypatch.undo()

    assert rival_errors == []
    digest = (tmp_path / "inbox/archive/2026-06.md").read_text(encoding="utf-8")
    assert digest.count("(alert-done.md)") == 1
