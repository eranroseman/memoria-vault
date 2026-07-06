from datetime import UTC, datetime
from pathlib import Path

from memoria_vault.runtime.subsystems.processing.project import structural_impact as impact
from memoria_vault.runtime.subsystems.processing.project import (
    structural_impact_graph as impact_graph,
)


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def project(vault: Path, *, scope="alpha", active="thesis", output_mode="thesis", refutation=True):
    refutation_line = "refutation_sufficiency: true\n" if refutation else ""
    write(
        vault / "projects/demo/project.md",
        "---\n"
        "type: project\n"
        "check_status: checked\n"
        "title: Demo project\n"
        "description: Demo project\n"
        "slug: demo\n"
        f"scope_topics: [{scope}]\n"
        "inquiry: {}\n"
        "finer: {}\n"
        f"output_mode: {output_mode}\n"
        "question_version: 1\n"
        "question_log: []\n"
        f"thesis: '[[notes/{active}]]'\n"
        f"{refutation_line}"
        "---\n",
    )
    write(
        vault / "notes/thesis.md",
        "---\n"
        "type: note\n"
        "check_status: checked\n"
        "title: Demo thesis\n"
        "description: Demo thesis\n"
        "status: accepted\n"
        "role: thesis\n"
        "project: '[[projects/demo/project]]'\n"
        "evidence_set: []\n"
        "---\n",
    )


def claim(vault: Path, name: str, relation: str, target: str, *, topics="alpha"):
    write(
        vault / f"notes/{name}.md",
        "---\n"
        "type: note\n"
        "check_status: checked\n"
        f"title: {name}\n"
        f"claim_text: {name}\n"
        "status: accepted\n"
        f"topics: [{topics}]\n"
        "links:\n"
        f"  {relation}: ['[[notes/{target}]]']\n"
        "---\n",
    )


def gap(vault: Path, name: str, relation: str, target: str, *, topics="alpha"):
    write(
        vault / f"notes/{name}.md",
        "---\n"
        "type: note\n"
        "check_status: checked\n"
        f"title: {name}\n"
        "description: close the gap\n"
        "status: needs_review\n"
        "gap_type: additive\n"
        f"topics: [{topics}]\n"
        "links:\n"
        f"  {relation}: ['[[notes/{target}]]']\n"
        "---\n",
    )


def seed_mature_graph(vault: Path):
    project(vault)
    claim(vault, "a", "supports", "thesis")
    claim(vault, "b", "supports", "a")
    claim(vault, "c", "contradicts", "thesis")
    claim(vault, "d", "supports", "a")
    claim(vault, "e", "contradicts", "a")


def node(payload, path):
    return next(row for row in payload["nodes"] if row["path"] == path)


def test_normalize_target_extracts_dict_wikilink_and_status():
    assert impact_graph.normalize_target(
        {"target": "[[notes/a.md#section|Claim A]]", "status": "closed"}
    ) == ("notes/a", True)
    assert impact_graph.normalize_target({"target": "[[notes/a]]", "status": "open"}) == (
        "notes/a",
        False,
    )


def test_structural_impact_materializes_mature_argument_graph(tmp_path):
    seed_mature_graph(tmp_path)

    result = impact.run(
        tmp_path,
        "projects/demo/project",
        now=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
    )
    payload = result["payload"]

    assert result["changed"] is True
    assert result["path"] == "projects/demo/project-gate-index.md"
    assert payload["argument_stage"] == "mature"
    assert payload["evidence_saturation"] == "saturated"
    assert payload["saturation_conditions"] == {
        "mature_graph": True,
        "no_high_impact_open_gaps": True,
        "refutation_sufficiency": True,
    }
    assert payload["displayed_confidence"] == "load-bearing"
    assert payload["relation_count"] == 5
    assert payload["supports_count"] == 3
    assert payload["contradicts_count"] == 2
    assert node(payload, "notes/thesis.md")["on_path"] is True
    assert node(payload, "notes/a.md")["articulation"] is True
    assert node(payload, "notes/a.md")["impact"] >= 2
    assert {row["kind"] for row in payload["gap_findings"]} == {"conflict", "fragility"}
    assert {row["kind"] for row in payload["advisories"]} == {"structural"}

    rendered = (tmp_path / result["path"]).read_text(encoding="utf-8")
    assert "<!-- memoria-structural-impact:json -->" in rendered
    assert 'computed_at: "2026-06-16T12:00:00Z"' in rendered


