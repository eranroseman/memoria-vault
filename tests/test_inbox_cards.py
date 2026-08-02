"""Inbox helpers write attention projections, not Concept cards."""

import datetime
import os
import re
import threading
import time
from pathlib import Path

import pytest
import yaml

from memoria_vault.runtime import state
from memoria_vault.runtime.subsystems.lib import inbox, loudness

pytestmark = pytest.mark.contract


def _frontmatter(path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return yaml.safe_load(m.group(1))


def _today() -> str:
    return datetime.date.today().isoformat()


def _card(
    vault: Path,
    name: str,
    *,
    fingerprint: str,
    projection: str = "attention",
    status: str = "open",
    subdir: str = "inbox",
    card_loudness: str = "alert",
    extra: str = "",
) -> Path:
    """Hand-write an inbox card, YAML scalars verbatim.

    `inbox/**` is the one write target the reference actor policy grants a non-PI
    actor, so an adapter's spelling of these fields is a producible state and not a
    hypothetical: the scalars go in as written, padding and casing included.
    """
    path = vault / subdir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        "title: Standing\n"
        f"projection: {projection}\n"
        "attention_kind: alert\n"
        f"attention_status: {status}\n"
        f"fingerprint: {fingerprint}\n"
        "raised_by: sweep\n"
        f"loudness: {card_loudness}\n"
        "created: '2020-01-01'\n"
        "last_seen: '2020-01-01'\n"
        f"{extra}"
        "---\n\n# Finding\n\nBody.\n",
        encoding="utf-8",
    )
    return path


def _but_last_seen(frontmatter: dict) -> dict:
    return {key: value for key, value in frontmatter.items() if key != "last_seen"}


def _alert(vault: Path, **kwargs) -> Path | None:
    return inbox.write_finding(
        vault, "alert", "Retraction: w1", "DOI 10.1/x is retracted", "sweep", **kwargs
    )


def test_proposal_card_is_attention_projection(tmp_path):
    p = inbox.write_proposal(
        tmp_path,
        "candidate",
        "Smith 2024 on X",
        "Accept this source into the catalog",
        "fills the X gap",
        "venue is low-signal",
        "the gap outweighs the venue",
        "likely",
        "librarian",
        citekey="@smith2024",
    )
    fm = _frontmatter(p)
    assert fm["projection"] == "attention"
    assert fm["attention_kind"] == "candidate"
    assert fm["attention_status"] == "open"
    assert "type" not in fm


def test_proposal_carries_no_verdict(tmp_path):
    p = inbox.write_proposal(
        tmp_path,
        "gap",
        "Missing RCTs on Y",
        "Search for sources",
        "for",
        "against",
        "tipped",
        "unsure",
        "librarian",
    )
    fm = _frontmatter(p)
    assert "agent_recommendation" not in fm  # the verdict is a given — omitted
    assert "finding" not in fm


def test_finding_card_is_attention_projection(tmp_path):
    p = inbox.write_finding(
        tmp_path,
        "flag",
        "Broken citekey",
        "citekey @ghost resolves nowhere",
        "linter",
        target="notes/claims/c.md",
        evidence="grep output",
    )
    fm = _frontmatter(p)
    assert fm["projection"] == "attention"
    assert fm["attention_kind"] == "flag"
    assert fm["attention_status"] == "open"
    assert "type" not in fm
    body = p.read_text(encoding="utf-8")
    assert "# Finding" in body and "# Evidence" in body


def test_flag_requires_a_pointer(tmp_path):
    with pytest.raises(ValueError):
        inbox.write_finding(tmp_path, "flag", "t", "f", "linter")


def test_collision_appends_not_overwrites(tmp_path):
    a = inbox.write_proposal(
        tmp_path, "candidate", "Same Title", "a", "b", "c", "d", "likely", "librarian"
    )
    b = inbox.write_proposal(
        tmp_path, "candidate", "Same Title", "a", "b", "c", "d", "likely", "librarian"
    )
    assert a != b and a.exists() and b.exists()


