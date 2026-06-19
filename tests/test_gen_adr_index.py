"""L1 component tests for gen_adr_index (ADR-44)."""

import gen_adr_index as _m
import pytest

END = _m.END
START = _m.START
_dateish = _m._dateish
_written = _m._written
build = _m.build
collect_adrs = _m.collect_adrs
parse_adr = _m.parse_adr
render_table = _m.render_table
splice = _m.splice
status_cell = _m.status_cell
validate_adr = _m.validate_adr


def _frontmatter(**overrides):
    values = {
        "topic": "decisions",
        "id": "28",
        "title": "Write gate, a plugin",
        "status": "accepted",
        "date_proposed": "2026-06-01",
        "date_resolved": "2026-06-01",
        "assumes": "[]",
        "supersedes": "[]",
        "superseded_by": "[]",
    }
    values.update(overrides)
    body = "\n".join(f"{key}: {value}" for key, value in values.items())
    return f"---\n{body}\n---\n# body"


def test_parse_adr_reads_typed_frontmatter_fields():
    adr = parse_adr(_frontmatter())

    assert adr["id"] == 28
    assert adr["title"] == "Write gate, a plugin"
    assert adr["status"] == "accepted"
    assert adr["superseded_by"] == []
    assert validate_adr(_m.Path("docs/adr/28-x.md"), adr) == []


def test_status_cell_renders_superseded_target():
    superseded = parse_adr(_frontmatter(id="27", title="Old", status="superseded", superseded_by="[28]"))

    assert superseded["superseded_by"] == [28]
    assert status_cell(superseded) == "superseded → ADR-28"


def test_validate_adr_reports_missing_keys_and_bad_lifecycle_dates():
    bad = parse_adr("---\nid: 3\ntitle: Bad\nstatus: proposed\ndate_proposed: 2026-06-01\ndate_resolved: 2026-06-02\n---\n")
    bad_errs = validate_adr(_m.Path("docs/adr/03-bad.md"), bad)
    accepted_open = parse_adr(_frontmatter(id="4", title="Bad", date_resolved=""))
    superseded_missing_by = parse_adr(
        _frontmatter(id="5", title="Bad", status="superseded", date_resolved="2026-06-02")
    )

    assert any("missing frontmatter key `assumes`" in e for e in bad_errs)
    assert any("must leave date_resolved blank" in e for e in bad_errs)
    assert any("accepted ADR must set date_resolved" in e for e in validate_adr(_m.Path("docs/adr/04-bad.md"), accepted_open))
    assert any(
        "superseded ADR must set superseded_by" in e
        for e in validate_adr(_m.Path("docs/adr/05-bad.md"), superseded_missing_by)
    )


def test_validate_adr_reports_malformed_status_id_and_dates():
    malformed = parse_adr(
        _frontmatter(id="xx", title="Bad", status="banana", date_proposed="soon", date_resolved="")
    )
    malformed_errs = validate_adr(_m.Path("docs/adr/bad.md"), malformed)

    assert malformed["id"] is None
    assert any("invalid status `banana`" in e for e in malformed_errs)
    assert any("date_proposed must be" in e for e in malformed_errs)
    assert _dateish("2026-06-14")
    assert not _dateish("2026-6-14")


def test_validate_adr_accepts_unresolved_proposals():
    proposed = parse_adr(
        _frontmatter(id="6", title="Proposal", status="proposed", date_resolved="", assumes="[1]")
    )

    assert validate_adr(_m.Path("docs/adr/06-proposed.md"), proposed) == []


def test_render_table_sorts_by_id_and_uses_zero_padded_links():
    table = render_table(
        [
            {"id": 2, "slug": "second", "title": "Second", "status": "accepted", "superseded_by": []},
            {"id": 1, "slug": "first", "title": "First", "status": "accepted", "superseded_by": []},
        ]
    )

    assert table.index("[01]") < table.index("[02]")
    assert "[01](01-first.md)" in table


def test_collect_splice_and_build_round_trip(tmp_path):
    adr_dir = tmp_path
    (adr_dir / "01-alpha.md").write_text(_frontmatter(id="1", title="Alpha"))
    (adr_dir / "02-beta.md").write_text(_frontmatter(id="2", title="Beta", status="superseded", superseded_by="[1]"))
    (adr_dir / "_template.md").write_text("---\nid: 0\ntitle: T\nstatus: x\n---\n")
    readme = adr_dir / "README.md"
    readme.write_text(f"# Decisions\n\n{START}\n\nstale\n\n{END}\n\ntail\n")

    adrs = collect_adrs(adr_dir)
    out = splice(readme.read_text(), render_table(adrs))

    assert len(adrs) == 2
    assert out.count(START) == 1 and out.count(END) == 1
    assert out.endswith("tail\n")
    assert "stale" not in out
    assert build(adr_dir, _written(readme, out)) == out


def test_collect_adrs_exits_on_nonnumeric_id(tmp_path):
    (tmp_path / "03-no-id.md").write_text(_frontmatter(id="xx", title="No ID"))

    with pytest.raises(SystemExit, match="no numeric 'id'"):
        collect_adrs(tmp_path)


def test_collect_adrs_exits_on_invalid_frontmatter(tmp_path):
    (tmp_path / "03-invalid.md").write_text(_frontmatter(id="3", title="Invalid", date_resolved=""))

    with pytest.raises(SystemExit, match="ADR frontmatter invalid"):
        collect_adrs(tmp_path)


def test_build_exits_when_readme_markers_are_missing(tmp_path):
    (tmp_path / "01-alpha.md").write_text(_frontmatter(id="1", title="Alpha"))
    readme = tmp_path / "README.md"
    readme.write_text("# Decisions\n\nno markers here\n")

    with pytest.raises(SystemExit):
        build(tmp_path, readme)
