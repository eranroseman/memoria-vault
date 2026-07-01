"""Memoria Inspector plugin contract."""

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OBSIDIAN = ROOT / "vault-template" / ".obsidian"
PLUGIN = OBSIDIAN / "plugins" / "memoria-inspector"
MAIN = PLUGIN / "main.js"


def write_obsidian_mock(harness: Path) -> None:
    obsidian_module = harness / "node_modules" / "obsidian"
    obsidian_module.mkdir(parents=True)
    (obsidian_module / "index.js").write_text(
        """
class Plugin {
  constructor() { this.views = []; this.commands = []; this.intervals = []; this.app = null; }
  registerView(type, factory) { this.views.push({ type, factory }); }
  addRibbonIcon() {}
  addCommand(command) { this.commands.push(command); }
  registerInterval(interval) { this.intervals.push(interval); }
}
class ItemView {
  constructor() {
    this.containerEl = { children: [null, new global.MockElement("root", {})] };
  }
}
module.exports = { Plugin, ItemView };
""",
        encoding="utf-8",
    )


def test_memoria_inspector_is_enabled_and_declared():
    manifest = json.loads((PLUGIN / "manifest.json").read_text(encoding="utf-8"))
    enabled = json.loads((OBSIDIAN / "community-plugins.json").read_text(encoding="utf-8"))

    assert manifest["id"] == "memoria-inspector"
    assert manifest["name"] == "Memoria Inspector"
    assert "memoria-inspector" in enabled


def test_memoria_inspector_reads_operational_sources_without_queue_writes():
    text = MAIN.read_text(encoding="utf-8")

    for marker in (
        "system/logs/board-state.jsonl",
        "system/logs/audit.jsonl",
        "journal/",
        "system/metrics/lint-verdict-",
        "system/metrics/lane-",
        "system/dashboards/board-state",
        "system/dashboards/audit-log",
        "spaces/maintenance#Drift watch",
        "system/dashboards/fleet-health",
        "knowledge/views/knowledge.base",
        "GRAPH_PREFIXES",
        "knowledgeGraphSummary",
        "Knowledge graph",
        "graphRefs",
        "graphEdges",
        "graphTargetPath",
        "checked Concept",
        "registerView",
        "getRightLeaf",
        "adapter.read",
        "recentIntegrityFlags",
        "Integrity flags",
        'row.event !== "check-fired"',
        'row.status !== "failed"',
        "openLinkText",
    ):
        assert marker in text

    for forbidden in (
        ".memoria/queue",
        "workerQueueSummary",
        "Worker queue",
        "enqueueOperation",
        "adapter.write(",
        ".vault.modify",
        ".vault.create",
        ".vault.delete",
        "requestUrl",
        "fetch(",
        "child_process",
        'require("fs")',
        "require('fs')",
    ):
        assert forbidden not in text