def test_work_prompt_card_is_attention_projection(tmp_path):
    p = inbox.write_work_prompt(
        tmp_path,
        "Review: Draft answer",
        "Review the draft, then accept or archive",
        'Request REQ-b2 produced "Draft answer".',
        "request-control",
        target="projects/p1/draft.md",
        request_id="REQ-b2",
        posture="writer",
    )
    fm = _frontmatter(p)
    assert fm["projection"] == "attention"
    assert fm["attention_kind"] == "work-prompt"
    assert fm["attention_status"] == "open"
    assert fm["request_id"] == "REQ-b2"
    assert fm["posture"] == "writer"
    assert "task_id" not in fm
    assert "lane" not in fm
    assert "type" not in fm
    body = p.read_text(encoding="utf-8")
    assert "# Action" in body and "# What happened" in body and "# Where to look" in body


def test_work_prompt_carries_no_verdict(tmp_path):
    p = inbox.write_work_prompt(
        tmp_path,
        "Review: X",
        "review it",
        "request finished X",
        "request-control",
        request_id="REQ-1",
    )
    text = p.read_text(encoding="utf-8")
    assert "agent_recommendation" not in text  # work prompts never carry verdicts
    assert "finding" not in _frontmatter(p)


def test_work_prompt_requires_a_pointer(tmp_path):
    with pytest.raises(ValueError):
        inbox.write_work_prompt(tmp_path, "t", "a", "w", "board-export")


def test_work_prompt_dedupe_slug_is_idempotent(tmp_path):
    a = inbox.write_work_prompt(
        tmp_path,
        "Review: X",
        "a",
        "w",
        "request-control",
        request_id="REQ-1",
        dedupe_slug="review-REQ-1",
    )
    b = inbox.write_work_prompt(
        tmp_path,
        "Review: X",
        "a",
        "w",
        "request-control",
        request_id="REQ-1",
        dedupe_slug="review-REQ-1",
    )
    assert a is not None and a.name == "work-prompt-review-req-1.md"
    assert b is None  # second emit for the same card id writes nothing
    assert len(list((tmp_path / "inbox").glob("*.md"))) == 1


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


def test_finding_fingerprint_dedupes_against_open_card_and_touches_last_seen(tmp_path):
    a = inbox.write_finding(
        tmp_path,
        "alert",
        "Retraction: w1",
        "DOI 10.1/x is retracted",
        "sweep",
        fingerprint="retraction:10.1/x",
    )
    # age the card so the re-observe touch is observable
    today = _today()
    a.write_text(a.read_text(encoding="utf-8").replace(today, "2020-01-01"), encoding="utf-8")

    b = inbox.write_finding(
        tmp_path,
        "alert",
        "Retraction: w1",
        "DOI 10.1/x is retracted",
        "sweep",
        fingerprint="retraction:10.1/x",
    )

    assert a is not None and b is None
    assert len(list((tmp_path / "inbox").glob("*.md"))) == 1
    fm = _frontmatter(a)
    assert fm["fingerprint"] == "retraction:10.1/x"
    assert fm["last_seen"] == today
    # The touch records an observation and nothing else: the card keeps its own
    # birthday, its open status, and its body. A re-write that reset `created`
    # would silently restart every age-based reading of the standing card.
    assert fm["created"] == "2020-01-01"
    assert fm["attention_status"] == "open"
    assert "# Finding\n\nDOI 10.1/x is retracted" in a.read_text(encoding="utf-8")


