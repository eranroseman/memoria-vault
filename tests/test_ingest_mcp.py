"""L1 component tests for ingest_mcp (ADR-44)."""

import ingest_mcp as _m

INTAKE_LOG = _m.INTAKE_LOG
append_intake_anchor = _m.append_intake_anchor
json = _m.json


def test_ingest_pipeline_runner_is_importable():
    from operations.processing.ingest import runner

    assert callable(runner.run)


def test_ingest_mcp_pipeline_runs_tier0_fixture():
    from operations.processing.ingest import runner

    fixture = (
        "@article{x2024Test,\n  title = {A Test},\n  author = {Doe, Jane},\n"
        "  year = {2024},\n  doi = {10.1/x},\n  journal = {J Tests},\n}\n"
    )

    bundle = runner.run("x2024Test", fixture, enrich=False)

    assert bundle["lifecycle"] == "current"
    assert bundle["ingest_status"] == "tier0"
    assert bundle["holes"] == ["_proposed_classification", "brief"]
    assert bundle["frontmatter"]["title"] == "A Test"


def test_append_intake_anchor_is_idempotent(tmp_path):
    first = append_intake_anchor(tmp_path, "x2024Test", "catalog/sources/x2024Test/source.md")
    second = append_intake_anchor(tmp_path, "x2024Test", "catalog/sources/x2024Test/source.md")

    lines = (tmp_path / INTAKE_LOG).read_text().splitlines()

    assert first is True
    assert second is False
    assert len(lines) == 1
    assert json.loads(lines[0])["citekey"] == "x2024Test"


def test_citekey_sanitization_strips_traversal_chars():
    safe_ck = "../../etc/passwd".replace("/", "_").replace("..", "_").replace("\\", "_")

    assert "/" not in safe_ck
    assert ".." not in safe_ck
