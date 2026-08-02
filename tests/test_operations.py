from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from memoria_vault.runtime import operations, state, trusted_writer
from memoria_vault.runtime.capture import capture_source as _capture_source
from memoria_vault.runtime.hub_candidates import split_candidates_section
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.operations import (
    _pydantic_ai_chat,
    _run_digest_model,
    _run_prompt_model,
    _source_interviews,
    emit_explicit_disposition_event,
    load_operation_policy,
    load_runner_provider_config,
    require_allowed_network,
    resolve_operation_runner,
    run_operation_model_text,
    validate_operation_policy,
)
from memoria_vault.runtime.operations import (
    compile_source_digest as _compile_source_digest,
)
from memoria_vault.runtime.operations import (
    record_copi_interview_turn as _record_copi_interview_turn,
)
from memoria_vault.runtime.operations import run_prompt_operation as _run_prompt_operation
from memoria_vault.runtime.vaultio import read_frontmatter, split_frontmatter
from tests.cli_test_helpers import write_runner_provider_config
from tests.helpers import call_with_context, copy_memoria_dirs, git, init_git, patch_pydantic_ai


def capture_source(vault: Path, *args, **kwargs):
    return call_with_context(_capture_source, vault, *args, **kwargs)


def compile_source_digest(vault: Path, *args, **kwargs):
    return call_with_context(_compile_source_digest, vault, *args, **kwargs)


def record_copi_interview_turn(vault: Path, *args, **kwargs):
    return call_with_context(_record_copi_interview_turn, vault, *args, **kwargs)


def run_prompt_operation(vault: Path, *args, **kwargs):
    return call_with_context(_run_prompt_operation, vault, *args, **kwargs)


def workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas", "config")
    init_git(tmp_path, "operations@example.invalid", "Operations")
    return tmp_path


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


