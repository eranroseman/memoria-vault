#!/usr/bin/env python3
"""cluster_mcp.py — the clustering engine behind a gated MCP (ADR-33 / ADR-46).

Three tools over the vault's typed graph and text:

    cluster_build_graph   NetworkX over the authored `links:` edges and the given
                          `relationships` (ADR-52) -> nodes, typed edges, communities,
                          centrality, layout coordinates. JSON only.
    cluster_emit_canvas   The claim-debate map (graph-visualization design, section 2):
                          the same typed graph rendered as a JSON Canvas artifact —
                          supports green / contradicts red / extends neutral, node color
                          = maturity, node size = in-degree, communities as group nodes.
                          Propose-class: it writes ONLY into the ungated staging home
                          (notes/fleeting/maps/ by default) and refuses every
                          review-gated prefix; the human edits/promotes the artifact.
    cluster_model_topics  BERTopic over note text -> topics, doc-topic map, outliers.
                          Heavy deps (bertopic -> torch) live in requirements-cluster.txt,
                          NEVER the policy-core requirements (ADR-33).

The engine decides *how to display*, never *what is canonical* (D44/D48): every
result echoes its parameters, and defaults come from .memoria/schemas/calibration.yaml
(drift-bound — recalibrate on model-version change). Deterministic discipline:
fixed seed, params echoed, no writes.

    python cluster_mcp.py --vault <path>                  # run the MCP server (needs `mcp`)
    python cluster_mcp.py --vault <path> --graph          # one-shot graph JSON to stdout
    python cluster_mcp.py --vault <path> --canvas         # one-shot claim-debate Canvas
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


# ── Canvas emission (the claim-debate map; graph-visualization design §2) ──────
# JSON Canvas preset colors: "1" red · "4" green; untyped/extends edges stay neutral.
EDGE_COLORS = {"supports": "4", "contradicts": "1"}
# Node color = maturity (seedling → evergreen).
MATURITY_COLORS = {"seedling": "3", "budding": "5", "evergreen": "4"}
CANVAS_HOME = "notes/fleeting/maps"          # the ONLY canvas write target (allowlist)


def _scope_stems(vault: Path, scope: str, nodes: list[dict],
                 edges: list[dict]) -> set[str]:
    """Resolve a scope filter to node stems: a hub/topic note path -> the note
    plus everything it links (one hop); a folder prefix -> notes under it."""
    scope = scope.strip().strip("/")
    if scope.endswith(".md"):
        stem = Path(scope).stem
        keep = {stem}
        for e in edges:
            if e["source"] == stem:
                keep.add(e["target"])
            elif e["target"] == stem:
                keep.add(e["source"])
        return keep
    return {n["id"] for n in nodes if n["folder"] == scope
            or n["folder"].startswith(scope + "/")}


def emit_canvas(vault: Path, scope: str = "notes/claims",
                out: str = "", seed: int | None = None) -> dict:
    """The claim-debate map as a JSON Canvas artifact (propose-class, staging-only).

    File nodes for in-scope notes, typed edges (supports green / contradicts red /
    extends neutral), node color = maturity, node size = in-degree, communities
    rendered as group nodes. Deterministic for identical input (fixed seed)."""
    import networkx as nx

    cal = _calibration(vault)
    seed = seed if seed is not None else int(cal.get("seed", 42))
    nodes, edges = collect_edges(vault)
    keep = _scope_stems(vault, scope, nodes, edges)
    by_id = {n["id"]: n for n in nodes}
    # Canvas nodes must be real files; edges must join two surviving nodes.
    scoped = sorted(s for s in keep if s in by_id
                    and (vault / by_id[s]["folder"] / f"{s}.md").is_file())
    scoped_edges = sorted((e for e in edges
                           if e["source"] in scoped and e["target"] in scoped),
                          key=lambda e: (e["source"], e["type"], e["target"]))
    if not scoped:
        return {"error": "empty-scope", "scope": scope,
                "note": "no notes matched the hub/folder scope"}

    g = nx.Graph()
    g.add_nodes_from(scoped)
    g.add_edges_from((e["source"], e["target"]) for e in scoped_edges)
    layout = nx.spring_layout(g, seed=seed)
    communities = {}
    comms = sorted(nx.community.greedy_modularity_communities(g),
                   key=lambda c: (-len(c), min(c)))   # stable across hash seeds
    for i, comm in enumerate(comms):
        for stem in comm:
            communities[stem] = i
    indeg = dict.fromkeys(scoped, 0)
    for e in scoped_edges:
        indeg[e["target"]] += 1

    canvas_nodes, canvas_edges = [], []
    pos = {s: (round(float(layout[s][0]) * 1600), round(float(layout[s][1]) * 1200))
           for s in scoped}
    geom = {}
    for s in scoped:
        n = by_id[s]
        fm = _frontmatter(vault / n["folder"] / f"{s}.md")
        w = 360 + 40 * min(indeg[s], 6)          # node size = in-degree
        h = 96 + 12 * min(indeg[s], 6)
        x, y = pos[s][0] - w // 2, pos[s][1] - h // 2
        geom[s] = (x, y, w, h)
        node = {"id": s, "type": "file", "file": f"{n['folder']}/{s}.md",
                "x": x, "y": y, "width": w, "height": h}
        color = MATURITY_COLORS.get(str(fm.get("maturity", "")))
        if color:
            node["color"] = color
        canvas_nodes.append(node)
    for e in scoped_edges:
        edge = {"id": f"e-{e['source']}--{e['type']}--{e['target']}",
                "fromNode": e["source"], "toNode": e["target"],
                "fromSide": "right" if pos[e["target"]][0] >= pos[e["source"]][0] else "left",
                "toSide": "left" if pos[e["target"]][0] >= pos[e["source"]][0] else "right",
                "label": e["type"]}
        color = EDGE_COLORS.get(e["type"])
        if color:
            edge["color"] = color
        canvas_edges.append(edge)
    # Communities as group nodes (z-order: groups first, members on top).
    groups = []
    for i in sorted(set(communities.values())):
        members = [s for s in scoped if communities[s] == i]
        if len(members) < 2:
            continue
        xs = [geom[s][0] for s in members] + [geom[s][0] + geom[s][2] for s in members]
        ys = [geom[s][1] for s in members] + [geom[s][1] + geom[s][3] for s in members]
        pad = 40
        groups.append({"id": f"group-{i}", "type": "group",
                       "x": min(xs) - pad, "y": min(ys) - pad,
                       "width": max(xs) - min(xs) + 2 * pad,
                       "height": max(ys) - min(ys) + 2 * pad,
                       "label": f"community {i}"})

    if out:
        rel = out
    elif scope.strip("/") == "notes/claims":
        rel = f"{CANVAS_HOME}/claim-debate.canvas"
    else:
        rel = f"{CANVAS_HOME}/claim-debate-{Path(scope.rstrip('/')).stem}.canvas"
    norm = str(Path(rel)).replace("\\", "/")
    # Allowlist, not denylist: a canvas may land only under CANVAS_HOME (the
    # map lane's staging), resolved against symlink tricks, and only as .canvas.
    allowed_root = (vault / CANVAS_HOME).resolve()
    dest = (vault / norm).resolve()
    try:
        dest.relative_to(allowed_root)
    except ValueError:
        return {"error": "invalid-target", "target": rel,
                "note": f"canvas writes are restricted to {CANVAS_HOME}/ (staging — ADR-03/47)"}
    if dest.suffix != ".canvas":
        return {"error": "invalid-target", "target": rel,
                "note": "canvas artifacts must end in .canvas"}
    norm = f"{CANVAS_HOME}/{dest.relative_to(allowed_root)}".replace("\\", "/")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps({"nodes": groups + canvas_nodes, "edges": canvas_edges},
                               indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "canvas_path": norm, "nodes": len(canvas_nodes), "edges": len(canvas_edges),
        "groups": len(groups), "scope": scope,
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
    def cluster_emit_canvas(scope: str = "notes/claims", out: str = "",
                            seed: int = -1) -> dict:
        """The claim-debate map: write the typed claim graph as a JSON Canvas
        artifact (supports green / contradicts red, maturity-colored nodes,
        community groups). Propose-class — staging only, gated zones refused."""
        return emit_canvas(vault, scope, out, seed if seed >= 0 else None)

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
            c = emit_canvas(v, seed=7)
            ck("canvas lands in staging", c.get("canvas_path", "").startswith(CANVAS_HOME))
            doc = json.loads((v / c["canvas_path"]).read_text(encoding="utf-8"))
            ck("canvas has nodes + edges", bool(doc["nodes"]) and bool(doc["edges"]))
            gated = emit_canvas(v, out="notes/claims/x.canvas", seed=7)
            ck("gated target refused", gated.get("error") == "gated-target")
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
    ap.add_argument("--canvas", action="store_true",
                    help="one-shot: emit the claim-debate Canvas artifact")
    ap.add_argument("--scope", default="notes/claims",
                    help="canvas scope: a hub/topic note path or a folder prefix")
    ap.add_argument("--out", default="",
                    help="canvas output path relative to the vault (staging only)")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        sys.exit(_self_test())
    vault = resolve_vault(args.vault)
    if args.graph:
        print(json.dumps(build_graph(vault), indent=2))
        return
    if args.canvas:
        result = emit_canvas(vault, args.scope, args.out)
        print(json.dumps(result, indent=2))
        sys.exit(1 if "error" in result else 0)
    build_server(vault).run()


if __name__ == "__main__":
    main()
