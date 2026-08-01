"""Hub Candidates block writer (NODES §5): delimited, machine-owned terminal section."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.hub_candidates import (
    candidate_entry,
    render_candidates_section,
    split_candidates_section,
    write_hub_candidates,
)
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.vaultio import split_frontmatter
from tests.helpers import call_with_context, copy_memoria_dirs, init_git

HUB_ID = "01KBN6V6KX0000000000000007"
CURATED_BODY = "# Framing\n\nHuman text.\n"
HUB_TEXT = (
    f"---\ntype: hub\nid: {HUB_ID}\ntitle: Framing\ntag: framing\ntags: []\nlinks: {{}}\n---\n"
) + CURATED_BODY

# Deliberately crossed against the database verdict each test installs, so no
# assertion here can be satisfied by reading the wrong check-status source.
RETIRED_FIELD_HUB_TEXT = HUB_TEXT.replace("type: hub\n", "type: hub\ncheck_status: checked\n")
RETIRED_FIELD_HUB_TEXT_UNCHECKED = HUB_TEXT.replace(
    "type: hub\n", "type: hub\ncheck_status: unchecked\n"
)


def workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas", "config")
    init_git(tmp_path, "hub-candidates@example.invalid", "Hub Candidates")
    return tmp_path


def write_hub(vault: Path, rel: str = "hubs/framing.md", text: str = HUB_TEXT) -> Path:
    path = vault / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def observe_as(vault: Path, rel: str, status: str, concept_type: str = "hub") -> None:
    """Install a database verdict through the shipped observe-then-judge route."""
    state.record_observed_file_edit(
        vault,
        output_id=rel,
        concept_type=concept_type,
        output_sha256=sha256_file(vault / rel),
    )
    state.set_concept_verdict(vault, rel, status)


def snapshot(vault: Path, rel: str) -> dict[str, Any]:
    """Every surface a Candidates write moves: file bytes, staging, journal, verdict."""
    return {
        "text": (vault / rel).read_text(encoding="utf-8"),
        "staged": (vault / ".memoria/staging" / rel).exists(),
        "journal_head": state.journal_head(vault),
        "journal_export": sorted(
            (path.name, path.read_bytes()) for path in (vault / ".memoria/journal").glob("*.jsonl")
        ),
        "verdict": state.concept_check_status(vault, rel),
        "output": state.output_record(vault, rel),
    }


def body_of(path: Path) -> str:
    return split_frontmatter(path.read_text(encoding="utf-8"))[1]


def test_candidate_entry_neutralizes_reason_and_carries_run_attribution() -> None:
    entry = candidate_entry("digests/x.md", "reason with `ticks`", "run-1")

    assert entry == "- [[digests/x.md]] — reason with &#96;ticks&#96; %%run=run-1%%"


def test_candidate_entry_defuses_markup_smuggled_through_the_reason() -> None:
    entry = candidate_entry(
        "digests/x.md", "see <img src=x> and [click](https://evil.example)", "run-1"
    )

    assert "<img" not in entry
    assert "](https://evil.example)" not in entry
    assert entry.startswith("- [[digests/x.md]] — ")
    assert entry.endswith(" %%run=run-1%%")


def test_render_and_split_roundtrip() -> None:
    section = render_candidates_section("run-1", ["- [[digests/x.md]] — r %%run=run-1%%"])
    body = "# Hub\n\nCurated.\n" + section

    curated, found = split_candidates_section(body)

    assert curated == "# Hub\n\nCurated.\n"
    assert found == section
    assert section == (
        "## Candidates\n"
        "%%candidates: run=run-1%%\n"
        "- [[digests/x.md]] — r %%run=run-1%%\n"
        "%%end-candidates%%\n"
    )


def test_render_with_no_entries_is_still_a_delimited_section() -> None:
    section = render_candidates_section("run-1", [])

    assert section == "## Candidates\n%%candidates: run=run-1%%\n%%end-candidates%%\n"
    assert split_candidates_section("# Hub\n" + section) == ("# Hub\n", section)


def test_split_without_section_returns_body_unchanged() -> None:
    body = "# Hub\n\nCurated.\n"
    assert split_candidates_section(body) == (body, "")


def test_split_of_a_section_only_body_returns_empty_curated_part() -> None:
    section = render_candidates_section("run-1", [])

    assert split_candidates_section(section) == ("", section)


def test_split_keeps_an_unterminated_section_as_curated_text() -> None:
    """Without the end delimiter the region is not the machine's to replace."""
    body = "# Hub\n## Candidates\n%%candidates: run=run-1%%\n- [[digests/x.md]] — r\n"

    assert split_candidates_section(body) == (body, "")


def test_split_takes_the_terminal_section_when_the_body_quotes_an_opener() -> None:
    """The section is the file's terminal region, not its first opener."""
    quoted = "# Hub\n\n## Candidates\n%%candidates: run=quoted%%\n(prose, not a block)\n\n"
    section = render_candidates_section("run-1", ["- [[digests/x.md]] — r %%run=run-1%%"])

    assert split_candidates_section(quoted + section) == (quoted, section)


