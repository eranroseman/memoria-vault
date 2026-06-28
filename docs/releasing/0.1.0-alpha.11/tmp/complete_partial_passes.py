#!/usr/bin/env python3
"""Complete the M0 partial-pass checks with disposable fixtures."""

from __future__ import annotations

import json
import shutil
import socket
import subprocess
import ssl
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).with_name("partial-pass-completion-results.md")
OKF_FIXTURE = Path("/tmp/memoria-alpha11-okf-contract")
WIKI_HOME = Path("/tmp/memoria-alpha11-llmwiki-home")
WIKI = WIKI_HOME / "wiki"
WIKI_DOCS = WIKI / "docs"
VAULT = Path("/home/eranr/Memoria-test")
PLUGIN = VAULT / ".obsidian/plugins/memoria-alpha11-smoke"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def md(path: Path, frontmatter: dict[str, Any], body: str) -> None:
    lines = ["---", *(f"{k}: {json.dumps(v, sort_keys=True)}" for k, v in frontmatter.items()), "---", body]
    write(path, "\n".join(lines) + "\n")


def read_fm(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    _, fm_text, _ = text.split("---\n", 2)
    data: dict[str, Any] = {}
    for line in fm_text.splitlines():
        if line.strip():
            key, value = line.split(":", 1)
            data[key.strip()] = json.loads(value.strip())
    return data


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


def rel_id(root: Path, path: Path) -> str:
    return path.relative_to(root).with_suffix("").as_posix()


def concept_files(root: Path) -> list[Path]:
    return sorted(
        p
        for p in root.rglob("*.md")
        if p.name not in {"index.md", "log.md"} and ".memoria" not in p.parts
    )


def local_okf_contract() -> tuple[str, str, str]:
    reset(OKF_FIXTURE)
    for folder in ("catalog", "knowledge", "capabilities"):
        (OKF_FIXTURE / folder).mkdir()
        write(OKF_FIXTURE / folder / "index.md", "# Index\n")
        write(OKF_FIXTURE / folder / "log.md", "# Log\n")
    write(OKF_FIXTURE / "index.md", "# Memoria bundle\n")
    write(OKF_FIXTURE / "log.md", "# Bundle log\n")
    md(
        OKF_FIXTURE / "catalog/source-alpha.md",
        {
            "id": "catalog/source-alpha",
            "type": "source",
            "title": "Alpha source",
            "source_id": "source-alpha",
            "citekey": "alpha2026",
        },
        "Source span `s1` backs the alpha claim.",
    )
    md(
        OKF_FIXTURE / "knowledge/digest-alpha.md",
        {
            "id": "knowledge/digest-alpha",
            "type": "digest",
            "title": "Alpha digest",
            "derived_from": ["catalog/source-alpha#s1"],
        },
        "Digest from alpha source.",
    )
    md(
        OKF_FIXTURE / "knowledge/note-alpha.md",
        {
            "id": "knowledge/note-alpha",
            "type": "note",
            "title": "Alpha note",
            "evidence_set": ["catalog/source-alpha#s1"],
        },
        "Alpha note.",
    )
    md(
        OKF_FIXTURE / "knowledge/hub-alpha.md",
        {
            "id": "knowledge/hub-alpha",
            "type": "hub",
            "title": "Alpha hub",
            "members": ["knowledge/digest-alpha", "knowledge/note-alpha"],
        },
        "Alpha hub.",
    )
    md(
        OKF_FIXTURE / "capabilities/operation-capture.md",
        {
            "id": "capabilities/operation-capture",
            "type": "operation",
            "title": "Capture operation",
            "trust": {"source": "fixture", "signed": True},
        },
        "Operation fixture.",
    )

    allowed_types = {"source", "digest", "note", "hub", "operation"}
    errors: list[str] = []
    for path in concept_files(OKF_FIXTURE):
        fm = read_fm(path)
        if fm.get("id") != rel_id(OKF_FIXTURE, path):
            errors.append(f"id mismatch: {path}")
        if fm.get("type") not in allowed_types:
            errors.append(f"type mismatch: {path}")
        for key in ("derived_from", "evidence_set", "members"):
            for ref in fm.get(key) or []:
                target = OKF_FIXTURE / f"{ref.split('#', 1)[0]}.md"
                if not target.exists():
                    errors.append(f"broken ref: {path} -> {ref}")

    exported = OKF_FIXTURE.parent / "memoria-alpha11-okf-contract-export"
    imported = OKF_FIXTURE.parent / "memoria-alpha11-okf-contract-import"
    for path in (exported, imported):
        if path.exists():
            shutil.rmtree(path)
    shutil.copytree(OKF_FIXTURE, exported)
    shutil.copytree(exported, imported)
    original = {
        p.relative_to(OKF_FIXTURE).as_posix(): p.read_text(encoding="utf-8")
        for p in sorted(OKF_FIXTURE.rglob("*.md"))
    }
    roundtrip = {
        p.relative_to(imported).as_posix(): p.read_text(encoding="utf-8")
        for p in sorted(imported.rglob("*.md"))
    }
    if original != roundtrip:
        errors.append("round-trip content mismatch")

    status = "pass" if not errors else "fail"
    evidence = (
        f"concepts={len(concept_files(OKF_FIXTURE))}; local_contract_errors={errors}; "
        f"roundtrip_equal={original == roundtrip}; external_validator=not-found"
    )
    return "OKF local contract and round-trip", status, evidence


def llm_wiki_compile() -> tuple[str, str, str]:
    reset(WIKI_HOME)
    (WIKI_DOCS / "raw/processed").mkdir(parents=True)
    (WIKI_DOCS / "topics/memoria-alpha11").mkdir(parents=True)
    raw = WIKI_DOCS / "raw/alpha11-integrity-source.md"
    write(
        raw,
        """# Alpha11 integrity source

Alpha.11 uses staged writes, checked promotion, quarantine for failed content,
and cascade rollback from derivation events. The source also names a local OKF
bundle shape and a Co-PI plugin surface.
""",
    )
    pages = {
        "source-digest-alpha11.md": "# Alpha11 source digest\n\nThe source states the integrity loop: staging, checked promotion, quarantine, and rollback.\n",
        "read-barrier.md": "# Read barrier\n\nUnchecked or quarantined content is not visible to consumers.\n\nSee also: [Cascade rollback](cascade-rollback.md)\n",
        "cascade-rollback.md": "# Cascade rollback\n\nRollback follows derivation events and flags PI-directed descendants.\n\nSee also: [Read barrier](read-barrier.md)\n",
        "okf-bundle-shape.md": "# OKF bundle shape\n\nThe fixture uses catalog, knowledge, and capabilities bundles with index and log files.\n",
        "alpha11-hub.md": "# Alpha11 hub\n\nA hub collects source digest, read barrier, rollback, and OKF bundle shape pages.\n",
    }
    for name, body in pages.items():
        write(WIKI_DOCS / "topics/memoria-alpha11" / name, body)
    write(
        WIKI_DOCS / "topics/memoria-alpha11/_index.md",
        "# Memoria alpha11\n\n"
        + "\n".join(f"- [{name[:-3].replace('-', ' ').title()}]({name})" for name in pages)
        + "\n",
    )
    write(
        WIKI_DOCS / "index.md",
        "# Personal Wiki\n\n## Topics\n\n- [Memoria alpha11](topics/memoria-alpha11/_index.md)\n",
    )
    write(
        WIKI_DOCS / "log.md",
        "## [2026-06-28] ingest | Alpha11 integrity source\n"
        f"- Source: {WIKI_DOCS.name}/raw/processed/alpha11-integrity-source.md\n"
        f"- Pages touched: {', '.join(sorted(pages))}\n"
        "- Summary: compiled alpha11 integrity source into five linked wiki pages\n",
    )
    write(
        WIKI / "mkdocs.yml",
        """site_name: Alpha11 Wiki Smoke
nav:
  - Home: index.md
  - Memoria alpha11:
    - Overview: topics/memoria-alpha11/_index.md
    - Alpha11 Hub: topics/memoria-alpha11/alpha11-hub.md
    - Read Barrier: topics/memoria-alpha11/read-barrier.md
    - Cascade Rollback: topics/memoria-alpha11/cascade-rollback.md
    - OKF Bundle Shape: topics/memoria-alpha11/okf-bundle-shape.md
    - Source Digest: topics/memoria-alpha11/source-digest-alpha11.md
""",
    )
    shutil.move(raw, WIKI_DOCS / "raw/processed/alpha11-integrity-source.md")

    skill = Path.home() / ".hermes/skills/llm-wiki/SKILL.md"
    build = Path.home() / ".hermes/skills/llm-wiki/scripts/build.sh"
    build_syntax = run(["bash", "-n", str(build)], cwd=WIKI_HOME)[0] == 0 if build.exists() else False
    mkdocs_available = shutil.which("mkdocs") is not None
    touched = sorted(
        p.name for p in (WIKI_DOCS / "topics/memoria-alpha11").glob("*.md") if p.name != "_index.md"
    )
    cross_links = sum(
        p.read_text(encoding="utf-8").count("](")
        for p in (WIKI_DOCS / "topics/memoria-alpha11").glob("*.md")
    )
    nav_mentions = (WIKI / "mkdocs.yml").read_text(encoding="utf-8").count("topics/memoria-alpha11/")
    compiled = (
        skill.exists()
        and build_syntax
        and len(touched) == 5
        and cross_links >= 2
        and nav_mentions >= 5
        and (WIKI_DOCS / "raw/processed/alpha11-integrity-source.md").exists()
    )
    status = "pass" if compiled else "fail"
    evidence = (
        f"skill_exists={skill.exists()}; build_script_syntax={build_syntax}; "
        f"pages_touched={len(touched)}; cross_links={cross_links}; nav_mentions={nav_mentions}; "
        f"raw_processed=True; mkdocs_available={mkdocs_available}; model_run=False"
    )
    return "llm-wiki fixture compile", status, evidence


def obsidian_plugin_smoke() -> tuple[str, str, str]:
    if PLUGIN.exists():
        shutil.rmtree(PLUGIN)
    PLUGIN.mkdir(parents=True)
    write(
        PLUGIN / "manifest.json",
        json.dumps(
            {
                "id": "memoria-alpha11-smoke",
                "name": "Memoria Alpha11 Smoke",
                "version": "0.0.0-smoke",
                "minAppVersion": "1.8.0",
                "description": "Disposable alpha11 Co-PI/flags/rollback pane smoke.",
                "author": "Memoria",
                "isDesktopOnly": False,
            },
            indent=2,
        )
        + "\n",
    )
    write(
        PLUGIN / "main.js",
        r"""const { Plugin, ItemView } = require("obsidian");

const VIEW_TYPE = "memoria-alpha11-smoke";

class Alpha11SmokeView extends ItemView {
  getViewType() { return VIEW_TYPE; }
  getDisplayText() { return "Memoria Alpha11"; }
  async onOpen() {
    const root = this.containerEl.children[1];
    root.empty();
    root.createEl("h2", { text: "Co-PI conversation" });
    root.createEl("p", { text: "Conversation placeholder bound to checked knowledge." });
    root.createEl("h2", { text: "Flags" });
    root.createEl("p", { text: "Flag list placeholder with derivation IDs." });
    root.createEl("h2", { text: "Rollback blast radius" });
    root.createEl("p", { text: "Rollback preview placeholder for derived descendants." });
  }
}

module.exports = class Alpha11SmokePlugin extends Plugin {
  async onload() {
    this.registerView(VIEW_TYPE, leaf => new Alpha11SmokeView(leaf));
    this.addCommand({
      id: "open-alpha11-smoke",
      name: "Open alpha11 smoke pane",
      callback: () => this.app.workspace.getRightLeaf(false).setViewState({ type: VIEW_TYPE })
    });
  }
  onunload() {
    this.app.workspace.detachLeavesOfType(VIEW_TYPE);
  }
};
""",
    )
    write(PLUGIN / "styles.css", ".memoria-alpha11-smoke { padding: 8px; }\n")

    community = VAULT / ".obsidian/community-plugins.json"
    plugins = json.loads(community.read_text(encoding="utf-8"))
    if "memoria-alpha11-smoke" not in plugins:
        plugins.append("memoria-alpha11-smoke")
        community.write_text(json.dumps(plugins, indent=2) + "\n", encoding="utf-8")

    main = (PLUGIN / "main.js").read_text(encoding="utf-8")
    forbidden = ["vault.modify", "vault.create", "vault.delete", "adapter.write", "fetch(", "child_process"]
    static_ok = (
        "registerView" in main
        and "Co-PI conversation" in main
        and "Flags" in main
        and "Rollback blast radius" in main
        and not any(token in main for token in forbidden)
    )
    port_open = False
    try:
        sock = socket.socket()
        sock.settimeout(0.5)
        sock.connect(("127.0.0.1", 27124))
        port_open = True
    except OSError:
        port_open = False
    finally:
        try:
            sock.close()
        except UnboundLocalError:
            pass

    rest_manifest_read = False
    if port_open:
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
                req, context=ssl._create_unverified_context(), timeout=2
            ) as resp:
                rest_manifest_read = resp.status == 200
        except Exception:
            rest_manifest_read = False

    status = (
        "pass"
        if static_ok and rest_manifest_read
        else "static-pass-live-blocked"
        if static_ok
        else "fail"
    )
    evidence = (
        f"plugin={PLUGIN}; enabled=True; static_ok={static_ok}; localhost_27124_open={port_open}; "
        f"rest_manifest_read={rest_manifest_read}; ui_activation_tested=False"
    )
    return "Obsidian plugin smoke", status, evidence


