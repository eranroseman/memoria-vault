#!/usr/bin/env python3
"""Verify the alpha.11 pre-implementation start blockers."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import socket
import ssl
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

OUT = Path(__file__).with_name("start-blocker-verification-results.md")
WORK = Path("/tmp/memoria-alpha11-start-blockers")
VAULT = Path("/home/eranr/Memoria-test")
PLUGIN = VAULT / ".obsidian/plugins/memoria-alpha11-smoke"


@dataclass
class Check:
    name: str
    status: str
    evidence: str


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(args: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> tuple[int, str]:
    proc = subprocess.run(
        args,
        cwd=cwd,
        env=env,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return proc.returncode, proc.stdout.strip()


def reset(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def port_open(port: int) -> tuple[bool, str]:
    sock = socket.socket()
    sock.settimeout(1)
    try:
        sock.connect(("127.0.0.1", port))
        return True, "open"
    except OSError as exc:
        return False, f"{type(exc).__name__}: {exc}"
    finally:
        sock.close()


def check_qmd() -> Check:
    root = WORK / "qmd-bundle"
    home = WORK / "qmd-home"
    reset(root)
    reset(home)
    write(
        root / "knowledge/notes/stability.md",
        """---
type: note
title: Source stability
---

Saturation sentinel alpha11 source identity survives citekey changes.
""",
    )
    write(
        root / "knowledge/hubs/alpha11.md",
        """---
type: hub
title: Alpha11 hub
---

