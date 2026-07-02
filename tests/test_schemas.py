"""The canonical alpha.11 schema home: every consumer reads .memoria/schemas/."""

import shutil
from pathlib import Path

import yaml

from memoria_vault.runtime.subsystems.lib import schema

ALPHA11_TYPES = {
    "source",
    "person",
    "organization",
    "venue",
    "digest",
    "note",
    "hub",
    "project",
    "adapter",
    "operation",
    "skill",
    "workflow",
}


def _md(path: Path, frontmatter: dict, body: str = "Body.\n") -> None:
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
        root / "catalog/sources/source-alpha/source.md",
        {
            "type": "source",
            "check_status": "checked",
            "title": "Alpha source",
            "description": "Fixture source.",
            "source_id": "source-alpha",
            "citekey": "alpha2026",
        },
    )
    _md(
        root / "knowledge/digests/source-alpha.md",
        {
            "type": "digest",
            "check_status": "checked",
            "title": "Alpha digest",
            "description": "Per-source synthesis.",
            "source_id": "catalog/sources/source-alpha",
            "evidence_set": ["catalog/sources/source-alpha/source#s1"],
        },
    )
    _md(
        root / "knowledge/notes/alpha-method.md",
        {
            "type": "note",
            "check_status": "checked",
            "title": "Alpha method reduces drift",
            "evidence_set": ["catalog/sources/source-alpha/source#s1"],
        },
    )
    _md(
        root / "knowledge/hubs/drift.md",
        {
            "type": "hub",
            "check_status": "checked",
            "title": "Drift",
            "description": "Topic synthesis.",
            "members": ["knowledge/digests/source-alpha", "knowledge/notes/alpha-method"],
        },
    )
    _md(
        root / "knowledge/projects/project-alpha/project.md",
        {
            "type": "project",
            "check_status": "checked",
            "title": "Alpha project",
            "description": "Project direction.",
        },
    )
    _md(
        root / "capabilities/operations/capture.md",
        {
            "type": "operation",
            "check_status": "checked",
            "title": "Capture",
            "description": "Capture a source into the catalog.",
            "operation_id": "capture",
        },
    )
    return root


def test_alpha11_concept_types_load():
    types = schema.load_types()
    assert set(types) == ALPHA11_TYPES


def test_check_status_declared_for_every_type():
    types = schema.load_types()
    for name, sc in types.items():
        assert sc.get("initial_check_status") == "unchecked", name
        assert schema.check_status_for(sc) == ["unchecked", "checked", "quarantined"], name


def test_type_field_matches_filename_literal():
    types = schema.load_types()
    for name, sc in types.items():
        assert sc["required"]["type"] == f"literal:{name}"


def test_alpha11_portable_fields_declared():
    types = schema.load_types()
    for name, sc in types.items():
        required = sc.get("required") or {}
        optional = sc.get("optional") or {}
        assert required["title"] == "str", name
        assert required["check_status"] == "enum:check_status", name
        assert optional.get("resource") == "str", name
        if name == "note":
            assert optional.get("description") == "str"
        else:
            assert required["description"] == "str", name


def test_folder_map_covers_every_alpha11_type():
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
    source = schema.load_types()["source"]
    good = {
        "type": "source",
        "check_status": "unchecked",
        "title": "T",
        "description": "D",
        "source_id": "source-alpha",
    }
    assert schema.validate_frontmatter(good, source) == []
    assert any("description" in e for e in schema.validate_frontmatter({"type": "source"}, source))
    assert any(
        "check_status" in e
        for e in schema.validate_frontmatter(dict(good, check_status="unknown"), source)
    )


def test_note_links_are_typed_maps():
    note = schema.load_types()["note"]
    good = {
        "type": "note",
        "check_status": "checked",
        "title": "T",
        "links": {"supports": ["knowledge/notes/other.md"]},
    }
    assert schema.validate_frontmatter(good, note) == []
    assert any("links" in e for e in schema.validate_frontmatter(dict(good, links=["other"]), note))


def test_okf_core_empty_workspace_validates(tmp_path):
    assert schema.validate_okf_core_workspace(_empty_workspace(tmp_path)) == []


def test_memoria_profile_rejects_malformed_concept(tmp_path):
    root = _empty_workspace(tmp_path)
    _md(
        root / "catalog/sources/bad/source.md",
        {"type": "source", "check_status": "checked", "title": "Bad"},
    )
    errors = schema.validate_memoria_profile_workspace(root)
    assert any("description" in err for err in errors)
    assert any("source_id" in err for err in errors)


def test_m0_schema_reset_fixture_passes(tmp_path):
    root = _m0_schema_reset_fixture(tmp_path)
    assert schema.validate_okf_core_workspace(root) == []
    assert schema.validate_memoria_profile_workspace(root) == []


def test_round_trip_holds(tmp_path):
    root = _m0_schema_reset_fixture(tmp_path / "src")
    exported = tmp_path / "exported"
    imported = tmp_path / "imported"
    shutil.copytree(root, exported)
    shutil.copytree(exported, imported)
    for workspace in (root, exported, imported):
        assert schema.validate_okf_core_workspace(workspace) == []
        assert schema.validate_memoria_profile_workspace(workspace) == []
    original = {
        p.relative_to(root).as_posix(): p.read_text(encoding="utf-8")
        for p in sorted(root.rglob("*.md"))
    }
    round_trip = {
        p.relative_to(imported).as_posix(): p.read_text(encoding="utf-8")
        for p in sorted(imported.rglob("*.md"))
    }
    assert round_trip == original


def test_alpha11_schema_has_no_gated_prefixes_while_legacy_policy_keeps_fallback():
    from memoria_vault.runtime.policy import REVIEW_GATED_PREFIXES

    assert schema.gated_prefixes(schema.load_folders()) == []
    assert schema.load_gated_prefixes() == schema.FALLBACK_GATED_PREFIXES
    assert schema.FALLBACK_GATED_PREFIXES == REVIEW_GATED_PREFIXES
