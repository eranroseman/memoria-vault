"""Envelope actor flows end-to-end."""

import json

import pytest

from memoria_vault.runtime import state, worker
from tests.helpers import init_cli_workspace


def test_envelope_actor_helper_raises_on_missing() -> None:
    with pytest.raises(ValueError):
        worker._envelope_actor({"request_envelope": {}})
    assert worker._envelope_actor({"request_envelope": {"actor": "agent"}}) == "agent"


def test_agent_enveloped_create_concept_lands_agent_actor(tmp_path, capsys) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    from memoria_vault.engine import api as engine_api

    engine_api.run_operation(
        workspace,
        "create-concept",
        {
            "target_path": "notes/actor-test.md",
            "content": (
                "---\ntype: note\ntitle: Actor test\nmode: claim\n"
                "claim_text: x\n---\n\nBody.\n"
            ),
            "concept_type": "note",
        },
        actor="agent",
    )
    with state.connect(workspace) as conn:
        req = conn.execute(
            "SELECT actor FROM operation_requests WHERE operation_id='create-concept'"
        ).fetchone()
        assert req["actor"] == "agent"
        rows = conn.execute(
            "SELECT payload_json FROM event_log"
            " WHERE json_extract(payload_json,'$.operation')='create-concept'"
            "   AND json_extract(payload_json,'$.actor') IS NOT NULL"
        ).fetchall()
    actors = {json.loads(row["payload_json"]).get("actor") for row in rows}
    assert actors, "create-concept journaled no actor-bearing events"
    assert actors == {"agent"}