def test_memoria_inspector_renders_populated_operational_panels(tmp_path: Path):
    harness = tmp_path / "inspector-render-harness"
    write_obsidian_mock(harness)

    files = {
        "system/logs/board-state.jsonl": (
            '{"totals":{"running":1,"ready":2,"blocked":1,"review_queue":3,"retrying":0},'
            '"lanes":{"knowledge":{"ready":2,"running":1,"blocked":0}}}\n'
        ),
        "system/logs/audit.jsonl": (
            '{"timestamp":"2026-06-29T10:00:00Z","decision":"deny",'
            '"action":"direct-write","profile":"memoria-writer",'
            '"path":"knowledge/notes/nope.md","task_id":"task-1"}\n'
        ),
        "journal/test-machine.jsonl": (
            '{"event":"check-fired","status":"failed","timestamp":"2026-06-29T10:01:00Z",'
            '"check":"quote-anchor","route":"ask","target_id":"knowledge/notes/candidate.md",'
            '"reason":"quote missing"}\n'
        ),
        "system/metrics/lint-verdict-2026-06-29.md": (
            "---\n"
            "period: 2026-06-29\n"
            "verdict: PASS\n"
            "finding_count: 1\n"
            "critical_count: 0\n"
            "high_count: 0\n"
            "medium_count: 1\n"
            "low_count: 0\n"
            "---\n"
        ),
        "system/metrics/lane-knowledge-2026-06-29.md": (
            "---\n"
            "lane: knowledge\n"
            "period: 2026-06-29\n"
            "trust_score: 97\n"
            "band: pass\n"
            "samples: 4\n"
            "---\n"
        ),
        "catalog/sources/source-alpha/source.md": (
            "---\ntype: source\ncheck_status: checked\ntitle: Source Alpha\n---\n"
        ),
        "knowledge/digests/source-alpha.md": (
            "---\n"
            "type: digest\n"
            "check_status: checked\n"
            "title: Digest Alpha\n"
            "links: knowledge/notes/candidate.md\n"
            "---\n"
        ),
        "knowledge/notes/candidate.md": (
            "---\n"
            "type: note\n"
            "check_status: checked\n"
            "title: Candidate Note\n"
            "links: catalog/sources/source-alpha\n"
            "---\n"
        ),
        "knowledge/hubs/memory.md": (
            "---\ntype: hub\ncheck_status: checked\ntitle: Memory Hub\n---\n"
        ),
        "knowledge/projects/project-alpha/project.md": (
            "---\ntype: project\ncheck_status: checked\ntitle: Project Alpha\n---\n"
        ),
    }
    script = """
global.__elements = [];
global.window = { setInterval() { return 1; } };
global.MockElement = class MockElement {
  constructor(tag, opts = {}) {
    this.tag = tag;
    this.text = opts.text || "";
    this.cls = opts.cls || "";
    this.attr = opts.attr || {};
    this.children = [];
    this.listeners = {};
    this.value = "";
    this.checked = false;
    global.__elements.push(this);
  }
  empty() { this.children = []; }
  addClass(cls) { this.cls = this.cls ? `${this.cls} ${cls}` : cls; }
  createEl(tag, opts = {}) {
    const child = new global.MockElement(tag, opts);
    if (opts.attr) child.attr = opts.attr;
    this.children.push(child);
    return child;
  }
  createDiv(opts = {}) { return this.createEl("div", opts); }
  createSpan(opts = {}) { return this.createEl("span", opts); }
  setText(text) { this.text = text; }
  addEventListener(name, handler) { this.listeners[name] = handler; }
};

const files = __FILES__;
const PluginClass = require(__MAIN__);

function fileRecord(path) {
  const name = path.split("/").pop();
  const dot = name.lastIndexOf(".");
  return {
    path,
    basename: dot >= 0 ? name.slice(0, dot) : name,
    extension: dot >= 0 ? name.slice(dot + 1) : "",
  };
}

const app = {
  vault: {
    getFiles() { return Object.keys(files).map(fileRecord); },
    adapter: {
      async read(path) {
        if (!(path in files)) throw new Error(`missing fixture: ${path}`);
        return files[path];
      },
      async write() { throw new Error("render test should not write files"); },
    },
  },
  workspace: {
    getLeavesOfType() { return []; },
    getRightLeaf() {
      return { async setViewState(state) { this.state = state; } };
    },
    revealLeaf() {},
    openLinkText() {},
  },
};

(async () => {
  const plugin = new PluginClass();
  plugin.app = app;
  await plugin.onload();
  const view = plugin.views[0].factory({});
  await view.onOpen();
  console.log(JSON.stringify({
    texts: global.__elements.map((element) => element.text).filter(Boolean),
  }));
})().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
"""
    (harness / "run-render.js").write_text(
        script.replace("__FILES__", json.dumps(files)).replace("__MAIN__", json.dumps(str(MAIN))),
        encoding="utf-8",
    )

    proc = subprocess.run(
        ["node", str(harness / "run-render.js")],
        check=False,
        text=True,
        capture_output=True,
        env={**os.environ, "NODE_PATH": str(harness / "node_modules")},
    )

    assert proc.returncode == 0, proc.stderr or proc.stdout
    rendered = json.loads(proc.stdout)
    text = "\n".join(rendered["texts"])

    for expected in (
        "Memoria Inspector",
        "Linter",
        "PASS",
        "2026-06-29 - 1 finding",
        "Integrity flags",
        "quote-anchor",
        "ask",
        "quote missing",
        "Knowledge graph",
        "Source Alpha",
        "Digest Alpha",
        "Candidate Note",
        "Memory Hub",
        "Project Alpha",
        "2 declared edges across 5 checked Concepts",
        "Board counts",
        "review queue",
        "knowledge: 2 ready, 1 running, 0 blocked",
        "Recent audit",
        "deny",
        "direct-write",
        "task-1",
        "Fleet trust",
        "knowledge",
        "97/100 (pass)",
        "4 samples",
    ):
        assert expected in text
