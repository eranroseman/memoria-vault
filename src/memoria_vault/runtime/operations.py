"""Alpha.11 operation runner primitives."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any
from urllib import error, request

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
from memoria_vault.runtime.vaultio import read_frontmatter, safe_read

REQUIRED_POLICY_FIELDS = {
    "operation_id",
    "allowed_tools",
    "allowed_paths",
    "allowed_network",
    "runner",
    "model",
    "prompt_version",
    "io_schema",
    "risk_class",
    "required_checks",
}


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
    source_rel = f"catalog/sources/{_source_id(source_id)}/source.md"
    _checked_source(vault, source_rel)
    answer = response.strip()
    if not answer:
        raise ValueError("response is required")
    question = prompt.strip() or "What matters about this source?"
    body = f"{source_rel}\n{project_id.strip()}\n{question}\n{answer}"
    turn_sha = _sha256_text(body)
    event = append_journal_event(
        vault,
        {
            "event": "copi-interview",
            "run_id": run_id or f"copi-interview:{Path(source_rel).parent.name}",
            "source_id": source_rel,
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
        f"record copi interview {Path(source_rel).parent.name}",
        [],
        machine=machine,
    )
    return {"event": event, "commit": commit}


def load_operation_policy(vault: Path, operation_id: str) -> dict[str, Any]:
    """Load a checked operation Concept and require the WP5 policy contract."""
    vault = Path(vault)
    op_path = vault / "capabilities" / "operations" / f"{safe_filename(operation_id)}.md"
    if not op_path.is_file():
        raise FileNotFoundError(op_path)
    policy = read_frontmatter(op_path)
    if policy.get("type") != "operation":
        raise ValueError(f"{operation_id} is not an operation Concept")
    if policy.get("check_status") != "checked":
        raise ValueError(f"{operation_id} is not checked")
    missing = sorted(field for field in REQUIRED_POLICY_FIELDS if field not in policy)
    if missing:
        raise ValueError(f"{operation_id} missing operation policy fields: {', '.join(missing)}")
    io_schema = policy["io_schema"]
    if not isinstance(io_schema, dict):
        raise ValueError(f"{operation_id} io_schema must be a map")
    for key in ("input", "output"):
        value = io_schema.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{operation_id} io_schema.{key} must be a non-empty string")
    return policy


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


def compile_source_digest(
    vault: Path,
    source_id: str,
    hub_topics: Iterable[str],
    *,
    operation_id: str = "compile-source-digest",
    machine: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Compile one checked source into a checked digest plus hub suggestions."""
    vault = Path(vault)
    policy = load_operation_policy(vault, operation_id)
    _require_tool(policy, "trusted_writer")
    promotion_checks = required_promotion_checks(policy)

    source_id = _source_id(source_id)
    topics = [_topic_title(topic) for topic in hub_topics]
    if not 5 <= len(topics) <= 15:
        raise ValueError("hub_topics must contain 5 to 15 topics")

    source_rel = f"catalog/sources/{source_id}/source.md"
    source_fm = _checked_source(vault, source_rel)
    content_rel = normalize_path(str(source_fm.get("content_path") or ""))
    content_path = vault / content_rel
    if not content_path.is_file():
        raise FileNotFoundError(content_path)

    digest_rel = f"knowledge/digests/{source_id}.md"
    _require_path(policy, source_rel)
    _require_path(policy, content_rel)
    _require_path(policy, digest_rel)
    for topic in topics:
        _require_path(policy, f"knowledge/hubs/{_topic_slug(topic)}.md")

    run_id = run_id or f"{operation_id}:{source_id}"
    started = append_journal_event(
        vault,
        {"event": "run", "run_id": run_id, "workflow": operation_id, "status": "started"},
        machine=machine,
    )

    content = safe_read(content_path)
    interviews = _source_interviews(vault, source_rel)
    digest_text = _run_digest_model(policy, source_fm, content, topics, interviews)
    model_call = append_journal_event(
        vault,
        {
            "event": "model_call",
            "run_id": run_id,
            "runner": policy["runner"],
            "provider": policy.get("provider", "local"),
            "model": policy["model"],
            "route": policy.get("route", "digest-compile"),
            "purpose": "digest_compile",
            "prompt_version": policy["prompt_version"],
            "toolset": policy["allowed_tools"],
            "fallback_used": False,
            "compression_used": False,
            "input_hash": _compile_input_hash(content_path, interviews),
            "output_hash": _sha256_text(digest_text),
        },
        machine=machine,
    )

    digest_stage = stage_concept(
        vault,
        digest_rel,
        _concept_text(
            {
                "type": "digest",
                "check_status": "unchecked",
                "title": f"Digest: {source_fm['title']}",
                "description": source_fm["description"],
                "source_id": f"catalog/sources/{source_id}",
                "confidence": "medium",
                "evidence_set": [source_rel],
                "massw": {
                    "context": source_fm["title"],
                    "key_idea": topics[0],
                    "method": "compile-source-digest",
                    "outcome": topics[1],
                    "projected_impact": topics[2],
                },
            },
            f"Digest: {source_fm['title']}",
            digest_text,
        ),
        inputs=[
            {"id": source_rel, "sha256": sha256_file(vault / source_rel)},
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
        hub_rel = f"knowledge/hubs/{_topic_slug(topic)}.md"
        hub_exists = (vault / hub_rel).exists()
        stage = stage_concept(
            vault,
            hub_rel,
            _concept_text(
                {
                    "type": "hub",
                    "check_status": "unchecked",
                    "title": topic,
                    "description": f"Machine suggestion from {source_fm['title']}.",
                    "members": [digest_rel, source_rel],
                    "confidence": "low",
                    "tags": ["suggestion"],
                },
                topic,
                f"Suggested update from `{digest_rel}`. Curated hubs are not overwritten.\n",
            ),
            inputs=[
                {"id": digest_rel, "sha256": digest_check["output_sha256"]},
                {"id": source_rel, "sha256": sha256_file(vault / source_rel)},
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


def _checked_source(vault: Path, source_rel: str) -> dict[str, Any]:
    source_path = vault / source_rel
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    frontmatter = read_frontmatter(source_path)
    if frontmatter.get("type") != "source" or frontmatter.get("check_status") != "checked":
        raise ValueError(f"{source_rel} is not a checked source")
    return frontmatter


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


def _topic_title(value: str) -> str:
    title = " ".join(str(value).split())
    if not title:
        raise ValueError("hub topic titles are required")
    return title


def _topic_slug(value: str) -> str:
    return safe_filename(value.lower().replace(" ", "-")).strip("._-")


def _source_interviews(vault: Path, source_rel: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted((vault / "journal").glob("*.jsonl")):
        for event in iter_jsonl(path):
            if event.get("event") != "copi-interview" or event.get("source_id") != source_rel:
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
    source_fm: dict[str, Any],
    content: str,
    topics: list[str],
    interviews: list[dict[str, Any]],
) -> str:
    if policy["model"] == "deterministic-fixture":
        text = _digest_body(source_fm, content, topics, interviews)
    else:
        prompt = _digest_prompt(source_fm, content, topics, interviews)
        if policy["runner"] == "direct_api":
            text = _direct_api_chat(policy, prompt)
        elif policy["runner"] == "hermes":
            text = _hermes_chat(policy, prompt)
        else:
            raise ValueError(f"unsupported operation runner: {policy['runner']}")
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
            "PI interview notes:\n" + (interview_text or "- none"),
            "Source text:\n" + " ".join(content.split()),
        ]
    )


def _direct_api_chat(policy: dict[str, Any], prompt: str) -> str:
    base_url = (
        os.environ.get("MEMORIA_MODEL_BASE_URL")
        or os.environ.get("OPENAI_BASE_URL")
        or "https://api.openai.com/v1"
    ).rstrip("/")
    _require_network(policy, base_url)
    payload = {
        "model": policy["model"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": int(os.environ.get("MEMORIA_MODEL_MAX_TOKENS", "2048")),
    }
    api_key = (
        os.environ.get("MEMORIA_MODEL_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("KILOCODE_API_KEY")
    )
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with request.urlopen(
            req, timeout=float(os.environ.get("MEMORIA_MODEL_TIMEOUT", "90"))
        ) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (OSError, error.HTTPError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"direct_api model request failed: {exc}") from exc
    content = ((data.get("choices") or [{}])[0].get("message") or {}).get("content")
    text = str(content or "").strip()
    if not text:
        raise RuntimeError("direct_api model returned no message content")
    return text


def _hermes_chat(policy: dict[str, Any], prompt: str) -> str:
    base_url = os.environ.get("MEMORIA_HERMES_BASE_URL") or str(policy.get("base_url") or "")
    if base_url:
        _require_network(policy, base_url)
    else:
        _require_network_label(policy, "hermes-config")

    agent_cls = _hermes_agent_class()
    agent = agent_cls(
        model=policy["model"],
        provider=policy.get("provider") or os.environ.get("MEMORIA_HERMES_PROVIDER") or None,
        base_url=base_url or None,
        api_key=os.environ.get("MEMORIA_HERMES_API_KEY") or None,
        enabled_toolsets=_hermes_enabled_toolsets(policy),
        quiet_mode=True,
        skip_context_files=True,
        skip_memory=True,
        max_iterations=int(
            os.environ.get("MEMORIA_HERMES_MAX_ITERATIONS") or policy.get("max_iterations") or 10
        ),
    )
    text = str(agent.chat(prompt) or "").strip()
    if not text:
        raise RuntimeError("hermes model returned no message content")
    return text


def _hermes_agent_class():
    try:
        from run_agent import AIAgent

        return AIAgent
    except ModuleNotFoundError:
        hermes_path = Path(
            os.environ.get("MEMORIA_HERMES_AGENT_PATH", "~/.hermes/hermes-agent")
        ).expanduser()
        if hermes_path.is_dir() and str(hermes_path) not in sys.path:
            sys.path.insert(0, str(hermes_path))
        try:
            from run_agent import AIAgent

            return AIAgent
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "hermes operation runner requires the Hermes Python library "
                "or MEMORIA_HERMES_AGENT_PATH"
            ) from exc


def _hermes_enabled_toolsets(policy: dict[str, Any]) -> list[str]:
    value = policy.get("hermes_enabled_toolsets", [])
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError("hermes_enabled_toolsets must be a list of toolset names")
    forbidden = {
        "all",
        "browser",
        "computer_use",
        "development",
        "file",
        "full_stack",
        "hermes-cli",
        "terminal",
    }
    selected = [item.strip() for item in value if item.strip()]
    unsafe = sorted(
        item for item in selected if item in forbidden or item.startswith(("hermes-", "mcp-"))
    )
    if unsafe:
        raise PermissionError(
            "hermes operation runner cannot enable write-capable or external toolsets: "
            + ", ".join(unsafe)
        )
    return selected


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
    for allowed in policy.get("allowed_network") or []:
        if base_url.startswith(str(allowed).rstrip("/")):
            return
    raise PermissionError(f"operation {policy['operation_id']} cannot access {base_url}")


def require_allowed_network(policy: dict[str, Any], target_url: str) -> None:
    _require_network(policy, target_url)


def _require_network_label(policy: dict[str, Any], label: str) -> None:
    allowed = {str(value).strip().rstrip("/") for value in policy.get("allowed_network") or []}
    if label in allowed:
        return
    raise PermissionError(f"operation {policy['operation_id']} cannot access {label}")


def _concept_text(frontmatter: dict[str, Any], title: str, body: str) -> str:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - packaged deployments install PyYAML.
        raise RuntimeError("operation runner requires PyYAML to write frontmatter") from exc

    rendered = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{rendered}\n---\n# {title}\n\n{body.rstrip()}\n"


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()
