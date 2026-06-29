from __future__ import annotations

import json
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
    assert events[1]["runner"] == "direct_api"
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


def test_compile_source_digest_can_use_direct_api_runner(tmp_path: Path, monkeypatch) -> None:
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

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": (
                                    "## Synthesis\n\nModel-written Alpha framing outcomes.\n\n"
                                    "## Hub suggestions\n\n- Framing\n"
                                )
                            }
                        }
                    ]
                }
            ).encode()

    def fake_urlopen(req, timeout):
        seen["url"] = req.full_url
        seen["timeout"] = timeout
        seen["auth"] = req.get_header("Authorization")
        seen["payload"] = json.loads(req.data.decode())
        return Response()

    monkeypatch.setenv("MEMORIA_MODEL_BASE_URL", "http://model.test/v1")
    monkeypatch.setenv("MEMORIA_MODEL_API_KEY", "test-key")
    monkeypatch.setattr("memoria_vault.runtime.operations.request.urlopen", fake_urlopen)

    result = compile_source_digest(
        vault,
        "source-alpha",
        ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
        machine="op-machine",
    )

    assert seen["url"] == "http://model.test/v1/chat/completions"
    assert seen["auth"] == "Bearer test-key"
    assert seen["payload"]["model"] == "memoria-test-model"
    assert "Alpha content" in seen["payload"]["messages"][0]["content"]
    assert "## Synthesis" in seen["payload"]["messages"][0]["content"]
    assert "Model-written Alpha framing outcomes." in (vault / result["digest_path"]).read_text(
        encoding="utf-8"
    )
    events = list(iter_jsonl(vault / "journal/op-machine.jsonl"))
    assert events[1]["model"] == "memoria-test-model"


def test_compile_source_digest_can_use_hermes_runner(tmp_path: Path, monkeypatch) -> None:
    vault = workspace(tmp_path)
    policy = vault / "capabilities/operations/compile-source-digest.md"
    policy.write_text(
        policy.read_text(encoding="utf-8")
        .replace("allowed_network: []", "allowed_network:\n  - hermes-config")
        .replace("runner: direct_api", "runner: hermes")
        .replace("model: deterministic-fixture", "model: memoria-hermes-model"),
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

    class FakeHermesAgent:
        def __init__(self, **kwargs):
            seen["kwargs"] = kwargs

        def chat(self, prompt):
            seen["prompt"] = prompt
            return (
                "## Synthesis\n\nHermes-written Alpha framing outcomes.\n\n"
                "## Hub suggestions\n\n- Framing\n"
            )

    monkeypatch.setattr(
        "memoria_vault.runtime.operations._hermes_agent_class",
        lambda: FakeHermesAgent,
    )

    result = compile_source_digest(
        vault,
        "source-alpha",
        ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
        machine="op-machine",
    )

    assert seen["kwargs"]["model"] == "memoria-hermes-model"
    assert seen["kwargs"]["enabled_toolsets"] == []
    assert seen["kwargs"]["quiet_mode"] is True
    assert seen["kwargs"]["skip_context_files"] is True
    assert seen["kwargs"]["skip_memory"] is True
    assert seen["kwargs"]["max_iterations"] == 10
    assert "Alpha content" in seen["prompt"]
    assert "Hermes-written Alpha framing outcomes." in (vault / result["digest_path"]).read_text(
        encoding="utf-8"
    )
    events = list(iter_jsonl(vault / "journal/op-machine.jsonl"))
    assert events[1]["runner"] == "hermes"
    assert events[1]["model"] == "memoria-hermes-model"


def test_hermes_runner_rejects_write_capable_toolsets(tmp_path: Path, monkeypatch) -> None:
    vault = workspace(tmp_path)
    policy = vault / "capabilities/operations/compile-source-digest.md"
    policy.write_text(
        policy.read_text(encoding="utf-8")
        .replace("allowed_network: []", "allowed_network:\n  - hermes-config")
        .replace("runner: direct_api", "runner: hermes")
        .replace("model: deterministic-fixture", "model: memoria-hermes-model")
        .replace(
            "prompt_version: compile-source-digest.v1",
            (
                "prompt_version: compile-source-digest.v1\n"
                "hermes_enabled_toolsets:\n"
                "  - file\n"
                "  - hermes-cli"
            ),
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

    class FakeHermesAgent:
        def __init__(self, **_kwargs):
            raise AssertionError("unsafe policy should fail before AIAgent construction")

    monkeypatch.setattr(
        "memoria_vault.runtime.operations._hermes_agent_class",
        lambda: FakeHermesAgent,
    )

    with pytest.raises(PermissionError, match="write-capable or external toolsets"):
        compile_source_digest(
            vault,
            "source-alpha",
            ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
            machine="op-machine",
        )

    assert not (vault / "knowledge/digests/source-alpha.md").exists()


def test_compile_source_digest_rejects_nonconforming_direct_api_output(
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

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps(
                {"choices": [{"message": {"content": "Loose summary only."}}]}
            ).encode()

    monkeypatch.setenv("MEMORIA_MODEL_BASE_URL", "http://model.test/v1")

    def fake_urlopen(_req, timeout):
        return Response()

    monkeypatch.setattr("memoria_vault.runtime.operations.request.urlopen", fake_urlopen)

    with pytest.raises(ValueError, match="digest output must include ## Synthesis"):
        compile_source_digest(
            vault,
            "source-alpha",
            ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
            machine="op-machine",
        )

    assert not (vault / "knowledge/digests/source-alpha.md").exists()


def test_compile_source_digest_rejects_ungrounded_direct_api_output(
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

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": (
                                    "## Synthesis\n\nCompletely unrelated banana prose.\n\n"
                                    "## Hub suggestions\n\n- unrelated\n"
                                )
                            }
                        }
                    ]
                }
            ).encode()

    def fake_urlopen(_req, timeout):
        return Response()

    monkeypatch.setenv("MEMORIA_MODEL_BASE_URL", "http://model.test/v1")
    monkeypatch.setattr("memoria_vault.runtime.operations.request.urlopen", fake_urlopen)

    with pytest.raises(ValueError, match="source-grounding smoke check"):
        compile_source_digest(
            vault,
            "source-alpha",
            ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
            machine="op-machine",
        )

    assert not (vault / "knowledge/digests/source-alpha.md").exists()
