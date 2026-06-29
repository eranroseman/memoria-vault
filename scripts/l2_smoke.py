#!/usr/bin/env python3
"""Helpers for scripts/test-l2.sh."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
for path in (ROOT / "src", ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from memoria_vault.runtime.jsonl import iter_jsonl

DISABLED_TOOLSETS = [
    "browser",
    "clarify",
    "code_execution",
    "computer_use",
    "cronjob",
    "delegation",
    "file",
    "homeassistant",
    "image_gen",
    "memory",
    "messaging",
    "moa",
    "session_search",
    "spotify",
    "terminal",
    "tts",
    "video",
    "video_gen",
    "vision",
    "web",
    "x_search",
    "yuanbao",
]
SMOKE_PLATFORM_TOOLSETS = ["skills", "obsidian"]
MODEL = "memoria-l2-smoke"
ARTIFACT = "knowledge/notes/l2-smoke-direct-write.md"
ARTIFACT_BODY = """---
type: note
check_status: checked
title: L2 direct write smoke
l2_live_smoke: true
---

# L2 live smoke

This direct write should be blocked by the Memoria policy gate.
"""


class SmokeHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        if self.path.rstrip("/") == "/v1/models":
            self._json(200, {"object": "list", "data": [{"id": MODEL, "object": "model"}]})
            return
        self._json(404, {"error": {"message": "not found"}})

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/v1/chat/completions":
            self._json(404, {"error": {"message": "not found"}})
            return
        request = self._read_json()
        if _has_tool_result(request):
            self._respond_final(bool(request.get("stream")))
            return
        self._respond_tool_call(request, bool(request.get("stream")))

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8")) if raw else {}

    def _respond_tool_call(self, request: dict[str, Any], stream: bool) -> None:
        tool_name = _select_put_tool(request)
        if not tool_name:
            self._json(400, {"error": {"message": "no put_content tool supplied"}})
            return
        args = json.dumps({"path": ARTIFACT, "content": ARTIFACT_BODY})
        if not stream:
            self._json(
                200,
                {
                    "id": "chatcmpl-l2-smoke",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": MODEL,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": "call_l2_smoke",
                                        "type": "function",
                                        "function": {"name": tool_name, "arguments": args},
                                    }
                                ],
                            },
                            "finish_reason": "tool_calls",
                        }
                    ],
                },
            )
            return
        self._sse(
            [
                _chunk(
                    {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "index": 0,
                                "id": "call_l2_smoke",
                                "type": "function",
                                "function": {"name": tool_name, "arguments": ""},
                            }
                        ],
                    }
                ),
                _chunk({"tool_calls": [{"index": 0, "function": {"arguments": args}}]}),
                _chunk({}, finish_reason="tool_calls"),
            ]
        )

    def _respond_final(self, stream: bool) -> None:
        if not stream:
            self._json(
                200,
                {
                    "id": "chatcmpl-l2-smoke-final",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": MODEL,
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": "L2_SMOKE_DONE"},
                            "finish_reason": "stop",
                        }
                    ],
                },
            )
            return
        self._sse(
            [
                _chunk({"role": "assistant", "content": ""}),
                _chunk({"content": "L2_SMOKE_DONE"}),
                _chunk({}, finish_reason="stop"),
            ]
        )

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _sse(self, chunks: list[dict[str, Any]]) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        for chunk in chunks:
            self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
            self.wfile.flush()
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


def _select_put_tool(request: dict[str, Any]) -> str:
    for tool in request.get("tools") or []:
        function = tool.get("function") or {}
        name = function.get("name") or ""
        if "obsidian" in name and "put_content" in name:
            return name
    return ""


def _has_tool_result(request: dict[str, Any]) -> bool:
    return any(message.get("role") == "tool" for message in request.get("messages") or [])


def _chunk(delta: dict[str, Any], finish_reason: str | None = None) -> dict[str, Any]:
    return {
        "id": "chatcmpl-l2-smoke",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": MODEL,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
    }


def serve_model(host: str, port: int, port_file: Path | None = None) -> None:
    server = ThreadingHTTPServer((host, port), SmokeHandler)
    bound_host, bound_port = server.server_address
    if port_file:
        port_file.write_text(f"http://{bound_host}:{bound_port}/v1\n", encoding="utf-8")
    print(f"http://{bound_host}:{bound_port}/v1", flush=True)
    server.serve_forever()


def safe_vault_path(vault: Path, relpath: str) -> Path:
    candidate = Path(relpath)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"path must stay inside the vault: {relpath}")
    resolved = (vault / candidate).resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes the vault: {relpath}") from exc
    return resolved


def put_content(vault: Path, path: str, content: str) -> dict[str, str]:
    target = safe_vault_path(vault, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"path": path, "status": "written"}


def append_content(vault: Path, path: str, content: str) -> dict[str, str]:
    target = safe_vault_path(vault, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(content)
    return {"path": path, "status": "appended"}


def get_content(vault: Path, path: str) -> str:
    return safe_vault_path(vault, path).read_text(encoding="utf-8")


def serve_obsidian_shim(vault: Path) -> None:
    try:
        from mcp.server.fastmcp import FastMCP  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "Missing MCP SDK. Install runtime deps first: "
            "python -m pip install -r vault-template/.memoria/mcp/requirements.txt"
        ) from exc

    mcp = FastMCP("l2-obsidian-shim")

    @mcp.tool(name="obsidian_put_content")
    def _put(path: str, content: str) -> dict[str, str]:
        """Write a complete vault-relative file."""
        return put_content(vault, path, content)

    @mcp.tool(name="obsidian_append_content")
    def _append(path: str, content: str) -> dict[str, str]:
        """Append text to a vault-relative file."""
        return append_content(vault, path, content)

    @mcp.tool(name="obsidian_get_content")
    def _get(path: str) -> str:
        """Read a vault-relative file."""
        return get_content(vault, path)

    mcp.run()


def prepare_vault(root: Path, vault: Path) -> None:
    if vault.exists():
        shutil.rmtree(vault)
    shutil.copytree(root / "vault-template", vault, dirs_exist_ok=True)
    (vault / "system/logs").mkdir(parents=True, exist_ok=True)
    audit = vault / "system/logs/audit.jsonl"
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.touch()


def write_profile(
    profile_src: Path,
    profile_stage: Path,
    *,
    repo_root: Path,
    vault: Path,
    python: str,
    provider: str,
    model: str,
    base_url: str,
    context_length: int,
) -> None:
    if profile_stage.exists():
        shutil.rmtree(profile_stage)
    profile_stage.mkdir(parents=True)
    shutil.copy2(profile_src / "SOUL.md", profile_stage / "SOUL.md")
    if (profile_src / "skills").is_dir():
        shutil.copytree(profile_src / "skills", profile_stage / "skills")

    distribution = yaml.safe_load((profile_src / "distribution.yaml").read_text(encoding="utf-8"))
    distribution["name"] = "memoria-writer"
    distribution["display_name"] = "Memoria L2 Writer Smoke"
    (profile_stage / "distribution.yaml").write_text(
        yaml.safe_dump(distribution, sort_keys=False),
        encoding="utf-8",
    )

    config = {
        "model": {
            "provider": provider,
            "base_url": base_url,
            "default": model,
            "context_length": context_length,
            "ollama_num_ctx": context_length,
        },
        "mcp_servers": {
            "obsidian": {
                "command": python,
                "args": [
                    str(repo_root / "scripts/l2_smoke.py"),
                    "obsidian-shim",
                    "--vault",
                    str(vault),
                ],
                "timeout": 30,
            }
        },
        "platform_toolsets": {
            "cli": SMOKE_PLATFORM_TOOLSETS,
            "cron": SMOKE_PLATFORM_TOOLSETS,
            "api_server": SMOKE_PLATFORM_TOOLSETS,
        },
        "agent": {"tool_use_enforcement": True, "disabled_toolsets": DISABLED_TOOLSETS},
        "terminal": {"cwd": str(vault)},
        "checkpoints": {"enabled": False},
        "plugins": {"enabled": ["memoria-policy-gate"]},
    }
    (profile_stage / "config.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )


def deploy_policy_plugin(root: Path, profile_dir: Path, profile: str, vault: Path) -> None:
    source = root / "vault-template/.memoria/plugins/memoria-policy-gate"
    target = profile_dir / "plugins/memoria-policy-gate"
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / "plugin.yaml", target / "plugin.yaml")
    text = (source / "__init__.py").read_text(encoding="utf-8")
    text = text.replace("{{PROFILE}}", profile).replace("{{VAULT_PATH}}", str(vault))
    text = text.replace(
        "if str(_MCP_DIR) not in sys.path:\n    sys.path.insert(0, str(_MCP_DIR))\n",
        "if str(_MCP_DIR) not in sys.path:\n"
        "    sys.path.insert(0, str(_MCP_DIR))\n"
        f"if {str(root / 'src')!r} not in sys.path:\n"
        f"    sys.path.insert(0, {str(root / 'src')!r})\n",
    )
    (target / "__init__.py").write_text(text, encoding="utf-8")


def assert_smoke(vault: Path, artifact_rel: str, audit_before: int) -> None:
    artifact = vault / artifact_rel
    if artifact.exists():
        raise AssertionError(f"direct Obsidian write unexpectedly created {artifact_rel}")

    audit_path = vault / "system/logs/audit.jsonl"
    rows = list(iter_jsonl(audit_path))
    new_rows = rows[audit_before:]
    deny_rows = [
        row
        for row in new_rows
        if row.get("path") == artifact_rel
        and row.get("decision") == "deny"
        and row.get("policy_rule") == "tool-registry.allowlist"
    ]
    if not deny_rows:
        raise AssertionError(f"no tool-registry deny audit row for {artifact_rel}")
    row = deny_rows[-1]
    for field in ("message", "task_id"):
        if not row.get(field):
            raise AssertionError(f"audit row missing {field}: {row}")
    print(f"direct Obsidian write denied: {artifact_rel}")
    print(f"policy-gate deny audit row asserted: task_id={row['task_id']}")


def count_audit_rows(vault: Path) -> int:
    audit = vault / "system/logs/audit.jsonl"
    if not audit.exists():
        return 0
    return len([line for line in audit.read_text(encoding="utf-8").splitlines() if line.strip()])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    prep = sub.add_parser("prepare-vault")
    prep.add_argument("--root", required=True, type=Path)
    prep.add_argument("--vault", required=True, type=Path)

    profile = sub.add_parser("write-profile")
    profile.add_argument("--profile-src", required=True, type=Path)
    profile.add_argument("--profile-stage", required=True, type=Path)
    profile.add_argument("--repo-root", required=True, type=Path)
    profile.add_argument("--vault", required=True, type=Path)
    profile.add_argument("--python", required=True)
    profile.add_argument("--provider", required=True)
    profile.add_argument("--model", required=True)
    profile.add_argument("--base-url", required=True)
    profile.add_argument("--context-length", required=True, type=int)

    plugin = sub.add_parser("deploy-policy-plugin")
    plugin.add_argument("--root", required=True, type=Path)
    plugin.add_argument("--profile-dir", required=True, type=Path)
    plugin.add_argument("--profile", required=True)
    plugin.add_argument("--vault", required=True, type=Path)

    audit = sub.add_parser("count-audit")
    audit.add_argument("--vault", required=True, type=Path)

    check = sub.add_parser("assert-smoke")
    check.add_argument("--vault", required=True, type=Path)
    check.add_argument("--artifact", required=True)
    check.add_argument("--audit-before", required=True, type=int)

    model = sub.add_parser("serve-model")
    model.add_argument("--host", default="127.0.0.1")
    model.add_argument("--port", type=int, default=0)
    model.add_argument("--port-file", type=Path)

    shim = sub.add_parser("obsidian-shim")
    shim.add_argument("--vault", required=True, type=Path)

    ns = parser.parse_args(argv)
    if ns.command == "prepare-vault":
        prepare_vault(ns.root, ns.vault)
    elif ns.command == "write-profile":
        write_profile(
            ns.profile_src,
            ns.profile_stage,
            repo_root=ns.repo_root,
            vault=ns.vault,
            python=ns.python,
            provider=ns.provider,
            model=ns.model,
            base_url=ns.base_url,
            context_length=ns.context_length,
        )
    elif ns.command == "deploy-policy-plugin":
        deploy_policy_plugin(ns.root, ns.profile_dir, ns.profile, ns.vault)
    elif ns.command == "count-audit":
        print(count_audit_rows(ns.vault))
    elif ns.command == "assert-smoke":
        assert_smoke(ns.vault, ns.artifact, ns.audit_before)
    elif ns.command == "serve-model":
        serve_model(ns.host, ns.port, ns.port_file)
    elif ns.command == "obsidian-shim":
        serve_obsidian_shim(ns.vault.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
