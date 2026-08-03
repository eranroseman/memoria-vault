"""The canonical schema home: every consumer reads .memoria/schemas/."""

import shutil
from pathlib import Path

import pytest
import yaml

from memoria_vault.runtime.vocabulary import schema
from tests.helpers import WORKSPACE_SEED

pytestmark = pytest.mark.contract

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


def _seeded_workspace(root: Path) -> Path:
    """Copy the shipped workspace seed and stand up empty bundle-root dirs.

    Bundle roots (notes/, hubs/, ...) are created by `memoria init`'s
    skeleton, not shipped inside `workspace_seed/`, so a raw copy needs them
    added for `validate_okf_core_workspace`'s bundle-root presence check.
    """
    shutil.copytree(WORKSPACE_SEED, root, dirs_exist_ok=True)
    for bundle in schema.bundle_roots(schema.load_folders()):
        (root / bundle).mkdir(parents=True, exist_ok=True)
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


def test_concept_type_registry_is_seeded_and_every_doc_type_names_a_member():
    registry = schema.load_concept_types()
    assert set(registry) == {
        "work",
        "digest",
        "note",
        "hub",
        "project",
        "capability",
        "operation",
        "skill",
        "adapter",
        "workflow",
    }
    assert all(str(role).strip() for role in registry.values())
    for name, type_schema in schema.load_types().items():
        assert type_schema.get("concept_type") in registry, name


def test_load_types_rejects_doc_type_outside_registry(tmp_path):
    shutil.copytree(schema.SCHEMAS_DIR, tmp_path / "schemas")
    rogue = tmp_path / "schemas/types/note.yaml"
    data = yaml.safe_load(rogue.read_text(encoding="utf-8"))
    data["concept_type"] = "gizmo"
    rogue.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    with pytest.raises(ValueError, match=r"not in concept-types\.yaml"):
        schema.load_types(tmp_path / "schemas")


def test_schemas_dir_without_registry_fails_closed(tmp_path):
    schemas_dir = tmp_path / "schemas"
    shutil.copytree(schema.SCHEMAS_DIR, schemas_dir)
    (schemas_dir / "concept-types.yaml").unlink()
    with pytest.raises(ValueError, match=r"missing required concept-types\.yaml"):
        schema.load_concept_types(schemas_dir)
    with pytest.raises(ValueError, match=r"missing required concept-types\.yaml"):
        schema.load_types(schemas_dir)


@pytest.mark.parametrize("concept_type", [None, ""])
def test_load_types_requires_explicit_concept_type(tmp_path, concept_type):
    schemas_dir = tmp_path / "schemas"
    shutil.copytree(schema.SCHEMAS_DIR, schemas_dir)
    type_file = schemas_dir / "types/note.yaml"
    data = yaml.safe_load(type_file.read_text(encoding="utf-8"))
    if concept_type is None:
        data.pop("concept_type")
    else:
        data["concept_type"] = concept_type
    type_file.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    with pytest.raises(
        ValueError, match=r"note\.yaml: concept_type .* is not in concept-types\.yaml"
    ):
        schema.load_types(schemas_dir)


def test_concept_type_for_resolves_each_document_type():
    assert {
        name: schema.concept_type_for(name)
        for name in {
            "code-artifact",
            "digest",
            "fulltext",
            "hub",
            "note",
            "project",
        }
    } == {
        "code-artifact": "project",
        "digest": "digest",
        "fulltext": "work",
        "hub": "hub",
        "note": "note",
        "project": "project",
    }
    with pytest.raises(ValueError, match=r"unknown document type"):
        schema.concept_type_for("gizmo")


def test_type_schemas_do_not_ship_dead_gated_keys():
    for name, type_schema in schema.load_types().items():
        assert "gated" not in type_schema, name


def test_schema_seed_does_not_ship_unused_calibration_file():
    assert not (schema.SCHEMAS_DIR / "calibration.yaml").exists()


