from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from memoria_vault.runtime.capture import capture_source
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.operations import (
    compile_source_digest,
    load_operation_policy,
    record_copi_interview_turn,
)
from memoria_vault.runtime.vaultio import read_frontmatter

ROOT = Path(__file__).resolve().parent.parent


def workspace(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "vault-template/.memoria/schemas", tmp_path / ".memoria/schemas")
    shutil.copytree(ROOT / "vault-template/capabilities", tmp_path / "capabilities")
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


def test_load_operation_policy_requires_io_schema_shape(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    policy = vault / "capabilities/operations/compile-source-digest.md"
    policy.write_text(
        policy.read_text(encoding="utf-8").replace(
            "  output: digest_plus_hubs_and_suggestions",
            "  output: []",
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=r"compile-source-digest io_schema\.output must be a non-empty string",
    ):
        load_operation_policy(vault, "compile-source-digest")


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

    digest = vault / "knowledge/digests/source-alpha.md"
    digest_fm = read_frontmatter(digest)
    assert digest_fm["type"] == "digest"
    assert digest_fm["check_status"] == "checked"
    assert digest_fm["source_id"] == "catalog/sources/source-alpha"
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
    assert read_frontmatter(staged_hub)["check_status"] == "unchecked"
    assert read_frontmatter(staged_hub)["tags"] == ["suggestion"]
    promoted_hub = vault / "knowledge/hubs/methods.md"
    assert read_frontmatter(promoted_hub)["check_status"] == "checked"

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
    assert events[1]["model"] == "deterministic-fixture"
    assert events[-1]["suggestions"] == result["hub_suggestions"]
    assert events[-1]["outputs"] == ["knowledge/digests/source-alpha.md", *result["hub_paths"]]

    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {
        "journal/op-machine.jsonl",
        "knowledge/digests/source-alpha.md",
        "knowledge/hubs/gaps.md",
        "knowledge/hubs/impact.md",
        "knowledge/hubs/methods.md",
        "knowledge/hubs/outcomes.md",
    }


def test_compile_source_digest_rejects_unsupported_required_promotion_check(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    policy = vault / "capabilities/operations/compile-source-digest.md"
    policy.write_text(
        policy.read_text(encoding="utf-8").replace(
            "  - memoria-runtime",
            "  - later-integrity",
        ),
        encoding="utf-8",
    )
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

    assert not (vault / "knowledge/digests/source-alpha.md").exists()


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
    assert result["interview_count"] == 1
    assert "The PI cares about the methods caveat." in digest.read_text(encoding="utf-8")
    assert interview["event"]["turn_sha256"] in {
        row["sha256"] for row in result["derived"]["inputs"] if row.get("role") == "copi-interview"
    }
    committed = set(
        git(vault, "show", "--name-only", "--format=", interview["commit"]).splitlines()
    )
    assert committed == {"journal/copi-machine.jsonl"}


def test_compile_source_digest_can_use_pydantic_ai_runner(tmp_path: Path, monkeypatch) -> None:
    vault = workspace(tmp_path)
    policy = vault / "capabilities/operations/compile-source-digest.md"
    policy.write_text(
        policy.read_text(encoding="utf-8")
        .replace("allowed_network: []", "allowed_network:\n  - http://model.test/v1")
        .replace("model: deterministic-fixture", "model: memoria-test-model"),
        encoding="utf-8",
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


@pytest.mark.parametrize("runner", ["hermes", "raw-http"])
def test_operation_policy_rejects_unsupported_runner_values(tmp_path: Path, runner: str) -> None:
    vault = workspace(tmp_path)
    policy = vault / "capabilities/operations/compile-source-digest.md"
    policy.write_text(
        policy.read_text(encoding="utf-8").replace("runner: pydantic-ai", f"runner: {runner}"),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=f"unsupported operation runner: {runner}"):
        load_operation_policy(vault, "compile-source-digest")


def test_compile_source_digest_rejects_nonconforming_pydantic_ai_output(
    tmp_path: Path, monkeypatch
) -> None:
    vault = workspace(tmp_path)
    policy = vault / "capabilities/operations/compile-source-digest.md"
    policy.write_text(
        policy.read_text(encoding="utf-8")
        .replace("allowed_network: []", "allowed_network:\n  - http://model.test/v1")
        .replace("model: deterministic-fixture", "model: memoria-test-model"),
        encoding="utf-8",
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

    assert not (vault / "knowledge/digests/source-alpha.md").exists()


def test_compile_source_digest_rejects_ungrounded_pydantic_ai_output(
    tmp_path: Path, monkeypatch
) -> None:
    vault = workspace(tmp_path)
    policy = vault / "capabilities/operations/compile-source-digest.md"
    policy.write_text(
        policy.read_text(encoding="utf-8")
        .replace("allowed_network: []", "allowed_network:\n  - http://model.test/v1")
        .replace("model: deterministic-fixture", "model: memoria-test-model"),
        encoding="utf-8",
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

    assert not (vault / "knowledge/digests/source-alpha.md").exists()