def test_structural_impact_preserves_index_when_values_do_not_change(tmp_path):
    seed_mature_graph(tmp_path)
    first = impact.run(
        tmp_path,
        "projects/demo/project",
        now=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
    )
    index = tmp_path / first["path"]
    original = index.read_text(encoding="utf-8")

    second = impact.run(
        tmp_path,
        "projects/demo/project",
        now=datetime(2026, 6, 16, 13, 0, tzinfo=UTC),
    )

    assert second["changed"] is False
    assert index.read_text(encoding="utf-8") == original
    assert second["payload"]["computed_at"] == "2026-06-16T12:00:00Z"


def test_structural_impact_ranks_on_path_gaps_and_prunes_off_path(tmp_path):
    seed_mature_graph(tmp_path)
    gap(tmp_path, "on-path-gap", "supports", "a")
    claim(tmp_path, "f", "supports", "on-path-gap")
    claim(tmp_path, "g", "supports", "on-path-gap")
    gap(tmp_path, "off-path-gap", "supports", "ghost")

    result = impact.run(tmp_path, "projects/demo/project")
    payload = result["payload"]

    assert payload["argument_stage"] == "mature"
    assert payload["evidence_saturation"] == "unsaturated"
    assert payload["open_high_impact_gaps"] == 1
    assert node(payload, "notes/on-path-gap.md")["on_path"] is True
    assert node(payload, "notes/on-path-gap.md")["impact"] >= 2
    assert node(payload, "notes/off-path-gap.md")["on_path"] is False
    assert node(payload, "notes/off-path-gap.md")["impact"] == 0
    assert any(
        row["kind"] == "additive" and row["path"] == "notes/on-path-gap.md"
        for row in payload["gap_findings"]
    )


def test_structural_impact_requires_refutation_sufficiency_stamp(tmp_path):
    project(tmp_path, refutation=False)
    claim(tmp_path, "a", "supports", "thesis")
    claim(tmp_path, "b", "supports", "a")
    claim(tmp_path, "c", "contradicts", "thesis")
    claim(tmp_path, "d", "supports", "a")
    claim(tmp_path, "e", "contradicts", "a")

    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert payload["argument_stage"] == "mature"
    assert payload["refutation_floor_met"] is True
    assert payload["refutation_sufficiency"] is False
    assert payload["evidence_saturation"] == "unsaturated"
    assert payload["saturation_conditions"]["refutation_sufficiency"] is False


def test_structural_impact_cold_start_when_scope_does_not_overlap(tmp_path):
    project(tmp_path, scope="beta")
    claim(tmp_path, "a", "supports", "thesis", topics="alpha")
    claim(tmp_path, "b", "supports", "a", topics="alpha")
    claim(tmp_path, "c", "contradicts", "thesis", topics="alpha")
    claim(tmp_path, "d", "supports", "a", topics="alpha")
    claim(tmp_path, "e", "contradicts", "a", topics="alpha")

    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert payload["relation_count"] == 5
    assert payload["scope_overlap_count"] == 0
    assert payload["argument_stage"] == "cold-start"
    assert payload["evidence_saturation"] == "unknown"
    assert payload["displayed_confidence"] == "below-threshold"
    assert payload["gap_findings"] == []
    assert payload["advisories"] == []


def test_structural_impact_refutation_advisory_only_above_readiness(tmp_path):
    project(tmp_path)
    claim(tmp_path, "a", "supports", "thesis")
    claim(tmp_path, "b", "supports", "a")
    claim(tmp_path, "c", "contradicts", "a")
    claim(tmp_path, "d", "supports", "a")

    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert payload["argument_stage"] == "developing"
    assert payload["advisories"] == []

    claim(tmp_path, "e", "supports", "c")
    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert payload["argument_stage"] == "mature"
    assert any(row["kind"] == "refutation" for row in payload["advisories"])


def test_survey_mode_uses_coverage_saturation(tmp_path):
    project(tmp_path, active="", output_mode="survey")
    for name, target in (
        ("a", "b"),
        ("b", "c"),
        ("c", "a"),
        ("d", "a"),
        ("e", "b"),
    ):
        claim(tmp_path, name, "supports", target)

    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert payload["mode"] == "survey"
    assert payload["argument_stage"] == "mature"
    assert payload["evidence_saturation"] == "saturated"
    assert payload["saturation_conditions"] == {
        "mature_graph": True,
        "no_open_scope_gaps": True,
    }

    gap(tmp_path, "survey-gap", "supports", "a")
    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert payload["evidence_saturation"] == "unsaturated"
    assert any(row["path"] == "notes/survey-gap.md" for row in payload["gap_findings"])