def test_frontmatter_has_no_verdict_or_standing_fields():
    types = schema.load_types()
    for name, sc in types.items():
        payload = {**(sc.get("required") or {}), **(sc.get("optional") or {})}
        assert "check_status" not in payload, name
        assert "standing" not in payload, name
        assert sc.get("enums", {}).get("check_status", []) == [], name


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
        assert home in skeleton, f"home {home} missing from schema skeleton"
    for root in folders["bundle_roots"] + folders["machine_staging_roots"]:
        assert root in skeleton, f"root {root} missing from schema skeleton"
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


def test_schema_rejects_undeclared_fields_while_x_hatch_passes():
    note = schema.load_types()["note"]
    good = {
        "id": "01KBN6V6KX0000000000000001",
        "type": "note",
        "title": "T",
        "tags": [],
        "links": {},
        "x": {"local": "ok", "nested": {"deep": 1}},
    }
    assert schema.validate_frontmatter(good, note) == []
    errors = schema.validate_frontmatter(dict(good, surprise=True), note)
    assert any("surprise: unknown field" in error for error in errors)
    retired = schema.validate_frontmatter(dict(good, citations=[]), note)
    assert [error for error in retired if "citations" in error] == ["citations: field is retired"]


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


def test_note_links_accept_every_frontmatter_legal_relation_and_still_refuse_tension():
    # The six verbs are spelled out rather than read from `edges.LINK_RELATIONS`:
    # a fixture derived from the roster it claims to cover stays green when the
    # roster narrows. This is the independent statement the owner is held to.
    served = ("contradicts", "extends", "qualifier", "rebuttal", "supports", "warrant")
    note = schema.load_types()["note"]
    frontmatter = {
        "id": "01KBN6V6KX0000000000000001",
        "type": "note",
        "title": "T",
        "tags": [],
        "links": {
            relation: [f"notes/{relation}-one.md", f"[[notes/{relation}-two]]"]
            for relation in served
        },
    }

    assert schema.validate_frontmatter(frontmatter, note) == []
    # `tension` is machine-surfaced and PI-confirmed: an edge relation that
    # frontmatter may never author, so it fails validation like any non-relation.
    tension = schema.validate_frontmatter(
        dict(frontmatter, links={"tension": ["notes/other.md"]}), note
    )
    assert any("links.tension: unknown relation" in error for error in tension)
    # Catches a widening too: the rejection message names the whole roster.
    assert any(str(list(served)) in error for error in tension)


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

    assert schema.load_folders().get("gated_prefixes", []) == []
    assert REVIEW_GATED_PREFIXES == ("notes/", "hubs/")


def test_schema_module_carries_no_dead_validation_machinery():
    assert not hasattr(schema, "UNIVERSAL_LIFECYCLE")
    source = Path(schema.__file__).read_text(encoding="utf-8")
    assert "required_any" not in source
    assert "promotion_gate" not in source
    assert "promoted_at" not in source


def test_consequence_mark_fields_registered_on_kb_doc_types():
    types = schema.load_types()
    enum = ["grounds-lost", "warrant-lost", "qualifier-regression", "rebuttal-strengthened"]
    for name in ("note", "hub", "project", "digest"):
        type_schema = types[name]
        optional = type_schema.get("optional") or {}
        assert optional.get("stale") == "bool", name
        assert optional.get("consequence") == "enum:consequence", name
        assert type_schema.get("enums", {}).get("consequence") == enum, name
    marked = {
        "id": "01KBN6V6KX0000000000000001",
        "type": "note",
        "title": "T",
        "tags": [],
        "links": {},
        "stale": True,
        "consequence": "grounds-lost",
    }
    assert schema.validate_frontmatter(marked, types["note"]) == []
    bad = schema.validate_frontmatter(dict(marked, consequence="vibes"), types["note"])
    assert any("not in enum consequence" in error for error in bad)
    bad_stale = schema.validate_frontmatter(dict(marked, stale="yes"), types["note"])
    assert any("stale: expected bool" in error for error in bad_stale)


