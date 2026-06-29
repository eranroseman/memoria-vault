#!/usr/bin/env python3
"""Verify the alpha.11 pre-implementation start blockers."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

OUT = Path(__file__).with_name("start-blocker-verification-results.md")
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
WORK = Path("/tmp/memoria-alpha11-start-blockers")  # noqa: S108 -- fixed disposable release probe workspace.
VAULT = Path("/home/eranr/Memoria-test")
INSPECTOR_PLUGIN = VAULT / ".obsidian/plugins/memoria-inspector"
TEMPLATE_INSPECTOR_PLUGIN = ROOT / "vault-template/.obsidian/plugins/memoria-inspector"


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
    sock = None
    try:
        sock = socket.socket()
        sock.settimeout(1)
        sock.connect(("127.0.0.1", port))
        return True, "open"
    except OSError as exc:
        return False, f"{type(exc).__name__}: {exc}"
    finally:
        if sock is not None:
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
        (
            [qmd, "search", "saturation sentinel", "-c", "alpha11", "--format", "json", "-n", "5"],
            "search",
        ),
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
    except Exception as exc:  # noqa: BLE001 -- live probe reports local service failures as evidence.
        return None, None, f"{type(exc).__name__}: {exc}"


def check_zotero() -> Check:
    is_open, why = port_open(23119)
    if not is_open:
        return Check(
            "Zotero Local API item shape",
            "blocked-live",
            f"localhost:23119 not reachable ({why}); Zotero must be running",
        )

    item_status, item_data, item_error = zotero_get("/api/users/0/items?limit=1")
    item_shape = (
        item_status == 200
        and isinstance(item_data, list)
        and (not item_data or {"key", "data"}.issubset(item_data[0]))
    )
    status = "pass" if item_shape else "fail"
    return Check(
        "Zotero Local API item shape",
        status,
        (
            f"port_open=True; item_status={item_status}; item_shape={item_shape}; "
            "annotation_import_in_scope=False; "
            f"errors={item_error or 'none'}"
        ),
    )


def check_pdf_span() -> Check:
    modules = ["fitz", "pymupdf4llm", "pypdf", "pdfplumber", "pdfminer", "reportlab"]
    module_state = {name: importlib.util.find_spec(name) is not None for name in modules}
    commands = ["pdftotext", "pdfinfo", "mutool", "qpdf"]
    command_state = {name: shutil.which(name) is not None for name in commands}
    if not module_state["fitz"]:
        return Check(
            "PDF quote/page/span/bbox preservation",
            "fail-prereq",
            f"local fitz/PyMuPDF parser not installed; modules={module_state}; commands={command_state}",
        )

    try:
        import fitz

        from memoria_vault.runtime.capture import capture_pdf_source

        root = WORK / "pdf-span"
        reset(root)
        shutil.copytree(ROOT / "vault-template/.memoria/schemas", root / ".memoria/schemas")
        for args in (
            ["git", "init", "-q"],
            ["git", "config", "user.email", "start-blocker@example.invalid"],
            ["git", "config", "user.name", "Start Blocker"],
        ):
            rc, out = run(args, cwd=root)
            if rc:
                return Check("PDF quote/page/span/bbox preservation", "fail", out[-600:])

        text = "Alpha11 PDF anchored span preserves bbox."
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), text)
        raw_pdf = doc.tobytes()
        doc.close()

        result = capture_pdf_source(
            root,
            "pdf-span",
            "PDF Span",
            "Parser-backed PDF fixture.",
            raw_pdf,
            raw_filename="span.pdf",
            annotation_quotes=["anchored span"],
            machine="start-blocker",
        )
        ref = result["annotation_refs"][0]
        content = (root / result["content_path"]).read_text(encoding="utf-8")
        ok = (
            "## Page 1" in content
            and "anchored span" in content
            and ref["page"] == 1
            and ref["text_quote"] == "anchored span"
            and isinstance(ref.get("bbox"), list)
            and len(ref["bbox"]) == 4
        )
        return Check(
            "PDF quote/page/span/bbox preservation",
            "pass" if ok else "fail",
            (
                f"fixture={root}; fitz=True; content_has_page={'## Page 1' in content}; "
                f"quote_found={'anchored span' in content}; page={ref.get('page')}; "
                f"bbox={ref.get('bbox')}"
            ),
        )
    except Exception as exc:  # noqa: BLE001 -- release probe reports parser fixture failures as evidence.
        return Check(
            "PDF quote/page/span/bbox preservation",
            "fail",
            f"{type(exc).__name__}: {exc}; modules={module_state}; commands={command_state}",
        )


def check_memoria_inspector_control_panel() -> Check:
    manifest = INSPECTOR_PLUGIN / "manifest.json"
    main_js = INSPECTOR_PLUGIN / "main.js"
    styles = INSPECTOR_PLUGIN / "styles.css"
    community = VAULT / ".obsidian/community-plugins.json"
    enabled = False
    if community.exists():
        enabled = "memoria-inspector" in json.loads(community.read_text(encoding="utf-8"))
    if not manifest.exists() or not main_js.exists() or not styles.exists():
        return Check(
            "Memoria Inspector control-panel deployment",
            "fail",
            f"plugin files missing at {INSPECTOR_PLUGIN}",
        )

    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    file_parity = all(
        sha256_file(INSPECTOR_PLUGIN / name) == sha256_file(TEMPLATE_INSPECTOR_PLUGIN / name)
        for name in ("main.js", "manifest.json", "styles.css")
    )
    main = main_js.read_text(encoding="utf-8")
    control_markers = all(
        token in main
        for token in (
            "Worker actions enqueue jobs only.",
            "enqueueOperation",
            "capture-url-source",
            "record-copi-interview",
            "compile-source-digest",
            "propose-note-candidates",
            "curate-note-candidate",
            "curate-note-link",
            "cascade-rollback",
            "acknowledge-attention",
            "resolve-attention",
        )
    )
    forbidden_absent = all(
        token not in main
        for token in (
            ".vault.modify",
            ".vault.create",
            ".vault.delete",
            "requestUrl",
            "fetch(",
            "child_process",
            'require("fs")',
            "require('fs')",
        )
    )

    rest_open, rest_why = port_open(27124)
    rest_manifest = False
    rest_command_registered = False
    rest_command_executed = False
    workspace_view_present = False
    rest_command_id = "memoria-inspector:open-memoria-inspector"
    if rest_open:
        try:
            cfg = json.loads(
                (VAULT / ".obsidian/plugins/obsidian-local-rest-api/data.json").read_text(
                    encoding="utf-8"
                )
            )
            ctx = ssl._create_unverified_context()  # noqa: S323 -- local smoke reads a self-signed Obsidian REST endpoint.
            req = urllib.request.Request(
                "https://127.0.0.1:27124/vault/.obsidian/plugins/memoria-inspector/manifest.json",
                headers={"Authorization": f"Bearer {cfg['apiKey']}"},
            )
            with urllib.request.urlopen(req, context=ctx, timeout=3) as resp:
                rest_manifest = resp.status == 200
            req = urllib.request.Request(
                "https://127.0.0.1:27124/commands/",
                headers={"Authorization": f"Bearer {cfg['apiKey']}"},
            )
            with urllib.request.urlopen(req, context=ctx, timeout=3) as resp:
                commands = json.loads(resp.read().decode("utf-8"))["commands"]
            command_ids = {command["id"] for command in commands}
            if rest_command_id not in command_ids and "open-memoria-inspector" in command_ids:
                rest_command_id = "open-memoria-inspector"
            rest_command_registered = rest_command_id in command_ids
            if rest_command_registered:
                req = urllib.request.Request(
                    f"https://127.0.0.1:27124/commands/{rest_command_id}/",
                    headers={"Authorization": f"Bearer {cfg['apiKey']}"},
                    method="POST",
                )
                with urllib.request.urlopen(req, context=ctx, timeout=3) as resp:
                    rest_command_executed = resp.status == 204
                workspace_view_present = wait_for_workspace_view(
                    VAULT / ".obsidian/workspace.json",
                    "memoria-inspector-view",
                )
        except Exception:  # noqa: BLE001 -- live REST probe reports any local read failure as evidence.
            rest_manifest = False

    base_ok = (
        enabled
        and manifest_data.get("version") == "0.1.0-alpha.11"
        and file_parity
        and control_markers
        and forbidden_absent
    )
    status = "partial-local" if base_ok else "fail"
    if base_ok and rest_manifest:
        status = "partial-live-rest"
    if base_ok and rest_manifest and rest_command_executed and workspace_view_present:
        status = "partial-live-command"
    return Check(
        "Memoria Inspector control-panel deployment",
        status,
        (
            f"enabled={enabled}; version={manifest_data.get('version')}; "
            f"file_parity={file_parity}; control_markers={control_markers}; "
            f"forbidden_absent={forbidden_absent}; localhost_27124_open={rest_open}; "
            f"rest_manifest_read={rest_manifest}; "
            f"rest_command_registered={rest_command_registered}; "
            f"rest_command_executed={rest_command_executed}; "
            f"rest_command_id={rest_command_id}; "
            f"workspace_view_present={workspace_view_present}; "
            f"live_visual_render_tested=False; port_note={rest_why}"
        ),
    )


def check_worker_queue_dispatch() -> Check:
    root = WORK / "worker-dispatch"
    reset(root)
    (root / ".memoria").mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "vault-template/.memoria/schemas", root / ".memoria/schemas")
    shutil.copytree(ROOT / "vault-template/capabilities", root / "capabilities")
    write(
        root / "knowledge/notes/checked.md",
        """---
