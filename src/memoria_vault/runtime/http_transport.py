"""Stdlib loopback HTTP transport over the engine API."""

from __future__ import annotations

import json
import math
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from memoria_vault import __version__
from memoria_vault.engine import api as engine_api
from memoria_vault.engine.surface_contract import (
    SURFACE_ACTIONS,
    SURFACE_CONTRACT_VERSION,
    http_routes,
)
from memoria_vault.runtime.policy.paths import normalize_path, within_scope

MAX_BODY_BYTES = 1_000_000
HTTP_ROUTES = http_routes()
HTTP_PATHS = {path for _method, path in HTTP_ROUTES}
ALLOWED_ORIGIN = "app://obsidian.md"


class MemoriaHTTPServer(ThreadingHTTPServer):
    """Loopback server carrying boot identity and idle-exit bookkeeping."""

    daemon_threads = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.boot_id = ""
        self.last_authenticated = time.monotonic()
        self._authenticated_lock = threading.Lock()
        self._authenticated_in_flight = 0
        self._idle_shutdown_reserved = False
        self.serve_forever_started = threading.Event()

    def record_authenticated_activity(self) -> None:
        """Mark an authenticated request without changing the in-flight count."""
        with self._authenticated_lock:
            self.last_authenticated = time.monotonic()

    @contextmanager
    def authenticated_request(self) -> Iterator[bool]:
        """Count all work after a request has passed bearer authentication."""
        with self._authenticated_lock:
            admitted = not self._idle_shutdown_reserved
            if admitted:
                self._authenticated_in_flight += 1
                self.last_authenticated = time.monotonic()
        try:
            yield admitted
        finally:
            if admitted:
                with self._authenticated_lock:
                    self._authenticated_in_flight -= 1

    def reserve_idle_shutdown(self, idle_exit_seconds: float) -> bool:
        """Atomically prevent later authenticated work when the server is idle."""
        with self._authenticated_lock:
            if (
                self._idle_shutdown_reserved
                or self._authenticated_in_flight != 0
                or time.monotonic() - self.last_authenticated < idle_exit_seconds
            ):
                return False
            self._idle_shutdown_reserved = True
            return True

    def service_actions(self) -> None:
        """Signal only after the stdlib serve loop has safely started."""
        self.serve_forever_started.set()
        super().service_actions()


def host_allowed(host_header: str | None, port: int) -> bool:
    """Return whether a request names this loopback listener exactly."""
    return host_header in {f"127.0.0.1:{port}", f"localhost:{port}"}


def origin_allowed(origin: str | None) -> bool:
    """Return whether a browser request originates from the Obsidian app."""
    return origin is None or origin == ALLOWED_ORIGIN


class PayloadTooLarge(ValueError):
    pass