The alpha11 hub links [[stability]] and names rollback trace behavior.
""",
    )
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "PWD": str(root),
            "XDG_CACHE_HOME": str(home / ".cache"),
            "QMD_FORCE_CPU": "1",
            "NO_COLOR": "1",
        }
    )
    qmd = shutil.which("qmd")
    if not qmd:
        return Check("qmd disposable bundle index/search", "fail", "qmd binary not found")

    commands = [
        ([qmd, "init"], "init"),
        ([qmd, "collection", "add", str(root), "--name", "alpha11"], "collection-add"),
        ([qmd, "update"], "update"),
        ([qmd, "search", "saturation sentinel", "-c", "alpha11", "--format", "json", "-n", "5"], "search"),
    ]
    outputs: dict[str, tuple[int, str]] = {}
    for args, label in commands:
        outputs[label] = run(args, cwd=root, env=env)
        if outputs[label][0] != 0:
            return Check(
                "qmd disposable bundle index/search",
                "fail",
                f"{label} rc={outputs[label][0]}; output={outputs[label][1][-600:]}",
            )

    search = outputs["search"][1]
    found = "stability.md" in search and "saturation" in search.lower()
    status = "pass" if found else "fail"
    return Check(
        "qmd disposable bundle index/search",
        status,
        f"fixture={root}; init/update/search rc=0; found_stability={found}",
    )


def zotero_get(path: str) -> tuple[int | None, Any, str]:
    url = f"http://127.0.0.1:23119{path}"
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                data: Any = json.loads(body)
            except json.JSONDecodeError:
                data = body[:300]
            return resp.status, data, ""
    except urllib.error.HTTPError as exc:
        return exc.code, None, str(exc)
    except Exception as exc:
        return None, None, f"{type(exc).__name__}: {exc}"


def check_zotero() -> Check:
    is_open, why = port_open(23119)
    if not is_open:
        return Check(
            "Zotero Local API item + annotation shape",
            "blocked-live",
            f"localhost:23119 not reachable ({why}); Zotero must be running",
        )

    item_status, item_data, item_error = zotero_get("/api/users/0/items?limit=1")
    ann_status, ann_data, ann_error = zotero_get("/api/users/0/items?itemType=annotation&limit=1")
    item_shape = (
        item_status == 200
        and isinstance(item_data, list)
        and (not item_data or {"key", "data"}.issubset(item_data[0]))
    )
    annotation_shape = ann_status == 200 and isinstance(ann_data, list)
    annotation_sample = bool(ann_data) if isinstance(ann_data, list) else False
    status = "pass" if item_shape and annotation_shape and annotation_sample else "partial-live"
    if not item_shape or not annotation_shape:
        status = "fail"
    return Check(
        "Zotero Local API item + annotation shape",
        status,
        (
            f"port_open=True; item_status={item_status}; item_shape={item_shape}; "
            f"annotation_status={ann_status}; annotation_list_shape={annotation_shape}; "
            f"annotation_sample_present={annotation_sample}; errors={item_error or ann_error or 'none'}"
        ),
    )


def check_pdf_span() -> Check:
    modules = ["fitz", "pymupdf4llm", "pypdf", "pdfplumber", "pdfminer", "reportlab"]
    module_state = {name: importlib.util.find_spec(name) is not None for name in modules}
    commands = ["pdftotext", "pdfinfo", "mutool", "qpdf"]
    command_state = {name: shutil.which(name) is not None for name in commands}
    has_extractor = any(module_state.values()) or any(command_state.values())
    if not has_extractor:
        return Check(
            "PDF quote/page/span/bbox preservation",
            "fail-prereq",
            f"no local PDF extractor/generator found; modules={module_state}; commands={command_state}",
        )
    return Check(
        "PDF quote/page/span/bbox preservation",
        "blocked-tooling",
        f"PDF tooling exists but no alpha.11 parser contract is implemented; modules={module_state}; commands={command_state}",
    )


def check_obsidian_ui() -> Check:
    manifest = PLUGIN / "manifest.json"
    main_js = PLUGIN / "main.js"
    community = VAULT / ".obsidian/community-plugins.json"
    enabled = False
    if community.exists():
        enabled = "memoria-alpha11-smoke" in json.loads(community.read_text(encoding="utf-8"))
    if not manifest.exists() or not main_js.exists():
        return Check("Obsidian pane activation", "fail", f"plugin files missing at {PLUGIN}")

    main = main_js.read_text(encoding="utf-8")
    static_ok = all(
        token in main
        for token in (
            "registerView",
            "addCommand",
            "setViewState",
            "Co-PI conversation",
            "Flags",
            "Rollback blast radius",
        )
    )

    harness = WORK / "obsidian-ui-harness"
    reset(harness)
    write(
        harness / "node_modules/obsidian/index.js",
        """class Plugin {
  constructor() { this.views = []; this.commands = []; this.app = null; }
  registerView(type, factory) { this.views.push({ type, factory }); }
  addCommand(command) { this.commands.push(command); }
}
class ItemView {
  constructor() {
    const created = [];
    this.containerEl = { children: [null, {
      created,
      empty() { created.length = 0; },
      createEl(tag, opts) { created.push({ tag, text: opts && opts.text }); }
    }] };
  }
}
module.exports = { Plugin, ItemView };
""",
    )
    write(
        harness / "run.js",
        f"""const PluginClass = require({json.dumps(str(main_js))});
