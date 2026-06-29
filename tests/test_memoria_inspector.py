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


def test_memoria_inspector_reads_operational_sources_and_queues_worker_jobs():
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
        ".memoria/queue/",
        ".memoria/queue/pending",
        "GRAPH_PREFIXES",
        "knowledgeGraphSummary",
        "Knowledge graph",
        "graphRefs",
        "graphEdges",
        "graphTargetPath",
        "checked Concept",
        "workerQueueSummary",
        "Worker queue",
        "failed_at",
        "job_id",
        "registerView",
        "getRightLeaf",
        "adapter.read",
        "recentIntegrityFlags",
        "Integrity flags",
        'row.event !== "check-fired"',
        'row.status !== "failed"',
        "enqueueOperation",
        'kind: "operation"',
        "operation_id: operationId",
        "integrity-evidence-check",
        "integrity-quote-anchor-check",
        "integrity-claim-quote-check",
        "integrity-provenance-checkpoint",
        "integrity-link-target-check",
        "check-source-metadata",
        "Check provenance",
        "regenerate-tracked-projections",
        "rebuild-checked-qmd-source",
        "analyze-gaps",
        "analyze-project-argument",
        "render-project-argument-canvas",
        "Project path",
        "Analyze project",
        "Render canvas",
        "answer-query",
        "Ask query",
        "capture-url-source",
        "Source URL",
        "Capture URL",
        "record-copi-interview",
        "Co-PI interview takeaway",
        "Record interview",
        "compile-source-digest",
        "Hub topics",
        "Compile digest",
        "propose-note-candidates",
        "Digest path",
        "Note candidate JSON array",
        "Propose notes",
        "curate-note-candidate",
        "Note candidate path",
        "Accept note",
        "Reject note",
        "enqueueNoteCuration",
        "curate-note-link",
        "Link source note path",
        "Link target path",
        "Supports",
        "Contradicts",
        "Extends",
        "enqueueNoteLink",
        "cascade-rollback",
        "acknowledge-attention",
        "resolve-attention",
        "enqueueAttention",
        "target_id: target",
        "include_target: includeTarget.checked",
        "path.startsWith(QUEUE_PENDING)",
        "openLinkText",
    ):
        assert marker in text

    for forbidden in (
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

    assert text.count("adapter.write(") == 1
    assert "app.vault.adapter.write(path," in text


def test_memoria_inspector_control_panel_enqueues_real_operation_jobs(tmp_path: Path):
    harness = tmp_path / "inspector-harness"
    write_obsidian_mock(harness)
    (harness / "run.js").write_text(
        f"""
global.__elements = [];
global.window = {{ setInterval() {{ return 1; }} }};
global.MockElement = class MockElement {{
  constructor(tag, opts = {{}}) {{
    this.tag = tag;
    this.text = opts.text || "";
    this.cls = opts.cls || "";
    this.attr = opts.attr || {{}};
    this.children = [];
    this.listeners = {{}};
    this.value = "";
    this.checked = false;
    global.__elements.push(this);
  }}
  empty() {{ this.children = []; }}
  addClass(cls) {{ this.cls = this.cls ? `${{this.cls}} ${{cls}}` : cls; }}
  createEl(tag, opts = {{}}) {{
    const child = new global.MockElement(tag, opts);
    if (opts.attr) child.attr = opts.attr;
    this.children.push(child);
    return child;
  }}
  createDiv(opts = {{}}) {{ return this.createEl("div", opts); }}
  createSpan(opts = {{}}) {{ return this.createEl("span", opts); }}
  setText(text) {{ this.text = text; }}
  addEventListener(name, handler) {{ this.listeners[name] = handler; }}
}};

const PluginClass = require({json.dumps(str(MAIN))});
const writes = [];
const app = {{
  vault: {{
    getFiles() {{ return []; }},
    adapter: {{
      async read() {{ return ""; }},
      async write(path, text) {{ writes.push({{ path, job: JSON.parse(text) }}); }},
    }},
  }},
  workspace: {{
    getLeavesOfType() {{ return []; }},
    getRightLeaf() {{
      return {{ async setViewState(state) {{ this.state = state; }} }};
    }},
    revealLeaf() {{}},
    openLinkText() {{}},
  }},
}};

function byText(text) {{
  const found = global.__elements.find((element) => element.text === text);
  if (!found) throw new Error(`missing element text: ${{text}}`);
  return found;
}}
function byPlaceholder(text) {{
  const found = global.__elements.find((element) => element.attr && element.attr.placeholder === text);
  if (!found) throw new Error(`missing input placeholder: ${{text}}`);
  return found;
}}
async function click(text) {{
  const element = byText(text);
  if (!element.listeners.click) throw new Error(`missing click handler: ${{text}}`);
  await element.listeners.click();
}}

(async () => {{
  const plugin = new PluginClass();
  plugin.app = app;
  await plugin.onload();
  const view = plugin.views[0].factory({{}});
  await view.onOpen();

  await click("Check evidence");
  await click("Check quotes");
  await click("Check claims");
  await click("Check provenance");
  await click("Check links");
  await click("Check sources");
  await click("Refresh projections");
  await click("Rebuild search");
  await click("Analyze gaps");

  byPlaceholder("Project path").value = "knowledge/projects/project-alpha.md";
  await click("Analyze project");
  await click("Render canvas");

  byPlaceholder("Ask query").value = "memory consolidation";
  await click("Ask query");

  byPlaceholder("Source URL").value = "https://example.test/source";
  await click("Capture URL");

  byPlaceholder("Co-PI source id").value = "source-alpha";
  byPlaceholder("Co-PI interview takeaway").value = "important finding";
  await click("Record interview");

  byPlaceholder("Hub topics").value = "Memory, Evidence";
  await click("Compile digest");

  byPlaceholder("Digest path").value = "knowledge/digests/source-alpha.md";
  byPlaceholder("Note candidate JSON array").value = JSON.stringify([{{ title: "Candidate" }}]);
  await click("Propose notes");

  byPlaceholder("Note candidate path").value = "knowledge/notes/candidate.md";
  await click("Accept note");
  await click("Reject note");

  byPlaceholder("Link source note path").value = "knowledge/notes/candidate.md";
  byPlaceholder("Link target path").value = "knowledge/notes/thesis.md";
  await click("Supports");
  await click("Contradicts");
  await click("Extends");

  byPlaceholder("Attention or trace target path").value = "catalog/sources/source-alpha/source.md";
  const include = global.__elements.find((element) => element.attr && element.attr.type === "checkbox");
  include.checked = true;
  await click("Rollback trace");
  await click("Acknowledge");
  await click("Resolve");

  console.log(JSON.stringify(writes.map((write) => write.job)));
}})().catch((error) => {{
  console.error(error.stack || error.message);
  process.exit(1);
}});
""",
        encoding="utf-8",
    )

    proc = subprocess.run(
        ["node", str(harness / "run.js")],
        check=False,
        text=True,
        capture_output=True,
        env={**os.environ, "NODE_PATH": str(harness / "node_modules")},
    )

    assert proc.returncode == 0, proc.stderr or proc.stdout
    jobs = json.loads(proc.stdout)
    by_operation = {job["operation_id"]: job for job in jobs}

    assert [job["kind"] for job in jobs] == ["operation"] * len(jobs)
    assert [job["status"] for job in jobs] == ["pending"] * len(jobs)
    assert all(job["source"] == "memoria-inspector" for job in jobs)
    assert all(job["job_id"].startswith(f"{job['operation_id']}-") for job in jobs)
    assert [job["operation_id"] for job in jobs] == [
        "integrity-evidence-check",
        "integrity-quote-anchor-check",
        "integrity-claim-quote-check",
        "integrity-provenance-checkpoint",
        "integrity-link-target-check",
        "check-source-metadata",
        "regenerate-tracked-projections",
        "rebuild-checked-qmd-source",
        "analyze-gaps",
        "analyze-project-argument",
        "render-project-argument-canvas",
        "answer-query",
        "capture-url-source",
        "record-copi-interview",
        "compile-source-digest",
        "propose-note-candidates",
        "curate-note-candidate",
        "curate-note-candidate",
        "curate-note-link",
        "curate-note-link",
        "curate-note-link",
        "cascade-rollback",
        "acknowledge-attention",
        "resolve-attention",
    ]
    assert set(by_operation) == {job["operation_id"] for job in jobs}
    assert by_operation["integrity-evidence-check"]["payload"] == {"shadow": False}
    assert by_operation["integrity-quote-anchor-check"]["payload"] == {"shadow": False}
    assert by_operation["integrity-claim-quote-check"]["payload"] == {"shadow": False}
    assert by_operation["integrity-provenance-checkpoint"]["payload"] == {"shadow": False}
    assert by_operation["integrity-link-target-check"]["payload"] == {"shadow": False}
    assert by_operation["check-source-metadata"]["payload"] == {"shadow": False}
    assert by_operation["regenerate-tracked-projections"]["payload"] == {}
    assert by_operation["rebuild-checked-qmd-source"]["payload"] == {}
    assert by_operation["analyze-gaps"]["payload"] == {}
    assert by_operation["analyze-project-argument"]["payload"] == {
        "project_path": "knowledge/projects/project-alpha.md"
    }
    assert by_operation["render-project-argument-canvas"]["payload"] == {
        "project_path": "knowledge/projects/project-alpha.md"
    }
    assert by_operation["answer-query"]["payload"] == {"query": "memory consolidation"}
    assert by_operation["capture-url-source"]["payload"] == {"url": "https://example.test/source"}
    assert by_operation["record-copi-interview"]["payload"] == {
        "source_id": "source-alpha",
        "response": "important finding",
    }
    assert by_operation["compile-source-digest"]["payload"] == {
        "source_id": "source-alpha",
        "hub_topics": ["Memory", "Evidence"],
    }
    assert by_operation["propose-note-candidates"]["payload"] == {
        "digest_path": "knowledge/digests/source-alpha.md",
        "candidates": [{"title": "Candidate"}],
    }
    assert [job["payload"] for job in jobs if job["operation_id"] == "curate-note-candidate"] == [
        {
            "note_path": "knowledge/notes/candidate.md",
            "status": "accepted",
            "reason": "pi-note-curation",
        },
        {
            "note_path": "knowledge/notes/candidate.md",
            "status": "rejected",
            "reason": "pi-note-curation",
        },
    ]
    assert [job["payload"] for job in jobs if job["operation_id"] == "curate-note-link"] == [
        {
            "source_note_path": "knowledge/notes/candidate.md",
            "target_path": "knowledge/notes/thesis.md",
            "link_type": "supports",
            "reason": "pi-note-link",
        },
        {
            "source_note_path": "knowledge/notes/candidate.md",
            "target_path": "knowledge/notes/thesis.md",
            "link_type": "contradicts",
            "reason": "pi-note-link",
        },
        {
            "source_note_path": "knowledge/notes/candidate.md",
            "target_path": "knowledge/notes/thesis.md",
            "link_type": "extends",
            "reason": "pi-note-link",
        },
    ]
    assert by_operation["cascade-rollback"]["payload"] == {
        "target_id": "catalog/sources/source-alpha/source.md",
        "reason": "pi-requested-rollback",
        "include_target": True,
    }
    assert by_operation["acknowledge-attention"]["payload"] == {
        "target_id": "catalog/sources/source-alpha/source.md",
        "reason": "pi-attention-decision",
    }
    assert by_operation["resolve-attention"]["payload"] == {
        "target_id": "catalog/sources/source-alpha/source.md",
        "reason": "pi-attention-decision",
    }


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
        ".memoria/queue/pending/job-a.json": (
            '{"operation_id":"answer-query","job_id":"job-a","created_at":"2026-06-29T10:02:00Z"}'
        ),
        ".memoria/queue/running/job-b.json": (
            '{"operation_id":"check-source-metadata","job_id":"job-b",'
            '"started_at":"2026-06-29T10:03:00Z"}'
        ),
        ".memoria/queue/failed/job-c.json": (
            '{"operation_id":"capture-url-source","job_id":"job-c",'
            '"failed_at":"2026-06-29T10:04:00Z","error":"bad url"}'
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
      async write() { throw new Error("render test should not enqueue jobs"); },
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
        "Worker queue",
        "pending",
        "running",
        "failed",
        "capture-url-source",
        "job-c",
        "bad url",
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
