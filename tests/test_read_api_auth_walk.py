"""Read-API auth walk — U1 checklist letter (b).

Spec: docs/superpowers/specs/2026-07-17-u1-read-api-design.md §6(b), §2, §5.
Every HTTP_ROUTES route requires the per-boot bearer token — shipped
behavior (http_transport.py Handler._handle), pinned here registry-driven
via http_routes() so new rows join the walk automatically. The sole
unauthenticated endpoint is the BOOT-owned GET /v1/status liveness probe,
outside the registry; its test is order-tolerant (skips until the surfaces
bootstrap plan's BOOT tasks serve the route).
"""

from __future__ import annotations

import http.client
import json
import threading
from collections.abc import Iterator
from http import HTTPStatus
from pathlib import Path

import pytest

from memoria_vault.cli import main
from memoria_vault.engine.surface_contract import http_routes
from memoria_vault.runtime.http_transport import make_http_server

TOKEN = "auth-walk-token"


@pytest.fixture(scope="module")
def walk_workspace(tmp_path_factory: pytest.TempPathFactory) -> Path:
    workspace = tmp_path_factory.mktemp("auth-walk") / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    return workspace


@pytest.fixture(scope="module")
def server_address(walk_workspace: Path) -> Iterator[tuple[str, int]]:
    server = make_http_server(walk_workspace, host="127.0.0.1", port=0, token=TOKEN)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield ("127.0.0.1", int(server.server_address[1]))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _request(
    address: tuple[str, int], method: str, path: str, token: str | None
) -> tuple[int, dict]:
    connection = http.client.HTTPConnection(*address, timeout=10)
    headers: dict[str, str] = {}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    body = None
    if method == "POST":
        body = b"{}"
        headers["Content-Type"] = "application/json"
    try:
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        return response.status, json.loads(response.read().decode("utf-8"))
    finally:
        connection.close()


@pytest.mark.parametrize(("method", "path"), sorted(http_routes()))
def test_every_registry_route_requires_bearer_token(
    server_address: tuple[str, int], method: str, path: str
) -> None:
    missing_status, missing = _request(server_address, method, path, token=None)
    wrong_status, wrong = _request(server_address, method, path, token=f"wrong-{TOKEN}")
    with_token_status, _payload = _request(server_address, method, path, token=TOKEN)

    assert missing_status == HTTPStatus.UNAUTHORIZED
    assert missing["ok"] is False
    assert missing["error"].startswith("unauthorized")
    assert wrong_status == HTTPStatus.UNAUTHORIZED
    assert wrong["ok"] is False
    assert wrong["error"].startswith("unauthorized")
    # The token is the only gate at the door: with it, dispatch proceeds
    # (missing params may still 400/404, but never 401).
    assert with_token_status != HTTPStatus.UNAUTHORIZED


def test_v1_status_liveness_probe_is_unauthenticated_once_boot_lands(
    server_address: tuple[str, int],
) -> None:
    """(b)-exception, BOOT-owned. Owner: the surfaces bootstrap plan's BOOT
    tasks (docs/superpowers/plans/2026-07-15-surfaces-bootstrap-and-plugins.md)
    serve GET /v1/status pre-dispatch, outside HTTP_ROUTES. Order-tolerant:
    while absent (404 even with the token), skip with the dependency named."""
    probe_status, _probe = _request(server_address, "GET", "/v1/status", token=TOKEN)
    if probe_status == HTTPStatus.NOT_FOUND:
        pytest.skip(
            "GET /v1/status not served yet - lands with the surfaces bootstrap "
            "plan's BOOT tasks (2026-07-15-surfaces-bootstrap-and-plugins.md)"
        )
    status, payload = _request(server_address, "GET", "/v1/status", token=None)
    assert status == HTTPStatus.OK
    assert payload.get("ok") is True
