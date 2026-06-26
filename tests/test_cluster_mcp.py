"""The cluster MCP: typed-graph metrics (networkx) + clean degradation (ADR-33)."""

import sys
from types import SimpleNamespace

import cluster_mcp
import pytest

networkx = pytest.importorskip("networkx", reason="cluster graph path needs networkx")


def _vault(tmp_path):
    (tmp_path / "notes/claims").mkdir(parents=True)
    (tmp_path / "notes/hubs").mkdir(parents=True)
    (tmp_path / "catalog/papers").mkdir(parents=True)
    (tmp_path / "notes/claims/a.md").write_text(
        "---\ntype: claim\nlinks:\n  supports: ['[[b]]']\n  contradicts: ['[[c]]']\n---\n",
        encoding="utf-8",
    )
    (tmp_path / "notes/claims/b.md").write_text(
        "---\ntype: claim\nlinks:\n  supports: ['[[a]]']\n---\n", encoding="utf-8"
    )
    (tmp_path / "notes/claims/c.md").write_text("---\ntype: claim\n---\n", encoding="utf-8")
    (tmp_path / "notes/hubs/h.md").write_text(
        "---\ntype: hub\nlinks:\n  members: ['[[a]]', '[[b]]']\n---\n", encoding="utf-8"
    )
    (tmp_path / "catalog/papers/x2024.md").write_text(
        "---\ntype: paper\nrelationships:\n  cited_by: ['[[y2025]]']\n---\n", encoding="utf-8"
    )
    return tmp_path


def test_collect_edges_types_and_kinds(tmp_path):
    v = _vault(tmp_path)
    nodes, edges = cluster_mcp.collect_edges(v)
    assert {n["id"] for n in nodes} == {"a", "b", "c", "h", "x2024"}
    kinds = {(e["type"], e["kind"]) for e in edges}
    assert ("supports", "links") in kinds
    assert ("contradicts", "links") in kinds
    assert ("cited_by", "relationships") in kinds
    assert all(e["source"] != e["target"] for e in edges)


def test_build_graph_deterministic(tmp_path):
    v = _vault(tmp_path)
    g1 = cluster_mcp.build_graph(v, seed=13)
    g2 = cluster_mcp.build_graph(v, seed=13)
    assert g1["layout"] == g2["layout"]
    assert g1["params_echo"]["seed"] == 13
    assert set(g1["communities"]) <= {n["id"] for n in g1["nodes"]} | {"y2025"}
    assert all(0 <= c <= 1 for c in g1["centrality"].values())


def test_seed_defaults_from_calibration(tmp_path):
    v = _vault(tmp_path)
    (v / ".memoria/schemas").mkdir(parents=True)
    (v / ".memoria/schemas/calibration.yaml").write_text(
        "clustering:\n  seed: 99\n", encoding="utf-8"
    )
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
    (v / ".memoria/schemas").mkdir(parents=True)
    (v / ".memoria/schemas/calibration.yaml").write_text(
        "clustering:\n  hdbscan_min_cluster_size: 2\n  full_cluster_min_documents: 7\n",
        encoding="utf-8",
    )
    (v / "notes/sources").mkdir(parents=True)
    for i in range(6):
        (v / f"notes/sources/source-{i}.md").write_text(f"source body {i}", encoding="utf-8")

    out = cluster_mcp.model_topics(v)

    assert out["error"] == "too-few-documents"
    assert out["documents"] == 6
    assert out["required_documents"] == 7
    assert "7 non-empty notes" in out["note"]


def test_empty_vault_no_crash(tmp_path):
    g = cluster_mcp.build_graph(tmp_path, seed=1)
    assert g["nodes"] == [] and g["edges"] == []


# ── cluster_emit_canvas — the claim-debate map (#345) ────────────────────────


