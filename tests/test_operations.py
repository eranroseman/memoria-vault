from __future__ import annotations

import shutil
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.capture import capture_source
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.operations import (
    compile_source_digest,
    load_operation_policy,
    load_runner_provider_config,
    record_copi_interview_turn,
    require_allowed_network,
    resolve_operation_runner,
    validate_operation_policy,
)
from memoria_vault.runtime.vaultio import read_frontmatter

ROOT = Path(__file__).resolve().parent.parent


def workspace(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "vault-template/.memoria/schemas", tmp_path / ".memoria/schemas")
    shutil.copytree(ROOT / "vault-template/.memoria/config", tmp_path / ".memoria/config")
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "operations@example.invalid")
    git(tmp_path, "config", "user.name", "Operations")
    return tmp_path


def git(vault: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=vault,
        check=False,
        text=True,
        capture_output=True,
    )
    if proc.returncode:
        raise AssertionError(proc.stderr or proc.stdout)
    return proc.stdout.strip()


def compile_policy(**updates):
    policy = deepcopy(load_operation_policy(Path(), "compile-source-digest"))
    if "model" in updates:
        model = updates.pop("model")
        policy["runner"]["test"]["model"] = model
    if "provider" in updates:
        provider = updates.pop("provider")
        policy["runner"]["test"]["provider"] = provider
    policy.update(updates)
    return policy


def patch_compile_policy(monkeypatch: pytest.MonkeyPatch, **updates) -> dict:
    policy = compile_policy(**updates)
    monkeypatch.setattr(
        "memoria_vault.runtime.operations.load_operation_policy",
        lambda _vault, _operation_id: policy,
    )
    return policy


