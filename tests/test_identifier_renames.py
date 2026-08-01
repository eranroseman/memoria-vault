from __future__ import annotations

import ast
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


def test_frontmatter_type_filters_carry_no_dead_work_literal() -> None:
    """NODES spec §4: ``"work"`` is a DB-store concept type (catalog rows); no
    markdown file carries ``type: work`` (no type yaml declares it), so any
    frontmatter type filter naming ``"work"`` is dead code.

    The comparison operand is resolved, not pattern-matched: a filter hoisted
    into a named roster (``SEARCHABLE_TYPES``) is the same dead branch as an
    inline set literal and must fail the same way. DB-row filters
    (``row.get("type")``) are untouched — ``"work"`` is live there.
    """
    modules = {
        path: ast.parse(path.read_text(encoding="utf-8"))
        for root in (ROOT / "src", ROOT / "scripts")
        for path in _text_files(root)
        if path.suffix == ".py"
    }
    rosters: dict[str, set[str]] = {}
    for tree in modules.values():
        for name, members in _module_string_rosters(tree).items():
            rosters.setdefault(name, set()).update(members)

    offenders = []
    for path, tree in sorted(modules.items()):
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            operands = [node.left, *node.comparators]
            if not any(_reads_frontmatter_type(operand) for operand in operands):
                continue
            for operand in operands:
                if _reads_frontmatter_type(operand):
                    continue
                members = (
                    rosters.get(operand.id, set())
                    if isinstance(operand, ast.Name)
                    else _string_members(operand)
                )
                if "work" in members:
                    offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")
                    break

    assert offenders == []


def _string_members(node: ast.AST) -> set[str]:
    """The literal strings a comparison operand can match."""
    if isinstance(node, ast.Constant):
        return {node.value} if isinstance(node.value, str) else set()
    if isinstance(node, ast.Set | ast.Tuple | ast.List):
        return {member for elt in node.elts for member in _string_members(elt)}
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id in {"frozenset", "set", "tuple", "list"}:
            return {member for arg in node.args for member in _string_members(arg)}
    return set()


def _module_string_rosters(tree: ast.Module) -> dict[str, set[str]]:
    """Module-level ``NAME = {...}`` string containers, by name."""
    rosters: dict[str, set[str]] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        else:
            continue
        members = _string_members(value)
        if members:
            for target in targets:
                if isinstance(target, ast.Name):
                    rosters.setdefault(target.id, set()).update(members)
    return rosters


def _reads_frontmatter_type(node: ast.AST) -> bool:
    """True for ``frontmatter.get("type")`` and its ``str(... or "")`` wrappers."""
    if isinstance(node, ast.BoolOp):
        return any(_reads_frontmatter_type(value) for value in node.values)
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if (
        isinstance(func, ast.Attribute)
        and func.attr == "get"
        and isinstance(func.value, ast.Name)
        and func.value.id in {"frontmatter", "fm"}
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "type"
    ):
        return True
    return any(_reads_frontmatter_type(arg) for arg in node.args)


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
