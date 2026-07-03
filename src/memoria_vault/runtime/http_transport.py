"""Stdlib loopback HTTP transport over the engine API."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from memoria_vault.engine import api as engine_api

MAX_BODY_BYTES = 1_000_000


def make_http_server(
    workspace: Path,
    *,
    host: str,
    port: int,
    token: str,
) -> ThreadingHTTPServer:
    """Create a token-authenticated loopback server for one workspace."""
    workspace = Path(workspace).resolve()

    class Handler(BaseHTTPRequestHandler):
        server_version = "MemoriaHTTP/0.1"

        def do_GET(self) -> None:
            self._handle("GET")

        def do_POST(self) -> None:
            self._handle("POST")

        def log_message(self, message_format: str, *args: object) -> None:
            return

        def _handle(self, method: str) -> None:
            if not is_authorized(self.headers.get("Authorization"), token):
                self._write({"ok": False, "error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
                return
            try:
                payload, status = _dispatch(workspace, method, self.path, self._json_body)
            except Exception as exc:  # noqa: BLE001 -- HTTP boundary returns JSON errors.
                payload, status = {"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST
            self._write(payload, status)

        def _json_body(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length") or "0")
            if length > MAX_BODY_BYTES:
                raise ValueError("request body too large")
            if length == 0:
                return {}
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("JSON body must be an object")
            return data

        def _write(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            self.send_response(int(status))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return ThreadingHTTPServer((host, port), Handler)


def is_authorized(authorization: str | None, token: str) -> bool:
    return authorization == f"Bearer {token}"


def _dispatch(
    workspace: Path,
    method: str,
    raw_path: str,
    body: Any,
) -> tuple[dict[str, Any], HTTPStatus]:
    parsed = urlparse(raw_path)
    query = parse_qs(parsed.query)
    path = parsed.path.rstrip("/") or "/"
    if method == "GET":
        return _read(workspace, path, query), HTTPStatus.OK
    if method == "POST":
        return _write(workspace, path, body()), HTTPStatus.OK
    return {"ok": False, "error": "method not allowed"}, HTTPStatus.METHOD_NOT_ALLOWED


def _read(workspace: Path, path: str, query: dict[str, list[str]]) -> dict[str, Any]:
    if path == "/status":
        return {"ok": True, **engine_api.read_status(workspace)}
    if path == "/operations":
        return engine_api.read_operations(workspace)
    if path == "/requests":
        return engine_api.read_requests(workspace, status=_one(query, "status"))
    if path == "/request":
        return engine_api.read_request(workspace, _required(query, "id"))
    if path == "/attention":
        return engine_api.read_attention(
            workspace,
            status=_one(query, "status"),
            kind=_one(query, "kind"),
            worklist=_one(query, "worklist").lower() == "true",
        )
    if path == "/attention/card":
        return engine_api.read_attention_card(workspace, _required(query, "path"))
    if path == "/concepts":
        return engine_api.read_concepts(workspace, concept_type=_one(query, "type"))
    if path == "/concept":
        return engine_api.read_concept(workspace, _required(query, "target"))
    if path == "/work":
        return engine_api.read_work(workspace, _required(query, "id"))
    return {"ok": False, "error": "not found"}


def _write(workspace: Path, path: str, body: dict[str, Any]) -> dict[str, Any]:
    if path != "/operation/run":
        return {"ok": False, "error": "not found"}
    operation_id = str(body.get("operation_id") or "").strip()
    if not operation_id:
        raise ValueError("operation_id is required")
    payload = body.get("payload") if isinstance(body.get("payload"), dict) else {}
    return engine_api.run_operation(
        workspace,
        operation_id,
        payload,
        idempotency_key=str(body.get("idempotency_key") or "") or None,
        schedule_id=str(body.get("schedule_id") or "") or None,
        actor=str(body.get("actor") or "agent"),
        command=f"http:{operation_id}",
        surface="memoria-http",
        machine="memoria-http",
    )


def _one(query: dict[str, list[str]], key: str) -> str:
    values = query.get(key) or []
    return str(values[0]) if values else ""


def _required(query: dict[str, list[str]], key: str) -> str:
    value = _one(query, key).strip()
    if not value:
        raise ValueError(f"{key} is required")
    return value