def test_finding_fingerprint_reraises_after_resolution(tmp_path):
    a = inbox.write_finding(
        tmp_path, "alert", "Retraction: w1", "f", "sweep", fingerprint="retraction:10.1/x"
    )
    a.write_text(
        a.read_text(encoding="utf-8").replace(
            "attention_status: open", "attention_status: resolved"
        ),
        encoding="utf-8",
    )
    a.write_text(a.read_text(encoding="utf-8").replace(_today(), "2020-01-01"), encoding="utf-8")

    b = inbox.write_finding(
        tmp_path, "alert", "Retraction: w1", "f", "sweep", fingerprint="retraction:10.1/x"
    )

    assert b is not None and b != a
    assert _frontmatter(b)["attention_status"] == "open"
    assert len(list((tmp_path / "inbox").glob("*.md"))) == 2
    # The resolved card is not the standing one: it is neither touched nor removed.
    # Compaction owns its removal, and it is the only `.unlink()` in `src/` that may
    # free an `inbox/` name -- because only it also journals the release row.
    assert _frontmatter(a)["last_seen"] == "2020-01-01"


@pytest.mark.parametrize(
    ("field", "scalar"),
    [
        ("projection", '" attention "'),
        ("projection", "Attention"),
        ("status", '" open "'),
        ("status", "OPEN"),
        ("fingerprint", '" retraction:10.1/x "'),
    ],
)
def test_finding_fingerprint_reads_frontmatter_the_way_lifecycle_reads_it(tmp_path, field, scalar):
    """One unstripped read is all it takes for two readers to disagree about a card.

    `lifecycle._closed_cards` folded `projection` without stripping it while its own
    sibling did both, so `projection: " attention "` was invisible to journaling and
    visible to compaction -- archived and deleted with no journal row at all. These
    are two more frontmatter reads in the same family, so they normalize the same
    way: `.strip().lower()` on the two vocabulary fields.

    `fingerprint` is stripped and *not* folded. It is an identity rather than a term
    from a fixed vocabulary -- the sibling identity field, the journal's `target_id`,
    is not folded either -- and folding it would merge two conditions whose producer
    deliberately distinguishes them. Each case perturbs exactly one field.
    """
    fields = {"projection": "attention", "status": "open", "fingerprint": "retraction:10.1/x"}
    fields[field] = scalar  # `status` writes `attention_status`; see `_card`
    standing = _card(tmp_path, "alert-standing.md", **fields)
    before = _frontmatter(standing)

    b = _alert(tmp_path, fingerprint="retraction:10.1/x")

    after = _frontmatter(standing)
    assert b is None
    assert len(list((tmp_path / "inbox").glob("*.md"))) == 1
    assert after["last_seen"] == _today()
    # The *reader* normalizes; the writer must not. A touch that wrote the folded
    # value back would quietly rewrite the PI's card to the runtime's spelling, and
    # every field it did not think to preserve with it.
    assert _but_last_seen(after) == _but_last_seen(before)


def test_finding_fingerprint_is_not_case_folded(tmp_path):
    """The deliberate half of the normalization decision, pinned in its own direction.

    `retraction:10.1/X` and `retraction:10.1/x` are two identities. The retraction
    sweep folds case itself (`normalize_doi`) precisely because that is the producer's
    call to make; a reader that folded for everyone would collapse producers whose
    keys are case-sensitive by nature, and paths are the obvious one.
    """
    standing = _card(tmp_path, "alert-standing.md", fingerprint="retraction:10.1/X")

    b = _alert(tmp_path, fingerprint="retraction:10.1/x")

    assert b is not None
    assert len(list((tmp_path / "inbox").glob("*.md"))) == 2
    assert _frontmatter(standing)["last_seen"] == "2020-01-01"


def test_finding_fingerprint_is_not_case_folded_on_the_way_in_either(tmp_path):
    """The same decision on the *write* side, where canonicalization happens.

    A hand-built standing card can only ever observe a folding reader. The argument
    is canonicalized in one place -- the `.strip()` this task added -- and a `.lower()`
    there is a one-token edit that makes `retraction:10.1/X` and `retraction:10.1/x`
    one identity, which is exactly what the reader's contract says they are not. Both
    cards are written by the writer under test, so only the write side can decide it.
    """
    a = _alert(tmp_path, fingerprint="retraction:10.1/X")
    b = _alert(tmp_path, fingerprint="retraction:10.1/x")

    assert a is not None and b is not None and a != b
    assert _frontmatter(a)["fingerprint"] == "retraction:10.1/X"
    assert _frontmatter(b)["fingerprint"] == "retraction:10.1/x"


