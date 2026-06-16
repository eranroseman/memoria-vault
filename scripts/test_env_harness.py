#!/usr/bin/env python3
"""Replay the ADR-80 Phase 1 model-free test-env cassette.

The cassette records tool-call shape plus deterministic fixture arguments. Replay
builds or reuses a disposable vault, drives real Memoria operations where possible,
and asserts artifact shape without a live model, GPU, Obsidian GUI, or screenshots.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request

import yaml

DEFAULT_CASSETTE = Path("fixtures/test-env/cassettes/alpha6-l4-golden-path.json")
SKIP_COPY = {".git"}


class HarnessError(RuntimeError):
    pass


@dataclass
class ReplayResult:
    cassette: str
    vault: Path
    steps: list[dict[str, Any]]
    artifacts: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "cassette": self.cassette,
            "vault": str(self.vault),
            "steps": self.steps,
            "artifacts": sorted(set(self.artifacts)),
        }


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
    data = json.loads(path.read_text(encoding="utf-8"))
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


def write_recorded_cassette(cassette: dict[str, Any], path: Path) -> None:
    recorded = json.loads(json.dumps(cassette, sort_keys=True))
    for step in recorded["steps"]:
        step["arg_shape"] = arg_shape(step.get("args", {}))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(recorded, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def add_operation_paths(root: Path) -> None:
    for rel in (
        "src/.memoria/mcp",
        "src/.memoria/operations/processing/ingest",
        "src/.memoria/operations/processing/project",
        "src/.memoria/operations/lib",
    ):
        path = str(root / rel)
        if path not in sys.path:
            sys.path.insert(0, path)


def populate_vault(root: Path, vault: Path) -> None:
    src = root / "src"
    if not vault.exists() or not any(vault.iterdir()):
        shutil.copytree(src, vault, dirs_exist_ok=True, ignore=shutil.ignore_patterns(*SKIP_COPY))
    import schema

    folders = schema.load_folders(root / "src/.memoria/schemas")
    for folder in folders["skeleton"]:
        (vault / folder).mkdir(parents=True, exist_ok=True)


def parse_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    data = yaml.safe_load(text[4:end])
    return data if isinstance(data, dict) else {}


def write_frontmatter(path: Path, fm: dict[str, Any], body: str) -> None:
    rendered = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, default_flow_style=False)
    path.write_text(f"---\n{rendered}---\n\n{body.lstrip()}", encoding="utf-8")


def validate_typed_note(vault: Path, rel: str) -> None:
    import schema

    path = vault / rel
    fm = parse_frontmatter(path)
    note_type = fm.get("type")
    if not note_type:
        return
    types = schema.load_types()
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
        rows = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines() if line]
        if not rows or rows[-1].get("decision") != expect["audit_decision"]:
            raise HarnessError(f"expected last audit decision {expect['audit_decision']!r}")
        artifacts.append("system/logs/audit.jsonl")


def apply_classification(vault: Path, args: dict[str, Any]) -> str:
    import classify

    citekey = args["citekey"]
    rel = f"catalog/papers/{citekey}.md"
    path = vault / rel
    fm = parse_frontmatter(path)
    body = path.read_text(encoding="utf-8").split("\n---", 1)[1].lstrip("-\n")
    floor, margin = classify.thresholds(vault)
    decision = classify.decide(args["merged"], floor=floor, margin=margin)
    if decision["status"] == "applied":
        fm["research_area"] = decision["research_area"]
        fm["methodology"] = decision["methodology"]
        proposed = fm.setdefault("_proposed_classification", {})
        proposed["research_area"] = decision["research_area"]
        proposed["methodology"] = decision["methodology"]
    classify.append_audit(vault, citekey, decision, floor, margin)
    write_frontmatter(path, fm, body)
    return rel


def run_policy_deny_assertion(root: Path, vault: Path, args: dict[str, Any]) -> None:
    lane_dir = vault / ".memoria/lane-overrides"
    lane_dir.mkdir(parents=True, exist_ok=True)
    profile = str(args["profile"]).removeprefix("memoria-")
    (lane_dir / f"{profile}.yaml").write_text(
        f"profile: {args['profile']}\n"
        "policy:\n"
        "  allow:\n"
        "    write:\n"
        "      - \"inbox/**\"\n"
        "  deny:\n"
        "    write:\n"
        "      - \"notes/claims/**\"\n"
        "  require:\n"
        "    - audit_log\n"
        "routing:\n"
        "  write_scope:\n"
        "    - \"inbox/\"\n",
        encoding="utf-8",
    )
    plugin = root / "src/.memoria/plugins/memoria-policy-gate/__init__.py"
    spec = importlib.util.spec_from_file_location("memoria_policy_gate_harness", plugin)
    if spec is None or spec.loader is None:
        raise HarnessError("cannot load memoria-policy-gate plugin")
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    gate.PROFILE = args["profile"]
    gate.VAULT = vault
    result = gate._gate(
        args["tool_name"],
        {"filepath": args["path"], "content": args["content"]},
        args["task_id"],
    )
    if result.get("action") != "block":
        raise HarnessError(f"deny assertion did not block: {result}")
    if "failed-closed" in result.get("message", ""):
        raise HarnessError(f"deny assertion failed closed instead of policy-denying: {result}")


def run_step(root: Path, vault: Path, step: dict[str, Any]) -> list[str]:
    import ingest_paper
    import structural_impact

    import inbox

    tool = step["tool"]
    args = step.get("args", {})
    artifacts: list[str] = []
    if tool == "ingest.paper":
        note = ingest_paper.ingest_text(args["citekey"], args["bibtex"])
        path = vault / note["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(ingest_paper.render(note), encoding="utf-8")
        artifacts.append(note["path"])
    elif tool == "classify.apply":
        artifacts.append(apply_classification(vault, args))
    elif tool == "vault.write_markdown":
        path = vault / args["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(args["content"], encoding="utf-8")
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
    elif tool == "policy.deny_assertion":
        run_policy_deny_assertion(root, vault, args)
    else:
        raise HarnessError(f"unknown cassette tool: {tool}")
    assert_expectations(vault, step.get("expect", {}), artifacts)
    return artifacts


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
        payload = json.loads(text[start + len("<!-- memoria-structural-impact:json -->"):end])
        if payload["relation_count"] < int(gate["min_relation_count"]):
            raise HarnessError("project gate relation count below expected floor")
        if payload["saturation_state"] != gate["expected_saturation_state"]:
            raise HarnessError(
                f"project gate saturation {payload['saturation_state']!r} != "
                f"{gate['expected_saturation_state']!r}"
            )


def replay(root: Path, vault: Path, cassette_path: Path) -> ReplayResult:
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
    return ReplayResult(cassette=cassette["name"], vault=vault, steps=steps, artifacts=artifacts)


def run_model_smoke() -> int:
    """Opt-in ADR-80 G3 smoke for a local OpenAI-compatible tool-call endpoint."""
    base_url = os.environ.get("MEMORIA_MODEL_BASE_URL", "").rstrip("/")
    model = os.environ.get("MEMORIA_MODEL_NAME", "local-tool-smoke")
    if not base_url:
        print("model-smoke: skipped (set MEMORIA_MODEL_BASE_URL to run the live tool-call smoke)")
        return 0
    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "Call the provided tool to write inbox/model-smoke.md with body ok.",
            }
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "vault_write",
                    "description": "Write a vault-relative markdown file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"},
                        },
                        "required": ["path", "content"],
                    },
                },
            }
        ],
        "tool_choice": {"type": "function", "function": {"name": "vault_write"}},
        "max_tokens": 64,
    }
    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (OSError, error.HTTPError, json.JSONDecodeError) as exc:
        raise HarnessError(f"model-smoke request failed: {exc}") from exc
    message = ((data.get("choices") or [{}])[0].get("message") or {})
    calls = message.get("tool_calls") or []
    if not calls:
        raise HarnessError(f"model-smoke produced no tool_calls: {data}")
    fn = (calls[0].get("function") or {})
    if fn.get("name") != "vault_write":
        raise HarnessError(f"model-smoke called unexpected tool: {fn.get('name')!r}")
    print("model-smoke: PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("replay", "record", "model-smoke"), nargs="?", default="replay")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--vault", type=Path)
    parser.add_argument("--cassette", type=Path, default=DEFAULT_CASSETTE)
    parser.add_argument("--out", type=Path, help="record output path")
    parser.add_argument("--json", action="store_true", help="print replay summary as JSON")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    cassette_path = args.cassette if args.cassette.is_absolute() else root / args.cassette
    if args.command == "model-smoke":
        return run_model_smoke()
    cassette = load_cassette(cassette_path)
    if args.command == "record":
        out = args.out or cassette_path
        write_recorded_cassette(cassette, out if out.is_absolute() else root / out)
        print(f"recorded: {out}")
        return 0

    if args.vault is None:
        with tempfile.TemporaryDirectory(prefix="memoria-test-env-") as tmp:
            result = replay(root, Path(tmp), cassette_path)
            print(json.dumps(result.as_dict(), indent=2) if args.json else "test-env-harness: PASS")
            return 0
    result = replay(root, args.vault, cassette_path)
    print(json.dumps(result.as_dict(), indent=2) if args.json else "test-env-harness: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except HarnessError as exc:
        print(f"test-env-harness: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
