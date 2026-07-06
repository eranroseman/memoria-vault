"""Operation runner primitives for the standalone Memoria engine."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Iterable
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from memoria_vault.runtime import state
from memoria_vault.runtime.capabilities import read_capability_manifest
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.trusted_writer import (
    append_journal_event,
    commit_writer_changes,
    normalize_promotion_checks,
    promote_checked,
    stage_concept,
)
from memoria_vault.runtime.vaultio import (
    concept_text,
    frontmatter_doc,
    safe_read,
    split_frontmatter,
)

REQUIRED_POLICY_FIELDS = {
    "operation_id",
    "allowed_tools",
    "allowed_paths",
    "allowed_network",
    "runner",
    "prompt_version",
    "io_schema",
    "risk_class",
    "required_checks",
}
SUPPORTED_OPERATION_RUNNERS = frozenset({"pydantic-ai"})
PROVIDER_CONFIG = ".memoria/config/providers.yaml"
RUNNER_MODES = frozenset({"test", "live"})
RUNNER_PROVIDER_NAMES = ("local", "gateway")


def record_copi_interview_turn(
    vault: Path,
    source_id: str,
    response: str,
    *,
    prompt: str = "What matters about this source?",
    project_id: str = "",
    machine: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Record one PI interview turn for later source synthesis."""
    vault = Path(vault)
    source_id = _source_id(source_id)
    source_ref = _source_ref(source_id)
    _checked_source(vault, source_ref)
    answer = response.strip()
    if not answer:
        raise ValueError("response is required")
    question = prompt.strip() or "What matters about this source?"
    body = f"{source_id}\n{project_id.strip()}\n{question}\n{answer}"
    turn_sha = _sha256_text(body)
    event = append_journal_event(
        vault,
        {
            "event": "copi-interview",
            "run_id": run_id or f"copi-interview:{source_id}",
            "source_id": source_id,
            "project_id": project_id.strip(),
            "prompt": question,
            "response": answer,
            "turn_id": f"journal:copi-interview:{turn_sha.removeprefix('sha256:')}",
            "turn_sha256": turn_sha,
            "actor": "pi",
        },
        machine=machine,
    )
    commit = commit_writer_changes(
        vault,
        f"record copi interview {source_id}",
        [],
        machine=machine,
    )
    return {"event": event, "commit": commit}


def load_operation_policy(vault: Path, operation_id: str) -> dict[str, Any]:
    """Load a packaged product operation manifest and require the WP5 policy contract."""
    manifest = read_capability_manifest("operation", operation_id)
    policy = validate_operation_policy(operation_id, manifest["frontmatter"])
    _validate_manifest_untrusted_fields(operation_id, policy, manifest["text"])
    return policy


def validate_operation_policy(operation_id: str, policy: dict[str, Any]) -> dict[str, Any]:
    """Validate one operation policy frontmatter map."""
    if policy.get("type") != "operation":
        raise ValueError(f"{operation_id} is not an operation manifest")
    retired = sorted(field for field in ("check_status", "standing") if field in policy)
    if retired:
        raise ValueError(
            f"{operation_id} operation manifest uses retired fields: {', '.join(retired)}"
        )
    missing = sorted(field for field in REQUIRED_POLICY_FIELDS if field not in policy)
    if missing:
        raise ValueError(f"{operation_id} missing operation policy fields: {', '.join(missing)}")
    _validate_runner_policy(operation_id, policy["runner"])
    _untrusted_fields(operation_id, policy)
    io_schema = policy["io_schema"]
    if not isinstance(io_schema, dict):
        raise ValueError(f"{operation_id} io_schema must be a map")
    for key in ("input", "output"):
        value = io_schema.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{operation_id} io_schema.{key} must be a non-empty string")
    return policy


def _validate_manifest_untrusted_fields(
    operation_id: str, policy: dict[str, Any], manifest_text: str
) -> None:
    _frontmatter, body = split_frontmatter(manifest_text)
    required = ["input"] if "{{input}}" in body else []
    if operation_id == "compile-source-digest":
        required.extend(["source_text", "pi_interview_notes"])
    _require_untrusted_fields(operation_id, policy, required)


