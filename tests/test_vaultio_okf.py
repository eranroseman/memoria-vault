"""OKF v0.2 actor grammar (spec §7): human:<id>, <producer>/<version>, process:<id>."""

from memoria_vault.runtime.vaultio import okf_actor, okf_verified_actor


def test_pi_hand_authored_is_human_actor() -> None:
    assert okf_actor("pi") == "human:pi"


def test_pi_authority_machine_authored_is_not_human() -> None:
    assert okf_actor("pi", agent_identity="floor", machine_authored=True) == "floor/unversioned"


def test_operation_actor_is_process_with_operation_id() -> None:
    assert okf_actor("operation", operation_id="capture-bibtex-source") == "process:capture-bibtex-source"


def test_integrity_actor_without_operation_id_falls_back_to_actor() -> None:
    assert okf_actor("integrity") == "process:integrity"


def test_agent_identity_with_slash_passes_through() -> None:
    assert okf_actor("agent", agent_identity="reference_agent/gemini-2.5-pro") == "reference_agent/gemini-2.5-pro"


def test_agent_identity_without_slash_gets_unversioned() -> None:
    assert okf_actor("agent", agent_identity="floor") == "floor/unversioned"


def test_agent_without_identity_is_generic() -> None:
    assert okf_actor("agent") == "agent/unversioned"


def test_verified_actor_pi_is_human_even_when_relayed() -> None:
    assert okf_verified_actor("pi") == "human:pi"


def test_verified_actor_operation_is_process() -> None:
    assert okf_verified_actor("operation", operation_id="mark-checked") == "process:mark-checked"
