"""Derived passage index for query substrates."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.trusted_writer import OperationContext
from memoria_vault.runtime.vaultio import parse_frontmatter, safe_read

EMBEDDING_MODEL_ID = "memoria-hash-test-v1"
VECTOR_DIM = 16


def rebuild_passage_index(vault: Path, *, context: OperationContext) -> dict[str, Any]:
    """Rebuild all derived passage and concept-edge state from checked documents."""
    return _rebuild_passage_index(vault)


def rebuild_passage_index_explicit(vault: Path, *, actor: str, machine: str) -> dict[str, Any]:
    """Rebuild derived search state outside an operation envelope."""
    if actor not in state.ACTORS:
        raise ValueError(f"index actor must be one of {sorted(state.ACTORS)}")
    if not machine.strip():
        raise ValueError("index machine must be nonblank")
    return _rebuild_passage_index(vault)


def _rebuild_passage_index(vault: Path) -> dict[str, Any]:
    rows = _passage_rows(vault)
    passage_result = state.replace_indexed_passages(vault, rows)
    edge_result = state.replace_concept_edges(vault, _concept_edges(rows))
    return {"passages": passage_result, "concept_edges": edge_result}


def refresh_stale_passages(vault: Path, *, context: OperationContext) -> dict[str, Any]:
    """Refresh changed checked documents before a query, without a daemon."""
    rows = _passage_rows(vault)
    states = state.file_index_states(vault)
    stale_paths = {
        row["path"]
        for row in rows
        if states.get(row["path"], {}).get("source_mtime_ns") != row["source_mtime_ns"]
        or states.get(row["path"], {}).get("source_sha256") != row["text_sha256"]
        or states.get(row["path"], {}).get("check_status") != row["check_status"]
    }
    if not stale_paths:
        return {"passages": {"inserted": 0, "paths": 0}, "concept_edges": {"inserted": 0}}
    stale_rows = [row for row in rows if row["path"] in stale_paths]
    return {
        "passages": state.replace_indexed_passages(vault, stale_rows, paths=stale_paths),
        "concept_edges": state.replace_concept_edges(vault, _concept_edges(rows)),
    }


def hash_embedding(text: str, *, dim: int = VECTOR_DIM) -> list[float]:
    """Deterministic test embedder: stable, local, and dependency-free."""
    digest = hashlib.sha256(text.encode()).digest()
    return [((digest[index % len(digest)] / 255.0) * 2.0) - 1.0 for index in range(dim)]


def _passage_rows(vault: Path) -> list[dict[str, Any]]:
    from memoria_vault.runtime.search_index import checked_search_documents

    documents = checked_search_documents(vault)
    seen = {str(document["path"]) for document in documents}
    documents.extend(_previously_indexed_documents(vault, seen))
    rows = []
    for document in documents:
        rows.append(_passage_row(vault, document))
    return rows


def _previously_indexed_documents(vault: Path, seen: set[str]) -> list[dict[str, Any]]:
    docs = []
    for relpath in state.file_index_states(vault):
        rel = normalize_path(relpath)
        if rel in seen or state.concept_check_status(vault, rel) != "checked":
            continue
        path = Path(vault) / rel
        if not path.is_file():
            continue
        text = safe_read(path)
        docs.append(
            {
                "path": rel,
                "text": text,
                "frontmatter": parse_frontmatter(text),
                "source": path,
            }
        )
    return docs


def _passage_row(vault: Path, document: dict[str, Any]) -> dict[str, Any]:
    path = normalize_path(str(document["path"]))
    text = str(document["text"])
    frontmatter = (
        document.get("frontmatter") if isinstance(document.get("frontmatter"), dict) else {}
    )
    text_sha256 = "sha256:" + hashlib.sha256(text.encode()).hexdigest()
    work_id = _work_id(frontmatter, path)
    return {
        "passage_id": hashlib.sha256(f"{path}\0{text_sha256}".encode()).hexdigest()[:24],
        "origin": "generated"
        if path.startswith(("fulltexts/", "graph-neighborhoods/"))
        else "file",
        "concept_id": f"catalog/sources/{work_id}" if path.startswith("fulltexts/") else path,
        "work_id": work_id,
        "path": path,
        "anchor": _anchor(text),
        "page": "p0001",
        "byte_start": 0,
        "byte_end": len(text.encode()),
        "text_sha256": text_sha256,
        "text": text,
        "check_status": _check_status(vault, path, work_id),
        "mode": str(frontmatter.get("mode") or ""),
        "question_status": str(frontmatter.get("question_status") or ""),
        "source_mtime_ns": _source_mtime_ns(document),
        "embedding_model_id": EMBEDDING_MODEL_ID,
        "vector_dim": VECTOR_DIM,
        "vector": hash_embedding(text),
    }


def _concept_edges(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # ponytail: explicit concept-edge extraction waits for curated link rows; this keeps
    # the table rebuildable without inventing edges from prose.
    return []


def _work_id(frontmatter: dict[str, Any], path: str) -> str:
    raw = str(frontmatter.get("work_id") or frontmatter.get("id") or "")
    if raw.startswith("catalog/sources/"):
        return raw.rsplit("/", 1)[-1]
    if raw:
        return raw.split("#", 1)[0].strip("/")
    if path.startswith("fulltexts/"):
        return Path(path).stem
    return ""


def _check_status(vault: Path, path: str, work_id: str) -> str:
    if path.startswith("fulltexts/") and work_id:
        source = state.catalog_source(vault, work_id)
        return str(source.get("check_status") if source else "unchecked")
    return state.concept_check_status(vault, path)


def _anchor(text: str) -> str:
    match = re.search(r"\^p\d{4,}", text)
    return match.group(0).removeprefix("^") if match else "p0001"


def _source_mtime_ns(document: dict[str, Any]) -> int:
    source = document.get("source")
    if isinstance(source, Path) and source.exists():
        return source.stat().st_mtime_ns
    path = document.get("path")
    if isinstance(path, str):
        return int(hashlib.sha256(str(document.get("text") or "").encode()).hexdigest()[:12], 16)
    return 0
