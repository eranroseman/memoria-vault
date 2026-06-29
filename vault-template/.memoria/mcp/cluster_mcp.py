#!/usr/bin/env python3
"""cluster_mcp.py — the clustering operation behind a gated MCP (ADR-33 / ADR-46).

Three tools over the vault's typed graph and text:

    cluster_build_graph   NetworkX over the authored `links:` edges and the given
                          `relationships` (ADR-52) -> nodes, typed edges, communities,
                          centrality, layout coordinates. JSON only.
    cluster_emit_canvas   The note-debate map (graph-visualization design, section 2):
                          the same typed graph rendered as a JSON Canvas artifact —
                          supports green / contradicts red / extends neutral, node color
                          = note status, node size = in-degree, communities as group nodes.
                          It writes only into the checked-note map staging home
                          (knowledge/notes/maps/ by default) and refuses every
                          other target; the human edits/promotes curated hubs.
    cluster_model_topics  BERTopic over note text -> topics, doc-topic map, outliers.
                          Heavy deps (bertopic -> torch) live in requirements-cluster.txt,
                          NEVER the policy-core requirements (ADR-33).

The operation decides *how to display*, never *what is canonical* (D44/D48): every
result echoes its parameters, and defaults come from .memoria/schemas/calibration.yaml
(drift-bound — recalibrate on model-version change). Deterministic discipline:
fixed seed, params echoed, no writes.

    python cluster_mcp.py --vault <path>                  # run the MCP server (needs `mcp`)
    python cluster_mcp.py --vault <path> --graph          # one-shot graph JSON to stdout
    python cluster_mcp.py --vault <path> --canvas         # one-shot claim-debate Canvas
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from memoria_vault.runtime.paths import resolve_vault

_FM_RE = re.compile(r"^---\n(.*?)\n---", re.S)
_WIKI = re.compile(r"\[\[([^\]|#]+)")

CONCEPT_FOLDERS = (
    "knowledge/notes",
    "knowledge/hubs",
    "knowledge/projects",
    "catalog/sources",
    "catalog/entities",
)


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
    except Exception:  # noqa: BLE001
        return {}


def _raw_targets(value) -> list[str]:
    """Wikilink/plain values -> raw target strings."""
    out = []
    vals = value if isinstance(value, list) else [value]
    for v in vals:
        if not isinstance(v, str) or not v:
            continue
        hits = _WIKI.findall(v)
        for h in hits or [v]:
            out.append(h.strip())
    return out


def collect_edges(vault: Path) -> tuple[list[dict], list[dict]]:
    """The typed graph: nodes from Concepts; edges from links:/relationships."""
    nodes: list[dict] = []
    edges: list[dict] = []
    seen: set[str] = set()
    records: list[tuple[str, dict]] = []

    def add_node(path: Path, frontmatter: dict) -> None:
        rel = path.relative_to(vault).as_posix()
        node_id = rel.removesuffix(".md")
        if node_id in seen:
            return
        seen.add(node_id)
        nodes.append(
            {
                "id": node_id,
                "path": rel,
                "type": frontmatter.get("type", ""),
                "folder": path.parent.relative_to(vault).as_posix(),
            }
        )
        records.append((node_id, frontmatter))

    for folder in CONCEPT_FOLDERS:
        d = vault / folder
        if not d.is_dir():
            continue
        for path in sorted(d.rglob("*.md")):
            add_node(path, _frontmatter(path))

    stem_index: dict[str, str | None] = {}
    for node in nodes:
        stem = Path(node["id"]).name
        stem_index[stem] = node["id"] if stem not in stem_index else None

    for node_id, frontmatter in records:
        for kind in ("links", "relationships"):
            conn = frontmatter.get(kind)
            if not isinstance(conn, dict):
                continue
            for edge_type, value in conn.items():
                for raw in _raw_targets(value):
                    target = _target_id(raw, stem_index)
                    if target and target != node_id:
                        edges.append(
                            {
                                "source": node_id,
                                "target": target,
                                "type": edge_type,
                                "kind": kind,
                            }
                        )
    return nodes, edges


def _target_id(raw: str, stem_index: dict[str, str | None]) -> str:
    target = raw.strip().replace("\\", "/").lstrip("./")
    target = target.removesuffix(".md")
    if "/" not in target and stem_index.get(target):
        return str(stem_index[target])
    return target


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
    layout = (
        {
            k: [round(float(x), 4), round(float(y), 4)]
            for k, (x, y) in nx.spring_layout(g, seed=seed).items()
        }
        if g.number_of_nodes()
        else {}
    )
    return {
        "nodes": nodes,
        "edges": edges,
        "communities": communities,
        "centrality": {k: round(v, 4) for k, v in centrality.items()},
        "layout": layout,
        "params_echo": {"seed": seed, "algorithm": "greedy_modularity + spring_layout"},
    }


# Canvas emission: the note-debate map.
# JSON Canvas preset colors: "1" red · "4" green; untyped/extends edges stay neutral.
EDGE_COLORS = {"supports": "4", "contradicts": "1"}
# Node color = review status.
STATUS_COLORS = {"candidate": "3", "accepted": "4", "rejected": "1", "superseded": "6"}
DEFAULT_SCOPE = "knowledge/notes"
CANVAS_HOME = "knowledge/notes/maps"


def _scope_stems(vault: Path, scope: str, nodes: list[dict], edges: list[dict]) -> set[str]:
    """Resolve a scope filter to node stems: a hub/topic note path -> the note
    plus everything it links (one hop); a folder prefix -> notes under it."""
    scope = scope.strip().strip("/")
    if scope.endswith(".md"):
        node_id = scope.removesuffix(".md")
        keep = {node_id}
        for e in edges:
            if e["source"] == node_id:
                keep.add(e["target"])
            elif e["target"] == node_id:
                keep.add(e["source"])
        return keep
    return {
        n["id"]
        for n in nodes
        if n["folder"] == scope
        or n["folder"].startswith(scope + "/")
        or n["id"].startswith(scope + "/")
    }


def emit_canvas(
    vault: Path, scope: str = DEFAULT_SCOPE, out: str = "", seed: int | None = None
) -> dict:
    """The note-debate map as a JSON Canvas artifact.

    File nodes for in-scope notes, typed edges (supports green / contradicts red /
    extends neutral), node color = status, node size = in-degree, communities
    rendered as group nodes. Deterministic for identical input (fixed seed)."""
    import networkx as nx

    cal = _calibration(vault)
    seed = seed if seed is not None else int(cal.get("seed", 42))
    nodes, edges = collect_edges(vault)
    keep = _scope_stems(vault, scope, nodes, edges)
    by_id = {n["id"]: n for n in nodes}
    # Canvas nodes must be real files; edges must join two surviving nodes.
    scoped = sorted(s for s in keep if s in by_id and (vault / by_id[s]["path"]).is_file())
    scoped_edges = sorted(
        (e for e in edges if e["source"] in scoped and e["target"] in scoped),
        key=lambda e: (e["source"], e["type"], e["target"]),
    )
    if not scoped:
        return {
            "error": "empty-scope",
            "scope": scope,
            "note": "no notes matched the hub/folder scope",
        }

    g = nx.Graph()
    g.add_nodes_from(scoped)
    g.add_edges_from((e["source"], e["target"]) for e in scoped_edges)
    layout = nx.spring_layout(g, seed=seed)
    communities = {}
    comms = sorted(
        nx.community.greedy_modularity_communities(g), key=lambda c: (-len(c), min(c))
    )  # stable across hash seeds
    for i, comm in enumerate(comms):
        for stem in comm:
            communities[stem] = i
    indeg = dict.fromkeys(scoped, 0)
    for e in scoped_edges:
        indeg[e["target"]] += 1

    canvas_nodes, canvas_edges = [], []
    pos = {
        s: (round(float(layout[s][0]) * 1600), round(float(layout[s][1]) * 1200)) for s in scoped
    }
    geom = {}
    for s in scoped:
        n = by_id[s]
        fm = _frontmatter(vault / n["path"])
        w = 360 + 40 * min(indeg[s], 6)  # node size = in-degree
        h = 96 + 12 * min(indeg[s], 6)
        x, y = pos[s][0] - w // 2, pos[s][1] - h // 2
        geom[s] = (x, y, w, h)
        node = {
            "id": s,
            "type": "file",
            "file": n["path"],
            "x": x,
            "y": y,
            "width": w,
            "height": h,
        }
        color = STATUS_COLORS.get(str(fm.get("status", "")))
        if color:
            node["color"] = color
        canvas_nodes.append(node)
    for e in scoped_edges:
        edge = {
            "id": f"e-{e['source']}--{e['type']}--{e['target']}",
            "fromNode": e["source"],
            "toNode": e["target"],
            "fromSide": "right" if pos[e["target"]][0] >= pos[e["source"]][0] else "left",
            "toSide": "left" if pos[e["target"]][0] >= pos[e["source"]][0] else "right",
            "label": e["type"],
        }
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
        groups.append(
            {
                "id": f"group-{i}",
                "type": "group",
                "x": min(xs) - pad,
                "y": min(ys) - pad,
                "width": max(xs) - min(xs) + 2 * pad,
                "height": max(ys) - min(ys) + 2 * pad,
                "label": f"community {i}",
            }
        )

    if out:
        rel = out
    elif scope.strip("/") == DEFAULT_SCOPE:
        rel = f"{CANVAS_HOME}/note-debate.canvas"
    else:
        rel = f"{CANVAS_HOME}/note-debate-{Path(scope.rstrip('/')).stem}.canvas"
    norm = str(Path(rel)).replace("\\", "/")
    # Allowlist, not denylist: a canvas may land only under CANVAS_HOME (the
    # map lane's staging), resolved against symlink tricks, and only as .canvas.
    allowed_root = (vault / CANVAS_HOME).resolve()
    dest = (vault / norm).resolve()
    try:
        dest.relative_to(allowed_root)
    except ValueError:
        return {
            "error": "invalid-target",
            "target": rel,
            "note": f"canvas writes are restricted to {CANVAS_HOME}/",
        }
    if dest.suffix != ".canvas":
        return {
            "error": "invalid-target",
            "target": rel,
            "note": "canvas artifacts must end in .canvas",
        }
    norm = f"{CANVAS_HOME}/{dest.relative_to(allowed_root)}".replace("\\", "/")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        json.dumps(
            {"nodes": groups + canvas_nodes, "edges": canvas_edges}, indent=2, sort_keys=True
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "canvas_path": norm,
        "nodes": len(canvas_nodes),
        "edges": len(canvas_edges),
        "groups": len(groups),
        "scope": scope,
        "params_echo": {"seed": seed, "algorithm": "greedy_modularity + spring_layout"},
    }


def model_topics(
    vault: Path,
    folder: str = DEFAULT_SCOPE,
    min_cluster_size: int | None = None,
    seed: int | None = None,
) -> dict:
    """BERTopic over note bodies. Heavy path — requires requirements-cluster.txt."""
    try:
        from bertopic import BERTopic  # type: ignore
        from umap import UMAP  # type: ignore
    except ImportError:
        return {
            "error": "bertopic-not-installed",
            "note": "pip install -r .memoria/mcp/requirements-cluster.txt",
        }
    cal = _calibration(vault)
    seed = seed if seed is not None else int(cal.get("seed", 42))
    mcs = min_cluster_size or int(cal.get("hdbscan_min_cluster_size", 5))
    nn = int(cal.get("umap_n_neighbors", 15))
    corpus_floor = int(cal.get("full_cluster_min_documents", 10))
    required_documents = max(mcs * 2, corpus_floor)
    docs, names = [], []
    d = vault / folder
    for p in sorted(d.rglob("*.md")) if d.is_dir() else []:
        body = _FM_RE.sub("", p.read_text(encoding="utf-8"), count=1).strip()
        if body:
            docs.append(body)
            names.append(p.relative_to(vault).as_posix().removesuffix(".md"))
    if len(docs) < required_documents:
        return {
            "error": "too-few-documents",
            "documents": len(docs),
            "required_documents": required_documents,
            "note": f"need at least {required_documents} non-empty notes under {folder}",
        }
    embedding = cal.get("embedding_model") or "all-MiniLM-L6-v2"
    topic_model = BERTopic(
        embedding_model=embedding,
        min_topic_size=mcs,
        umap_model=UMAP(n_neighbors=nn, random_state=seed),
    )
    topics, _ = topic_model.fit_transform(docs)
    info = topic_model.get_topic_info()
    return {
        "topics": [
            {"topic": int(r["Topic"]), "size": int(r["Count"]), "label": str(r["Name"])}
            for _, r in info.iterrows()
        ],
        "doc_topic_map": dict(zip(names, [int(t) for t in topics], strict=True)),
        "outliers": [n for n, t in zip(names, topics, strict=True) if t == -1],
        "params_echo": {
            "embedding_model": embedding,
            "min_cluster_size": mcs,
            "umap_n_neighbors": nn,
            "full_cluster_min_documents": corpus_floor,
            "required_documents": required_documents,
            "seed": seed,
        },
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
    def cluster_emit_canvas(scope: str = DEFAULT_SCOPE, out: str = "", seed: int = -1) -> dict:
        """The note-debate map: write the typed note graph as a JSON Canvas
        artifact (supports green / contradicts red, status-colored nodes,
        community groups). Writes only under knowledge/notes/maps/."""
        return emit_canvas(vault, scope, out, seed if seed >= 0 else None)

    @server.tool()
    def cluster_model_topics(
        folder: str = DEFAULT_SCOPE, min_cluster_size: int = 0, seed: int = -1
    ) -> dict:
        """BERTopic topics over note text: topics, doc-topic map, outliers.
        Errors cleanly if the optional cluster deps are not installed."""
        return model_topics(vault, folder, min_cluster_size or None, seed if seed >= 0 else None)

    return server


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--vault", help="vault root (or MEMORIA_VAULT_PATH)")
    ap.add_argument("--graph", action="store_true", help="one-shot graph JSON to stdout")
    ap.add_argument(
        "--canvas", action="store_true", help="one-shot: emit the note-debate Canvas artifact"
    )
    ap.add_argument(
        "--scope",
        default=DEFAULT_SCOPE,
        help="canvas scope: a hub/topic note path or a folder prefix",
    )
    ap.add_argument(
        "--out", default="", help="canvas output path relative to the vault (staging only)"
    )
    args = ap.parse_args()
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