def test_the_touch_preserves_the_pis_hand_escalation(tmp_path):
    """`last_seen` is the only field a re-observation may move, and `loudness` is why.

    The PI hand-escalates a standing retraction alert to `loudness: block` --
    `inbox/**` is the one write target the policy grants a non-PI actor, and hand
    editing this surface is the premise of the whole feature. `loudness.is_open_blocker`
    reads that field to hold delegation and review-gated promotion, so a touch that
    rebuilt the card from the *new* observation's frontmatter -- the natural
    alternative, since `write_finding` assembled exactly such a dict five lines
    earlier -- would silently reset it to `alert` and open the gate on a schedule.
    Whole-dict equality rather than field assertions, because the fields a rebuild
    drops are the ones nobody thought to name: here, the PI's own `pi_note`.
    """
    standing = _card(
        tmp_path,
        "alert-standing.md",
        fingerprint="retraction:10.1/x",
        card_loudness="block",
        extra="pi_note: escalated after the third recurrence\n",
    )
    before = _frontmatter(standing)

    b = _alert(tmp_path, fingerprint="retraction:10.1/x")

    after = _frontmatter(standing)
    assert b is None
    assert after["last_seen"] == _today() and before["last_seen"] == "2020-01-01"
    assert _but_last_seen(after) == _but_last_seen(before)
    assert loudness.is_open_blocker(after)  # the gate still holds after the touch


@pytest.mark.parametrize(
    ("projection", "status"),
    [
        ("attention", "resolved"),
        ("attention", "deferred"),
        ("attention", ""),
        ("note", "open"),
    ],
)
def test_finding_fingerprint_ignores_a_card_that_is_not_open_attention(
    tmp_path, projection, status
):
    """Only an *open* attention card is a standing one; every other state re-raises.

    Named producers: `resolved` is the PI's hand before compaction sweeps it;
    `deferred` is the PI's "not now", which compaction leaves in `inbox/` forever --
    so a deferred card costs one fresh card per deferral, bounded, because that card
    is open and suppresses the next sweep; the empty status is a hand-cleared field;
    and `projection: note` is an ordinary note that happens to carry the key. Every
    one of them re-raises, which is the safe direction: a card too many is visible
    and removable, a suppressed alert is neither.
    """
    standing = _card(
        tmp_path,
        "alert-standing.md",
        fingerprint="retraction:10.1/x",
        projection=projection,
        status=status,
    )

    b = _alert(tmp_path, fingerprint="retraction:10.1/x")

    assert b is not None and b != standing
    assert len(list((tmp_path / "inbox").glob("*.md"))) == 2
    assert _frontmatter(standing)["last_seen"] == "2020-01-01"


def test_finding_fingerprint_wins_over_the_dedupe_slug_existence_check(tmp_path):
    """The fingerprint check runs first, and the two are orthogonal.

    Observable only when both are passed: the slug's slot is free, so a dedupe-first
    implementation writes a second card there. Fingerprint-first touches the standing
    card wherever it lives and leaves the slot empty.
    """
    standing = _card(tmp_path, "alert-standing.md", fingerprint="retraction:10.1/x")
    slot = tmp_path / "inbox/alert-retraction-10-1-x.md"

    b = _alert(tmp_path, dedupe_slug="retraction:10.1/x", fingerprint="retraction:10.1/x")

    assert b is None
    assert not slot.exists()
    assert len(list((tmp_path / "inbox").glob("*.md"))) == 1
    assert _frontmatter(standing)["last_seen"] == _today()


