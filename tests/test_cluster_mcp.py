"""The cluster MCP reads alpha.11 Concepts and degrades cleanly."""

from __future__ import annotations

import sys
from types import SimpleNamespace

import cluster_mcp
import pytest

networkx = pytest.importorskip("networkx", reason="cluster graph path needs networkx")


def _write(path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _vault(tmp_path):
    _write(
        tmp_path / "knowledge/notes/a.md",
        "---\ntype: note\nstatus: accepted\nlinks:\n"
        "  supports: ['knowledge/notes/b.md']\n"
        "  contradicts: ['[[knowledge/notes/c.md]]']\n---\n",
    )
    _write(
        tmp_path / "knowledge/notes/b.md",
        "---\ntype: note\nlinks:\n  supports: ['[[a]]']\n---\n",
    )
    _write(tmp_path / "knowledge/notes/c.md", "---\ntype: note\n---\n")
    _write(
        tmp_path / "knowledge/hubs/h.md",
        "---\ntype: hub\nlinks:\n"
        "  members: ['knowledge/notes/a.md', 'knowledge/notes/b.md']\n---\n",
    )
    _write(
        tmp_path / "catalog/sources/x2024/source.md",
        "---\ntype: source\nlinks:\n  authors: ['catalog/entities/person-x.md']\n---\n",
    )
    _write(
        tmp_path / "catalog/entities/person-x.md",
        "---\ntype: person\nlinks:\n  sources: ['catalog/sources/x2024/source.md']\n---\n",
    )
    return tmp_path


def test_collect_edges_types_and_kinds(tmp_path):
    v = _vault(tmp_path)
    nodes, edges = cluster_mcp.collect_edges(v)
    assert {n["id"] for n in nodes} == {
        "knowledge/notes/a",
        "knowledge/notes/b",
        "knowledge/notes/c",
        "knowledge/hubs/h",
        "catalog/sources/x2024/source",
        "catalog/entities/person-x",
    }
    assert all(n["path"].endswith(".md") for n in nodes)
    kinds = {(e["type"], e["kind"]) for e in edges}
    assert ("supports", "links") in kinds
    assert ("contradicts", "links") in kinds
    assert ("authors", "links") in kinds
    assert all(e["source"] != e["target"] for e in edges)


def test_build_graph_deterministic(tmp_path):
    v = _vault(tmp_path)
    g1 = cluster_mcp.build_graph(v, seed=13)
    g2 = cluster_mcp.build_graph(v, seed=13)
    assert g1["layout"] == g2["layout"]
    assert g1["params_echo"]["seed"] == 13
    assert set(g1["communities"]) <= {n["id"] for n in g1["nodes"]}
    assert all(0 <= c <= 1 for c in g1["centrality"].values())


def test_seed_defaults_from_calibration(tmp_path):
    v = _vault(tmp_path)
    _write(v / ".memoria/schemas/calibration.yaml", "clustering:\n  seed: 99\n")
    g = cluster_mcp.build_graph(v)
    assert g["params_echo"]["seed"] == 99


def test_topics_degrade_cleanly(tmp_path):
    v = _vault(tmp_path)
    out = cluster_mcp.model_topics(v)
    assert out.get("error") in ("bertopic-not-installed", "too-few-documents")


def test_topics_use_calibrated_corpus_floor(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "bertopic", SimpleNamespace(BERTopic=object))
    monkeypatch.setitem(sys.modules, "umap", SimpleNamespace(UMAP=object))
    v = _vault(tmp_path)
    _write(
        v / ".memoria/schemas/calibration.yaml",
        "clustering:\n  hdbscan_min_cluster_size: 2\n  full_cluster_min_documents: 7\n",
    )
    for i in range(6):
        _write(v / f"knowledge/notes/source-{i}.md", f"---\ntype: note\n---\nsource body {i}")

    out = cluster_mcp.model_topics(v)

    assert out["error"] == "too-few-documents"
    assert out["documents"] == 6
    assert out["required_documents"] == 7
    assert "7 non-empty notes" in out["note"]


def test_empty_vault_no_crash(tmp_path):
    g = cluster_mcp.build_graph(tmp_path, seed=1)
    assert g["nodes"] == [] and g["edges"] == []


def _canvas_vault(tmp_path):
    v = _vault(tmp_path)
    _write(
        v / "knowledge/notes/a.md",
        "---\ntype: note\nstatus: accepted\nlinks:\n"
        "  supports: ['knowledge/notes/b.md']\n"
        "  contradicts: ['knowledge/notes/c.md']\n"
        "  extends: ['knowledge/notes/d.md']\n---\n",
    )
    _write(v / "knowledge/notes/d.md", "---\ntype: note\nstatus: candidate\n---\n")
    return v


def _emit(v, **kw):
    import json

    out = cluster_mcp.emit_canvas(v, **kw)
    assert "error" not in out, out
    doc = json.loads((v / out["canvas_path"]).read_text(encoding="utf-8"))
    return out, doc


def test_emit_canvas_valid_structure(tmp_path):
    v = _canvas_vault(tmp_path)
    out, doc = _emit(v)
    assert out["canvas_path"] == "knowledge/notes/maps/note-debate.canvas"
    ids = [n["id"] for n in doc["nodes"]]
    assert len(ids) == len(set(ids))
    file_nodes = [n for n in doc["nodes"] if n["type"] == "file"]
    assert {n["id"] for n in file_nodes} == {
        "knowledge/notes/a",
        "knowledge/notes/b",
        "knowledge/notes/c",
        "knowledge/notes/d",
    }
    for node in file_nodes:
        assert (v / node["file"]).is_file()
        assert all(key in node for key in ("x", "y", "width", "height"))
    for edge in doc["edges"]:
        assert edge["fromNode"] in ids and edge["toNode"] in ids
        assert edge["fromSide"] in ("left", "right") and edge["toSide"] in ("left", "right")
    edge_ids = [edge["id"] for edge in doc["edges"]]
    assert len(edge_ids) == len(set(edge_ids))


def test_emit_canvas_color_mapping(tmp_path):
    v = _canvas_vault(tmp_path)
    _, doc = _emit(v)
    by_type = {edge["label"]: edge for edge in doc["edges"]}
    assert by_type["supports"]["color"] == "4"
    assert by_type["contradicts"]["color"] == "1"
    assert "color" not in by_type["extends"]
    by_id = {node["id"]: node for node in doc["nodes"]}
    assert by_id["knowledge/notes/a"]["color"] == "4"
    assert by_id["knowledge/notes/d"]["color"] == "3"
    assert "color" not in by_id["knowledge/notes/b"]


def test_emit_canvas_deterministic(tmp_path):
    v = _canvas_vault(tmp_path)
    _, first = _emit(v, seed=13)
    _, second = _emit(v, seed=13)
    assert first == second


def test_emit_canvas_scope_filters(tmp_path):
    v = _canvas_vault(tmp_path)
    _write(v / "knowledge/notes/sub/e.md", "---\ntype: note\n---\n")
    out, doc = _emit(v, scope="knowledge/hubs/h.md")
    assert out["canvas_path"].endswith("note-debate-h.canvas")
    ids = {node["id"] for node in doc["nodes"] if node["type"] == "file"}
    assert ids == {"knowledge/hubs/h", "knowledge/notes/a", "knowledge/notes/b"}
    _, doc2 = _emit(v, scope="knowledge/notes")
    ids2 = {node["id"] for node in doc2["nodes"] if node["type"] == "file"}
    assert "knowledge/hubs/h" not in ids2
    assert "catalog/sources/x2024/source" not in ids2


def test_emit_canvas_refuses_targets_outside_staging(tmp_path):
    v = _canvas_vault(tmp_path)
    for bad in (
        "knowledge/notes/map.canvas",
        "knowledge/hubs/map.canvas",
        "catalog/sources/map.canvas",
        "system/map.canvas",
        "../escape.canvas",
        "knowledge/notes/maps/../../hubs/x.canvas",
    ):
        out = cluster_mcp.emit_canvas(v, out=bad)
        assert out["error"] == "invalid-target", bad
        assert not (v / bad).exists()
    out = cluster_mcp.emit_canvas(v, out="knowledge/notes/maps/evil.md")
    assert out["error"] == "invalid-target"


def test_emit_canvas_empty_scope_errors(tmp_path):
    v = _canvas_vault(tmp_path)
    out = cluster_mcp.emit_canvas(v, scope="knowledge/nothing-here")
    assert out["error"] == "empty-scope"
