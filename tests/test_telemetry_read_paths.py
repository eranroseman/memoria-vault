"""Runtime proof: read paths record telemetry and never dirty the tracked tree."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from memoria_vault.engine import api as engine_api
from memoria_vault.runtime import state
from memoria_vault.runtime.attention.inbox import write_finding
from memoria_vault.runtime.vaultio import frontmatter_doc
from tests.helpers import git, init_git

pytestmark = pytest.mark.runtime

# Only the DB and its sidecars are allowed to appear or change during a read: they are
# gitignored (`product/workspace_seed/.gitignore`) and excluded from the floor digest.
_SQLITE_SUFFIXES = (".sqlite", ".sqlite-wal", ".sqlite-shm", ".sqlite-journal")


def _vault_with_card(tmp_path: Path) -> tuple[Path, str]:
    vault = tmp_path
    init_git(vault, "reads@example.invalid", "Telemetry Reads")
    (vault / ".gitignore").write_text(".memoria/memoria.sqlite*\n", encoding="utf-8")
    path = write_finding(vault, "flag", "Check w1", "w1 drifted", "sweep", target="notes/w1.md")
    assert path is not None
    rel = path.relative_to(vault).as_posix()
    git(vault, "add", ".")
    git(vault, "commit", "-q", "-m", "seed")
    return vault, rel


def _rewrite_card(vault: Path, rel: str, **frontmatter: object) -> str:
    """Replace the seeded card so a test can vary one frontmatter field at a time."""
    (vault / rel).write_text(
        frontmatter_doc(
            {
                "title": "Rewritten card",
                "projection": "attention",
                "attention_kind": "flag",
                "attention_status": "open",
                "loudness": "alert",
                **frontmatter,
            },
            "# Finding\n\nrewritten\n",
        ),
        encoding="utf-8",
    )
    git(vault, "add", ".")
    git(vault, "commit", "-q", "-m", "rewrite card")
    return rel


def _tree(vault: Path) -> dict[str, str]:
    """Every path under the vault with its content hash, minus git internals and the DB.

    A `git status` comparison alone cannot see a gitignored file appearing, and a
    tracked-file diff cannot see an untracked one. This sees both.
    """
    tree: dict[str, str] = {}
    for path in sorted(vault.rglob("*")):
        rel = path.relative_to(vault).as_posix()
        if rel.startswith(".git/") or rel == ".git":
            continue
        if path.is_dir():
            tree[rel + "/"] = ""
            continue
        if rel.endswith(_SQLITE_SUFFIXES):
            continue
        tree[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return tree


def _read_observed(vault: Path) -> list[dict]:
    with state.connect(vault) as conn:
        # `rowid`, not `event_id`: the id is a uuid4 hex, so ordering by it shuffles
        # the rows and a two-read test reads whichever one sorted first.
        rows = conn.execute(
            "SELECT session_id, surface, payload_json FROM telemetry_events"
            " WHERE event_type = 'read-observed.v1' ORDER BY rowid"
        ).fetchall()
    return [dict(row) for row in rows]


def test_attention_detail_read_emits_one_read_observed_row(tmp_path: Path) -> None:
    vault, rel = _vault_with_card(tmp_path)

    engine_api.read_attention_card(vault, rel)

    rows = _read_observed(vault)
    assert len(rows) == 1
    assert json.loads(rows[0]["payload_json"]) == {"workflow": "attention", "staleness_hit": False}
    # Server-side row: never fabricate the client's own columns.
    assert rows[0]["session_id"] is None
    assert rows[0]["surface"] is None


@pytest.mark.parametrize(
    ("mark", "expected"),
    [
        (True, True),
        # A quoted string is not a boolean. `staleness_hit` is measured, so only the
        # real `stale: true` mark counts — the same reading `feedback.yaml` gets.
        ("true", False),
        (False, False),
    ],
)
def test_stale_mark_decides_the_staleness_hit(tmp_path: Path, mark: object, expected: bool) -> None:
    vault, rel = _vault_with_card(tmp_path)
    _rewrite_card(vault, rel, target="notes/w2.md", stale=mark)

    engine_api.read_attention_card(vault, rel)

    (row,) = _read_observed(vault)
    assert json.loads(row["payload_json"]) == {"workflow": "attention", "staleness_hit": expected}


def test_staleness_falls_back_to_the_consequence_mirror_when_it_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Order-tolerance with the graph plan's ERP-C, exercised in both directions.

    `state.concept_consequence` does not exist yet, so the `hasattr` guard is what
    decides. Standing the symbol up here is the only way this branch gets coverage
    before ERP-C lands — and it pins the contract ERP-C has to meet: called with
    `(workspace, target)`, never asked about a card with no target, and a raising
    mirror degrading to `False` rather than breaking the read.
    """
    vault, rel = _vault_with_card(tmp_path)
    seen: list[tuple[Path, str]] = []

    def _mirror(workspace: Path, target: str) -> bool:
        seen.append((workspace, target))
        return True

    def _broken_mirror(workspace: Path, target: str) -> bool:
        raise RuntimeError("consequence mirror unavailable")

    monkeypatch.setattr(state, "concept_consequence", _mirror, raising=False)
    engine_api.read_attention_card(vault, rel)

    assert seen == [(vault, "notes/w1.md")]
    (row,) = _read_observed(vault)
    assert json.loads(row["payload_json"])["staleness_hit"] is True

    monkeypatch.setattr(state, "concept_consequence", _broken_mirror, raising=False)
    engine_api.read_attention_card(vault, rel)

    assert json.loads(_read_observed(vault)[1]["payload_json"])["staleness_hit"] is False

    # A card with no target has nothing to ask the mirror about, so it is not asked.
    seen.clear()
    monkeypatch.setattr(state, "concept_consequence", _mirror, raising=False)
    _rewrite_card(vault, rel, citekey="x2024demo")
    engine_api.read_attention_card(vault, rel)

    assert seen == []
    assert json.loads(_read_observed(vault)[2]["payload_json"])["staleness_hit"] is False