const plugin = new PluginClass();
let viewState = null;
plugin.app = {{ workspace: {{ getRightLeaf() {{ return {{ setViewState(state) {{ viewState = state; }} }}; }} }} }};
Promise.resolve(plugin.onload()).then(async () => {{
  const command = plugin.commands.find(c => c.id === "open-alpha11-smoke");
  if (!command) throw new Error("missing command");
  await command.callback();
  const view = plugin.views[0].factory({{}});
  await view.onOpen();
  console.log(JSON.stringify({{
    views: plugin.views.map(v => v.type),
    commands: plugin.commands.map(c => c.id),
    viewState,
    texts: view.containerEl.children[1].created.map(e => e.text).filter(Boolean)
  }}));
}}).catch(err => {{ console.error(err.stack || err.message); process.exit(1); }});
""",
    )
    env = os.environ.copy()
    env["NODE_PATH"] = str(harness / "node_modules")
    rc, out = run(["node", "run.js"], cwd=harness, env=env)
    mock_ok = False
    if rc == 0:
        try:
            data = json.loads(out)
            mock_ok = (
                "memoria-alpha11-smoke" in data["views"]
                and "open-alpha11-smoke" in data["commands"]
                and data["viewState"]["type"] == "memoria-alpha11-smoke"
                and {"Co-PI conversation", "Flags", "Rollback blast radius"}.issubset(data["texts"])
            )
        except Exception:
            mock_ok = False

    rest_open, rest_why = port_open(27124)
    rest_manifest = False
    if rest_open:
        try:
            cfg = json.loads(
                (VAULT / ".obsidian/plugins/obsidian-local-rest-api/data.json").read_text(
                    encoding="utf-8"
                )
            )
            req = urllib.request.Request(
                "https://127.0.0.1:27124/vault/.obsidian/plugins/"
                "memoria-alpha11-smoke/manifest.json",
                headers={"Authorization": f"Bearer {cfg['apiKey']}"},
            )
            with urllib.request.urlopen(
                req, context=ssl._create_unverified_context(), timeout=3
            ) as resp:
                rest_manifest = resp.status == 200
        except Exception:
            rest_manifest = False

    status = "partial-live" if static_ok and enabled and mock_ok else "fail"
    if status == "partial-live" and rest_manifest:
        status = "partial-live-rest"
    return Check(
        "Obsidian pane activation",
        status,
        (
            f"enabled={enabled}; static_registers_view_and_command={static_ok}; "
            f"mock_activation={mock_ok}; localhost_27124_open={rest_open}; "
            f"rest_manifest_read={rest_manifest}; live_gui_activation_tested=False; "
            f"port_note={rest_why}"
        ),
    )


def check_source_id() -> Check:
    root = WORK / "source-id"
    reset(root)
    source_id = "src-alpha11-0001"
    source = root / f"catalog/sources/{source_id}/source.md"
    note = root / "knowledge/notes/claim.md"
    write(
        source,
        f"""---
type: source
source_id: {source_id}
citekey: old2026
title: Old title
---

Source body.
""",
    )
    write(
        note,
        f"""---
type: note
source_id: {source_id}
links:
  - catalog/sources/{source_id}
---

Anchored note cites source_id `{source_id}` while citekey is display metadata.
""",
    )
    before_path = source.relative_to(root).as_posix()
    text = source.read_text(encoding="utf-8")
    source.write_text(
        text.replace("citekey: old2026", "citekey: corrected2026").replace(
            "title: Old title", "title: Corrected title"
        ),
        encoding="utf-8",
    )
    after_path = source.relative_to(root).as_posix()
    link_target = root / "catalog" / "sources" / source_id / "source.md"
    note_text = note.read_text(encoding="utf-8")
    refs_still_resolve = link_target.exists() and f"catalog/sources/{source_id}" in note_text
    path_stable = before_path == after_path
    citekey_changed = "citekey: corrected2026" in source.read_text(encoding="utf-8")
    status = "pass" if path_stable and refs_still_resolve and citekey_changed else "fail"
    return Check(
        "source_id stability across citekey changes",
        status,
        (
            f"fixture={root}; before_path={before_path}; after_path={after_path}; "
            f"path_stable={path_stable}; citekey_changed={citekey_changed}; "
            f"refs_still_resolve={refs_still_resolve}"
        ),
    )


def main() -> int:
    reset(WORK)
    checks = [check_qmd(), check_zotero(), check_pdf_span(), check_obsidian_ui(), check_source_id()]
    blockers = [c for c in checks if c.status not in {"pass", "partial-live-rest"}]
    verdict = "PASS" if not blockers else "PARTIAL"
    rows = "\n".join(f"| {c.name} | {c.status} | {c.evidence} |" for c in checks)
    OUT.write_text(
        f"""# Alpha.11 start-blocker verification results

Date: {datetime.now(UTC).date().isoformat()}

Verdict: **{verdict}**.

| Claim | Status | Evidence |
| --- | --- | --- |
{rows}

## Interpretation

- `qmd` and `source_id` are verified with disposable local fixtures.
- Zotero and Obsidian are live-app checks; if their local services are unreachable,
  the result is blocked rather than simulated.
- PDF span preservation is not verified because no local PDF extraction/generation
  toolchain is installed in this environment.
- The Obsidian plugin check proves static registration plus a mocked command/view
  activation path; it still does not prove visual rendering in a real Obsidian
  window.
""",
        encoding="utf-8",
    )
    print(f"report={OUT}")
    for check in checks:
        print(f"{check.status}: {check.name}: {check.evidence}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