def test_write_replaces_wholesale_and_body_survives_100_regenerations(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    hub = write_hub(vault)

    call_with_context(
        write_hub_candidates,
        vault,
        "hubs/framing.md",
        [candidate_entry("digests/a.md", "first", "run-a")],
        run_id="run-a",
    )
    assert "%%candidates: run=run-a%%" in hub.read_text(encoding="utf-8")

    for round_number in range(100):
        call_with_context(
            write_hub_candidates,
            vault,
            "hubs/framing.md",
            [candidate_entry("digests/b.md", f"round {round_number}", "run-b")],
            run_id="run-b",
        )

    # Asserted against the fixture's own bytes, never against what the splitter
    # under test decides the curated region is.
    assert body_of(hub) == CURATED_BODY + (
        "## Candidates\n"
        "%%candidates: run=run-b%%\n"
        "- [[digests/b.md]] — round 99 %%run=run-b%%\n"
        "%%end-candidates%%\n"
    )
    assert state.concept_check_status(vault, "hubs/framing.md") == "unchecked"


def test_write_stamps_the_delimiter_with_the_context_run_not_the_entry_run(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    hub = write_hub(vault)

    call_with_context(
        write_hub_candidates,
        vault,
        "hubs/framing.md",
        [candidate_entry("digests/a.md", "r", "entry-run")],
        run_id="context-run",
    )

    assert body_of(hub) == CURATED_BODY + (
        "## Candidates\n"
        "%%candidates: run=context-run%%\n"
        "- [[digests/a.md]] — r %%run=entry-run%%\n"
        "%%end-candidates%%\n"
    )


def test_write_with_no_entries_leaves_an_empty_section_that_regenerates(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    hub = write_hub(vault)

    for entries, run in (
        ([candidate_entry("digests/a.md", "r", "run-a")], "run-a"),
        ([], "run-b"),
        ([candidate_entry("digests/c.md", "r", "run-c")], "run-c"),
    ):
        call_with_context(write_hub_candidates, vault, "hubs/framing.md", entries, run_id=run)

    assert body_of(hub) == CURATED_BODY + (
        "## Candidates\n"
        "%%candidates: run=run-c%%\n"
        "- [[digests/c.md]] — r %%run=run-c%%\n"
        "%%end-candidates%%\n"
    )


def test_write_normalizes_a_curated_body_missing_its_final_newline_exactly_once(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    hub = write_hub(vault, text=HUB_TEXT.rstrip("\n"))

    for run in ("run-a", "run-b"):
        call_with_context(
            write_hub_candidates,
            vault,
            "hubs/framing.md",
            [candidate_entry("digests/a.md", "r", run)],
            run_id=run,
        )

    assert body_of(hub) == "# Framing\n\nHuman text.\n" + (
        "## Candidates\n"
        "%%candidates: run=run-b%%\n"
        "- [[digests/a.md]] — r %%run=run-b%%\n"
        "%%end-candidates%%\n"
    )


def test_write_on_a_hub_with_no_curated_body_writes_only_the_section(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    hub = write_hub(vault, text=HUB_TEXT[: -len(CURATED_BODY)])

    for run in ("run-a", "run-b"):
        call_with_context(
            write_hub_candidates,
            vault,
            "hubs/framing.md",
            [candidate_entry("digests/a.md", "r", run)],
            run_id=run,
        )

    assert body_of(hub) == (
        "## Candidates\n"
        "%%candidates: run=run-b%%\n"
        "- [[digests/a.md]] — r %%run=run-b%%\n"
        "%%end-candidates%%\n"
    )


def test_write_on_registered_unchecked_hub_stays_unchecked_and_clears_staging(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    hub = write_hub(vault)
    observe_as(vault, "hubs/framing.md", "unchecked")
    before = state.journal_head(vault)

    event = call_with_context(
        write_hub_candidates,
        vault,
        "hubs/framing.md",
        [candidate_entry("digests/a.md", "r", "run-a")],
        run_id="run-a",
        inputs=["digests/a.md"],
    )

    assert event["event"] == "derived"
    assert event["inputs"] == [{"id": "digests/a.md"}]
    assert state.concept_check_status(vault, "hubs/framing.md") == "unchecked"
    assert state.journal_head(vault) != before
    assert not (vault / ".memoria/staging/hubs/framing.md").exists()
    assert body_of(hub).startswith(CURATED_BODY)


def test_write_on_checked_hub_stays_checked_and_journal_backed(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    hub = write_hub(vault)
    observe_as(vault, "hubs/framing.md", "checked")
    before = state.journal_head(vault)

    event = call_with_context(
        write_hub_candidates,
        vault,
        "hubs/framing.md",
        [candidate_entry("digests/a.md", "r", "run-a")],
        run_id="run-a",
    )

    assert state.concept_check_status(vault, "hubs/framing.md") == "checked"
    assert event["event"] == "check-fired"
    assert event["check"] == "memoria-runtime"
    assert state.journal_head(vault) != before
    assert body_of(hub) == CURATED_BODY + (
        "## Candidates\n"
        "%%candidates: run=run-a%%\n"
        "- [[digests/a.md]] — r %%run=run-a%%\n"
        "%%end-candidates%%\n"
    )


def test_write_forwards_promotion_checks_to_the_checked_writer(tmp_path: Path) -> None:
    """`checks` reaches the writer's roster gate; only "memoria-runtime" is supported."""
    vault = workspace(tmp_path)
    write_hub(vault)
    observe_as(vault, "hubs/framing.md", "checked")
    before = snapshot(vault, "hubs/framing.md")

    with pytest.raises(ValueError, match="unsupported promotion checks: hub-candidates"):
        call_with_context(
            write_hub_candidates,
            vault,
            "hubs/framing.md",
            [candidate_entry("digests/a.md", "r", "run-a")],
            run_id="run-a",
            checks=["hub-candidates"],
        )

    assert snapshot(vault, "hubs/framing.md") == before


def test_write_refuses_quarantined_hub_without_writing(tmp_path: Path) -> None:
    """Staging a quarantined hub would silently reset its verdict to unchecked."""
    vault = workspace(tmp_path)
    write_hub(vault)
    observe_as(vault, "hubs/framing.md", "quarantined")
    before = snapshot(vault, "hubs/framing.md")

    with pytest.raises(ValueError, match="quarantined"):
        call_with_context(
            write_hub_candidates,
            vault,
            "hubs/framing.md",
            [candidate_entry("digests/a.md", "r", "run-a")],
            run_id="run-a",
        )

    assert snapshot(vault, "hubs/framing.md") == before


def test_write_refuses_non_hub_target_without_writing(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    note = vault / "notes/claim.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text(
        f"---\ntype: note\nid: {HUB_ID}\ntitle: Claim\ntags: []\nlinks: {{}}\n---\nBody.\n",
        encoding="utf-8",
    )
    before = snapshot(vault, "notes/claim.md")

    with pytest.raises(ValueError, match="not a hub"):
        call_with_context(write_hub_candidates, vault, "notes/claim.md", [], run_id="run-x")

    assert snapshot(vault, "notes/claim.md") == before


def test_write_refuses_retired_frontmatter_field_on_unchecked_hub_without_writing(
    tmp_path: Path,
) -> None:
    """A retired field is invalid input: the staging path must not normalize it away."""
    vault = workspace(tmp_path)
    write_hub(vault, text=RETIRED_FIELD_HUB_TEXT)
    observe_as(vault, "hubs/framing.md", "unchecked")
    before = snapshot(vault, "hubs/framing.md")
    assert before["verdict"] == "unchecked"

    with pytest.raises(ValueError, match="retired frontmatter field is ignored: check_status"):
        call_with_context(
            write_hub_candidates,
            vault,
            "hubs/framing.md",
            [candidate_entry("digests/a.md", "r", "run-a")],
            run_id="run-a",
        )

    assert snapshot(vault, "hubs/framing.md") == before
    assert "check_status: checked" in (vault / "hubs/framing.md").read_text(encoding="utf-8")


def test_write_refuses_retired_frontmatter_field_on_checked_hub_without_writing(
    tmp_path: Path,
) -> None:
    """The checked writer has its own validation boundary; it must fail closed too."""
    vault = workspace(tmp_path)
    write_hub(vault, text=RETIRED_FIELD_HUB_TEXT_UNCHECKED)
    observe_as(vault, "hubs/framing.md", "checked")
    before = snapshot(vault, "hubs/framing.md")
    assert before["verdict"] == "checked"

    with pytest.raises(ValueError, match="retired frontmatter field is ignored: check_status"):
        call_with_context(
            write_hub_candidates,
            vault,
            "hubs/framing.md",
            [candidate_entry("digests/a.md", "r", "run-a")],
            run_id="run-a",
        )

    assert snapshot(vault, "hubs/framing.md") == before
    assert "check_status: unchecked" in (vault / "hubs/framing.md").read_text(encoding="utf-8")


def test_write_accepts_a_schema_valid_hub_carrying_no_retired_field(
    tmp_path: Path,
) -> None:
    """The other direction of the fail-closed rule: valid frontmatter still writes."""
    vault = workspace(tmp_path)
    hub = write_hub(vault)
    observe_as(vault, "hubs/framing.md", "unchecked")

    call_with_context(
        write_hub_candidates,
        vault,
        "hubs/framing.md",
        [candidate_entry("digests/a.md", "r", "run-a")],
        run_id="run-a",
    )

    frontmatter, body = split_frontmatter(hub.read_text(encoding="utf-8"))
    assert frontmatter["id"] == HUB_ID
    assert frontmatter["type"] == "hub"
    assert "check_status" not in frontmatter
    assert body.endswith("%%end-candidates%%\n")