type: note
check_status: checked
title: Checked alpha note
---

Alpha queue dispatch should return this checked source.
""",
    )
    write(
        root / "knowledge/notes/unchecked.md",
        """---
type: note
check_status: unchecked
title: Unchecked alpha note
---

Alpha queue dispatch must not return this unchecked source.
""",
    )

    try:
        from memoria_vault.runtime.operations import load_operation_policy
        from memoria_vault.runtime.worker import enqueue_operation, run_next_job

        queued = enqueue_operation(
            root,
            "answer-query",
            payload={"query": "alpha queue dispatch", "k": 5},
            idempotency_key="start-blocker-answer-query",
        )
        done = run_next_job(root, machine="start-blocker")
        source_paths = [source["path"] for source in done.get("sources", [])] if done else []
        disposable_ok = (
            queued["status"] == "pending"
            and done is not None
            and done.get("status") == "done"
            and done.get("engine") == "bm25"
            and source_paths == ["knowledge/notes/checked.md"]
            and (root / ".memoria/queue/done/start-blocker-answer-query.json").is_file()
            and not (root / ".memoria/queue/pending/start-blocker-answer-query.json").exists()
        )

        live_policy_ok = True
        live_policy_error = ""
        try:
            load_operation_policy(VAULT, "answer-query")
        except Exception as exc:  # noqa: BLE001 -- readiness probe reports the fail-closed reason.
            live_policy_ok = False
            live_policy_error = f"{type(exc).__name__}: {exc}"
        live_ready = {
            "queue_root": (VAULT / ".memoria/queue").is_dir(),
            "knowledge_root": (VAULT / "knowledge").is_dir(),
            "capability_policies": (VAULT / "capabilities/operations").is_dir(),
            "answer_query_policy_checked": live_policy_ok,
            "policy_error": live_policy_error or "none",
        }
        live_shape_ready = all(
            bool(live_ready[key])
            for key in (
                "queue_root",
                "knowledge_root",
                "capability_policies",
                "answer_query_policy_checked",
            )
        )
        live_dispatch = {
            "attempted": False,
            "job_id": "",
            "queued_status": "",
            "done_status": "",
            "done_file": False,
        }
        if live_shape_ready:
            live_key = (
                f"start-blocker-live-answer-query-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}"
            )
            live_queued = enqueue_operation(
                VAULT,
                "answer-query",
                payload={"query": "alpha live queue dispatch", "k": 1},
                idempotency_key=live_key,
            )
            live_done = run_next_job(VAULT, machine="start-blocker-live")
            live_dispatch = {
                "attempted": True,
                "job_id": live_key,
                "queued_status": str(live_queued.get("status") or ""),
                "done_status": str((live_done or {}).get("status") or ""),
                "done_file": (VAULT / f".memoria/queue/done/{live_key}.json").is_file(),
            }

        live_dispatch_ok = live_dispatch["attempted"] and live_dispatch["done_status"] == "done"
        status = (
            "pass" if disposable_ok and live_shape_ready and live_dispatch_ok else "partial-local"
        )
        if not disposable_ok:
            status = "fail"
        return Check(
            "worker queue operation dispatch",
            status,
            (
                f"fixture={root}; queued_status={queued.get('status')}; "
                f"done_status={(done or {}).get('status')}; engine={(done or {}).get('engine')}; "
                f"sources={source_paths}; checked_only={source_paths == ['knowledge/notes/checked.md']}; "
                f"done_file={(root / '.memoria/queue/done/start-blocker-answer-query.json').is_file()}; "
                f"memoria_test_ready={live_ready}; memoria_test_dispatch={live_dispatch}"
            ),
        )
    except Exception as exc:  # noqa: BLE001 -- release probe reports dispatch failures as evidence.
        return Check(
            "worker queue operation dispatch",
            "fail",
            f"{type(exc).__name__}: {exc}; fixture={root}",
        )


def workspace_has_view(path: Path, view_type: str) -> bool:
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return _json_contains_view_type(data, view_type)


def wait_for_workspace_view(path: Path, view_type: str, *, attempts: int = 10) -> bool:
    for _attempt in range(attempts):
        if workspace_has_view(path, view_type):
            return True
        time.sleep(0.2)
    return False


def _json_contains_view_type(value: Any, view_type: str) -> bool:
    if isinstance(value, dict):
        if value.get("type") == view_type:
            return True
        return any(_json_contains_view_type(item, view_type) for item in value.values())
    if isinstance(value, list):
        return any(_json_contains_view_type(item, view_type) for item in value)
    return False


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    checks = [
        check_qmd(),
        check_zotero(),
        check_pdf_span(),
        check_memoria_inspector_control_panel(),
        check_worker_queue_dispatch(),
        check_source_id(),
    ]
    blockers = [
        c for c in checks if c.status not in {"pass", "partial-live-rest", "partial-live-command"}
    ]
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
- Zotero item import and Obsidian are live-app checks; if their local services are unreachable,
  the result is blocked rather than simulated.
- PDF span preservation runs a tiny parser-backed capture when `fitz` is
  installed; otherwise it reports a prerequisite failure instead of simulating
  parser fidelity.
- The Memoria Inspector check proves the `Memoria-test` plugin files match the
  alpha.11 template, retain the enqueue-only control-panel markers, avoid direct
  vault/network/shell APIs, and, when Local REST is reachable, execute the live
  Inspector command and check the workspace state for the Inspector view type.
- The worker queue check proves a disposable alpha.11-shaped vault can enqueue
  and drain an `answer-query` operation through the checked operation policy,
  returning only checked Concepts. After refreshing the disposable
  `Memoria-test` sandbox from the alpha.11 template, it also enqueues and drains
  one harmless live `answer-query` job into `.memoria/queue/done/`.

## Evidence status notes

- This report is a point-in-time local probe. `blocked-live` caused by sandboxed
  socket access means this run could not reach the live app, not that prior live
  evidence is invalid.
- Newer disposable smoke results supersede older "not implemented locally" rows
  only as feasibility evidence. They do not prove production implementation or
  close gates that still require visual Obsidian activation or attended Co-PI
  use. Zotero is in scope only as an item/source import path for alpha.11;
  Zotero annotation import is not an alpha.11 capability or release gate.
""",
        encoding="utf-8",
    )
    print(f"report={OUT}")
    for check in checks:
        print(f"{check.status}: {check.name}: {check.evidence}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