def test_explicit_disposition_event_uses_the_validated_server_schema(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    event = emit_explicit_disposition_event(
        vault,
        decision="accept",
        item_type="evidence-set",
        item_id="ev-deadbeef",
        actor="pi",
        machine="PI laptop",
    )

    assert {key: event[key] for key in event if key != "timestamp"} == {
        "event": "disposition",
        "schema": "disposition.v1",
        "decision": "accept",
        "item_type": "evidence-set",
        "item_id": "ev-deadbeef",
        "actor": "pi",
        "machine": "PI_laptop",
    }
    assert event["timestamp"]
    assert state.read_event_log(vault, event_types=("disposition",)) == [event]


def patch_compile_policy(monkeypatch: pytest.MonkeyPatch, **updates) -> dict:
    policy = compile_policy(**updates)
    monkeypatch.setattr(
        "memoria_vault.runtime.operations.load_operation_policy",
        lambda _vault, _operation_id: policy,
    )
    return policy


def test_load_operation_policy_requires_io_schema_shape() -> None:
    policy = compile_policy(io_schema={"input": "checked_work_id", "output": []})
    with pytest.raises(
        ValueError,
        match=r"compile-source-digest io_schema\.output must be a non-empty string",
    ):
        validate_operation_policy("compile-source-digest", policy)


def test_operation_policy_rejects_retired_frontmatter_state() -> None:
    policy = compile_policy(check_status="checked", standing="current")

    with pytest.raises(
        ValueError,
        match="compile-source-digest operation manifest uses retired fields: check_status, standing",
    ):
        validate_operation_policy("compile-source-digest", policy)


def test_load_operation_policy_requires_untrusted_prompt_fields(monkeypatch) -> None:
    policy = compile_policy()
    policy.pop("untrusted_fields")

    monkeypatch.setattr(
        "memoria_vault.runtime.operations.read_capability_manifest",
        lambda _operation_id: {
            "frontmatter": policy,
            "text": "---\n---\nFrom {{input}}, write a report.\n",
        },
    )

    with pytest.raises(ValueError, match="missing untrusted_fields declarations"):
        load_operation_policy(Path(), "compile-source-digest")


def test_operation_policy_rejects_malformed_untrusted_fields() -> None:
    policy = compile_policy(untrusted_fields=["input", ""])

    with pytest.raises(ValueError, match="untrusted_fields entries must be non-empty strings"):
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


def test_runner_provider_config_rejects_removed_root_providers(tmp_path: Path) -> None:
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


def test_runner_provider_config_normalizes_malformed_yaml(tmp_path: Path) -> None:
    config = tmp_path / ".memoria/config/providers.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("runner_providers: [\n", encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        load_runner_provider_config(tmp_path)

    assert str(exc_info.value) == ".memoria/config/providers.yaml could not be parsed"


def test_runner_provider_config_rejects_invalid_key_env_without_echoing_it(tmp_path: Path) -> None:
    sentinel = "sk-live-pasted-secret"
    config = tmp_path / ".memoria/config/providers.yaml"
    config.parent.mkdir(parents=True)
    config.write_text(
        "\n".join(
            [
                "version: 1",
                "runner_providers:",
                "  local: {url: http://model.test/v1, key_env: null}",
                f"  gateway: {{url: https://gateway.test/v1, key_env: {sentinel}}}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc_info:
        load_runner_provider_config(tmp_path)

    assert "gateway.key_env must match [A-Z][A-Z0-9_]*" in str(exc_info.value)
    assert sentinel not in str(exc_info.value)


def test_runner_provider_config_rejects_control_key_env_without_echoing_it(
    tmp_path: Path,
) -> None:
    config = tmp_path / ".memoria/config/providers.yaml"
    config.parent.mkdir(parents=True)
    config.write_text(
        "version: 1\n"
        "runner_providers:\n"
        "  local: {url: http://model.test/v1, key_env: null}\n"
        '  gateway: {url: https://gateway.test/v1, key_env: "BAD\\u001bNAME"}\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc_info:
        load_runner_provider_config(tmp_path)

    assert "\x1b" not in str(exc_info.value)


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
    curated_hub = vault / "hubs/framing.md"
    curated_hub.parent.mkdir(parents=True)
    curated_text = (
        "---\ntype: hub\nid: 01KBN6V6KX0000000000000002\ntitle: Framing\n"
        "tag: framing\ntags: []\nlinks: {}\ndescription: Human curation.\n---\n"
        "# Framing\n\nHuman text.\n"
    )
    curated_hub.write_text(curated_text, encoding="utf-8")

    result = compile_source_digest(
        vault,
        "source-alpha",
        ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
        machine="op-machine",
        run_id="compile-alpha",
    )

    digest = vault / "digests/source-alpha.md"
    digest_fm = read_frontmatter(digest)
    assert digest_fm["type"] == "digest"
    assert "check_status" not in digest_fm
    assert digest_fm["work_id"] == "source-alpha"
    assert state.concept_check_status(vault, "digests/source-alpha.md") == "checked"
    assert result["derived"]["inputs"][0]["id"] == "catalog/sources/source-alpha"
    assert result["hub_paths"] == [
        "hubs/methods.md",
        "hubs/outcomes.md",
        "hubs/gaps.md",
        "hubs/impact.md",
    ]
    assert result["hub_suggestions"] == ["hubs/framing.md"]
    hub_body = split_frontmatter(curated_hub.read_text(encoding="utf-8"))[1]
    curated_body, section = split_candidates_section(hub_body)
    assert curated_body == "# Framing\n\nHuman text.\n"
    assert "%%candidates: run=compile-alpha%%" in section
    assert (
        "- [[digests/source-alpha.md]] — suggested hub update from this digest "
        "%%run=compile-alpha%%"
    ) in section
    assert read_frontmatter(curated_hub)["description"] == "Human curation."

    staged_hub = vault / ".memoria/staging/hubs/framing.md"
    assert not staged_hub.exists()
    promoted_hub = vault / "hubs/methods.md"
    promoted_hub_fm = read_frontmatter(promoted_hub)
    assert "check_status" not in promoted_hub_fm
    assert promoted_hub_fm["tag"] == "methods"
    assert state.concept_check_status(vault, "hubs/methods.md") == "checked"

    events = list(iter_jsonl(vault / ".memoria/journal/op-machine.jsonl"))
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
    assert events[1]["usage"] is None
    assert events[1]["cost_usd"] is None
    assert events[1]["elapsed_s"] == 0.0
    assert events[-1]["suggestions"] == result["hub_suggestions"]
    assert events[-1]["outputs"] == ["digests/source-alpha.md", *result["hub_paths"]]
    assert events[4]["output_id"] == "hubs/framing.md"
    assert events[4]["inputs"] == [
        {"id": "digests/source-alpha.md", "sha256": result["checked"]["output_sha256"]},
        {"id": "catalog/sources/source-alpha", "sha256": events[2]["inputs"][0]["sha256"]},
    ]
    assert result["hub_events"][0]["output_id"] == "hubs/framing.md"
    assert len(result["hub_events"]) == 5

    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {
        state.JOURNAL_HEAD_REL,
        "digests/source-alpha.md",
        "hubs/framing.md",
        "hubs/gaps.md",
        "hubs/impact.md",
        "hubs/methods.md",
        "hubs/outcomes.md",
    }


def test_prompt_operation_neutralizes_model_output_before_staging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = workspace(tmp_path)
    raw_output = (
        "![model](http://beacon.example/model.png) "
        "<script>signal()</script> http://beacon.example/bare"
    )
    monkeypatch.setattr(
        "memoria_vault.runtime.operations._run_prompt_model",
        lambda _policy, _runner, _prompt, _input: {
            "text": raw_output,
            "usage": {
                "input_tokens": 17,
                "output_tokens": 5,
                "cache_read_tokens": 2,
                "cache_write_tokens": 1,
                "total_tokens": 25,
            },
            "cost_usd": 0.0125,
            "elapsed_s": 0.25,
        },
    )

    result = run_prompt_operation(
        vault,
        "analyze-claims",
        {"input_text": "A checked claim."},
        machine="prompt-machine",
        run_id="prompt-alpha",
    )

    materialized = (vault / result["output_path"]).read_text(encoding="utf-8")
    assert "![model]" not in materialized
    assert "<script>" not in materialized
    assert "](http://beacon.example" not in materialized
    assert "`http://beacon.example/model.png`" in materialized
    assert "`http://beacon.example/bare`" in materialized
    events = list(iter_jsonl(vault / ".memoria/journal/prompt-machine.jsonl"))
    assert events[1]["output_hash"] == (
        "sha256:" + hashlib.sha256(raw_output.encode("utf-8")).hexdigest()
    )
    assert events[1]["usage"] == {
        "input_tokens": 17,
        "output_tokens": 5,
        "cache_read_tokens": 2,
        "cache_write_tokens": 1,
        "total_tokens": 25,
    }
    assert events[1]["cost_usd"] == pytest.approx(0.0125)
    assert events[1]["elapsed_s"] == pytest.approx(0.25)


def test_run_operation_model_text_records_telemetry_without_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = workspace(tmp_path)
    policy = compile_policy()
    monkeypatch.setattr(
        "memoria_vault.runtime.operations._run_prompt_model",
        lambda _policy, _runner, _prompt, _input: {
            "text": "tier-two verdict text",
            "usage": {
                "input_tokens": 17,
                "output_tokens": 5,
                "cache_read_tokens": 2,
                "cache_write_tokens": 1,
                "total_tokens": 25,
            },
            "cost_usd": 0.0125,
            "elapsed_s": 0.25,
        },
    )

    call = call_with_context(
        run_operation_model_text,
        vault,
        policy,
        chat_runner(),
        "tier-two prompt body",
        input_text="left excerpt\n\nright excerpt",
        call_id="surface-tensions:tier2:testcall",
        route="surface-tensions-tier2",
        purpose="surface-tensions",
        machine="tier2-machine",
    )

    assert call["output"] == "tier-two verdict text"
    events = list(iter_jsonl(vault / ".memoria/journal/tier2-machine.jsonl"))
    model_call = next(event for event in events if event["event"] == "model_call")
    assert model_call["usage"] == {
        "input_tokens": 17,
        "output_tokens": 5,
        "cache_read_tokens": 2,
        "cache_write_tokens": 1,
        "total_tokens": 25,
    }
    assert model_call["cost_usd"] == pytest.approx(0.0125)
    assert model_call["elapsed_s"] == pytest.approx(0.25)
    # No content capture: counts, cost, and timing only — never prompt or output text.
    serialized = json.dumps(model_call)
    assert "tier-two prompt body" not in serialized
    assert "tier-two verdict text" not in serialized
    assert "left excerpt" not in serialized
    assert all(isinstance(value, int) for value in model_call["usage"].values())
    assert isinstance(model_call["cost_usd"], float)
    assert isinstance(model_call["elapsed_s"], float)


def test_digest_and_hub_apply_neutralize_source_model_and_topic_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = workspace(tmp_path)
    capture_source(
        vault,
        "source-beacon",
        "Work ![title](http://beacon.example/title.png)",
        'Description <img src="http://beacon.example/description.png">',
        "Source content about framing, methods, outcomes, gaps, and impact.",
        machine="capture-machine",
    )
    raw_digest = (
        "## Synthesis\n\n"
        "Model ![body](http://beacon.example/body.png) <script>signal()</script>\n\n"
        "## Hub suggestions\n\n- Framing\n"
    )
    monkeypatch.setattr(
        "memoria_vault.runtime.operations._run_digest_model",
        lambda _policy, _runner, _source, _content, _topics, _interviews: {
            "text": raw_digest,
            "usage": None,
            "cost_usd": None,
            "elapsed_s": 0.0,
        },
    )

    result = compile_source_digest(
        vault,
        "source-beacon",
        [
            "![Topic](http://beacon.example/topic.png)",
            "Methods",
            "Outcomes",
            "Gaps",
            "Impact",
        ],
        machine="digest-machine",
    )

    rendered = [
        (vault / result["digest_path"]).read_text(encoding="utf-8"),
        *[(vault / path).read_text(encoding="utf-8") for path in result["hub_paths"]],
    ]
    combined = "\n".join(rendered)
    assert "![" not in combined
    assert "<script>" not in combined
    assert "<img" not in combined
    for url in (
        "http://beacon.example/title.png",
        "http://beacon.example/description.png",
        "http://beacon.example/body.png",
        "http://beacon.example/topic.png",
    ):
        assert f"`{url}`" in combined
    events = list(iter_jsonl(vault / ".memoria/journal/digest-machine.jsonl"))
    assert events[1]["output_hash"] == (
        "sha256:" + hashlib.sha256(raw_digest.encode("utf-8")).hexdigest()
    )


def test_digest_and_hub_render_composed_fenced_fragments_inert(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        pytest.skip("Pandoc is optional")
    vault = workspace(tmp_path)
    source_title = '```\n<img src="https://evil.example/source-title">\n```'
    model_topic = '```\n<img src="https://evil.example/model-topic">\n```'
    capture_source(
        vault,
        "source-fenced-fragment",
        source_title,
        "Third-party description.",
        "Source content about framing, methods, outcomes, gaps, and impact.",
        machine="capture-machine",
    )
    monkeypatch.setattr(
        "memoria_vault.runtime.operations._run_digest_model",
        lambda _policy, _runner, _source, _content, _topics, _interviews: {
            "text": "## Synthesis\n\nModel digest.\n\n## Hub suggestions\n\n- Framing\n",
            "usage": None,
            "cost_usd": None,
            "elapsed_s": 0.0,
        },
    )

    result = compile_source_digest(
        vault,
        "source-fenced-fragment",
        [model_topic, "Methods", "Outcomes", "Gaps", "Impact"],
        machine="digest-machine",
    )

    for path in [result["digest_path"], *result["hub_paths"]]:
        rendered = subprocess.run(
            [pandoc, "-f", "commonmark", "-t", "html"],
            input=(vault / path).read_text(encoding="utf-8"),
            text=True,
            capture_output=True,
            check=True,
        ).stdout
        assert "<img" not in rendered


def test_compile_source_digest_rejects_removed_source_markdown_without_catalog_row(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    removed = vault / "catalog/sources/removed/source.md"
    removed.parent.mkdir(parents=True, exist_ok=True)
    removed.write_text(
        "---\n"
        "type: source\n"
        "check_status: checked\n"
        "title: Removed Source\n"
        "description: Should not be treated as a Work row.\n"
        "work_id: removed\n"
        "content_path: .memoria/blobs/source-content/removed/content.txt\n"
        "text_status: full-text\n"
        "---\n"
        "# Removed Source\n",
        encoding="utf-8",
    )
    content = vault / ".memoria/blobs/source-content/removed/content.txt"
    content.parent.mkdir(parents=True, exist_ok=True)
    content.write_text("Removed source text.\n", encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="catalog/sources/removed"):
        compile_source_digest(
            vault,
            "removed",
            ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
            machine="op-machine",
            run_id="compile-removed",
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
    assert not (vault / "digests/source-alpha.md").exists()
    attention = vault / "inbox/flag-digest-full-text-source-alpha.md"
    attention_fm = read_frontmatter(attention)
    assert attention_fm["projection"] == "attention"
    assert attention_fm["attention_kind"] == "flag"
    assert attention_fm["attention_status"] == "open"
    assert attention_fm["target"] == "catalog/sources/source-alpha"
    assert attention_fm["raised_by"] == "compile-source-digest"
    events = list(iter_jsonl(vault / ".memoria/journal/op-machine.jsonl"))
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

    assert not (vault / "digests/source-alpha.md").exists()


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
        actor="pi",
        project_id="projects/project-alpha/project.md",
        machine="copi-machine",
    )
    for path in (vault / ".memoria/journal").glob("*.jsonl"):
        path.unlink()
    result = compile_source_digest(
        vault,
        "source-alpha",
        ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
        machine="op-machine",
    )

    digest = vault / result["digest_path"]
    assert interview["event"]["work_id"] == "source-alpha"
    assert result["interview_count"] == 1
    assert "The PI cares about the methods caveat." in digest.read_text(encoding="utf-8")
    assert interview["event"]["turn_sha256"] in {
        row["sha256"] for row in result["derived"]["inputs"] if row.get("role") == "copi-interview"
    }
    committed = set(
        git(vault, "show", "--name-only", "--format=", interview["commit"]).splitlines()
    )
    assert committed == {state.JOURNAL_HEAD_REL}


def test_source_interviews_follow_authoritative_event_order(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    for turn_id, timestamp in (
        ("first-inserted", "2026-07-13T02:00:00+00:00"),
        ("second-inserted", "2026-07-13T01:00:00+00:00"),
    ):
        trusted_writer.append_explicit_journal_event(
            vault,
            {
                "event": "copi-interview",
                "work_id": "source-alpha",
                "turn_id": turn_id,
                "turn_sha256": f"sha256:{turn_id}",
                "timestamp": timestamp,
            },
            actor="pi",
            machine="copi-machine",
        )

    assert [row["turn_id"] for row in _source_interviews(vault, "source-alpha")] == [
        "first-inserted",
        "second-inserted",
    ]


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

    monkeypatch.setenv("MEMORIA_MODEL_BASE_URL", "http://model.test/v1")
    monkeypatch.setenv("MEMORIA_MODEL_API_KEY", "legacy-model-secret")
    monkeypatch.setenv("OPENAI_API_KEY", "legacy-openai-secret")
    monkeypatch.setenv("KILOCODE_API_KEY", "legacy-gateway-secret")
    patch_pydantic_ai(
        monkeypatch,
        output=(
            "## Synthesis\n\nModel-written Alpha framing outcomes.\n\n"
            "## Hub suggestions\n\n- Framing\n"
        ),
        seen=seen,
    )

    result = compile_source_digest(
        vault,
        "source-alpha",
        ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
        machine="op-machine",
    )

    assert seen["provider_kwargs"] == {
        "base_url": "http://model.test/v1",
        "api_key": "api-key-not-set",
    }
    assert seen["model_name"] == "memoria-test-model"
    assert seen["model"] is not None
    assert seen["model_settings"]["temperature"] == 0
    assert seen["model_settings"]["max_tokens"] == 2048
    assert seen["model_settings"]["timeout"] == 90.0
    assert '<memoria_untrusted_data name="source_text">' in seen["prompt"]
    assert '<memoria_untrusted_data name="pi_interview_notes">' in seen["prompt"]
    assert "Alpha content" in seen["prompt"]
    assert "Source text:\nAlpha content" not in seen["prompt"]
    assert "## Synthesis" in seen["prompt"]
    assert "Model-written Alpha framing outcomes." in (vault / result["digest_path"]).read_text(
        encoding="utf-8"
    )
    events = list(iter_jsonl(vault / ".memoria/journal/op-machine.jsonl"))
    assert events[1]["model"] == "memoria-test-model"


def test_compile_source_digest_gateway_refuses_missing_configured_key_before_adapter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = workspace(tmp_path)
    write_runner_provider_config(vault)
    patch_compile_policy(
        monkeypatch,
        provider="gateway",
        allowed_network=["https://gateway.test/v1"],
        model="gateway-test-model",
    )
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Alpha content about framing, methods, outcomes, gaps, and impact.",
        machine="capture-machine",
    )
    sentinels = {
        "MEMORIA_MODEL_API_KEY": "legacy-model-secret",
        "OPENAI_API_KEY": "legacy-openai-secret",
        "KILOCODE_API_KEY": "",
    }
    for name, value in sentinels.items():
        monkeypatch.setenv(name, value)
    seen = patch_pydantic_ai(
        monkeypatch,
        output=(
            "## Synthesis\n\nModel-written Alpha framing outcomes.\n\n"
            "## Hub suggestions\n\n- Framing\n"
        ),
    )
    loader_calls: list[None] = []

    def unexpected_loader() -> tuple[object, object, object]:
        loader_calls.append(None)
        raise AssertionError("pydantic-ai loader must not run without a configured gateway key")

    monkeypatch.setattr(
        "memoria_vault.runtime.operations._load_pydantic_ai_openai", unexpected_loader
    )

    with pytest.raises(RuntimeError) as exc_info:
        compile_source_digest(
            vault,
            "source-alpha",
            ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
            machine="op-machine",
        )

    assert str(exc_info.value) == (
        "provider gateway requires KILOCODE_API_KEY - set it: memoria secrets set KILOCODE_API_KEY"
    )
    assert seen == {}
    assert loader_calls == []
    assert "legacy-model-secret" not in str(exc_info.value)
    assert "legacy-openai-secret" not in str(exc_info.value)


def test_compile_source_digest_gateway_uses_only_configured_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = workspace(tmp_path)
    write_runner_provider_config(vault)
    patch_compile_policy(
        monkeypatch,
        provider="gateway",
        allowed_network=["https://gateway.test/v1"],
        model="gateway-test-model",
    )
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Alpha content about framing, methods, outcomes, gaps, and impact.",
        machine="capture-machine",
    )
    monkeypatch.setenv("MEMORIA_MODEL_API_KEY", "legacy-model-secret")
    monkeypatch.setenv("OPENAI_API_KEY", "legacy-openai-secret")
    monkeypatch.setenv("KILOCODE_API_KEY", "gateway-key")
    seen = patch_pydantic_ai(
        monkeypatch,
        output=(
            "## Synthesis\n\nModel-written Alpha framing outcomes.\n\n"
            "## Hub suggestions\n\n- Framing\n"
        ),
    )

    compile_source_digest(
        vault,
        "source-alpha",
        ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
        machine="op-machine",
    )

    assert seen["provider_kwargs"] == {
        "base_url": "https://gateway.test/v1",
        "api_key": "gateway-key",
    }


@pytest.mark.parametrize(
    "key_env",
    ["", "PASTED_SECRET\x1b", 7],
    ids=["empty", "control-text", "non-string"],
)
def test_resolve_runner_api_key_rejects_malformed_direct_runner_without_reflection(
    key_env: object,
) -> None:

    with pytest.raises(ValueError) as exc_info:
        operations._resolve_runner_api_key({"provider": "gateway", "key_env": key_env})

    assert str(exc_info.value) == "runner key_env must match [A-Z][A-Z0-9_]*"
    if isinstance(key_env, str) and key_env:
        assert key_env not in str(exc_info.value)


def test_resolve_runner_api_key_uses_generic_provider_for_malformed_direct_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    supplied_provider = "gateway-secret\x1b"
    monkeypatch.delenv("KILOCODE_API_KEY", raising=False)

    with pytest.raises(RuntimeError) as exc_info:
        operations._resolve_runner_api_key(
            {"provider": supplied_provider, "key_env": "KILOCODE_API_KEY"}
        )

    assert str(exc_info.value) == (
        "provider runner requires KILOCODE_API_KEY - set it: memoria secrets set KILOCODE_API_KEY"
    )
    assert supplied_provider not in str(exc_info.value)


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

    monkeypatch.setenv("MEMORIA_MODEL_BASE_URL", "http://model.test/v1")
    patch_pydantic_ai(monkeypatch, output="Loose summary only.")

    with pytest.raises(ValueError, match="digest output must include ## Synthesis"):
        compile_source_digest(
            vault,
            "source-alpha",
            ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
            machine="op-machine",
        )

    assert not (vault / "digests/source-alpha.md").exists()


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

    monkeypatch.setenv("MEMORIA_MODEL_BASE_URL", "http://model.test/v1")
    patch_pydantic_ai(
        monkeypatch,
        output=(
            "## Synthesis\n\nCompletely unrelated banana prose.\n\n"
            "## Hub suggestions\n\n- unrelated\n"
        ),
    )

    with pytest.raises(ValueError, match="source-grounding smoke check"):
        compile_source_digest(
            vault,
            "source-alpha",
            ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
            machine="op-machine",
        )

    assert not (vault / "digests/source-alpha.md").exists()


def chat_runner(model: str = "gpt-test") -> dict[str, object]:
    return {
        "mode": "test",
        "runner": "pydantic-ai",
        "provider": "local",
        "model": model,
        "base_url": "http://model.test/v1",
        "key_env": None,
        "params": {"temperature": 0},
    }


CHAT_POLICY = {"operation_id": "chat-test", "allowed_network": ["http://model.test/v1"]}


def test_pydantic_ai_chat_returns_text_usage_cost_and_timing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = patch_pydantic_ai(monkeypatch, output="model text", total_price=Decimal("0.0125"))

    result = _pydantic_ai_chat(CHAT_POLICY, chat_runner(), "prompt body")

    assert result["text"] == "model text"
    assert result["usage"] == {
        "input_tokens": 17,
        "output_tokens": 5,
        "cache_read_tokens": 2,
        "cache_write_tokens": 1,
        "total_tokens": 25,
    }
    assert isinstance(result["cost_usd"], float)
    assert result["cost_usd"] == pytest.approx(0.0125)
    assert isinstance(result["elapsed_s"], float)
    assert result["elapsed_s"] >= 0.0
    assert seen["prompt"] == "prompt body"
    assert seen["provider_kwargs"] == {
        "base_url": "http://model.test/v1",
        "api_key": "api-key-not-set",
    }
    assert seen["usage_calls"] == 1


def test_pydantic_ai_chat_unpriced_model_yields_null_cost_with_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_pydantic_ai(monkeypatch, output="model text")

    result = _pydantic_ai_chat(CHAT_POLICY, chat_runner(), "prompt body")

    assert result["cost_usd"] is None
    assert result["usage"] == {
        "input_tokens": 17,
        "output_tokens": 5,
        "cache_read_tokens": 2,
        "cache_write_tokens": 1,
        "total_tokens": 25,
    }


def test_pydantic_ai_chat_still_rejects_empty_output(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_pydantic_ai(monkeypatch, output="")

    with pytest.raises(RuntimeError, match="pydantic-ai model returned no message content"):
        _pydantic_ai_chat(CHAT_POLICY, chat_runner(), "prompt body")


def test_run_prompt_model_fixture_branch_returns_null_telemetry() -> None:
    policy = compile_policy()
    runner = chat_runner(model="deterministic-fixture")

    result = _run_prompt_model(policy, runner, "prompt body", "input body")

    assert result["usage"] is None
    assert result["cost_usd"] is None
    assert result["elapsed_s"] == 0.0
    assert result["text"].startswith(f"## {policy['title']}")


def test_run_digest_model_fixture_branch_returns_null_telemetry() -> None:
    policy = compile_policy()
    runner = chat_runner(model="deterministic-fixture")
    source_fm = {"title": "Alpha Source", "description": "A fixture source."}

    result = _run_digest_model(
        policy,
        runner,
        source_fm,
        "Alpha content about framing, methods, outcomes, gaps, and impact.",
        ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
        [],
    )

    assert result["usage"] is None
    assert result["cost_usd"] is None
    assert result["elapsed_s"] == 0.0
    assert "## Synthesis" in result["text"]
    assert "## Hub suggestions" in result["text"]
