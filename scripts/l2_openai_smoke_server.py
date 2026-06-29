#!/usr/bin/env python3
"""Deterministic local OpenAI-compatible endpoint for the L2 smoke."""

from __future__ import annotations

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--port-file", type=Path)
    args = parser.parse_args(argv)

    server = ThreadingHTTPServer((args.host, args.port), SmokeHandler)
    host, port = server.server_address
    if args.port_file:
        args.port_file.write_text(f"http://{host}:{port}/v1\n", encoding="utf-8")
    print(f"http://{host}:{port}/v1", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