def test_finding_fingerprint_touches_exactly_one_of_several_open_cards(tmp_path):
    """N>1 on both axes: several cards in `inbox/`, several of them matching.

    A duplicate pair is the state this parameter exists to stop producing, so it is
    also the state it has to survive reading: every sweep before this change left
    another one. The scan settles it by sorted order and touches that card alone.
    """
    other = _card(tmp_path, "alert-a-other.md", fingerprint="retraction:10.1/other")
    first = _card(tmp_path, "alert-b-match.md", fingerprint="retraction:10.1/x")
    second = _card(tmp_path, "alert-c-match.md", fingerprint="retraction:10.1/x")

    b = _alert(tmp_path, fingerprint="retraction:10.1/x")

    assert b is None
    assert len(list((tmp_path / "inbox").glob("*.md"))) == 3
    assert _frontmatter(other)["last_seen"] == "2020-01-01"
    # The two semantic claims -- exactly one match touched, non-matches never touched
    # -- hold on any filesystem. The next line is the determinism claim, and it is the
    # only one that needs readdir order to differ from lexical order to catch an
    # unsorted scan; on a filesystem where they coincide it is merely true.
    assert _frontmatter(first)["last_seen"] == _today()
    assert _frontmatter(second)["last_seen"] == "2020-01-01"


def test_finding_without_a_fingerprint_writes_neither_field_and_still_collides(tmp_path):
    """The default arm, produced rather than assumed: no fingerprint, no scan, no fields."""
    a = _alert(tmp_path)
    b = _alert(tmp_path)

    assert a is not None and b is not None and a != b
    fm = _frontmatter(a)
    assert "fingerprint" not in fm
    assert "last_seen" not in fm
    # Blast radius. The workspace lock is scoped to the fingerprint branch, so this
    # writer's other callers -- the trusted writer's foreign-edit flag among them --
    # keep both their footprint and their timing. `.memoria/locks/` appears only when
    # a caller asks for the dedupe that needs serializing.
    #
    # The state DB is not part of that claim and is expected: I1 A.3 records one
    # `attention-admitted` telemetry row per actual write, and `telemetry_events`
    # lives in `.memoria/memoria.sqlite`. Every other `.memoria/` child is still an
    # absence this pins.
    assert not (tmp_path / ".memoria" / "locks").exists()
    assert [child.name for child in (tmp_path / ".memoria").iterdir()] == ["memoria.sqlite"]
    assert sorted(child.name for child in tmp_path.iterdir()) == [".memoria", "inbox"]


def test_finding_fingerprint_scan_survives_an_unreadable_inbox_file(tmp_path):
    """One file in `inbox/` that is not text must not take a sweep down.

    `inbox/**` is the one write target the policy grants a non-PI actor, and the PI's
    editor writes there too, so a stray non-UTF-8 file named `.md` is producible. It
    sorts ahead of the standing card here, so a scan that read it directly would raise
    before ever reaching the match it was called to find.
    """
    (tmp_path / "inbox").mkdir()
    (tmp_path / "inbox/alert-binary.md").write_bytes(b"\xff\xfe\x00 not utf-8")
    standing = _card(tmp_path, "alert-standing.md", fingerprint="retraction:10.1/x")

    b = _alert(tmp_path, fingerprint="retraction:10.1/x")

    assert b is None
    assert _frontmatter(standing)["last_seen"] == _today()


def test_finding_fingerprint_never_looks_inside_the_inbox_archive(tmp_path):
    """Cross-section contract 12: every `inbox/` reader is non-recursive.

    The archive digest is where an archived card's `fingerprint` survives
    (`lifecycle._DIGEST_FIELDS` carries it), so a recursive glob here would let an
    archived card suppress the re-raise this parameter exists to allow -- permanently,
    since the journal forbids removing what the digest holds. The fixture is a whole
    card under `archive/` rather than a digest, because a digest has no frontmatter
    and so cannot fail the glob: only a card can.
    """
    archived = _card(
        tmp_path, "alert-archived.md", fingerprint="retraction:10.1/x", subdir="inbox/archive"
    )

    b = _alert(tmp_path, fingerprint="retraction:10.1/x")

    assert b is not None and b.parent == tmp_path / "inbox"
    assert _frontmatter(archived)["last_seen"] == "2020-01-01"


