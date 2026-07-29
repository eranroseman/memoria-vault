"""Token-ceiling circuit breaker for live model dispatch."""

from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace

import pytest

from memoria_vault.runtime import operations
from tests.helpers import patch_pydantic_ai

POLICY = {
    "operation_id": "compile-source-digest",
    "allowed_network": ["http://127.0.0.1:11434"],
}
RUNNER = {
    "mode": "live",
    "runner": "pydantic-ai",
    "provider": "local",
    "model": "ceiling-test-model",
    "base_url": "http://127.0.0.1:11434",
    "key_env": None,
    "params": {"temperature": 0, "max_tokens": 64},
}


def _reset_ledger(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(operations._TOKEN_LEDGER, "total_tokens", 0)


def test_ceiling_trips_after_budget_is_spent(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_ledger(monkeypatch)
    monkeypatch.setenv(operations.TOKEN_CEILING_ENV, "100")
    seen = patch_pydantic_ai(monkeypatch, output="fixture reply")

    assert operations._pydantic_ai_chat(POLICY, RUNNER, "prompt one") == "fixture reply"
    assert operations._TOKEN_LEDGER["total_tokens"] == 64

    operations._pydantic_ai_chat(POLICY, RUNNER, "prompt two")
    assert operations._TOKEN_LEDGER["total_tokens"] == 128

    with pytest.raises(RuntimeError, match="model token ceiling reached"):
        operations._pydantic_ai_chat(POLICY, RUNNER, "prompt three")
    assert seen["prompt"] == "prompt two"
    assert len(seen["models"]) == 2


def test_ceiling_refuses_at_the_exact_boundary_before_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _reset_ledger(monkeypatch)
    monkeypatch.setenv(operations.TOKEN_CEILING_ENV, "64")
    seen = patch_pydantic_ai(monkeypatch, output="fixture reply")

    assert operations._pydantic_ai_chat(POLICY, RUNNER, "prompt one") == "fixture reply"
    assert operations._TOKEN_LEDGER["total_tokens"] == 64

    with pytest.raises(RuntimeError, match="model token ceiling reached"):
        operations._pydantic_ai_chat(POLICY, RUNNER, "prompt two")
    assert seen["prompt"] == "prompt one"
    assert len(seen["models"]) == 1


@pytest.mark.parametrize("ceiling", [None, ""])
def test_disabled_ceiling_never_trips(
    monkeypatch: pytest.MonkeyPatch, ceiling: str | None
) -> None:
    _reset_ledger(monkeypatch)
    if ceiling is None:
        monkeypatch.delenv(operations.TOKEN_CEILING_ENV, raising=False)
    else:
        monkeypatch.setenv(operations.TOKEN_CEILING_ENV, ceiling)
    patch_pydantic_ai(monkeypatch, output="fixture reply")

    for index in range(3):
        assert operations._pydantic_ai_chat(POLICY, RUNNER, f"prompt {index}") == "fixture reply"
    assert operations._TOKEN_LEDGER["total_tokens"] == 192


def test_reported_usage_is_preferred_over_max_tokens_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _reset_ledger(monkeypatch)
    monkeypatch.delenv(operations.TOKEN_CEILING_ENV, raising=False)

    class UsageAgent:
        def __init__(self, model: object) -> None:
            self.model = model

        def run_sync(self, prompt: str, *, model_settings: dict) -> SimpleNamespace:
            return SimpleNamespace(
                output="usage reply",
                usage=lambda: SimpleNamespace(total_tokens=7),
            )

    class Passthrough:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

    monkeypatch.setattr(
        "memoria_vault.runtime.operations._load_pydantic_ai_openai",
        lambda: (UsageAgent, lambda model, provider: model, Passthrough),
    )

    assert operations._pydantic_ai_chat(POLICY, RUNNER, "prompt") == "usage reply"
    assert operations._TOKEN_LEDGER["total_tokens"] == 7


@pytest.mark.parametrize(
    "usage",
    [
        lambda: SimpleNamespace(total_tokens=True),
        lambda: (_ for _ in ()).throw(RuntimeError("usage unavailable")),
    ],
    ids=["boolean-total", "raising-accessor"],
)
def test_invalid_reported_usage_falls_back_to_max_tokens(
    monkeypatch: pytest.MonkeyPatch, usage: Callable[[], object]
) -> None:
    _reset_ledger(monkeypatch)
    monkeypatch.delenv(operations.TOKEN_CEILING_ENV, raising=False)

    class UsageAgent:
        def __init__(self, model: object) -> None:
            self.model = model

        def run_sync(self, prompt: str, *, model_settings: dict) -> SimpleNamespace:
            return SimpleNamespace(output="usage reply", usage=usage)

    class Passthrough:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

    monkeypatch.setattr(
        "memoria_vault.runtime.operations._load_pydantic_ai_openai",
        lambda: (UsageAgent, lambda model, provider: model, Passthrough),
    )

    assert operations._pydantic_ai_chat(POLICY, RUNNER, "prompt") == "usage reply"
    assert operations._TOKEN_LEDGER["total_tokens"] == 64


def test_non_integer_ceiling_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_ledger(monkeypatch)
    monkeypatch.setenv(operations.TOKEN_CEILING_ENV, "not-a-number")
    seen = patch_pydantic_ai(monkeypatch, output="fixture reply")

    with pytest.raises(ValueError, match="must be an integer"):
        operations._pydantic_ai_chat(POLICY, RUNNER, "prompt")
    assert seen == {}
