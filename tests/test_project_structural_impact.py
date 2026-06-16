from datetime import UTC, datetime
from pathlib import Path

import structural_impact as impact


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def project(vault: Path, *, scope="alpha", active="thesis"):
    write(
        vault / "projects/demo/project.md",
        "---\n"
        "type: project\n"
        "lifecycle: current\n"
        "title: Demo project\n"
        "slug: demo\n"
        f"scope_topics: [{scope}]\n"
        "inquiry: {}\n"
        "finer: {}\n"
        "output_mode: thesis\n"
        "question_version: 1\n"
        "question_log: []\n"
        f"active_thesis: '[[{active}]]'\n"
        "---\n",
    )
    write(
        vault / "projects/demo/thesis.md",
        "---\n"
        "type: thesis\n"
        "lifecycle: provisional\n"
        "title: Demo thesis\n"
        "project: '[[demo]]'\n"
        "sources: []\n"
        "---\n",
    )


def claim(vault: Path, name: str, relation: str, target: str, *, topics="alpha"):
    write(
        vault / f"notes/claims/{name}.md",
        "---\n"
        "type: claim\n"
        "lifecycle: current\n"
        f"title: {name}\n"
        f"topics: [{topics}]\n"
        "links:\n"
        f"  {relation}: ['[[{target}]]']\n"
        "---\n",
    )


def gap(vault: Path, name: str, relation: str, target: str, *, topics="alpha"):
    write(
        vault / f"inbox/{name}.md",
        "---\n"
        "type: gap\n"
        "lifecycle: proposed\n"
        f"title: {name}\n"
        "action: close the gap\n"
        "argument_for: x\n"
        "argument_against: y\n"
        "what_tipped_it: z\n"
        "certainty: likely\n"
        f"topics: [{topics}]\n"
        "links:\n"
        f"  {relation}: ['[[{target}]]']\n"
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
    assert payload["graph_maturity"] == "mature"
    assert payload["saturation_state"] == "saturated"
    assert payload["displayed_confidence"] == "load-bearing"
    assert payload["relation_count"] == 5
    assert payload["supports_count"] == 3
    assert payload["contradicts_count"] == 2
    assert node(payload, "projects/demo/thesis.md")["on_path"] is True
    assert node(payload, "notes/claims/a.md")["articulation"] is True
    assert node(payload, "notes/claims/a.md")["impact"] >= 2

    rendered = (tmp_path / result["path"]).read_text(encoding="utf-8")
    assert "<!-- memoria-structural-impact:json -->" in rendered
    assert "computed_at: \"2026-06-16T12:00:00Z\"" in rendered


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

    assert payload["graph_maturity"] == "mature"
    assert payload["saturation_state"] == "unsaturated"
    assert payload["open_high_impact_gaps"] == 1
    assert node(payload, "inbox/on-path-gap.md")["on_path"] is True
    assert node(payload, "inbox/on-path-gap.md")["impact"] >= 2
    assert node(payload, "inbox/off-path-gap.md")["on_path"] is False
    assert node(payload, "inbox/off-path-gap.md")["impact"] == 0


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
    assert payload["graph_maturity"] == "cold-start"
    assert payload["saturation_state"] == "unknown"
    assert payload["displayed_confidence"] == "below-threshold"