def test_a_read_denied_by_scope_records_nothing(tmp_path: Path) -> None:
    """A denied read is not an observed read: the emitter sits behind the scope check."""
    vault, rel = _vault_with_card(tmp_path)

    with pytest.raises(FileNotFoundError, match="attention projection not found"):
        engine_api.read_attention_card(vault, rel, read_scope=["notes/elsewhere.md"])

    assert _read_observed(vault) == []


def test_a_failing_telemetry_write_never_breaks_the_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault, rel = _vault_with_card(tmp_path)

    def _explode(*args: object, **kwargs: object) -> str:
        raise RuntimeError("telemetry table is gone")

    monkeypatch.setattr("memoria_vault.runtime.telemetry.record_telemetry_event", _explode)

    payload = engine_api.read_attention_card(vault, rel)

    assert payload["attention"]["path"] == rel
    assert _read_observed(vault) == []


def test_repeated_reads_leave_the_tracked_tree_and_the_journal_untouched(tmp_path: Path) -> None:
    """The negative claim, asserted as an absence rather than as a happy return.

    Four independent ways a read could dirty the vault, each pinned: a new or changed
    file anywhere in the tree, a `git status` change, a new commit, and a journal row
    (which is what would move the tracked `.memoria/journal-head` anchor).
    """
    vault, rel = _vault_with_card(tmp_path)
    engine_api.read_attention_card(vault, rel)  # let the DB file itself be created first
    tree_before = _tree(vault)
    status_before = git(vault, "status", "--porcelain")
    head_before = git(vault, "rev-parse", "HEAD")
    with state.connect(vault) as conn:
        journal_before = conn.execute("SELECT COUNT(*) FROM event_log").fetchone()[0]

    for _ in range(25):
        engine_api.read_attention_card(vault, rel)
        engine_api.read_attention(vault)

    assert _tree(vault) == tree_before
    assert git(vault, "status", "--porcelain") == status_before
    assert git(vault, "rev-parse", "HEAD") == head_before
    with state.connect(vault) as conn:
        journal_after = conn.execute("SELECT COUNT(*) FROM event_log").fetchone()[0]
    assert journal_after == journal_before
    assert state.verify_journal_chain(vault)["ok"] is True
    assert not (vault / state.JOURNAL_HEAD_REL).exists()
    # The reads really did run and really did record: 26 detail reads, and the list
    # read (`read_attention`) is not a detail read, so it contributes nothing.
    assert len(_read_observed(vault)) == 26