def test_finding_fingerprint_reads_only_the_markdown_in_the_inbox(tmp_path):
    """The scan is `*.md`, not `*` -- `inbox/` holds in-flight temp files too.

    `write_text_durable` writes `.{name}.{rand}.tmp` beside its target before renaming
    it into place, and an *unfingerprinted* `write_finding` does that outside this
    lock, so a `glob("*")` reader can meet a half-written sibling carrying a matching
    fingerprint. It sorts first, because the name begins with a dot. The scan would
    touch a file that is about to be renamed away and report the condition as
    standing -- so no card is raised at all, which is the one outcome worse than the
    duplicate being fixed.
    """
    inflight = _card(tmp_path, ".alert-standing.md.ab12cd.tmp", fingerprint="retraction:10.1/x")

    b = _alert(tmp_path, fingerprint="retraction:10.1/x")

    assert b is not None and b.suffix == ".md"
    assert _frontmatter(inflight)["last_seen"] == "2020-01-01"


@pytest.mark.parametrize(
    ("projection", "status", "fingerprint"),
    [
        ("attentionish", "open", "retraction:10.1/x"),
        ("attention", "opened", "retraction:10.1/x"),
        ("attention", "open", "retraction:10.1/xyz"),
    ],
)
def test_finding_fingerprint_matches_each_field_exactly_not_by_prefix(
    tmp_path, projection, status, fingerprint
):
    """Three equality tests, so three chances to become a prefix or substring test.

    The five normalization cases pin `.strip().lower()` and say nothing about the
    operator: `startswith` passes every one of them. Each case here is a near miss on
    exactly one field, and every near miss must re-raise -- a `10.1/xyz` retraction is
    not a `10.1/x` retraction, and a card the PI typed `opened` on was never open.
    """
    standing = _card(
        tmp_path,
        "alert-standing.md",
        fingerprint=fingerprint,
        projection=projection,
        status=status,
    )

    b = _alert(tmp_path, fingerprint="retraction:10.1/x")

    assert b is not None and b != standing
    assert len(list((tmp_path / "inbox").glob("*.md"))) == 2
    assert _frontmatter(standing)["last_seen"] == "2020-01-01"


def test_the_touch_replaces_the_card_rather_than_truncating_it(tmp_path):
    """A half-written attention card reads as no card at all, and the gate opens.

    `write_frontmatter_doc` goes through `write_text_durable`: a sibling temp file,
    then `os.replace`. An in-place `write_text` truncates first, and the window is not
    academic -- `loudness.open_blockers` globs `inbox/*.md` on the review-gate path
    *without* the workspace lock, and `parse_frontmatter` returns `{}` for a document
    whose closing `---` has not been written yet. A `loudness: block` card would be
    invisible to the gate for the length of that write.

    The hardlink is the deterministic proxy for "replaced, not truncated": only a
    rename leaves the old inode's bytes intact behind it.
    """
    standing = _card(
        tmp_path, "alert-standing.md", fingerprint="retraction:10.1/x", card_loudness="block"
    )
    before = standing.read_text(encoding="utf-8")
    witness = tmp_path / "witness.md"  # outside inbox/, so the scan never sees it
    os.link(standing, witness)

    b = _alert(tmp_path, fingerprint="retraction:10.1/x")

    assert b is None
    assert witness.read_text(encoding="utf-8") == before
    assert _frontmatter(standing)["last_seen"] == _today()