def _untrusted_fields(operation_id: str, policy: dict[str, Any]) -> set[str]:
    fields = policy.get("untrusted_fields", [])
    if not isinstance(fields, list) or not all(isinstance(field, str) for field in fields):
        raise ValueError(f"{operation_id} untrusted_fields must be a list of strings")
    normalized = {field.strip() for field in fields if field.strip()}
    if len(normalized) != len(fields):
        raise ValueError(f"{operation_id} untrusted_fields entries must be non-empty strings")
    return normalized


def _require_untrusted_fields(
    operation_id: str, policy: dict[str, Any], fields: Iterable[str]
) -> None:
    declared = _untrusted_fields(operation_id, policy)
    missing = sorted({field for field in fields if field} - declared)
    if missing:
        raise ValueError(
            f"{operation_id} missing untrusted_fields declarations: {', '.join(missing)}"
        )


def resolve_operation_runner(
    vault: Path,
    policy: dict[str, Any],
    mode: str | None = None,
) -> dict[str, Any]:
    """Resolve the one manifest-declared runner branch selected by run mode."""
    operation_id = str(policy.get("operation_id") or "<unknown>")
    run_mode = normalize_run_mode(mode)
    runner_policy = _validate_runner_policy(operation_id, policy.get("runner"))[run_mode]
    provider = str(runner_policy["provider"])
    provider_config = load_runner_provider_config(vault)
    if provider not in provider_config:
        raise ValueError(f"{operation_id} runner.{run_mode} unknown provider: {provider}")
    spec = provider_config[provider]
    base_url = str(spec.get("url") or "").strip().rstrip("/")
    if not base_url:
        raise ValueError(f"{PROVIDER_CONFIG} runner provider {provider} requires url")
    return {
        "mode": run_mode,
        "runner": str(runner_policy.get("engine") or "pydantic-ai"),
        "provider": provider,
        "model": str(runner_policy["model"]),
        "base_url": base_url,
        "key_env": spec.get("key_env"),
        "params": {
            key: runner_policy[key]
            for key in ("temperature", "max_tokens", "timeout")
            if key in runner_policy
        },
    }


def normalize_run_mode(mode: str | None = None) -> str:
    """Return the supported runner mode, defaulting to the local test branch."""
    value = str(mode or "test").strip()
    if value not in RUNNER_MODES:
        raise ValueError(f"unsupported run mode: {value}")
    return value


