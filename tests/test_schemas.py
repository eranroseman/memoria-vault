"""The canonical schema home: every consumer reads .memoria/schemas/."""

import shutil
from pathlib import Path

import yaml

from memoria_vault.runtime.subsystems.lib import schema

SCHEMA_TYPES = {
    "code-artifact",
    "digest",
    "fulltext",
    "note",
    "hub",
    "project",
}
CONCEPT_ROOTS = {"notes", "hubs", "projects", "digests", "fulltexts"}


def _md(path: Path, frontmatter: dict, body: str = "Body.\n") -> None:
    if CONCEPT_ROOTS & set(path.parts):
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
        root / "digests/source-alpha.md",
        {
            "type": "digest",
            "title": "Alpha digest",
            "description": "Per-source synthesis.",
            "work_id": "source-alpha",
        },
    )
    _md(
        root / "notes/alpha-method.md",
        {
            "type": "note",
            "title": "Alpha method reduces drift",
        },
    )
    _md(
        root / "hubs/drift.md",
        {
            "type": "hub",
            "title": "Drift",
            "description": "Topic synthesis.",
            "tag": "drift",
        },
    )
    _md(
        root / "projects/project-alpha/project.md",
        {
            "type": "project",
            "title": "Alpha project",
            "description": "Project direction.",
        },
    )
    return root


def test_concept_types_load():
    types = schema.load_types()
    assert set(types) == SCHEMA_TYPES


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


def test_portable_fields_declared():
    types = schema.load_types()
    for name, sc in types.items():
        required = sc.get("required") or {}
        optional = sc.get("optional") or {}
        assert required["title"] == "str", name
        assert required["id"] == (
            "str" if name in {"code-artifact", "digest", "fulltext"} else "ulid"
        ), name
        assert required["tags"] == "list", name
        assert required["links"] == "links", name
        assert optional.get("archived") == "bool", name
    assert optional.get("x") == "map", name
    assert types["digest"]["required"]["work_id"] == "str"
    assert types["fulltext"]["required"]["work_id"] == "str"
    assert types["code-artifact"]["required"]["artifact_id"] == "str"
    assert types["hub"]["required"]["tag"] == "str"


def test_folder_map_covers_every_type():
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
    digest = schema.load_types()["digest"]
    good = {
        "id": "source-alpha",
        "type": "digest",
        "title": "T",
        "tags": [],
        "links": {},
        "work_id": "source-alpha",
    }
    assert schema.validate_frontmatter(good, digest) == []
    assert any("work_id" in e for e in schema.validate_frontmatter({"type": "digest"}, digest))
    assert any("id" in e for e in schema.validate_frontmatter(dict(good, id=123), digest))


def test_schema_accepts_undeclared_meaning_fields_during_alpha16_migration():
    note = schema.load_types()["note"]
    good = {
        "id": "01KBN6V6KX0000000000000001",
        "type": "note",
        "title": "T",
        "tags": [],
        "links": {},
        "x": {"local": "ok"},
    }
    assert schema.validate_frontmatter(good, note) == []
    assert schema.validate_frontmatter(dict(good, surprise=True), note) == []


def test_note_links_are_typed_maps():
    note = schema.load_types()["note"]
    good = {
        "id": "01KBN6V6KX0000000000000001",
        "type": "note",
        "title": "T",
        "tags": [],
        "links": {"supports": ["notes/target.md"]},
    }
    assert schema.validate_frontmatter(good, note) == []
    assert any("links" in e for e in schema.validate_frontmatter(dict(good, links=[]), note))
    assert any(
        "links.related: unknown relation" in e
        for e in schema.validate_frontmatter(dict(good, links={"related": ["target"]}), note)
    )
    assert any(
        "links.supports: expected list" in e
        for e in schema.validate_frontmatter(
            dict(good, links={"supports": "notes/target.md"}), note
        )
    )
    assert any(
        "expected local Concept target" in e
        for e in schema.validate_frontmatter(
            dict(good, links={"supports": ["[[/notes/target.md]]"]}), note
        )
    )
    assert any(
        "target must not escape the workspace" in e
        for e in schema.validate_frontmatter(dict(good, links={"supports": ["../target"]}), note)
    )


def test_okf_core_empty_workspace_validates(tmp_path):
    assert schema.validate_okf_core_workspace(_empty_workspace(tmp_path)) == []


def test_okf_core_requires_universal_concept_frontmatter(tmp_path):
    root = _empty_workspace(tmp_path)
    bad = root / "notes/bad.md"
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
        root / "digests/bad.md",
        {"type": "digest", "title": "Bad"},
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
    assert REVIEW_GATED_PREFIXES == ("notes/", "hubs/")