def _canvas_vault(tmp_path):
    v = _vault(tmp_path)
    (v / "notes/claims/a.md").write_text(
        "---\ntype: claim\nmaturity: evergreen\nlinks:\n"
        "  supports: ['[[b]]']\n  contradicts: ['[[c]]']\n  extends: ['[[d]]']\n---\n",
        encoding="utf-8",
    )
    (v / "notes/claims/d.md").write_text(
        "---\ntype: claim\nmaturity: seedling\n---\n", encoding="utf-8"
    )
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
    assert out["canvas_path"] == "notes/fleeting/maps/claim-debate.canvas"
    ids = [n["id"] for n in doc["nodes"]]
    assert len(ids) == len(set(ids))  # unique node ids
    file_nodes = [n for n in doc["nodes"] if n["type"] == "file"]
    assert {n["id"] for n in file_nodes} == {"a", "b", "c", "d"}
    for n in file_nodes:  # file nodes -> real files
        assert (v / n["file"]).is_file()
        assert all(k in n for k in ("x", "y", "width", "height"))
    for e in doc["edges"]:  # edges join existing nodes
        assert e["fromNode"] in ids and e["toNode"] in ids
        assert e["fromSide"] in ("left", "right") and e["toSide"] in ("left", "right")
    edge_ids = [e["id"] for e in doc["edges"]]
    assert len(edge_ids) == len(set(edge_ids))


def test_emit_canvas_color_mapping(tmp_path):
    v = _canvas_vault(tmp_path)
    _, doc = _emit(v)
    by_type = {e["label"]: e for e in doc["edges"]}
    assert by_type["supports"]["color"] == "4"  # green
    assert by_type["contradicts"]["color"] == "1"  # red
    assert "color" not in by_type["extends"]  # neutral
    by_id = {n["id"]: n for n in doc["nodes"]}
    assert by_id["a"]["color"] == "4"  # evergreen
    assert by_id["d"]["color"] == "3"  # seedling
    assert "color" not in by_id["b"]  # no maturity declared


def test_emit_canvas_deterministic(tmp_path):
    v = _canvas_vault(tmp_path)
    _, d1 = _emit(v, seed=13)
    _, d2 = _emit(v, seed=13)
    assert d1 == d2


def test_emit_canvas_scope_filters(tmp_path):
    v = _canvas_vault(tmp_path)
    (v / "notes/claims/sub").mkdir()
    (v / "notes/claims/sub/e.md").write_text("---\ntype: claim\n---\n", encoding="utf-8")
    # hub scope: the hub plus its one-hop neighborhood, named after the hub
    out, doc = _emit(v, scope="notes/hubs/h.md")
    assert out["canvas_path"].endswith("claim-debate-h.canvas")
    stems = {n["id"] for n in doc["nodes"] if n["type"] == "file"}
    assert stems == {"h", "a", "b"}
    # folder-prefix scope excludes everything outside the prefix
    _, doc2 = _emit(v, scope="notes/claims")
    stems2 = {n["id"] for n in doc2["nodes"] if n["type"] == "file"}
    assert "h" not in stems2 and "x2024" not in stems2


def test_emit_canvas_refuses_targets_outside_staging(tmp_path):
    v = _canvas_vault(tmp_path)
    # allowlist: anything outside notes/fleeting/maps/ is refused — gated zones,
    # ungated-but-foreign homes, traversal escapes, and non-.canvas suffixes alike
    for bad in (
        "notes/claims/map.canvas",
        "notes/hubs/map.canvas",
        "catalog/papers/map.canvas",
        "system/map.canvas",
        "../escape.canvas",
        "notes/fleeting/maps/../../claims/x.canvas",
    ):
        out = cluster_mcp.emit_canvas(v, out=bad)
        assert out["error"] == "invalid-target", bad
        assert not (v / bad).exists()
    out = cluster_mcp.emit_canvas(v, out="notes/fleeting/maps/evil.md")
    assert out["error"] == "invalid-target"


def test_emit_canvas_empty_scope_errors(tmp_path):
    v = _canvas_vault(tmp_path)
    out = cluster_mcp.emit_canvas(v, scope="notes/nothing-here")
    assert out["error"] == "empty-scope"
