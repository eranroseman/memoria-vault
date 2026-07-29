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
def test_disabled_ceiling_never_trips(monkeypatch: pytest.MonkeyPatch, ceiling: str | None) -> None:
    _reset_ledger(monkeypatch)
    if ceiling is None:
        monkeypatch.delenv(operations.TOKEN_CEILING_ENV, raising=False)
    else:
        monkeypatch.setenv(operations.TOKEN_CEILING_ENV, ceiling)
    patch_pydantic_ai(monkeypatch, output="fixture reply")

    for index in range(3):
        assert operations._pydantic_ai_chat(POLICY, RUNNER, f"prompt {index}") == "fixture reply"
    assert operations._TOKEN_LEDGER["total_tokens"] == 192


def test_keyless_direct_chat_uses_inert_placeholder_despite_legacy_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _reset_ledger(monkeypatch)
    monkeypatch.delenv(operations.TOKEN_CEILING_ENV, raising=False)
    monkeypatch.setenv("MEMORIA_MODEL_API_KEY", "legacy-model-secret")
    monkeypatch.setenv("OPENAI_API_KEY", "legacy-openai-secret")
    monkeypatch.setenv("KILOCODE_API_KEY", "legacy-gateway-secret")
    seen = patch_pydantic_ai(monkeypatch, output="fixture reply")

    assert operations._pydantic_ai_chat(POLICY, RUNNER, "prompt") == "fixture reply"
    assert seen["provider_kwargs"] == {
        "base_url": "http://127.0.0.1:11434",
        "api_key": "api-key-not-set",
    }


@pytest.mark.parametrize(
    "failure_site",
    ["loader", "provider", "model", "agent", "dispatch", "output"],
)
def test_direct_chat_sdk_failure_does_not_reflect_configured_key(
    monkeypatch: pytest.MonkeyPatch,
    failure_site: str,
) -> None:
    _reset_ledger(monkeypatch)
    monkeypatch.delenv(operations.TOKEN_CEILING_ENV, raising=False)
    configured_key = "gateway-key"
    monkeypatch.setenv("KILOCODE_API_KEY", configured_key)

    class FakeProvider:
        def __init__(self, **kwargs: object) -> None:
            if failure_site == "provider":
                raise RuntimeError(f"provider rejected {configured_key}")

    class FakeModel:
        def __init__(self, model_name: str, *, provider: object) -> None:
            if failure_site == "model":
                raise RuntimeError(f"model rejected {configured_key}")

    class FakeResult:
        @property
        def output(self) -> str:
            if failure_site == "output":
                raise RuntimeError(f"output rejected {configured_key}")
            return "fixture reply"

    class FakeAgent:
        def __init__(self, model: object) -> None:
            if failure_site == "agent":
                raise RuntimeError(f"agent rejected {configured_key}")

        def run_sync(self, prompt: str, *, model_settings: dict[str, object]) -> FakeResult:
            if failure_site == "dispatch":
                raise RuntimeError(f"dispatch rejected {configured_key}")
            return FakeResult()

    def failing_loader() -> tuple[object, object, object]:
        if failure_site == "loader":
            raise RuntimeError(f"loader rejected {configured_key}")
        return FakeAgent, FakeModel, FakeProvider

    monkeypatch.setattr(
        "memoria_vault.runtime.operations._load_pydantic_ai_openai",
        failing_loader,
    )
    runner = {
        **RUNNER,
        "provider": "gateway",
        "base_url": "https://gateway.test/v1",
        "key_env": "KILOCODE_API_KEY",
    }
    policy = {**POLICY, "allowed_network": ["https://gateway.test/v1"]}

    with pytest.raises(RuntimeError) as exc_info:
        operations._pydantic_ai_chat(policy, runner, "prompt")

    assert str(exc_info.value) == "pydantic-ai model request failed"
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__suppress_context__ is True
    assert configured_key not in str(exc_info.value)


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
