"""Read-API scope walk — U1 checklist letter (c).

Spec: docs/superpowers/specs/2026-07-17-u1-read-api-design.md §6(c).
Driven by the registry's own `scope` field: every read row declaring
optional-read-scope refuses out-of-scope reads under a startup read_scope;
workspace-scope rows are exempt by that same field. Probe targets come from
the floor seed's manifest (tests/floor_lib.py seed_vault / ARG_TABLE) — the
same fixtures the shipped floor sweep (test_floor_sweep_reads.py, letter a)
uses. Walked over HTTP _dispatch: the one transport with a per-request
scope seam; MCP session-scope refusal stays pinned by
test_mcp_transport.py::test_mcp_reads_are_engine_scoped.

Reserved-scope amendment (2026-07-29): the registry also carries one
reserved, non-HTTP optional-read-scope row (`context.read`, U2-owned — no
transport keys). Per the amendment, this walk partitions optional-scope read
rows by transport: the HTTP walk/probes cover only rows with a dict `http`
binding, and the reserved row is asserted as the explicit non-HTTP
complement rather than silently omitted.
"""

from __future__ import annotations

import json
from http import HTTPStatus

import pytest

from memoria_vault.engine.surface_contract import SURFACE_ACTIONS
from memoria_vault.runtime.http_transport import _dispatch
from tests.floor_lib import ARG_TABLE, _fill, seed_vault

# A syntactically valid, non-root scope matching nothing in the seed.
VOID_SCOPE = ["scope-walk-void"]

# Reserved, non-HTTP optional-read-scope rows (2026-07-29 amendment): the
# explicit complement to the registry-derived HTTP set below. There is no
# permanent numeric assertion on either set — a new HTTP route joins
# SCOPED_READ_ROWS/PROBES automatically, and a new reserved row would need
# adding here deliberately.
RESERVED_NON_HTTP_SCOPED_IDS = {"context.read"}

# action id -> (expectation, marker template).
# "refused":  the void-scoped dispatch 404s and the error names the target
#             (letter (j): refusals name the refused thing).
# "excluded": the void-scoped dispatch stays 200 but the seeded marker
#             disappears from the payload (list reads refuse by exclusion —
#             hidden content is indistinguishable from absent content).
PROBES: dict[str, tuple[str, str | None]] = {
    "requests.list": ("excluded", "{request_id}"),
    "requests.get": ("refused", "{request_id}"),
    "attention.list": ("excluded", "{attention_path}"),
    "attention.get": ("refused", "{attention_path}"),
    "concepts.list": ("excluded", "{note_claim}"),
    "concepts.get": ("refused", "{note_claim}"),
    "work.get": ("refused", "{work_id}"),
    "journal.list": ("excluded", "{note_claim}"),
    "journal.get": ("refused", "3"),
    # exploration.list is honest-empty under a void scope; its marker-level
    # filtering is pinned by test_http_transport.py::
    # test_http_transport_exploration_respects_read_scope.
    "exploration.list": ("excluded", None),
    "project.slice.read": ("refused", "{project}"),
    "project.draft.read": ("refused", "{project}"),
}

SCOPED_READ_ROWS = [
    action
    for action in SURFACE_ACTIONS
    if action["kind"] == "read"
    and isinstance(action.get("http"), dict)
    and action["scope"] == "optional-read-scope"
]
WORKSPACE_READ_ROWS = [
    action
    for action in SURFACE_ACTIONS
    if action["kind"] == "read"
    and isinstance(action.get("http"), dict)
    and action["scope"] == "workspace"
]


@pytest.fixture(scope="module")
def vault(tmp_path_factory: pytest.TempPathFactory):
    return seed_vault(tmp_path_factory.mktemp("scope-walk"))


def test_scope_walk_covers_every_scope_declaring_read_row() -> None:
    """The registry is the iterator: a new scope-declaring row without a
    probe entry (or, if non-HTTP, without a reserved-set entry) fails here,
    forcing a deliberate walk extension. Per the 2026-07-29 reserved-scope
    amendment there is no permanent numeric HTTP-row assertion: the
    registry-derived HTTP set plus the reserved non-HTTP set must equal
    every optional-scope read row, and PROBES must equal the live HTTP set."""
    scoped_ids = {
        str(action["id"])
        for action in SURFACE_ACTIONS
        if action["kind"] == "read" and action["scope"] == "optional-read-scope"
    }
    http_scoped_ids = {str(action["id"]) for action in SCOPED_READ_ROWS}
    assert http_scoped_ids | RESERVED_NON_HTTP_SCOPED_IDS == scoped_ids
    assert set(PROBES) == http_scoped_ids


@pytest.mark.parametrize(
    "action_id", sorted(str(action["id"]) for action in SCOPED_READ_ROWS)
)
def test_scope_declaring_row_refuses_out_of_scope_reads(vault, action_id: str) -> None:
    v, manifest = vault
    method, path = _fill(ARG_TABLE[action_id]["http"], manifest)
    expectation, marker_template = PROBES[action_id]
    marker = _fill(marker_template, manifest) if marker_template else None

    open_payload, open_status = _dispatch(v, method, path, dict)
    scoped_payload, scoped_status = _dispatch(v, method, path, dict, read_scope=VOID_SCOPE)

    # The unscoped leg proves the probe target is real, so a refusal below
    # is scope enforcement rather than a missing fixture.
    assert open_status == HTTPStatus.OK
    if expectation == "refused":
        assert scoped_status == HTTPStatus.NOT_FOUND
        assert scoped_payload["ok"] is False
        assert marker in scoped_payload["error"]
    else:
        assert scoped_status == HTTPStatus.OK
        if marker is not None:
            assert marker in json.dumps(open_payload)
            assert marker not in json.dumps(scoped_payload)
        if action_id == "exploration.list":
            assert scoped_payload["exploration"]["items"] == []
            assert scoped_payload["exploration"]["empty"] is True


@pytest.mark.parametrize(
    "action_id", sorted(str(action["id"]) for action in WORKSPACE_READ_ROWS)
)
def test_workspace_scope_row_is_exempt_from_read_scope(vault, action_id: str) -> None:
    v, manifest = vault
    method, path = _fill(ARG_TABLE[action_id]["http"], manifest)

    payload, status = _dispatch(v, method, path, dict, read_scope=VOID_SCOPE)

    assert status == HTTPStatus.OK
    assert payload.get("ok") is True
