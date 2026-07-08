#!/usr/bin/env python3
"""Replay the package-gate model-free test-env cassette.

The cassette records tool-call shape plus deterministic fixture arguments. Replay
builds or reuses a disposable vault, drives real Memoria operations where possible,
and asserts artifact shape without a live model, GPU, Obsidian GUI, or screenshots.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT / "src", ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from memoria_vault.runtime import state
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.paths import load_json
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.vaultio import read_frontmatter

DEFAULT_CASSETTE = Path("tests/fixtures/test-env/cassettes/package-gate-golden-path.json")


class HarnessError(RuntimeError):
    pass


def arg_shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: arg_shape(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [arg_shape(value[0])] if value else []
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if value is None:
        return "null"
    return "str"


def load_cassette(path: Path) -> dict[str, Any]:
    data = load_json(path)
    if data.get("schema_version") != 1:
        raise HarnessError(f"unsupported cassette schema_version: {data.get('schema_version')}")
    if data.get("match") != "tool_name+arg_shape":
        raise HarnessError(f"unsupported cassette match rule: {data.get('match')}")
    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        raise HarnessError("cassette has no steps")
    for step in steps:
        if arg_shape(step.get("args", {})) != step.get("arg_shape"):
            raise HarnessError(f"cassette step {step.get('id')} arg_shape does not match args")
    return data


def add_operation_paths(root: Path) -> None:
    for rel in ("src",):
        path = str(root / rel)
        if path not in sys.path:
            sys.path.insert(0, path)


def populate_vault(root: Path, vault: Path) -> None:
    if not (vault / ".memoria/schemas").is_dir():
        from memoria_vault.cli import main as cli_main

        rc = cli_main(["init", "--workspace", str(vault), "--yes", "--quiet"])
        if rc != 0:
            raise HarnessError(f"memoria init failed with exit {rc}")
    from memoria_vault.runtime.subsystems.lib import schema

    folders = schema.load_folders(vault / ".memoria/schemas")
    for folder in folders["skeleton"]:
        (vault / folder).mkdir(parents=True, exist_ok=True)


def validate_typed_note(vault: Path, rel: str) -> None:
    from memoria_vault.runtime.subsystems.lib import schema

    path = vault / rel
    fm = read_frontmatter(path)
    note_type = fm.get("type")
    if not note_type:
        return
    types = schema.load_types()
    folders = schema.load_folders()
    bundle_roots = tuple(f"{str(root).strip('/')}/" for root in schema.bundle_roots(folders))
    if not rel.startswith(bundle_roots):
        return
    if note_type not in types:
        raise HarnessError(f"{rel}: unknown type {note_type!r}")
    errors = schema.validate_frontmatter(fm, types[note_type])
    if errors:
        raise HarnessError(f"{rel}: schema errors: {errors}")


def assert_expectations(vault: Path, expect: dict[str, Any], artifacts: list[str]) -> None:
    for rel in expect.get("writes", []):
        if not (vault / rel).is_file():
            raise HarnessError(f"expected write missing: {rel}")
        validate_typed_note(vault, rel)
        artifacts.append(rel)
    for prefix in expect.get("writes_prefix", []):
        matches = sorted(vault.glob(f"{prefix}*.md"))
        if not matches:
            raise HarnessError(f"expected write prefix missing: {prefix}")
        for path in matches:
            rel = path.relative_to(vault).as_posix()
            validate_typed_note(vault, rel)
            artifacts.append(rel)
    for rel in expect.get("not_exists", []):
        if (vault / rel).exists():
            raise HarnessError(f"forbidden artifact exists: {rel}")
    if expect.get("audit_decision"):
        audit = vault / "system/logs/audit.jsonl"
        rows = list(iter_jsonl(audit))
        if not rows or rows[-1].get("decision") != expect["audit_decision"]:
            raise HarnessError(f"expected last audit decision {expect['audit_decision']!r}")
        artifacts.append("system/logs/audit.jsonl")


def run_step(root: Path, vault: Path, step: dict[str, Any]) -> list[str]:
    from memoria_vault.runtime.knowledge import write_project_argument_canvas
    from memoria_vault.runtime.subsystems.lib import inbox
    from memoria_vault.runtime.subsystems.processing.project import structural_impact

    tool = step["tool"]
    args = step.get("args", {})
    artifacts: list[str] = []
    if tool == "vault.write_markdown":
        path = vault / args["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(args["content"], encoding="utf-8")
        mark_file_status(vault, args["path"], args.get("verdict"))
        artifacts.append(args["path"])
    elif tool == "inbox.write_proposal":
        path = inbox.write_proposal(vault, **args)
        artifacts.append(path.relative_to(vault).as_posix())
    elif tool == "inbox.write_finding":
        path = inbox.write_finding(vault, **args)
        artifacts.append(path.relative_to(vault).as_posix())
    elif tool == "inbox.write_work_prompt":
        path = inbox.write_work_prompt(vault, **args)
        if path is not None:
            artifacts.append(path.relative_to(vault).as_posix())
    elif tool == "project.structural_impact":
        result = structural_impact.run(vault, args["project"])
        artifacts.append(result["path"])
    elif tool == "project.argument_canvas":
        result = write_project_argument_canvas(vault, args["project"])
        artifacts.append(result["canvas_path"])
    else:
        raise HarnessError(f"unknown cassette tool: {tool}")
    assert_expectations(vault, step.get("expect", {}), artifacts)
    return artifacts


def mark_file_status(vault: Path, rel: str, verdict: str | None) -> None:
    path = vault / rel
    frontmatter = read_frontmatter(path)
    if verdict not in state.CHECK_STATUSES:
        return
    state.record_observed_file_edit(
        vault,
        output_id=rel,
        concept_type=str(frontmatter.get("type") or "note"),
        output_sha256=sha256_file(path),
    )
    state.set_concept_verdict(vault, rel, verdict)


def assert_final(vault: Path, final: dict[str, Any]) -> None:
    for rel in final.get("exists", []):
        if not (vault / rel).exists():
            raise HarnessError(f"final assertion missing: {rel}")
    for rel in final.get("not_exists", []):
        if (vault / rel).exists():
            raise HarnessError(f"final assertion forbidden artifact exists: {rel}")
    gate = final.get("project_gate") or {}
    if gate:
        text = (vault / gate["path"]).read_text(encoding="utf-8")
        start = text.index("<!-- memoria-structural-impact:json -->")
        end = text.index("<!-- /memoria-structural-impact:json -->")
        payload = json.loads(text[start + len("<!-- memoria-structural-impact:json -->") : end])
        if payload["relation_count"] < int(gate["min_relation_count"]):
            raise HarnessError("project gate relation count below expected floor")
        if payload["evidence_saturation"] != gate["expected_saturation_state"]:
            raise HarnessError(
                f"project gate saturation {payload['evidence_saturation']!r} != "
                f"{gate['expected_saturation_state']!r}"
            )


def replay(root: Path, vault: Path, cassette_path: Path) -> dict[str, Any]:
    root = root.resolve()
    vault = vault.resolve()
    add_operation_paths(root)
    cassette = load_cassette(cassette_path)
    populate_vault(root, vault)
    steps: list[dict[str, Any]] = []
    artifacts: list[str] = []
    for step in cassette["steps"]:
        produced = list(dict.fromkeys(run_step(root, vault, step)))
        artifacts.extend(produced)
        steps.append({"id": step["id"], "tool": step["tool"], "artifacts": produced})
    assert_final(vault, cassette.get("final_assertions", {}))
    return {
        "cassette": cassette["name"],
        "vault": str(vault),
        "steps": steps,
        "artifacts": sorted(set(artifacts)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("replay",), nargs="?", default="replay")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--vault", type=Path)
    parser.add_argument("--cassette", type=Path, default=DEFAULT_CASSETTE)
    parser.add_argument("--json", action="store_true", help="print replay summary as JSON")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    cassette_path = args.cassette if args.cassette.is_absolute() else root / args.cassette

    if args.vault is None:
        with tempfile.TemporaryDirectory(prefix="memoria-test-env-") as tmp:
            result = replay(root, Path(tmp), cassette_path)
            print(json.dumps(result, indent=2) if args.json else "test-env-harness: PASS")
            return 0
    result = replay(root, args.vault, cassette_path)
    print(json.dumps(result, indent=2) if args.json else "test-env-harness: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except HarnessError as exc:
        print(f"test-env-harness: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