def load_runner_provider_config(vault: Path) -> dict[str, dict[str, Any]]:
    """Load OpenAI-compatible runner provider connections from workspace config."""
    path = Path(vault) / PROVIDER_CONFIG
    if not path.is_file():
        raise FileNotFoundError(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{PROVIDER_CONFIG} must be a map")
    providers = data.get("runner_providers")
    if not isinstance(providers, dict):
        raise ValueError(f"{PROVIDER_CONFIG} runner_providers must be a map")
    missing = [name for name in RUNNER_PROVIDER_NAMES if name not in providers]
    if missing:
        raise ValueError(f"{PROVIDER_CONFIG} missing runner providers: {', '.join(missing)}")
    resolved: dict[str, dict[str, Any]] = {}
    for name in RUNNER_PROVIDER_NAMES:
        spec = providers[name]
        if not isinstance(spec, dict):
            raise ValueError(f"{PROVIDER_CONFIG} runner provider {name} must be a map")
        url = str(spec.get("url") or spec.get("base_url") or "").strip().rstrip("/")
        if not url:
            raise ValueError(f"{PROVIDER_CONFIG} runner provider {name} requires url")
        key_env = spec.get("key_env")
        if key_env is not None and not isinstance(key_env, str):
            raise ValueError(f"{PROVIDER_CONFIG} runner provider {name}.key_env must be a string")
        resolved[name] = {"url": url, "key_env": key_env}
    return resolved


def _validate_runner_policy(operation_id: str, runner_policy: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(runner_policy, dict):
        raise ValueError(f"{operation_id} runner must define test and live branches")
    missing = sorted(mode for mode in RUNNER_MODES if mode not in runner_policy)
    if missing:
        raise ValueError(f"{operation_id} runner missing branches: {', '.join(missing)}")
    branches: dict[str, dict[str, Any]] = {}
    for mode in sorted(RUNNER_MODES):
        branch = runner_policy[mode]
        if not isinstance(branch, dict):
            raise ValueError(f"{operation_id} runner.{mode} must be a map")
        engine = str(branch.get("engine") or "pydantic-ai").strip()
        if engine not in SUPPORTED_OPERATION_RUNNERS:
            raise ValueError(f"{operation_id} unsupported operation runner: {engine}")
        provider = str(branch.get("provider") or "").strip()
        model = str(branch.get("model") or "").strip()
        if provider not in RUNNER_PROVIDER_NAMES:
            raise ValueError(f"{operation_id} runner.{mode} provider must be local or gateway")
        if not model:
            raise ValueError(f"{operation_id} runner.{mode}.model must be non-empty")
        branches[mode] = {**branch, "engine": engine, "provider": provider, "model": model}
    return branches


def required_promotion_checks(policy: dict[str, Any]) -> list[str]:
    """Return operation checks that are enforced before checked Concept promotion."""
    operation_id = str(policy.get("operation_id") or "<unknown>")
    checks = policy.get("required_checks")
    if not isinstance(checks, list):
        raise ValueError(f"{operation_id} required_checks must be a list")
    try:
        return normalize_promotion_checks(checks)
    except ValueError as exc:
        raise ValueError(f"{operation_id} cannot promote checked Concepts: {exc}") from exc


def run_prompt_operation(
    vault: Path,
    operation_id: str,
    payload: dict[str, Any],
    *,
    mode: str | None = None,
    machine: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Run one checked prompt operation through the standard staged write path."""
    vault = Path(vault)
    policy = load_operation_policy(vault, operation_id)
    runner = resolve_operation_runner(vault, policy, mode)
    _require_tool(policy, "trusted_writer")
    manifest = read_capability_manifest("operation", operation_id)
    _frontmatter, pattern = split_frontmatter(manifest["text"])
    if "{{input}}" not in pattern:
        raise ValueError(f"{operation_id} is not a prompt operation")

    input_refs = _prompt_input_refs(payload)
    input_text = str(payload.get("input_text") or "").strip()
    inputs = []
    if input_refs:
        parts = []
        for rel in input_refs:
            _require_path(policy, rel)
            text, input_row = _checked_prompt_input(vault, rel)
            parts.append(f"## {rel}\n\n{text}")
            inputs.append(input_row)
        if not input_text:
            input_text = "\n\n".join(parts)
    if not input_text:
        raise ValueError(f"{operation_id} requires input_text or input_ref")

    run_id = run_id or f"{operation_id}:{_sha256_text(input_text).removeprefix('sha256:')[:12]}"
    prompt = _prompt_text(vault, policy, pattern, input_text)
    started = append_journal_event(
        vault,
        {"event": "run", "run_id": run_id, "workflow": operation_id, "status": "started"},
        machine=machine,
    )
    output = _run_prompt_model(policy, runner, prompt, input_text)
    model_call = append_journal_event(
        vault,
        {
            "event": "model_call",
            "run_id": run_id,
            "mode": runner["mode"],
            "runner": runner["runner"],
            "provider": runner["provider"],
            "model": runner["model"],
            "model_params": runner["params"],
            "route": "prompt-operation",
            "purpose": operation_id,
            "prompt_version": policy["prompt_version"],
            "prompt_hash": _sha256_text(prompt),
            "toolset": policy["allowed_tools"],
            "fallback_used": False,
            "compression_used": False,
            "input_hash": _sha256_text(input_text),
            "output_hash": _sha256_text(output),
        },
        machine=machine,
    )
    output_path = f"notes/{safe_filename(operation_id)}-{safe_filename(run_id)}.md"
    frontmatter = {
        "type": "note",
        "title": f"{policy['title']} report",
        "description": str(policy.get("description") or policy["title"]),
        "evidence_set": [row["id"] for row in inputs],
        "tags": ["prompt-operation", operation_id],
    }
    stage = stage_concept(
        vault,
        output_path,
        concept_text(frontmatter, f"{policy['title']} report", output),
        inputs=inputs,
        operation=operation_id,
        run_id=run_id,
        machine=machine,
    )
    finished = append_journal_event(
        vault,
        {
            "event": "run",
            "run_id": run_id,
            "workflow": operation_id,
            "status": "done",
            "outputs": [output_path],
        },
        machine=machine,
    )
    commit = commit_writer_changes(
        vault,
        f"run prompt operation {operation_id}",
        [stage["staging_id"]],
        machine=machine,
    )
    return {
        "run_id": run_id,
        "operation_id": operation_id,
        "output_path": output_path,
        "staging_id": stage["staging_id"],
        "input_refs": [row["id"] for row in inputs],
        "started": started,
        "model_call": model_call,
        "derived": stage,
        "finished": finished,
        "commit": commit,
    }


def run_operation_model_text(
    vault: Path,
    policy: dict[str, Any],
    runner: dict[str, Any],
    prompt: str,
    *,
    input_text: str,
    run_id: str,
    route: str,
    purpose: str,
    machine: str | None = None,
) -> dict[str, Any]:
    """Run a policy-scoped text model call and record the model-call event."""
    output = _run_prompt_model(policy, runner, prompt, input_text)
    model_call = append_journal_event(
        Path(vault),
        {
            "event": "model_call",
            "run_id": run_id,
            "mode": runner["mode"],
            "runner": runner["runner"],
            "provider": runner["provider"],
            "model": runner["model"],
            "model_params": runner["params"],
            "route": route,
            "purpose": purpose,
            "prompt_version": policy["prompt_version"],
            "prompt_hash": _sha256_text(prompt),
            "toolset": policy["allowed_tools"],
            "fallback_used": False,
            "compression_used": False,
            "input_hash": _sha256_text(input_text),
            "output_hash": _sha256_text(output),
        },
        machine=machine,
    )
    return {"output": output, "model_call": model_call}


def compile_source_digest(
    vault: Path,
    source_id: str,
    hub_topics: Iterable[str],
    *,
    operation_id: str = "compile-source-digest",
    mode: str | None = None,
    machine: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Compile one checked source into a checked digest plus hub suggestions."""
    vault = Path(vault)
    policy = load_operation_policy(vault, operation_id)
    runner = resolve_operation_runner(vault, policy, mode)
    _require_tool(policy, "trusted_writer")
    promotion_checks = required_promotion_checks(policy)

    source_id = _source_id(source_id)
    topics = [_topic_title(topic) for topic in hub_topics]
    if not 5 <= len(topics) <= 15:
        raise ValueError("hub_topics must contain 5 to 15 topics")

    source_ref = _source_ref(source_id)
    source_fm = _checked_source(vault, source_ref)
    _require_digestable_text(vault, source_fm, machine=machine)
    citation = state.compact_citation(vault, source_ref)
    content_rel = normalize_path(str(source_fm.get("content_path") or ""))
    content_path = vault / content_rel
    if not content_path.is_file():
        raise FileNotFoundError(content_path)

    digest_rel = f"works/{source_id}/digest.md"
    _require_path(policy, source_ref)
    _require_path(policy, content_rel)
    _require_path(policy, digest_rel)
    for topic in topics:
        _require_path(policy, f"hubs/{_topic_slug(topic)}.md")

    run_id = run_id or f"{operation_id}:{source_id}"
    started = append_journal_event(
        vault,
        {"event": "run", "run_id": run_id, "workflow": operation_id, "status": "started"},
        machine=machine,
    )

    content = safe_read(content_path)
    interviews = _source_interviews(vault, source_id)
    digest_prompt = _digest_prompt(source_fm, content, topics, interviews)
    digest_text = _run_digest_model(policy, runner, source_fm, content, topics, interviews)
    model_call = append_journal_event(
        vault,
        {
            "event": "model_call",
            "run_id": run_id,
            "mode": runner["mode"],
            "runner": runner["runner"],
            "provider": runner["provider"],
            "model": runner["model"],
            "model_params": runner["params"],
            "route": policy.get("route", "digest-compile"),
            "purpose": "digest_compile",
            "prompt_version": policy["prompt_version"],
            "prompt_hash": _sha256_text(digest_prompt),
            "toolset": policy["allowed_tools"],
            "fallback_used": False,
            "compression_used": False,
            "input_hash": _compile_input_hash(content_path, interviews),
            "output_hash": _sha256_text(digest_text),
        },
        machine=machine,
    )

    digest_frontmatter = {
        "type": "digest",
        "title": f"Digest: {source_fm['title']}",
        "description": source_fm["description"],
        "work_id": source_id,
        "tags": topics,
        "links": {},
        "evidence_set": [source_ref],
    }
    if citation:
        digest_frontmatter["citations"] = [citation]
    digest_stage = stage_concept(
        vault,
        digest_rel,
        concept_text(
            digest_frontmatter,
            f"Digest: {source_fm['title']}",
            digest_text,
        ),
        inputs=[
            {"id": source_ref, "sha256": _source_input_sha(vault, source_ref, source_fm)},
            {"id": content_rel, "sha256": sha256_file(content_path)},
            *[
                {
                    "id": row["turn_id"],
                    "sha256": row["turn_sha256"],
                    "role": "copi-interview",
                }
                for row in interviews
            ],
        ],
        operation=operation_id,
        run_id=run_id,
        machine=machine,
    )
    digest_check = promote_checked(vault, digest_rel, checks=promotion_checks, machine=machine)

    hub_suggestions = []
    hub_stage_events = []
    hub_checks = []
    hub_paths = []
    for topic in topics:
        hub_rel = f"hubs/{_topic_slug(topic)}.md"
        hub_exists = (vault / hub_rel).exists()
        hub_frontmatter = {
            "type": "hub",
            "title": topic,
            "description": f"Machine suggestion from {source_fm['title']}.",
            "tag": _topic_slug(topic),
            "tags": ["suggestion"],
            "links": {},
        }
        if citation:
            hub_frontmatter["citations"] = [citation]
        stage = stage_concept(
            vault,
            hub_rel,
            concept_text(
                hub_frontmatter,
                topic,
                f"Suggested update from `{digest_rel}`. Curated hubs are not overwritten.\n",
            ),
            inputs=[
                {"id": digest_rel, "sha256": digest_check["output_sha256"]},
                {"id": source_ref, "sha256": _source_input_sha(vault, source_ref, source_fm)},
            ],
            operation=operation_id,
            run_id=run_id,
            machine=machine,
        )
        hub_stage_events.append(stage)
        if hub_exists:
            hub_suggestions.append(stage["staging_id"])
            continue
        hub_checks.append(promote_checked(vault, hub_rel, checks=promotion_checks, machine=machine))
        hub_paths.append(hub_rel)

    finished = append_journal_event(
        vault,
        {
            "event": "run",
            "run_id": run_id,
            "workflow": operation_id,
            "status": "done",
            "outputs": [digest_rel, *hub_paths],
            "suggestions": hub_suggestions,
        },
        machine=machine,
    )
    commit = commit_writer_changes(
        vault, f"compile digest {source_id}", [digest_rel, *hub_paths], machine=machine
    )
    return {
        "run_id": run_id,
        "digest_path": digest_rel,
        "hub_paths": hub_paths,
        "hub_suggestions": hub_suggestions,
        "started": started,
        "model_call": model_call,
        "derived": digest_stage,
        "checked": digest_check,
        "hub_events": hub_stage_events,
        "hub_checked": hub_checks,
        "finished": finished,
        "commit": commit,
        "interview_count": len(interviews),
    }


def _checked_source(vault: Path, source_ref: str) -> dict[str, Any]:
    source_ref = _source_ref(source_ref)
    row = state.catalog_source(vault, source_ref)
    if row is None:
        raise FileNotFoundError(source_ref)
    if row.get("check_status") != "checked":
        raise ValueError(f"{source_ref} is not a checked source")
    return {
        "type": "source",
        "check_status": row["check_status"],
        "title": row["title"],
        "description": row.get("description") or row["title"],
        "source_id": f"catalog/sources/{row['source_id']}",
        "content_path": row["content_path"],
        "identifiers": row.get("identifiers") or {},
        "citekey": row.get("citekey") or "",
        "csl_json": row.get("csl_json") or {},
        "provider_coverage": row.get("provider_coverage") or "partial",
        "text_status": row.get("text_status") or "metadata-only",
        "normalized_text_sha256": row.get("normalized_text_sha256") or "",
        "raw_text_sha256": row.get("raw_text_sha256") or "",
    }


def _require_digestable_text(
    vault: Path, source_fm: dict[str, Any], *, machine: str | None = None
) -> None:
    text_status = str(source_fm.get("text_status") or "metadata-only")
    if text_status == "full-text":
        return
    attention_path = _write_digest_text_attention(vault, source_fm, text_status, machine=machine)
    raise ValueError(
        "checked digest requires full-text source content; "
        f"text_status is {text_status}; attention_path is {attention_path}"
    )


def _write_digest_text_attention(
    vault: Path, source_fm: dict[str, Any], text_status: str, *, machine: str | None
) -> str:
    source_ref = _source_ref(str(source_fm["source_id"]))
    source_id = _source_id(source_ref)
    rel = f"inbox/flag-digest-full-text-{safe_filename(source_id)}.md"
    path = vault / rel
    if path.exists():
        return rel
    title = f"Digest needs full text for {source_id}"
    finding = (
        "Digest compilation is blocked because the source has "
        f"`text_status: {text_status}` instead of `full-text`."
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        frontmatter_doc(
            {
                "title": title,
                "projection": "attention",
                "attention_kind": "flag",
                "attention_status": "open",
                "finding": finding,
                "agent_recommendation": "issues-found",
                "target": source_ref,
                "raised_by": "compile-source-digest",
                "loudness": "alert",
                "created": date.today().isoformat(),
            },
            (
                f"# Finding\n\n{finding}\n\n# Evidence\n\n"
                f"`{source_ref}` must acquire full text before digest compilation.\n"
            ),
        ),
        encoding="utf-8",
    )
    append_journal_event(
        vault,
        {
            "event": "check-fired",
            "check": "source-full-text",
            "status": "failed",
            "reason": finding,
            "target_id": source_ref,
            "attention_path": rel,
            "shadow": False,
            "route": "ask",
        },
        machine=machine,
    )
    commit_writer_changes(vault, f"flag digest full text {source_id}", [rel], machine=machine)
    return rel


def _source_input_sha(vault: Path, source_ref: str, source_fm: dict[str, Any]) -> str:
    source_ref = _source_ref(source_ref)
    return str(
        source_fm.get("normalized_text_sha256")
        or source_fm.get("raw_text_sha256")
        or _sha256_text(json.dumps(source_fm, sort_keys=True))
    )


def _prompt_input_refs(payload: dict[str, Any]) -> list[str]:
    raw = payload.get("input_refs")
    if raw is None:
        raw = payload.get("input_ref")
    if raw is None:
        return []
    if isinstance(raw, str):
        return [normalize_path(raw)]
    if not isinstance(raw, list):
        raise ValueError("input_refs must be a list")
    refs = []
    for item in raw:
        if isinstance(item, str):
            refs.append(normalize_path(item))
        elif isinstance(item, dict) and isinstance(item.get("id"), str):
            refs.append(normalize_path(item["id"]))
        else:
            raise ValueError("input_refs entries must be strings or objects with id")
    return refs


def _checked_prompt_input(vault: Path, relpath: str) -> tuple[str, dict[str, str]]:
    path = vault / normalize_path(relpath)
    if not path.is_file():
        raise FileNotFoundError(path)
    if state.concept_check_status(vault, normalize_path(relpath)) != "checked":
        raise ValueError(f"{relpath} is not checked")
    return safe_read(path), {"id": normalize_path(relpath), "sha256": sha256_file(path)}


def _prompt_text(vault: Path, policy: dict[str, Any], pattern: str, input_text: str) -> str:
    _require_untrusted_fields(str(policy.get("operation_id") or "<unknown>"), policy, ["input"])
    preamble_path = vault / "system/patterns/_preamble.md"
    preamble = preamble_path.read_text(encoding="utf-8") if preamble_path.is_file() else ""
    prompt = pattern.replace(
        "{{input}}",
        'the sealed data block named "input" below',
    )
    return "\n\n".join(
        part
        for part in [
            preamble.strip(),
            "---",
            prompt.strip(),
            _sealed_untrusted_block("input", input_text),
        ]
        if part
    ).strip()


def _run_prompt_model(
    policy: dict[str, Any], runner: dict[str, Any], prompt: str, input_text: str
) -> str:
    if runner["model"] == "deterministic-fixture":
        return _prompt_fixture_body(policy, input_text)
    if runner["runner"] == "pydantic-ai":
        return _pydantic_ai_chat(policy, runner, prompt)
    raise ValueError(f"unsupported operation runner: {runner['runner']}")


def _prompt_fixture_body(policy: dict[str, Any], input_text: str) -> str:
    excerpt = " ".join(input_text.split())[:700]
    return "\n\n".join(
        [
            f"## {policy['title']}",
            str(policy.get("description") or "").strip(),
            "## Input excerpt",
            excerpt,
            "## Review note",
            "Deterministic fixture output; review before promotion.",
        ]
    ).strip()


def _require_tool(policy: dict[str, Any], tool: str) -> None:
    if tool not in (policy.get("allowed_tools") or []):
        raise PermissionError(f"operation {policy['operation_id']} does not allow {tool}")


def _require_path(policy: dict[str, Any], path: str) -> None:
    rel = normalize_path(path)
    for raw_prefix in policy.get("allowed_paths") or []:
        prefix = normalize_path(str(raw_prefix)).rstrip("/")
        if rel == prefix or rel.startswith(prefix + "/"):
            return
    raise PermissionError(f"operation {policy['operation_id']} cannot access {rel}")


def _source_id(value: str) -> str:
    text = normalize_path(value).removeprefix("catalog/sources/").removesuffix("/source.md")
    source_id = safe_filename(text.strip("/")).strip("._-")
    if not source_id:
        raise ValueError("source_id is required")
    return source_id


def _source_ref(value: str) -> str:
    return f"catalog/sources/{_source_id(value)}"


def _topic_title(value: str) -> str:
    title = " ".join(str(value).split())
    if not title:
        raise ValueError("hub topic titles are required")
    return title


def _topic_slug(value: str) -> str:
    return safe_filename(value.lower().replace(" ", "-")).strip("._-")


def _source_interviews(vault: Path, source_ref: str) -> list[dict[str, Any]]:
    source_id = _source_id(source_ref)
    rows: list[dict[str, Any]] = []
    for path in sorted((vault / "journal").glob("*.jsonl")):
        for event in iter_jsonl(path):
            event_source = event.get("source_id")
            if event.get("event") != "copi-interview" or not isinstance(event_source, str):
                continue
            try:
                matches_source = _source_id(event_source) == source_id
            except ValueError:
                matches_source = False
            if not matches_source:
                continue
            if isinstance(event.get("turn_id"), str) and isinstance(event.get("turn_sha256"), str):
                rows.append(event)
    return sorted(rows, key=lambda row: str(row.get("timestamp") or ""))


def _compile_input_hash(content_path: Path, interviews: list[dict[str, Any]]) -> str:
    material = "\n".join([sha256_file(content_path), *[row["turn_sha256"] for row in interviews]])
    return _sha256_text(material)


def _digest_body(
    source_fm: dict[str, Any],
    content: str,
    topics: list[str],
    interviews: list[dict[str, Any]],
) -> str:
    excerpt = " ".join(content.split())[:500]
    bullets = "\n".join(f"- {topic}" for topic in topics)
    interview_text = ""
    if interviews:
        turns = "\n".join(f"- {row.get('response')}" for row in interviews)
        interview_text = f"\n## PI interview\n\n{turns}\n"
    return (
        f"Source: {source_fm['title']}\n\n"
        f"## Synthesis\n\n{excerpt}\n\n"
        f"{interview_text}"
        f"## Hub suggestions\n\n{bullets}\n"
    )


def _run_digest_model(
    policy: dict[str, Any],
    runner: dict[str, Any],
    source_fm: dict[str, Any],
    content: str,
    topics: list[str],
    interviews: list[dict[str, Any]],
) -> str:
    if runner["model"] == "deterministic-fixture":
        text = _digest_body(source_fm, content, topics, interviews)
    else:
        _require_untrusted_fields(
            str(policy.get("operation_id") or "<unknown>"),
            policy,
            ["source_text", "pi_interview_notes"],
        )
        prompt = _digest_prompt(source_fm, content, topics, interviews)
        if runner["runner"] == "pydantic-ai":
            text = _pydantic_ai_chat(policy, runner, prompt)
        else:
            raise ValueError(f"unsupported operation runner: {runner['runner']}")
    return _validate_digest_output(text, content, topics, interviews)


def _digest_prompt(
    source_fm: dict[str, Any],
    content: str,
    topics: list[str],
    interviews: list[dict[str, Any]],
) -> str:
    interview_text = "\n".join(f"- {row.get('response')}" for row in interviews)
    return "\n\n".join(
        [
            "Compile a source-grounded Memoria digest. Use only the supplied source text and PI "
            "interview notes. Return markdown body only, with ## Synthesis and ## Hub suggestions "
            "sections. Do not return YAML frontmatter.",
            f"Title: {source_fm['title']}",
            f"Description: {source_fm['description']}",
            "Hub topics:\n" + "\n".join(f"- {topic}" for topic in topics),
            _sealed_untrusted_block("pi_interview_notes", interview_text or "- none"),
            _sealed_untrusted_block("source_text", " ".join(content.split())),
        ]
    )


def _sealed_untrusted_block(name: str, text: str) -> str:
    return "\n".join(
        [
            f'<memoria_untrusted_data name="{name}">',
            text,
            "</memoria_untrusted_data>",
        ]
    )


def _pydantic_ai_chat(policy: dict[str, Any], runner: dict[str, Any], prompt: str) -> str:
    base_url = str(runner["base_url"])
    _require_network(policy, base_url)
    key_env = runner.get("key_env")
    if isinstance(key_env, str) and key_env:
        api_key = os.environ.get(key_env)
    else:
        api_key = (
            os.environ.get("MEMORIA_MODEL_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or os.environ.get("KILOCODE_API_KEY")
        )
    Agent, OpenAIChatModel, OpenAIProvider = _load_pydantic_ai_openai()
    provider_kwargs = {"base_url": base_url}
    if api_key:
        provider_kwargs["api_key"] = api_key
    model = OpenAIChatModel(runner["model"], provider=OpenAIProvider(**provider_kwargs))
    agent = Agent(model)
    params = runner.get("params") if isinstance(runner.get("params"), dict) else {}
    settings = {
        "temperature": params.get("temperature", 0),
        "max_tokens": int(
            params.get("max_tokens", os.environ.get("MEMORIA_MODEL_MAX_TOKENS", 2048))
        ),
        "timeout": float(params.get("timeout", os.environ.get("MEMORIA_MODEL_TIMEOUT", 90))),
    }
    try:
        result = agent.run_sync(prompt, model_settings=settings)
    except Exception as exc:
        raise RuntimeError(f"pydantic-ai model request failed: {exc}") from exc
    text = str(getattr(result, "output", "") or "").strip()
    if not text:
        raise RuntimeError("pydantic-ai model returned no message content")
    return text


def _load_pydantic_ai_openai() -> tuple[Any, Any, Any]:
    try:
        from pydantic_ai import Agent
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider
    except ImportError as exc:
        raise RuntimeError("pydantic-ai runner requires pydantic-ai-slim[openai]") from exc
    return Agent, OpenAIChatModel, OpenAIProvider


def _validate_digest_output(
    text: str, content: str, topics: list[str], interviews: list[dict[str, Any]]
) -> str:
    stripped = text.strip()
    if not stripped:
        raise ValueError("digest output is required")
    if stripped.startswith("---"):
        raise ValueError("digest output must be markdown body, not frontmatter")
    for heading in ("## Synthesis", "## Hub suggestions"):
        if heading not in stripped:
            raise ValueError(f"digest output must include {heading}")
    expected_terms = _significant_terms(
        content, *topics, *[str(row.get("response") or "") for row in interviews]
    )
    observed_terms = _significant_terms(stripped)
    if expected_terms and len(expected_terms & observed_terms) < min(2, len(expected_terms)):
        raise ValueError("digest output failed source-grounding smoke check")
    return stripped


def _significant_terms(*values: str) -> set[str]:
    stopwords = {
        "about",
        "content",
        "digest",
        "source",
        "suggestion",
        "suggestions",
        "synthesis",
    }
    terms = set()
    for value in values:
        terms.update(
            term
            for term in re.findall(r"[A-Za-z][A-Za-z0-9-]{3,}", value.casefold())
            if term not in stopwords
        )
    return terms


def _require_network(policy: dict[str, Any], base_url: str) -> None:
    for allowed in _allowed_network_prefixes(policy):
        if _network_target(base_url).startswith(allowed):
            return
    raise PermissionError(f"operation {policy['operation_id']} cannot access {base_url}")


def require_allowed_network(policy: dict[str, Any], target_url: str) -> None:
    _require_network(policy, target_url)


def network_allowed(policy: dict[str, Any], target_url: str) -> bool:
    return any(
        _network_target(target_url).startswith(prefix)
        for prefix in _allowed_network_prefixes(policy)
    )


def _allowed_network_prefixes(policy: dict[str, Any]) -> list[str]:
    prefixes = []
    for value in policy.get("allowed_network") or []:
        text = str(value).strip()
        if not text:
            continue
        prefixes.append(text if text.endswith("://") else text.rstrip("/") + "/")
    return prefixes


def _network_target(target_url: str) -> str:
    text = str(target_url).strip()
    return text if text.endswith("://") else text.rstrip("/") + "/"


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()