def write_runner_provider_config(vault: Path, *, local_url: str = "http://model.test/v1") -> None:
    config = vault / ".memoria/config/providers.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        "\n".join(
            [
                "version: 1",
                "runner_providers:",
                f"  local: {{url: {local_url}, key_env: null}}",
                "  gateway: {url: https://gateway.test/v1, key_env: KILOCODE_API_KEY}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_load_operation_policy_requires_io_schema_shape() -> None:
    policy = compile_policy(io_schema={"input": "checked_work_id", "output": []})
    with pytest.raises(
        ValueError,
        match=r"compile-source-digest io_schema\.output must be a non-empty string",
    ):
        validate_operation_policy("compile-source-digest", policy)


def test_allowed_network_rejects_host_prefix_bypass() -> None:
    policy = {
        "operation_id": "net-test",
        "allowed_network": ["https://api.openalex.org/", "http://"],
    }

    require_allowed_network(policy, "https://api.openalex.org/works/W1")
    require_allowed_network(policy, "http://example.test/source")
    with pytest.raises(PermissionError, match=r"api\.openalex\.org\.evil"):
        require_allowed_network(policy, "https://api.openalex.org.evil/works/W1")


def test_runner_provider_config_rejects_legacy_root_providers(tmp_path: Path) -> None:
    config = tmp_path / ".memoria/config/providers.yaml"
    config.parent.mkdir(parents=True)
    config.write_text(
        """version: 1
providers:
  local: {url: http://model.test/v1, key_env: null}
  gateway: {url: https://gateway.test/v1, key_env: KILOCODE_API_KEY}
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="runner_providers must be a map"):
        load_runner_provider_config(tmp_path)


def test_compile_source_digest_traces_model_call_and_stages_hub_suggestions(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Alpha content about framing, methods, outcomes, gaps, and impact.",
        machine="capture-machine",
    )
    curated_hub = vault / "knowledge/hubs/framing.md"
    curated_hub.parent.mkdir(parents=True)
    curated_text = (
        "---\ntype: hub\ncheck_status: checked\ntitle: Framing\n"
        "description: Human curation.\n---\n# Framing\n\nHuman text.\n"
    )
    curated_hub.write_text(curated_text, encoding="utf-8")

    result = compile_source_digest(
        vault,
        "source-alpha",
        ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
        machine="op-machine",
        run_id="compile-alpha",
    )

    digest = vault / "knowledge/works/source-alpha.md"
    digest_fm = read_frontmatter(digest)
    assert digest_fm["type"] == "work"
    assert "check_status" not in digest_fm
    assert digest_fm["work_id"] == "source-alpha"
    assert state.concept_check_status(vault, "knowledge/works/source-alpha.md") == "checked"
    assert result["derived"]["inputs"][0]["id"] == "catalog/sources/source-alpha"
    assert result["hub_paths"] == [
        "knowledge/hubs/methods.md",
        "knowledge/hubs/outcomes.md",
        "knowledge/hubs/gaps.md",
        "knowledge/hubs/impact.md",
    ]
    assert len(result["hub_suggestions"]) == 1
    assert curated_hub.read_text(encoding="utf-8") == curated_text

    staged_hub = vault / ".memoria/staging/knowledge/hubs/framing.md"
    assert staged_hub.is_file()
    assert read_frontmatter(staged_hub)["tags"] == ["suggestion"]
    promoted_hub = vault / "knowledge/hubs/methods.md"
    promoted_hub_fm = read_frontmatter(promoted_hub)
    assert "check_status" not in promoted_hub_fm
    assert promoted_hub_fm["tag"] == "methods"
    assert state.concept_check_status(vault, "knowledge/hubs/methods.md") == "checked"

    events = list(iter_jsonl(vault / "journal/op-machine.jsonl"))
    assert [event["event"] for event in events] == [
        "run",
        "model_call",
        "derived",
        "check-fired",
        "derived",
        "derived",
        "check-fired",
        "derived",
        "check-fired",
        "derived",
        "check-fired",
        "derived",
        "check-fired",
        "run",
    ]
    assert events[1]["runner"] == "pydantic-ai"
    assert events[1]["mode"] == "test"
    assert events[1]["provider"] == "local"
    assert events[1]["model"] == "deterministic-fixture"
    assert events[1]["model_params"] == {"temperature": 0}
    assert events[1]["prompt_hash"].startswith("sha256:")
    assert events[-1]["suggestions"] == result["hub_suggestions"]
    assert events[-1]["outputs"] == ["knowledge/works/source-alpha.md", *result["hub_paths"]]

    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {
        state.JOURNAL_HEAD_REL,
        "knowledge/works/source-alpha.md",
        "knowledge/hubs/gaps.md",
        "knowledge/hubs/impact.md",
        "knowledge/hubs/methods.md",
        "knowledge/hubs/outcomes.md",
    }


def test_compile_source_digest_rejects_legacy_source_markdown_without_catalog_row(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    legacy = vault / "catalog/sources/legacy/source.md"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text(
        "---\n"
        "type: source\n"
        "check_status: checked\n"
        "title: Legacy Source\n"
        "description: Should not be treated as a Work row.\n"
        "source_id: legacy\n"
        "content_path: .memoria/blobs/source-content/legacy/content.txt\n"
        "text_status: full-text\n"
        "---\n"
        "# Legacy Source\n",
        encoding="utf-8",
    )
    content = vault / ".memoria/blobs/source-content/legacy/content.txt"
    content.parent.mkdir(parents=True, exist_ok=True)
    content.write_text("Legacy source text.\n", encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="catalog/sources/legacy"):
        compile_source_digest(
            vault,
            "legacy",
            ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
            machine="op-machine",
            run_id="compile-legacy",
        )


@pytest.mark.parametrize("text_status", ["metadata-only", "abstract-only"])
def test_compile_source_digest_blocks_checked_sources_without_full_text(
    tmp_path: Path, text_status: str
) -> None:
    vault = workspace(tmp_path)
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Title or abstract fallback only.",
        text_status=text_status,
        machine="capture-machine",
    )

    with pytest.raises(ValueError, match="checked digest requires full-text source content") as exc:
        compile_source_digest(
            vault,
            "source-alpha",
            ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
            machine="op-machine",
            run_id="compile-alpha",
        )

    assert f"text_status is {text_status}" in str(exc.value)
    assert "attention_path is inbox/flag-digest-full-text-source-alpha.md" in str(exc.value)
    assert not (vault / "knowledge/works/source-alpha.md").exists()
    attention = vault / "inbox/flag-digest-full-text-source-alpha.md"
    attention_fm = read_frontmatter(attention)
    assert attention_fm["projection"] == "attention"
    assert attention_fm["attention_kind"] == "flag"
    assert attention_fm["attention_status"] == "open"
    assert attention_fm["target"] == "catalog/sources/source-alpha"
    assert attention_fm["raised_by"] == "compile-source-digest"
    events = list(iter_jsonl(vault / "journal/op-machine.jsonl"))
    assert events[-1]["check"] == "source-full-text"
    assert events[-1]["attention_path"] == "inbox/flag-digest-full-text-source-alpha.md"


def test_compile_source_digest_rejects_unsupported_required_promotion_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = workspace(tmp_path)
    patch_compile_policy(monkeypatch, required_checks=["later-integrity"])
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Alpha content about framing, methods, outcomes, gaps, and impact.",
        machine="capture-machine",
    )

    with pytest.raises(
        ValueError,
        match="compile-source-digest cannot promote checked Concepts: "
        "unsupported promotion checks: later-integrity",
    ):
        compile_source_digest(
            vault,
            "source-alpha",
            ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
            machine="op-machine",
        )

    assert not (vault / "knowledge/works/source-alpha.md").exists()


def test_copi_interview_turn_feeds_digest_inputs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Alpha content about framing, methods, outcomes, gaps, and impact.",
        machine="capture-machine",
    )

    interview = record_copi_interview_turn(
        vault,
        "source-alpha",
        "The PI cares about the methods caveat.",
        project_id="knowledge/projects/project-alpha.md",
        machine="copi-machine",
    )
    result = compile_source_digest(
        vault,
        "source-alpha",
        ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
        machine="op-machine",
    )

    digest = vault / result["digest_path"]
    assert interview["event"]["source_id"] == "source-alpha"
    assert result["interview_count"] == 1
    assert "The PI cares about the methods caveat." in digest.read_text(encoding="utf-8")
    assert interview["event"]["turn_sha256"] in {
        row["sha256"] for row in result["derived"]["inputs"] if row.get("role") == "copi-interview"
    }
    committed = set(
        git(vault, "show", "--name-only", "--format=", interview["commit"]).splitlines()
    )
    assert committed == {state.JOURNAL_HEAD_REL}


def test_compile_source_digest_can_use_pydantic_ai_runner(tmp_path: Path, monkeypatch) -> None:
    vault = workspace(tmp_path)
    write_runner_provider_config(vault)
    patch_compile_policy(
        monkeypatch,
        allowed_network=["http://model.test/v1"],
        model="memoria-test-model",
    )
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Alpha content about framing, methods, outcomes, gaps, and impact.",
        machine="capture-machine",
    )
    seen = {}

    class FakeProvider:
        def __init__(self, **kwargs):
            seen["provider_kwargs"] = kwargs

    class FakeModel:
        def __init__(self, model_name, *, provider):
            seen["model_name"] = model_name
            seen["provider"] = provider

    class FakeAgent:
        def __init__(self, model):
            seen["model"] = model

        def run_sync(self, prompt, *, model_settings):
            seen["prompt"] = prompt
            seen["model_settings"] = model_settings
            return type(
                "Result",
                (),
                {
                    "output": (
                        "## Synthesis\n\nModel-written Alpha framing outcomes.\n\n"
                        "## Hub suggestions\n\n- Framing\n"
                    )
                },
            )()

    def fake_loader():
        return FakeAgent, FakeModel, FakeProvider

    monkeypatch.setenv("MEMORIA_MODEL_BASE_URL", "http://model.test/v1")
    monkeypatch.setenv("MEMORIA_MODEL_API_KEY", "test-key")
    monkeypatch.setattr("memoria_vault.runtime.operations._load_pydantic_ai_openai", fake_loader)

    result = compile_source_digest(
        vault,
        "source-alpha",
        ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
        machine="op-machine",
    )

    assert seen["provider_kwargs"] == {"base_url": "http://model.test/v1", "api_key": "test-key"}
    assert seen["model_name"] == "memoria-test-model"
    assert seen["model"] is not None
    assert seen["model_settings"]["temperature"] == 0
    assert seen["model_settings"]["max_tokens"] == 2048
    assert seen["model_settings"]["timeout"] == 90.0
    assert "Alpha content" in seen["prompt"]
    assert "## Synthesis" in seen["prompt"]
    assert "Model-written Alpha framing outcomes." in (vault / result["digest_path"]).read_text(
        encoding="utf-8"
    )
    events = list(iter_jsonl(vault / "journal/op-machine.jsonl"))
    assert events[1]["model"] == "memoria-test-model"


@pytest.mark.parametrize("runner", ["local", "hermes", "raw-http"])
def test_operation_policy_rejects_unsupported_runner_values(runner: str) -> None:
    policy = compile_policy(runner=runner)
    with pytest.raises(ValueError, match="runner must define test and live branches"):
        validate_operation_policy("compile-source-digest", policy)


def test_operation_policy_requires_both_runner_branches() -> None:
    policy = compile_policy()
    del policy["runner"]["live"]

    with pytest.raises(ValueError, match="runner missing branches: live"):
        validate_operation_policy("compile-source-digest", policy)


def test_resolve_operation_runner_selects_declared_live_branch(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    write_runner_provider_config(vault)
    policy = compile_policy()
    policy["runner"]["live"]["model"] = "gateway-model"

    runner = resolve_operation_runner(vault, policy, "live")

    assert runner["mode"] == "live"
    assert runner["provider"] == "gateway"
    assert runner["model"] == "gateway-model"
    assert runner["base_url"] == "https://gateway.test/v1"


def test_resolve_operation_runner_rejects_undeclared_provider(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    write_runner_provider_config(vault)
    policy = compile_policy()
    policy["runner"]["test"]["provider"] = "shadow"

    with pytest.raises(ValueError, match=r"runner\.test provider must be local or gateway"):
        validate_operation_policy("compile-source-digest", policy)


def test_compile_source_digest_rejects_nonconforming_pydantic_ai_output(
    tmp_path: Path, monkeypatch
) -> None:
    vault = workspace(tmp_path)
    write_runner_provider_config(vault)
    patch_compile_policy(
        monkeypatch,
        allowed_network=["http://model.test/v1"],
        model="memoria-test-model",
    )
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Alpha content about framing, methods, outcomes, gaps, and impact.",
        machine="capture-machine",
    )

    class FakeAgent:
        def __init__(self, _model):
            pass

        def run_sync(self, _prompt, *, model_settings):
            return type("Result", (), {"output": "Loose summary only."})()

    class FakeModel:
        def __init__(self, _model_name, *, provider):
            pass

    class FakeProvider:
        def __init__(self, **_kwargs):
            pass

    monkeypatch.setenv("MEMORIA_MODEL_BASE_URL", "http://model.test/v1")
    monkeypatch.setattr(
        "memoria_vault.runtime.operations._load_pydantic_ai_openai",
        lambda: (FakeAgent, FakeModel, FakeProvider),
    )

    with pytest.raises(ValueError, match="digest output must include ## Synthesis"):
        compile_source_digest(
            vault,
            "source-alpha",
            ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
            machine="op-machine",
        )

    assert not (vault / "knowledge/works/source-alpha.md").exists()


def test_compile_source_digest_rejects_ungrounded_pydantic_ai_output(
    tmp_path: Path, monkeypatch
) -> None:
    vault = workspace(tmp_path)
    write_runner_provider_config(vault)
    patch_compile_policy(
        monkeypatch,
        allowed_network=["http://model.test/v1"],
        model="memoria-test-model",
    )
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Alpha content about framing, methods, outcomes, gaps, and impact.",
        machine="capture-machine",
    )

    class FakeAgent:
        def __init__(self, _model):
            pass

        def run_sync(self, _prompt, *, model_settings):
            return type(
                "Result",
                (),
                {
                    "output": (
                        "## Synthesis\n\nCompletely unrelated banana prose.\n\n"
                        "## Hub suggestions\n\n- unrelated\n"
                    )
                },
            )()

    class FakeModel:
        def __init__(self, _model_name, *, provider):
            pass

    class FakeProvider:
        def __init__(self, **_kwargs):
            pass

    monkeypatch.setenv("MEMORIA_MODEL_BASE_URL", "http://model.test/v1")
    monkeypatch.setattr(
        "memoria_vault.runtime.operations._load_pydantic_ai_openai",
        lambda: (FakeAgent, FakeModel, FakeProvider),
    )

    with pytest.raises(ValueError, match="source-grounding smoke check"):
        compile_source_digest(
            vault,
            "source-alpha",
            ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
            machine="op-machine",
        )

    assert not (vault / "knowledge/works/source-alpha.md").exists()