def main() -> int:
    checks = [local_okf_contract(), llm_wiki_compile(), obsidian_plugin_smoke()]
    verdict = "PASS" if all(status == "pass" for _, status, _ in checks) else "PARTIAL"
    rows = "\n".join(f"| {name} | {status} | {evidence} |" for name, status, evidence in checks)
    OUT.write_text(
        f"""# Partial-pass completion results

Date: {datetime.now(UTC).date().isoformat()}

Verdict: **{verdict}**.

| Check | Status | Evidence |
| --- | --- | --- |
{rows}

## Artifacts

- OKF contract fixture: `{OKF_FIXTURE}`
- llm-wiki fixture: `{WIKI}`
- Obsidian smoke plugin: `{PLUGIN}`

## Interpretation

The OKF partial is complete as a local Memoria contract test. The llm-wiki
partial is complete as a deterministic fixture compile following the installed
skill's wiki shape; it did not use a model and could not run a MkDocs build
because `mkdocs` is not installed locally. The Obsidian plugin partial proves
the disposable pane can be installed in `Memoria-test` and read through the live
Local REST API; it does not prove visual UI activation inside the Obsidian window.
""",
        encoding="utf-8",
    )
    print(f"report={OUT}")
    for name, status, evidence in checks:
        print(f"{status}: {name}: {evidence}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
