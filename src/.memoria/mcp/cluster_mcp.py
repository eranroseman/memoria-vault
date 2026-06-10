#!/usr/bin/env python3
"""cluster_mcp.py — the clustering engine behind a gated MCP (ADR-33 / ADR-46).

Two read-only tools over the vault's typed graph and text:

    cluster_build_graph   NetworkX over the authored `links:` edges and the given
                          `relationships` (ADR-52) -> nodes, typed edges, communities,
                          centrality, layout coordinates. JSON only — Canvas emission
                          is the Librarian's map lane (propose-class), never this engine.
    cluster_model_topics  BERTopic over note text -> topics, doc-topic map, outliers.
                          Heavy deps (bertopic -> torch) live in requirements-cluster.txt,
                          NEVER the policy-core requirements (ADR-33).

The engine decides *how to display*, never *what is canonical* (D44/D48): every
result echoes its parameters, and defaults come from .memoria/schemas/calibration.yaml
(drift-bound — recalibrate on model-version change). Deterministic discipline:
fixed seed, params echoed, no writes.

    python cluster_mcp.py --vault <path>                  # run the MCP server (needs `mcp`)
    python cluster_mcp.py --vault <path> --graph          # one-shot graph JSON to stdout
    python cluster_mcp.py --self-test                     # offline fixture check (no mcp/bertopic)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

_FM_RE = re.compile(r"^---\n(.*?)\n---", re.S)
_WIKI = re.compile(r"\[\[([^\]|#]+)")

NOTE_FOLDERS = ("notes/claims", "notes/hubs", "notes/source")
ENTITY_FOLDERS = ("catalog/papers", "catalog/people", "catalog/organizations",
                  "catalog/venues", "catalog/datasets", "catalog/repositories")


def _frontmatter(path: Path) -> dict:
    import yaml

    m = _FM_RE.match(path.read_text(encoding="utf-8"))
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def _calibration(vault: Path) -> dict:
    try:
        import yaml

        f = vault / ".memoria" / "schemas" / "calibration.yaml"
        return yaml.safe_load(f.read_text(encoding="utf-8")).get("clustering", {})
    except Exception:
        return {}


def _stem_targets(value) -> list[str]:
    """Wikilink/plain values -> note stems."""
    out = []
    vals = value if isinstance(value, list) else [value]
    for v in vals:
        if not isinstance(v, str) or not v:
            continue
        hits = _WIKI.findall(v)
        for h in hits or [v]:
            out.append(Path(h.strip()).stem)
    return out


def collect_edges(vault: Path) -> tuple[list[dict], list[dict]]:
    """The typed graph: nodes from notes+entities; edges from links:/relationships."""
    nodes: list[dict] = []
    edges: list[dict] = []
    seen: set[str] = set()

    def add_node(stem: str, ntype: str, folder: str) -> None:
        if stem not in seen:
            seen.add(stem)
            nodes.append({"id": stem, "type": ntype, "folder": folder})

    for folders, kind in ((NOTE_FOLDERS, "links"), (ENTITY_FOLDERS, "relationships")):
        for folder in folders:
            d = vault / folder
            if not d.is_dir():
                continue
            for p in sorted(d.glob("*.md")):
                fm = _frontmatter(p)
                ntype = fm.get("type", "")
                add_node(p.stem, ntype, folder)
                conn = fm.get(kind)
                if not isinstance(conn, dict):
                    continue
                for edge_type, value in conn.items():
                    for target in _stem_targets(value):
                        if target and target != p.stem:
                            edges.append({"source": p.stem, "target": target,
                                          "type": edge_type, "kind": kind})
    return nodes, edges


def build_graph(vault: Path, seed: int | None = None) -> dict:
    """nodes + typed edges + communities + centrality + layout (NetworkX)."""
    import networkx as nx

    cal = _calibration(vault)
    seed = seed if seed is not None else int(cal.get("seed", 42))
    nodes, edges = collect_edges(vault)
    g = nx.Graph()
    for n in nodes:
        g.add_node(n["id"], **n)
    for e in edges:
        g.add_edge(e["source"], e["target"], type=e["type"], kind=e["kind"])
    communities: dict[str, int] = {}
    if g.number_of_nodes():
        for i, comm in enumerate(nx.community.greedy_modularity_communities(g)):
            for node in comm:
                communities[node] = i
    centrality = nx.degree_centrality(g) if g.number_of_nodes() else {}
    layout = {k: [round(float(x), 4), round(float(y), 4)]
              for k, (x, y) in nx.spring_layout(g, seed=seed).items()} if g.number_of_nodes() else {}
    return {
        "nodes": nodes, "edges": edges,
        "communities": communities,
        "centrality": {k: round(v, 4) for k, v in centrality.items()},
        "layout": layout,
        "params_echo": {"seed": seed, "algorithm": "greedy_modularity + spring_layout"},
    }


def model_topics(vault: Path, folder: str = "notes/source",
                 min_cluster_size: int | None = None, seed: int | None = None) -> dict:
    """BERTopic over note bodies. Heavy path — requires requirements-cluster.txt."""
    try:
        from bertopic import BERTopic  # type: ignore
        from umap import UMAP  # type: ignore
    except ImportError:
        return {"error": "bertopic-not-installed",
                "note": "pip install -r .memoria/mcp/requirements-cluster.txt"}
    cal = _calibration(vault)
    seed = seed if seed is not None else int(cal.get("seed", 42))
    mcs = min_cluster_size or int(cal.get("hdbscan_min_cluster_size", 5))
    nn = int(cal.get("umap_n_neighbors", 15))
    docs, names = [], []
    d = vault / folder
    for p in sorted(d.glob("*.md")) if d.is_dir() else []:
        body = _FM_RE.sub("", p.read_text(encoding="utf-8"), count=1).strip()
        if body:
            docs.append(body)
            names.append(p.stem)
    if len(docs) < max(mcs * 2, 10):
        return {"error": "too-few-documents", "documents": len(docs),
                "note": f"need at least {max(mcs * 2, 10)} non-empty notes under {folder}"}
    embedding = cal.get("embedding_model") or "all-MiniLM-L6-v2"
    topic_model = BERTopic(embedding_model=embedding, min_topic_size=mcs,
                           umap_model=UMAP(n_neighbors=nn, random_state=seed))
    topics, _ = topic_model.fit_transform(docs)
    info = topic_model.get_topic_info()
    return {
        "topics": [{"topic": int(r["Topic"]), "size": int(r["Count"]),
                    "label": str(r["Name"])} for _, r in info.iterrows()],
        "doc_topic_map": dict(zip(names, [int(t) for t in topics], strict=True)),
        "outliers": [n for n, t in zip(names, topics, strict=True) if t == -1],
        "params_echo": {"embedding_model": embedding, "min_cluster_size": mcs,
                        "umap_n_neighbors": nn, "seed": seed},
    }


def build_server(vault: Path):
    from mcp.server.fastmcp import FastMCP  # type: ignore

    server = FastMCP("memoria-cluster")

    @server.tool()
    def cluster_build_graph(seed: int = -1) -> dict:
        """Typed link/relationship graph: nodes, edges, communities, centrality,
        layout. Read-only; the map lane turns this into Canvas proposals."""
        return build_graph(vault, seed if seed >= 0 else None)

    @server.tool()
    def cluster_model_topics(folder: str = "notes/source",
                             min_cluster_size: int = 0, seed: int = -1) -> dict:
        """BERTopic topics over note text: topics, doc-topic map, outliers.
        Errors cleanly if the optional cluster deps are not installed."""
        return model_topics(vault, folder, min_cluster_size or None,
                            seed if seed >= 0 else None)

    return server


def _self_test() -> int:
    import tempfile
    failures = 0

    def ck(label: str, ok: bool) -> None:
        nonlocal failures
        print(("  ok " if ok else "  FAIL ") + label)
        if not ok:
            failures += 1

    with tempfile.TemporaryDirectory() as td:
        v = Path(td)
        (v / "notes/claims").mkdir(parents=True)
        (v / "catalog/papers").mkdir(parents=True)
        (v / "notes/claims/a.md").write_text(
            "---\ntype: claim\nlinks:\n  supports: ['[[b]]']\n  contradicts: ['[[c]]']\n---\n",
            encoding="utf-8")
        (v / "notes/claims/b.md").write_text("---\ntype: claim\n---\n", encoding="utf-8")
        (v / "notes/claims/c.md").write_text("---\ntype: claim\n---\n", encoding="utf-8")
        (v / "catalog/papers/x2024.md").write_text(
            "---\ntype: paper\nrelationships:\n  cited_by: ['[[y2025]]']\n---\n",
            encoding="utf-8")
        nodes, edges = collect_edges(v)
        ck("4 nodes collected", len(nodes) == 4)
        ck("3 typed edges", len(edges) == 3)
        ck("edge kinds split", {e["kind"] for e in edges} == {"links", "relationships"})
        ck("no self-edges", all(e["source"] != e["target"] for e in edges))
        try:
            import networkx  # noqa: F401

            g = build_graph(v, seed=7)
            ck("graph has communities + layout",
               set(g["communities"]) and set(g["layout"]))
            ck("params echoed", g["params_echo"]["seed"] == 7)
            g2 = build_graph(v, seed=7)
            ck("deterministic layout", g["layout"] == g2["layout"])
        except ImportError:
            print("  ok (skipped networkx checks — not installed)")
        topics = model_topics(v)
        ck("bertopic degrades cleanly",
           topics.get("error") in ("bertopic-not-installed", "too-few-documents"))
    print("self-test:", "PASS" if failures == 0 else f"{failures} FAILURE(S)")
    return 1 if failures else 0


def resolve_vault(arg: str | None) -> Path:
    raw = arg or os.environ.get("MEMORIA_VAULT_PATH") or os.environ.get("OBSIDIAN_VAULT_PATH")
    if not raw:
        sys.exit("provide --vault or set MEMORIA_VAULT_PATH")
    v = Path(raw).expanduser()
    if not v.is_dir():
        sys.exit(f"not a directory: {v}")
    return v


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", help="vault root (or MEMORIA_VAULT_PATH)")
    ap.add_argument("--graph", action="store_true", help="one-shot graph JSON to stdout")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        sys.exit(_self_test())
    vault = resolve_vault(args.vault)
    if args.graph:
        print(json.dumps(build_graph(vault), indent=2))
        return
    build_server(vault).run()


if __name__ == "__main__":
    main()