def _minimal_valid_fm(type_name: str, sc: dict) -> dict:
    fm: dict = {}
    for field, kind in (sc.get("required") or {}).items():
        if str(kind).startswith("literal:"):
            fm[field] = str(kind).split(":", 1)[1]
        elif kind == "ulid":
            fm[field] = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
        elif kind == "list":
            fm[field] = []
        elif kind == "links":
            fm[field] = {}
        else:
            fm[field] = "x"
    return fm


def test_okf_families_accepted_on_every_type() -> None:
    types = schema.load_types()
    okf_fm = {
        "generated": {"by": "human:pi", "at": "2026-08-02T00:00:00Z"},
        "verified": [{"by": "human:pi", "at": "2026-08-02T00:00:00Z"}],
        "sources": [{"id": "s1", "resource": "https://example.com"}],
        "usage_window": {"from": "2026-07-01", "to": "2026-07-31"},
    }
    for type_name, sc in types.items():
        for field in okf_fm:
            assert field in (sc.get("optional") or {}), f"{type_name} missing optional {field}"
        errors = schema.validate_frontmatter({**_minimal_valid_fm(type_name, sc), **okf_fm}, sc)
        assert errors == [], f"{type_name}: {errors}"


def test_timestamp_is_retired_frontmatter() -> None:
    from memoria_vault.runtime.vaultio import RETIRED_FRONTMATTER_FIELDS

    assert "timestamp" in RETIRED_FRONTMATTER_FIELDS


def test_okf_core_covers_files_outside_bundle_roots(tmp_path):
    root = _empty_workspace(tmp_path)
    (root / "orphan.md").write_text("no frontmatter here\n", encoding="utf-8")

    errors = schema.validate_okf_core_workspace(root)

    assert any("orphan.md" in err and "frontmatter" in err for err in errors)


def test_okf_core_checks_reserved_file_structure(tmp_path):
    root = _empty_workspace(tmp_path)
    (root / "index.md").write_text("---\ntype: system\n---\n# Index\n", encoding="utf-8")
    (root / "log.md").write_text("---\ntype: system\n---\n# Log\n", encoding="utf-8")

    errors = schema.validate_okf_core_workspace(root)

    assert any("index.md" in err and "okf_version" in err for err in errors)
    assert any("log.md" in err and "frontmatter" in err for err in errors)


def test_okf_core_requires_the_root_index_to_declare_the_version(tmp_path):
    root = _empty_workspace(tmp_path)
    (root / "index.md").write_text("# Index\n", encoding="utf-8")

    errors = schema.validate_okf_core_workspace(root)

    assert any(err.startswith("index.md:") and "okf_version" in err for err in errors)


def test_okf_core_rejects_a_root_index_declaring_another_version(tmp_path):
    root = _empty_workspace(tmp_path)
    (root / "index.md").write_text('---\nokf_version: "0.1"\n---\n# Index\n', encoding="utf-8")

    errors = schema.validate_okf_core_workspace(root)

    assert any(err.startswith("index.md:") and "0.2" in err for err in errors)


def test_okf_core_accepts_a_nested_bundle_index_declaring_the_version(tmp_path):
    """OKF §12: a project is a nested bundle, so its index.md may declare too."""
    root = _empty_workspace(tmp_path)
    (root / "index.md").write_text('---\nokf_version: "0.2"\n---\n# Index\n', encoding="utf-8")
    nested = root / "projects/demo/index.md"
    nested.parent.mkdir(parents=True, exist_ok=True)
    nested.write_text('---\nokf_version: "0.2"\n---\n# Demo\n', encoding="utf-8")

    assert schema.validate_okf_core_workspace(root) == []


def test_okf_core_skips_only_directories_inside_the_vault(tmp_path):
    """A vault living under a directory named like a skip target is still a
    vault: the skip list is read relative to the root, not absolutely."""
    root = _empty_workspace(tmp_path / "node_modules" / "vault")
    (root / "orphan.md").write_text("no frontmatter here\n", encoding="utf-8")

    errors = schema.validate_okf_core_workspace(root)

    assert any("orphan.md" in err for err in errors)


def test_seeded_workspace_is_okf_core_clean(tmp_path):
    root = _seeded_workspace(tmp_path)
    assert schema.validate_okf_core_workspace(root) == []
