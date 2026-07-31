"""Preregistered retrieval-fixture loader (R2 section 7)."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from memoria_vault.runtime.evidence import parse_source_span_ref
from memoria_vault.runtime.span_refs import resolve_span_ref

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "retrieval"

_REQUIRED_KEYS = frozenset({"id", "shape", "query", "gold", "metric", "registered", "frozen"})
_OPTIONAL_KEYS = frozenset({"frozen_on"})
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SHAPE1_METRIC_RE = re.compile(r"^(hit|recall)@[1-9]\d*$")
_SHAPE2_METRIC_RE = re.compile(r"^present@[12]$")


def load_retrieval_fixtures(*, spike_mode: bool = False) -> list[dict[str, Any]]:
    """Load every registered fixture; in spike mode, refuse any unfrozen row."""
    rows: list[dict[str, Any]] = []
    for path in sorted(FIXTURES_DIR.glob("*.yaml")):
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        if not isinstance(loaded, list):
            raise ValueError(f"retrieval fixture file must be a list of cases: {path.name}")
        rows.extend(validate_retrieval_fixture_rows(loaded, source=path.name))
    ids = [str(row["id"]) for row in rows]
    duplicates = sorted({case_id for case_id in ids if ids.count(case_id) > 1})
    if duplicates:
        raise ValueError(f"duplicate retrieval fixture id(s): {duplicates}")
    if spike_mode:
        unfrozen = [str(row["id"]) for row in rows if not row["frozen"]]
        if unfrozen:
            raise ValueError(
                f"spike mode refuses unfrozen retrieval fixtures (freeze first): {unfrozen}"
            )
    return rows


def validate_retrieval_fixture_rows(
    rows: list[Any], *, source: str = "<memory>"
) -> list[dict[str, Any]]:
    """Validate the registered form; return normalized rows (dates as ISO strings)."""
    validated: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"{source}: fixture case must be a mapping, got: {row!r}")
        case_id = row.get("id")
        missing = sorted(_REQUIRED_KEYS - set(row))
        unknown = sorted(set(row) - _REQUIRED_KEYS - _OPTIONAL_KEYS)
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"{source}: case <no id>: id must be a nonblank string")
        case_id = case_id.strip()
        if missing or unknown:
            raise ValueError(f"{source}: case {case_id}: missing {missing}, unknown {unknown}")
        shape = row["shape"]
        if type(shape) is not int or shape not in (1, 2):
            raise ValueError(f"{source}: {case_id}: shape must be 1 or 2, got: {shape!r}")
        query = row["query"]
        if not isinstance(query, str) or not query.strip():
            raise ValueError(f"{source}: {case_id}: query must be a nonblank string")
        query = query.strip()
        gold = row["gold"]
        if (
            not isinstance(gold, list)
            or not gold
            or not all(isinstance(item, str) and item.strip() for item in gold)
        ):
            raise ValueError(f"{source}: {case_id}: gold must be a nonempty list of refs/ids")
        metric = row["metric"]
        if not isinstance(metric, str):
            raise ValueError(f"{source}: {case_id}: metric must be a string")
        metric_re = _SHAPE1_METRIC_RE if shape == 1 else _SHAPE2_METRIC_RE
        if not metric_re.fullmatch(metric):
            raise ValueError(f"{source}: {case_id}: metric {metric!r} is invalid for shape {shape}")
        if shape == 1:
            for ref in gold:
                parse_source_span_ref(ref)
        registered = _normalize_calendar_date(row["registered"], "registered", source, case_id)
        frozen = row["frozen"]
        if not isinstance(frozen, bool):
            raise ValueError(f"{source}: {case_id}: frozen must be a bool")
        frozen_on = ""
        if "frozen_on" in row:
            frozen_on = _normalize_calendar_date(row["frozen_on"], "frozen_on", source, case_id)
        if frozen and not frozen_on:
            raise ValueError(f"{source}: {case_id}: frozen rows must record frozen_on (YYYY-MM-DD)")
        if not frozen and frozen_on:
            raise ValueError(f"{source}: {case_id}: frozen_on requires frozen: true")
        normalized: dict[str, Any] = {
            "id": case_id,
            "shape": shape,
            "query": query,
            "gold": [str(item) for item in gold],
            "metric": metric,
            "registered": registered,
            "frozen": frozen,
        }
        if frozen_on:
            normalized["frozen_on"] = frozen_on
        validated.append(normalized)
    return validated


def _normalize_calendar_date(value: object, field: str, source: str, case_id: str) -> str:
    """Return an ISO date while refusing scalar coercion and impossible dates."""
    if type(value) is date:
        return value.isoformat()
    if not isinstance(value, str) or not _DATE_RE.fullmatch(value):
        raise ValueError(f"{source}: {case_id}: {field} must be a valid ISO calendar date")
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValueError(f"{source}: {case_id}: {field} must be a valid ISO calendar date") from exc


def shape1_bm25_cases(vault: Path, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map Shape-1 gold span refs to containing-document paths for evaluate_bm25."""
    mapped: list[dict[str, Any]] = []
    for case in cases:
        if case["shape"] != 1:
            continue
        relevant = []
        for ref in case["gold"]:
            resolved = resolve_span_ref(vault, ref)
            if resolved is None:
                raise ValueError(f"{case['id']}: gold span ref does not resolve: {ref}")
            relevant.append(resolved["path"])
        mapped.append({"query": case["query"], "relevant": relevant})
    return mapped


def score_present_at_depth(payload: dict[str, Any], gold_ids: list[str]) -> bool:
    """Return whether every gold id appears in the grouped explore payload."""
    found: set[str] = set()
    _collect_ids(payload, found)
    return set(gold_ids) <= found


def _collect_ids(node: object, found: set[str]) -> None:
    if isinstance(node, dict):
        value = node.get("id")
        if isinstance(value, str):
            found.add(value)
        for child in node.values():
            _collect_ids(child, found)
    elif isinstance(node, list):
        for child in node:
            _collect_ids(child, found)
