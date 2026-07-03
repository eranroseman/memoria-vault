"""The canonical alpha.15 schema home: every consumer reads .memoria/schemas/."""

import shutil
from pathlib import Path

import yaml

from memoria_vault.runtime.subsystems.lib import schema

ALPHA15_TYPES = {
    "note",
    "work",
    "hub",
    "project",
}


def _md(path: Path, frontmatter: dict, body: str = "Body.\n") -> None:
    if "knowledge" in path.parts:
        frontmatter.setdefault("id", "01KBN6V6KX0000000000000001")
        frontmatter.setdefault("tags", [])
        frontmatter.setdefault("links", {})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n" + yaml.safe_dump(frontmatter, sort_keys=False) + "---\n" + body,
        encoding="utf-8",
    )


def _empty_workspace(root: Path) -> Path:
    for bundle in schema.bundle_roots(schema.load_folders()):
        (root / bundle).mkdir(parents=True)
        (root / bundle / "index.md").write_text("# Index\n", encoding="utf-8")
    return root


def _m0_schema_reset_fixture(root: Path) -> Path:
    _empty_workspace(root)
    _md(
        root / "knowledge/works/source-alpha.md",
        {
            "type": "work",
            "title": "Alpha digest",
            "description": "Per-source synthesis.",
            "work_id": "source-alpha",
        },
    )
    _md(
        root / "knowledge/notes/alpha-method.md",
        {
            "type": "note",
            "title": "Alpha method reduces drift",
        },
    )
    _md(
        root / "knowledge/hubs/drift.md",
        {
            "type": "hub",
            "title": "Drift",
            "description": "Topic synthesis.",
            "tag": "drift",
        },
    )
    _md(
        root / "knowledge/projects/project-alpha/project.md",
        {
            "type": "project",
            "title": "Alpha project",
            "description": "Project direction.",
        },
    )
    return root


def test_alpha15_concept_types_load():
    types = schema.load_types()
    assert set(types) == ALPHA15_TYPES


def test_frontmatter_has_no_verdict_or_standing_fields():
    types = schema.load_types()
    for name, sc in types.items():
        payload = {**(sc.get("required") or {}), **(sc.get("optional") or {})}
        assert "check_status" not in payload, name
        assert "standing" not in payload, name
        assert schema.check_status_for(sc) == [], name


def test_type_field_matches_filename_literal():
    types = schema.load_types()
    for name, sc in types.items():
        assert sc["required"]["type"] == f"literal:{name}"


def test_alpha15_portable_fields_declared():
    types = schema.load_types()
    for name, sc in types.items():
        required = sc.get("required") or {}
        optional = sc.get("optional") or {}
        assert required["title"] == "str", name
        assert required["id"] == "ulid", name
        assert required["tags"] == "list", name
        assert required["links"] == "map", name
        assert optional.get("archived") == "bool", name
        assert optional.get("x") == "map", name
    assert types["work"]["required"]["work_id"] == "str"
    assert types["hub"]["required"]["tag"] == "str"


def test_folder_map_covers_every_alpha15_type():
    types = schema.load_types()
    folders = schema.load_folders()
    for name in types:
        home = schema.home_for(name, folders)
        assert home, f"{name} has no folder home"
        assert home.startswith(types[name]["category"]), f"{name}: home {home}"


def test_skeleton_contains_every_home_and_barrier_root():
    folders = schema.load_folders()
    skeleton = set(folders["skeleton"])
    for home in folders["homes"].values():
        assert home in skeleton, f"home {home} missing from installer skeleton"
    for root in folders["bundle_roots"] + folders["machine_staging_roots"]:
        assert root in skeleton, f"root {root} missing from installer skeleton"
    assert folders["quarantine_root"] in skeleton


def test_validate_frontmatter_round_trip():
    work = schema.load_types()["work"]
    good = {
        "id": "01KBN6V6KX0000000000000001",
        "type": "work",
        "title": "T",
        "tags": [],
        "links": {},
        "work_id": "source-alpha",
    }
    assert schema.validate_frontmatter(good, work) == []
    assert any("work_id" in e for e in schema.validate_frontmatter({"type": "work"}, work))
    assert any("id" in e for e in schema.validate_frontmatter(dict(good, id="not-a-ulid"), work))


def test_note_links_are_typed_maps():
    note = schema.load_types()["note"]
    good = {
        "id": "01KBN6V6KX0000000000000001",
        "type": "note",
        "title": "T",
        "tags": [],
        "links": {"supports": ["knowledge/notes/target.md"]},
    }
    assert schema.validate_frontmatter(good, note) == []
    assert any("links" in e for e in schema.validate_frontmatter(dict(good, links=[]), note))


def test_okf_core_empty_workspace_validates(tmp_path):
    assert schema.validate_okf_core_workspace(_empty_workspace(tmp_path)) == []


def test_okf_core_requires_universal_concept_frontmatter(tmp_path):
    root = _empty_workspace(tmp_path)
    bad = root / "knowledge/notes/bad.md"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text(
        "---\ntype: note\ncheck_status: checked\ntitle: Bad\nlinks: []\n---\nBody.\n",
        encoding="utf-8",
    )

    errors = schema.validate_okf_core_workspace(root)

    assert any("id must be a ULID" in err for err in errors)
    assert any("links must be a map" in err for err in errors)


def test_memoria_workspace_rejects_malformed_concept(tmp_path):
    root = _empty_workspace(tmp_path)
    _md(
        root / "knowledge/works/bad.md",
        {"type": "work", "title": "Bad"},
    )
    errors = schema.validate_memoria_workspace(root)
    assert any("work_id" in err for err in errors)


def test_m0_schema_reset_fixture_passes(tmp_path):
    root = _m0_schema_reset_fixture(tmp_path)
    assert schema.validate_okf_core_workspace(root) == []
    assert schema.validate_memoria_workspace(root) == []


def test_round_trip_holds(tmp_path):
    root = _m0_schema_reset_fixture(tmp_path / "src")
    exported = tmp_path / "exported"
    imported = tmp_path / "imported"
    shutil.copytree(root, exported)
    shutil.copytree(exported, imported)
    for workspace in (root, exported, imported):
        assert schema.validate_okf_core_workspace(workspace) == []
        assert schema.validate_memoria_workspace(workspace) == []
    original = {
        p.relative_to(root).as_posix(): p.read_text(encoding="utf-8")
        for p in sorted(root.rglob("*.md"))
    }
    round_trip = {
        p.relative_to(imported).as_posix(): p.read_text(encoding="utf-8")
        for p in sorted(imported.rglob("*.md"))
    }
    assert round_trip == original


def test_schema_has_no_gated_prefixes_while_review_gate_keeps_fallback():
    from memoria_vault.runtime.policy import REVIEW_GATED_PREFIXES

    assert schema.gated_prefixes(schema.load_folders()) == []
    assert schema.load_gated_prefixes() == schema.FALLBACK_GATED_PREFIXES
    assert schema.FALLBACK_GATED_PREFIXES == REVIEW_GATED_PREFIXES
