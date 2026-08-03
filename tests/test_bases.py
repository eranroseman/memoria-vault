"""Ring 1 seeded Obsidian Base views (2026-07-12-surface-design-notes.md)."""

import pytest
import yaml

from tests.paths import WORKSPACE_SEED

pytestmark = pytest.mark.contract

RING1_BASES = ("catalog.base", "claims.base", "inbox.base", "projects.base", "sources.base")


def _base(name: str) -> dict:
    return yaml.safe_load((WORKSPACE_SEED / name).read_text(encoding="utf-8"))


def test_package_seed_ships_exactly_the_ring1_base_views():
    assert sorted(path.name for path in WORKSPACE_SEED.rglob("*.base")) == sorted(RING1_BASES)


def test_every_view_leads_with_the_title_property():
    # id-filenames decision: stable slug filenames, views read as titles.
    for name in RING1_BASES:
        for view in _base(name)["views"]:
            assert view["order"][0] == "title", (name, view["name"])


def test_inbox_base_matches_the_design():
    base = _base("inbox.base")
    assert [view["name"] for view in base["views"]] == [
        "Needs me",
        "Drift watch",
        "Loose ends",
        "All cards",
    ]
    assert 'projection == "attention"' in base["filters"]["and"]
    assert "loudness_rank" in base["formulas"]
    assert base["views"][2]["filters"]["and"] == ['loudness == "notice"']
    assert base["views"][3]["groupBy"]["property"] == "attention_kind"


def test_claims_base_matches_the_design():
    base = _base("claims.base")
    assert [view["name"] for view in base["views"]] == [
        "By maturity",
        "Open questions",
        "Contradictions",
        "Retracted",
    ]
    assert base["formulas"]["is_orphan"] == "file.backlinks.isEmpty()"
    assert base["formulas"]["consequence_glyph"] == 'if(stale, "⚠ " + consequence, "")'
    assert base["views"][0]["order"] == [
        "title",
        "formula.consequence_glyph",
        "certainty",
        "claim_text",
    ]
    assert base["views"][1]["filters"]["and"] == ["file.backlinks.isEmpty()"]
    assert base["views"][2]["filters"]["and"] == ["!links.contradicts.isEmpty()"]


def test_catalog_sources_projects_bases_carry_the_designed_view_names():
    assert [view["name"] for view in _base("catalog.base")["views"]] == [
        "Papers",
        "People",
        "Venues",
        "Needs-enrichment",
    ]
    assert [view["name"] for view in _base("sources.base")["views"]] == [
        "Reading pipeline",
        "Discuss queue",
    ]
    assert [view["name"] for view in _base("projects.base")["views"]] == [
        "Active",
        "Saturation",
        "Gaps",
    ]