def test_finding_fingerprint_argument_is_stripped_before_it_is_stored(tmp_path):
    """The stored key is canonical, so two producers that disagree on padding still match."""
    a = _alert(tmp_path, fingerprint="  retraction:10.1/x  ")

    b = _alert(tmp_path, fingerprint="retraction:10.1/x")

    assert a is not None and b is None
    assert _frontmatter(a)["fingerprint"] == "retraction:10.1/x"


def test_finding_whitespace_only_fingerprint_is_no_fingerprint(tmp_path):
    a = _alert(tmp_path, fingerprint="   ")

    assert a is not None
    assert "fingerprint" not in _frontmatter(a)
    assert "last_seen" not in _frontmatter(a)


def test_the_fingerprint_decision_and_the_write_it_drives_are_one_critical_section(
    tmp_path, monkeypatch
):
    """Two sweeps that overlap must raise one card, not the pair this task exists to stop.

    The check is a check-then-act over `inbox/`, and the module-mates settled this
    shape already: `lifecycle` puts the read that decides and the writes it drives in
    one `state.workspace_lock`. Unserialized, both callers read an inbox with no
    standing card and both write one -- and the loser of a race against compaction is
    worse than a duplicate, because `_touch_last_seen` renames a temp file into place
    and would resurrect a card the journal has already recorded as archived.

    No probe outside the lock, unlike the module-mates: every fingerprinted call
    intends to write or to touch, so there is no no-op case for a probe to keep off it.
    """
    real_match = inbox._open_fingerprint_match
    entered = threading.Event()
    rival_ready = threading.Event()
    results: list[object] = []

    def slow_match(vault, fingerprint):
        match = real_match(vault, fingerprint)
        entered.set()
        rival_ready.wait(5)
        time.sleep(0.2)  # hold the section open across the rival's whole attempt
        return match

    def rival() -> None:
        entered.wait(5)
        rival_ready.set()
        results.append(_alert(tmp_path, fingerprint="retraction:10.1/x"))

    monkeypatch.setattr(inbox, "_open_fingerprint_match", slow_match)
    thread = threading.Thread(target=rival)
    thread.start()
    try:
        first = _alert(tmp_path, fingerprint="retraction:10.1/x")
    finally:
        thread.join(30)

    assert entered.is_set() and rival_ready.is_set()  # the overlap was produced
    assert first is not None
    assert results == [None]  # the rival re-observed the card it could not see
    assert len(list((tmp_path / "inbox").glob("*.md"))) == 1
    assert _frontmatter(first)["last_seen"] == _today()


def test_a_fingerprinted_write_serializes_against_the_workspace_lock(tmp_path):
    """The lock is the workspace lock, not a private one -- which is what excludes compaction.

    Compaction unlinks archived cards under `state.workspace_lock`; a fingerprinted
    write that took any other lock would be excluded from nothing.
    """
    held = threading.Event()
    release = threading.Event()
    done: list[object] = []

    def holder() -> None:
        with state.workspace_lock(tmp_path):
            held.set()
            release.wait(5)

    thread = threading.Thread(target=holder)
    thread.start()
    try:
        assert held.wait(5)

        started = threading.Event()

        def writer() -> None:
            started.set()
            done.append(_alert(tmp_path, fingerprint="retraction:10.1/x"))

        write_thread = threading.Thread(target=writer)
        write_thread.start()
        try:
            assert started.wait(5)  # the writer really reached the call
            write_thread.join(0.3)
            assert done == []  # blocked behind the holder, not racing past it
        finally:
            release.set()
            write_thread.join(30)
    finally:
        release.set()
        thread.join(30)

    assert len(done) == 1 and done[0] is not None


def test_invalid_enums_rejected(tmp_path):
    with pytest.raises(ValueError):
        inbox.write_proposal(
            tmp_path, "candidate", "T", "a", "b", "c", "d", "very-sure", "librarian"
        )
    with pytest.raises(ValueError):
        inbox.write_finding(tmp_path, "alert", "T", "f", "linter", agent_recommendation="fine")
