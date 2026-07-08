from __future__ import annotations

from pathlib import Path

from memoria_vault.runtime import state
from tests.helpers import ROOT


def test_sqlite_schema_uses_work_id_and_event_log(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

        assert "event_log" in tables
        assert "journal_events" not in tables
        assert _columns(conn, "catalog_sources")["work_id"] == "TEXT"
        assert "source_id" not in _columns(conn, "catalog_sources")
        assert "work_id" in _columns(conn, "enrichment_runs")
        assert "event_id" in _columns(conn, "enrichment_runs")
        assert "journal_id" not in _columns(conn, "enrichment_runs")
        assert "work_id" in _columns(conn, "field_provenance")
        assert "work_id" in _columns(conn, "work_aspects")


def test_catalog_state_api_persists_work_id(tmp_path: Path) -> None:
    state.upsert_catalog_record(
        tmp_path,
        work_id="alpha-work",
        title="Alpha Work",
        item_type="paper",
        check_status="checked",
    )
    state.start_enrichment_run(
        tmp_path,
        run_id="enrich-alpha",
        work_id="alpha-work",
        required_provider_policy={"crossref": "required"},
    )

    source = state.catalog_source(tmp_path, "alpha-work")
    assert source is not None
    assert source["work_id"] == "alpha-work"
    assert source["item_type"] == "paper"

    with state.connect(tmp_path) as conn:
        assert conn.execute("SELECT work_id FROM catalog_sources").fetchone()[0] == "alpha-work"
        assert conn.execute("SELECT work_id FROM enrichment_runs").fetchone()[0] == "alpha-work"


def test_old_identifier_tokens_do_not_remain_in_implementation() -> None:
    old_tokens = ("source" + "_id", "source" + "_type", "journal" + "_events", "journal" + "_id")
    roots = [ROOT / "src", ROOT / "scripts"]
    offenders = []
    for root in roots:
        for path in _text_files(root):
            text = path.read_text(encoding="utf-8")
            for token in old_tokens:
                if token in text:
                    offenders.append(f"{path.relative_to(ROOT)}: {token}")

    assert offenders == []


def _columns(conn: object, table: str) -> dict[str, str]:
    return {row["name"]: row["type"] for row in conn.execute(f"PRAGMA table_info({table})")}


def _text_files(root: Path) -> list[Path]:
    suffixes = {".md", ".py", ".sql", ".yaml", ".yml", ".json", ".sh"}
    return [
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix in suffixes
        and "__pycache__" not in path.parts
        and ".mypy_cache" not in path.parts
    ]