def make_http_server(
    workspace: Path,
    *,
    host: str,
    port: int,
    token: str,
    read_scope: list[str] | None = None,
    boot_id: str = "",
) -> MemoriaHTTPServer:
    """Create a token-authenticated loopback server for one workspace."""
    workspace = Path(workspace).resolve()
    startup_read_scope = _normalize_read_scope(read_scope)

    class Handler(BaseHTTPRequestHandler):
        server_version = "MemoriaHTTP/0.1"

        def do_GET(self) -> None:
            self._handle("GET")

        def do_POST(self) -> None:
            self._handle("POST")

        def do_PUT(self) -> None:
            self._handle("PUT")

        def do_PATCH(self) -> None:
            self._handle("PATCH")

        def do_DELETE(self) -> None:
            self._handle("DELETE")

        def log_message(self, message_format: str, *args: object) -> None:
            return

        def _handle(self, method: str) -> None:
            port = int(self.server.server_address[1])
            hosts = self.headers.get_all("Host") or []
            if len(hosts) != 1 or not host_allowed(hosts[0], port):
                self._write({"ok": False, "error": "forbidden host"}, HTTPStatus.FORBIDDEN)
                return
            origins = self.headers.get_all("Origin") or []
            if len(origins) > 1 or (origins and not origin_allowed(origins[0])):
                self._write({"ok": False, "error": "forbidden origin"}, HTTPStatus.FORBIDDEN)
                return
            path = urlparse(self.path).path.rstrip("/") or "/"
            if path == "/v1/status":
                if method != "GET":
                    self._write(
                        {"ok": False, "error": "method not allowed"},
                        HTTPStatus.METHOD_NOT_ALLOWED,
                    )
                    return
                self._write(
                    {"ok": True, "boot_id": self.server.boot_id, "engine_version": __version__}
                )
                return
            if not is_authorized(self.headers.get("Authorization"), token):
                self._write({"ok": False, "error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
                return
            with self.server.authenticated_request() as admitted:
                if not admitted:
                    self._write(
                        {"ok": False, "error": "server stopping"},
                        HTTPStatus.SERVICE_UNAVAILABLE,
                    )
                    return
                if path == "/v1/shutdown":
                    if method != "POST":
                        self._write(
                            {"ok": False, "error": "method not allowed"},
                            HTTPStatus.METHOD_NOT_ALLOWED,
                        )
                        return
                    self._write({"ok": True, "stopping": True})
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return
                try:
                    payload, status = _dispatch(
                        workspace,
                        method,
                        self.path,
                        self._json_body,
                        read_scope=startup_read_scope,
                    )
                except Exception as exc:  # noqa: BLE001 -- HTTP boundary returns JSON errors.
                    payload, status = {"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST
                self._write(payload, status)

        def _json_body(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length") or "0")
            if length > MAX_BODY_BYTES:
                raise PayloadTooLarge("request body too large")
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

    server = MemoriaHTTPServer((host, port), Handler)
    server.boot_id = boot_id
    server.record_authenticated_activity()
    return server


def _finite_positive_duration(value: object, name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or not math.isfinite(value)
        or value <= 0
    ):
        raise ValueError(f"{name} must be a finite positive duration")
    return float(value)


def start_idle_monitor(
    server: MemoriaHTTPServer, idle_exit_seconds: float, poll_interval: float = 1.0
) -> threading.Thread:
    """Stop a ready server once its authenticated idle window expires."""
    idle_exit_seconds = _finite_positive_duration(idle_exit_seconds, "idle_exit_seconds")
    poll_interval = _finite_positive_duration(poll_interval, "poll_interval")

    def watch() -> None:
        server.serve_forever_started.wait()
        while True:
            if server.reserve_idle_shutdown(idle_exit_seconds):
                server.shutdown()
                return
            time.sleep(poll_interval)

    thread = threading.Thread(target=watch, daemon=True, name="memoria-idle-exit")
    thread.start()
    return thread


def bind_http_server(
    workspace: Path,
    *,
    host: str,
    candidate_ports: list[int],
    token: str,
    read_scope: list[str] | None = None,
    boot_id: str = "",
) -> MemoriaHTTPServer:
    """Bind the first free candidate port, retaining the final bind error."""
    last_error: OSError | None = None
    for candidate in candidate_ports:
        try:
            return make_http_server(
                workspace,
                host=host,
                port=candidate,
                token=token,
                read_scope=read_scope,
                boot_id=boot_id,
            )
        except OSError as exc:
            last_error = exc
    if last_error is None:
        raise OSError("no candidate ports given")
    raise last_error


def is_authorized(authorization: str | None, token: str) -> bool:
    return authorization == f"Bearer {token}"


def _dispatch(
    workspace: Path,
    method: str,
    raw_path: str,
    body: Any,
    *,
    read_scope: list[str] | None = None,
) -> tuple[dict[str, Any], HTTPStatus]:
    parsed = urlparse(raw_path)
    query = parse_qs(parsed.query)
    path = parsed.path.rstrip("/") or "/"
    if (method, path) not in HTTP_ROUTES:
        status = HTTPStatus.METHOD_NOT_ALLOWED if path in HTTP_PATHS else HTTPStatus.NOT_FOUND
        error = "method not allowed" if status == HTTPStatus.METHOD_NOT_ALLOWED else "not found"
        return {"ok": False, "error": error}, status
    try:
        startup_read_scope = _normalize_read_scope(read_scope)
        if method == "GET":
            return _read(workspace, path, query, startup_read_scope), HTTPStatus.OK
        if method == "POST":
            return _write(workspace, path, body()), HTTPStatus.OK
    except FileNotFoundError as exc:
        return {"ok": False, "error": str(exc)}, HTTPStatus.NOT_FOUND
    except PayloadTooLarge as exc:
        return {"ok": False, "error": str(exc)}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    except Exception as exc:  # noqa: BLE001 -- HTTP boundary returns JSON errors.
        return {"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST
    return {"ok": False, "error": "method not allowed"}, HTTPStatus.METHOD_NOT_ALLOWED


def _read(
    workspace: Path,
    path: str,
    query: dict[str, list[str]],
    startup_read_scope: list[str] | None = None,
) -> dict[str, Any]:
    read_scope = _read_scope(query, startup_read_scope)
    if path == "/status":
        return {"ok": True, **engine_api.read_status(workspace)}
    if path == "/operations":
        return engine_api.read_operations(workspace)
    if path == "/openapi.json":
        return openapi_schema()
    if path == "/requests":
        return engine_api.read_requests(
            workspace, status=_one(query, "status"), read_scope=read_scope
        )
    if path == "/request":
        return engine_api.read_request(workspace, _required(query, "id"), read_scope=read_scope)
    if path == "/attention":
        return engine_api.read_attention(
            workspace,
            status=_one(query, "status"),
            kind=_one(query, "kind"),
            worklist=_one(query, "worklist").lower() == "true",
            read_scope=read_scope,
        )
    if path == "/attention/card":
        return engine_api.read_attention_card(
            workspace, _required(query, "path"), read_scope=read_scope
        )
    if path == "/concepts":
        return engine_api.read_concepts(
            workspace, concept_type=_one(query, "type"), read_scope=read_scope
        )
    if path == "/concept":
        return engine_api.read_concept(workspace, _required(query, "target"), read_scope=read_scope)
    if path == "/work":
        return engine_api.read_work(workspace, _required(query, "id"), read_scope=read_scope)
    if path == "/journal":
        return engine_api.read_journal(
            workspace,
            operation=_one(query, "operation"),
            request_id=_one(query, "request_id"),
            path=_one(query, "path"),
            decision=_one(query, "decision"),
            date=_one(query, "date"),
            limit=_int_query(query, "limit", 50),
            read_scope=read_scope,
        )
    if path == "/journal/event":
        return engine_api.read_journal_event(
            workspace, _required_int(query, "event_id"), read_scope=read_scope
        )
    if path == "/project/slice":
        return engine_api.read_slice(
            workspace, _required(query, "project_path"), read_scope=read_scope
        )
    if path == "/project/draft":
        return engine_api.read_draft(
            workspace, _required(query, "project_path"), read_scope=read_scope
        )
    if path == "/exploration":
        return engine_api.read_exploration(
            workspace, limit=_int_query(query, "limit", 10), read_scope=read_scope
        )
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
        actor="agent",
        agent_identity=str(body.get("agent_identity") or ""),
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


def _required_int(query: dict[str, list[str]], key: str) -> int:
    return _int_value(_required(query, key), key)


def _int_query(query: dict[str, list[str]], key: str, default: int) -> int:
    value = _one(query, key).strip()
    return default if not value else _int_value(value, key)


def _int_value(value: str, key: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{key} must be an integer") from exc
    if parsed < 1:
        raise ValueError(f"{key} must be positive")
    return parsed


def _read_scope(
    query: dict[str, list[str]],
    startup_read_scope: list[str] | None = None,
) -> list[str] | None:
    request_scope = _query_read_scope(query)
    if startup_read_scope is None:
        return request_scope
    if request_scope is None:
        return list(startup_read_scope)
    return _scope_intersection(startup_read_scope, request_scope)


def _query_read_scope(query: dict[str, list[str]]) -> list[str] | None:
    values = [*query.get("read_scope", []), *query.get("scope", [])]
    return _normalize_read_scope(values)


def _normalize_read_scope(values: list[str] | None) -> list[str] | None:
    if not values:
        return None
    scope: list[str] = []
    for raw in values:
        for item in str(raw).split(","):
            if not item.strip():
                continue
            normalized = normalize_path(item)
            if not normalized:
                raise ValueError("http read_scope must be non-root")
            scope.append(normalized)
    return scope or None


def _scope_intersection(maximum: list[str], requested: list[str]) -> list[str]:
    narrowed: set[str] = set()
    for max_scope in maximum:
        for request_scope in requested:
            if within_scope(request_scope, [max_scope]):
                narrowed.add(request_scope)
            elif within_scope(max_scope, [request_scope]):
                narrowed.add(max_scope)
    return sorted(narrowed)


def openapi_schema() -> dict[str, Any]:
    paths: dict[str, Any] = {}
    for action in SURFACE_ACTIONS:
        http = action.get("http")
        if not isinstance(http, dict):
            continue
        method = str(http["method"]).lower()
        path = str(http["path"])
        paths.setdefault(path, {})[method] = {
            "operationId": action["id"],
            "summary": action["summary"],
            "parameters": _openapi_parameters(action, http),
            "responses": {
                "200": {"description": "OK"},
                "400": {"description": "Bad request"},
                "401": {"description": "Unauthorized"},
                "404": {"description": "Not found"},
                "405": {"description": "Method not allowed"},
                "413": {"description": "Request body too large"},
            },
        }
    return {
        "ok": True,
        "openapi": "3.1.0",
        "info": {"title": "Memoria local HTTP", "version": SURFACE_CONTRACT_VERSION},
        "paths": paths,
    }


def _openapi_parameters(action: dict[str, Any], http: dict[str, Any]) -> list[dict[str, Any]]:
    if str(action.get("kind")) != "read":
        return []
    param_specs = (
        http.get("params") if isinstance(http.get("params"), dict) else action.get("params")
    )
    params = []
    for name, spec in (param_specs or {}).items():
        if not isinstance(spec, dict):
            continue
        params.append(
            {
                "name": name,
                "in": "query",
                "required": bool(spec.get("required")),
                "schema": {"type": spec.get("type", "string")},
            }
        )
    if action.get("scope") == "optional-read-scope":
        for name in ("read_scope", "scope"):
            params.append(
                {
                    "name": name,
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string"},
                }
            )
    return params
