"""The cluster MCP: typed-graph metrics (networkx) + clean degradation (ADR-33)."""

import pytest

import cluster_mcp

networkx = pytest.importorskip("networkx", reason="cluster graph path needs networkx")


def _vault(tmp_path):
    (tmp_path / "notes/claims").mkdir(parents=True)
    (tmp_path / "notes/hubs").mkdir(parents=True)
    (tmp_path / "catalog/papers").mkdir(parents=True)
    (tmp_path / "notes/claims/a.md").write_text(
        "---\ntype: claim\nlinks:\n  supports: ['[[b]]']\n  contradicts: ['[[c]]']\n---\n",
        encoding="utf-8")
    (tmp_path / "notes/claims/b.md").write_text(
        "---\ntype: claim\nlinks:\n  supports: ['[[a]]']\n---\n", encoding="utf-8")
    (tmp_path / "notes/claims/c.md").write_text("---\ntype: claim\n---\n", encoding="utf-8")
    (tmp_path / "notes/hubs/h.md").write_text(
        "---\ntype: hub\nlinks:\n  members: ['[[a]]', '[[b]]']\n---\n", encoding="utf-8")
    (tmp_path / "catalog/papers/x2024.md").write_text(
        "---\ntype: paper\nrelationships:\n  cited_by: ['[[y2025]]']\n---\n", encoding="utf-8")
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
        "clustering:\n  seed: 99\n", encoding="utf-8")
    g = cluster_mcp.build_graph(v)
    assert g["params_echo"]["seed"] == 99


def test_topics_degrade_cleanly(tmp_path):
    v = _vault(tmp_path)
    out = cluster_mcp.model_topics(v)
    assert out.get("error") in ("bertopic-not-installed", "too-few-documents")


def test_empty_vault_no_crash(tmp_path):
    g = cluster_mcp.build_graph(tmp_path, seed=1)
    assert g["nodes"] == [] and g["edges"] == []
