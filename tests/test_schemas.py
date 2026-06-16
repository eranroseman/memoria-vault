"""The canonical schema home (ADR-47/49/50): every consumer reads .memoria/schemas/."""

import schema


def test_all_types_load():
    types = schema.load_types()
    assert len(types) == 22
    expected = {
        "paper", "person", "organization", "venue", "dataset", "repository",
        "project", "thesis", "code-note",
        "fleeting", "source", "claim", "hub", "index",
        "candidate", "gap", "flag", "alert", "work-prompt", "pattern", "eval-task",
        "worklist-item",
    }
    assert set(types) == expected


def test_type_field_matches_filename_literal():
    types = schema.load_types()
    for name, sc in types.items():
        assert sc["required"]["type"] == f"literal:{name}"


def test_lifecycle_subsets_of_universal_chain():
    types = schema.load_types()
    for name, sc in types.items():
        sub = schema.lifecycle_for(sc)
        assert sub, f"{name} has no lifecycle enum"
        assert set(sub) <= set(schema.UNIVERSAL_LIFECYCLE), name
        # subsets preserve the chain's order (ADR-50)
        order = [schema.UNIVERSAL_LIFECYCLE.index(s) for s in sub]
        assert order == sorted(order), f"{name} lifecycle out of chain order"


def test_folder_map_covers_every_type():
    types = schema.load_types()
    folders = schema.load_folders()
    for name in types:
        home = schema.home_for(name, folders)
        assert home, f"{name} has no folder home"
        category = types[name]["category"]
        if category != "inbox":
            assert home.startswith(category), f"{name}: home {home} outside {category}"


def test_gated_flags_match_gated_prefixes():
    """A type is gated iff its home sits under a gated prefix (ADR-03/47)."""
    types = schema.load_types()
    folders = schema.load_folders()
    prefixes = tuple(schema.gated_prefixes(folders))
    for name, sc in types.items():
        home = schema.home_for(name, folders) + "/"
        assert sc.get("gated", False) == home.startswith(prefixes), name


def test_skeleton_contains_every_home():
    folders = schema.load_folders()
    skeleton = set(folders["skeleton"])
    for home in folders["homes"].values():
        assert home in skeleton, f"home {home} missing from installer skeleton"


def test_validate_frontmatter_round_trip():
    types = schema.load_types()
    claim = types["claim"]
    good = {"type": "claim", "lifecycle": "current", "title": "T",
            "maturity": "evergreen", "sources": ["@smith2024"]}
    assert schema.validate_frontmatter(good, claim) == []
    # missing required
    errs = schema.validate_frontmatter({"type": "claim"}, claim)
    assert any("lifecycle" in e for e in errs)
    # bad enum
    errs = schema.validate_frontmatter(dict(good, lifecycle="proposed"), claim)
    assert any("lifecycle" in e for e in errs)  # claims never start proposed
    # bad literal
    errs = schema.validate_frontmatter(dict(good, type="hub"), claim)
    assert any("literal" in e for e in errs)


def test_project_and_thesis_schema_contracts():
    types = schema.load_types()
    project = types["project"]
    thesis = types["thesis"]

    assert project["initial_lifecycle"] == "current"
    assert thesis["initial_lifecycle"] == "proposed"
    assert thesis["promotion_gate"] == "current"

    project_note = {
        "type": "project",
        "lifecycle": "current",
        "title": "Does X improve Y?",
        "slug": "x-improves-y",
        "scope_topics": ["mobile-health"],
        "inquiry": {"population": "patients", "outcome": "adherence"},
        "finer": {"feasible": "small corpus", "novel": "yes", "relevant": "program"},
        "output_mode": "thesis",
        "question_version": 1,
        "question_log": [],
    }
    assert schema.validate_frontmatter(project_note, project) == []

    thesis_note = {
        "type": "thesis",
        "lifecycle": "proposed",
        "title": "X improves Y.",
        "project": "[[x-improves-y]]",
        "sources": [],
    }
    assert schema.validate_frontmatter(thesis_note, thesis) == []
    assert any(
        "lifecycle" in e
        for e in schema.validate_frontmatter(dict(thesis_note, lifecycle="banana"), thesis)
    )


def test_code_note_schema_contract():
    types = schema.load_types()
    code_note = types["code-note"]

    assert code_note["initial_lifecycle"] == "proposed"
    good = {
        "type": "code-note",
        "lifecycle": "proposed",
        "title": "Figure 3 receptivity curve",
        "project": "[[slug-bug]]",
        "agent": "codex",
        "task": "Implement the plotting script.",
        "acceptance": ["Script runs from a fresh checkout."],
    }
    assert schema.validate_frontmatter(good, code_note) == []
    assert any(
        "agent" in e
        for e in schema.validate_frontmatter(dict(good, agent="terminal-bot"), code_note)
    )


def test_required_any_on_flag_cards():
    types = schema.load_types()
    flag = types["flag"]
    base = {"type": "flag", "lifecycle": "proposed", "title": "T",
            "finding": "broken citekey", "agent_recommendation": "issues-found"}
    errs = schema.validate_frontmatter(base, flag)
    assert any("at least one of" in e for e in errs)
    assert schema.validate_frontmatter(dict(base, citekey="@x"), flag) == []


def test_honesty_card_fields_on_proposals():
    """Proposal cards carry the honesty body; verification cards lead with the finding (ADR-51)."""
    types = schema.load_types()
    for proposal in ("candidate", "gap"):
        req = types[proposal]["required"]
        for field in ("action", "argument_for", "argument_against",
                      "what_tipped_it", "certainty"):
            assert field in req, f"{proposal} missing honesty field {field}"
        assert "finding" not in req  # no verdict line on proposals (D49)
    for verification in ("flag", "alert"):
        assert "finding" in types[verification]["required"]
    # work prompts: action + what happened + where to look, never a verdict
    wp = types["work-prompt"]
    assert "action" in wp["required"] and "what_happened" in wp["required"]
    assert "agent_recommendation" not in wp["required"]
    assert "agent_recommendation" not in (wp.get("optional") or {})
    assert set(wp["required_any"]) == {"target", "task_id"}


def test_calibration_loads_with_confidence_floor():
    cal = schema.load_calibration()
    floor = cal["entity_resolution"]["confidence_floor"]
    assert 0.0 < floor < 1.0


def test_gated_prefix_fallbacks_match_folders_yaml():
    """Every dependency-free fallback for the review-gated zones must stay in sync
    with the schema home (folders.yaml). The MCPs run standalone (no operations/lib
    on their path, PyYAML optional), so they each carry the tuple hardcoded;
    schema.load_gated_prefixes is the one loader for in-repo consumers."""
    import patterns_mcp
    import policy_mcp
    canonical = tuple(schema.load_folders()["gated_prefixes"])
    assert canonical == schema.load_gated_prefixes()
    assert canonical == schema.FALLBACK_GATED_PREFIXES
    assert canonical == policy_mcp.REVIEW_GATED_PREFIXES
    assert canonical == patterns_mcp.REVIEW_GATED_PREFIXES
